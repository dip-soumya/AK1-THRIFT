"""
page.py  -  the scrolling canvas every screen is built on.

  * smooth inertial wheel scrolling (frame-rate independent lerp)
  * scroll-triggered reveals: register(y, fn) fires once when y enters the viewport
  * parallax layers, scroll progress bar, back-to-top, pinned HUD layer (the fox lives here)
  * Zone system: robust hover / click / drag hit-testing for canvas-drawn widgets
    (no Enter/Leave flicker between child items)
"""
import tkinter as tk

from . import theme
from .anim import mix
from .theme import F


class Zone:
    __slots__ = ("bbox", "click", "enter", "leave", "press", "drag", "release", "hud", "z",
                 "cursor", "active", "hovered")

    def __init__(self, bbox, click=None, enter=None, leave=None, press=None, drag=None, release=None,
                 hud=False, z=0, cursor="hand2", active=None):
        self.bbox = bbox            # tuple or callable -> (x1, y1, x2, y2)
        self.click, self.enter, self.leave = click, enter, leave
        self.press, self.drag, self.release = press, drag, release
        self.hud, self.z, self.cursor = hud, z, cursor
        self.active = active
        self.hovered = False

    def box(self):
        return self.bbox() if callable(self.bbox) else self.bbox


class Page(tk.Frame):
    key = "page"
    title = "PAGE"
    bg = theme.PAPER
    fox_lines = "home"

    def __init__(self, app, **kw):
        super().__init__(app.stage, bg=self.bg, highlightthickness=0)
        self.app = app
        self.E = app.anim
        self.A = app.assets
        self.W = app.W
        self.H = app.stage_h
        self.kw = kw
        self.alive = True
        self.cv = tk.Canvas(self, width=self.W, height=self.H, bg=self.bg, highlightthickness=0,
                            bd=0, yscrollincrement=1, confine=True)
        self.cv.pack(fill="both", expand=True)
        self.y = 0.0
        self.target = 0.0
        self.applied = 0
        self.content_h = self.H
        self.velocity = 0.0
        self._scroll_loop = None
        self.reveals = []
        self.parallax = []
        self.hud_listeners = []
        self.scroll_listeners = []
        self.zones = []
        self.hzones = []         # horizontal-swipe targets: (bbox_fn, handler(dx_px))
        self.warm = []           # (y, fn) expensive image prep to run in idle time, nearest first
        self.windows = []
        self.win_want = {}
        self.keep = []           # PhotoImage refs
        self.hover = None
        self.pressed = None
        self.press_xy = (0, 0)
        self.dragging = False
        self.mouse = (-1, -1)
        self.modal = None
        self.fox = None
        cv = self.cv
        cv.bind("<Motion>", self._on_motion)
        cv.bind("<Leave>", lambda e: self._set_hover(None))
        cv.bind("<ButtonPress-1>", self._on_press)
        cv.bind("<B1-Motion>", self._on_drag)
        cv.bind("<ButtonRelease-1>", self._on_release)

    # ================================================================== #
    #  lifecycle
    # ================================================================== #
    def build(self):
        """Override: draw the page, set self.content_h."""

    def finalize(self):
        self.content_h = max(self.H, int(self.content_h))
        self.cv.configure(scrollregion=(0, 0, self.W, self.content_h))
        self._build_hud()
        self.raise_hud()

    def on_enter(self):
        """Called when the transition curtain has fully lifted."""
        self._check_reveals()
        self._start_warmup()
        if self.fox:
            self.fox.enter(delay=150)
            self.E.after(900, lambda: self.fox.say(self.fox.next_line()), owner=self)
            self._fox_timer()

    def _start_warmup(self):
        """Prepare card photos / baked text in the background (never while you are scrolling),
        so a section that scrolls into view only has cheap work left to do."""
        if not self.warm:
            return
        self.warm.sort(key=lambda t: t[0])

        def step(dt, now):
            if not self.warm:
                return False
            if self._scroll_loop is not None:      # scrolling: stay out of the way
                return True
            t0 = self.E.now()
            while self.warm and self.E.now() - t0 < 0.006:
                vy = self.applied
                i = min(range(len(self.warm)), key=lambda k: abs(self.warm[k][0] - vy))
                _, fn = self.warm.pop(i)
                try:
                    fn()
                except Exception:  # noqa: BLE001
                    pass
            return bool(self.warm)
        self.E.frame(step, owner=self)

    def _fox_timer(self):
        def tick():
            if self.alive and self.fox and self.fox.bubble is None and self.modal is None:
                self.fox.say(self.fox.next_line())
            if self.alive:
                self._fox_timer()
        self.E.after(26000, tick, owner=self)

    def teardown(self):
        self.alive = False
        try:
            self.destroy()
        except tk.TclError:
            pass

    # ================================================================== #
    #  scrolling
    # ================================================================== #
    @property
    def max_scroll(self):
        return max(0, self.content_h - self.H)

    def on_wheel(self, e):
        if self.modal is not None:
            return
        self.scroll_by(-e.delta * 1.05)

    def hzone(self, bbox, handler):
        """Register a horizontally scrollable area (rail, carousel...) for touchpad swipes."""
        self.hzones.append((bbox, handler))

    def on_hwheel(self, e):
        """Sideways touchpad swipe / shift+wheel. Positive dx = reveal content to the right."""
        if self.modal is not None or not self.hzones:
            return
        try:
            mx = self.cv.winfo_pointerx() - self.cv.winfo_rootx()
            my = self.cv.winfo_pointery() - self.cv.winfo_rooty()
        except tk.TclError:
            return
        cy = my + self.applied
        dx = -e.delta * 1.1
        for bbox, handler in reversed(self.hzones):
            x1, y1, x2, y2 = bbox() if callable(bbox) else bbox
            if x1 <= mx <= x2 and y1 <= cy <= y2:
                handler(dx)
                return

    def scroll_by(self, d):
        self.scroll_to(self.target + d)

    def scroll_to(self, y, instant=False):
        self.target = max(0.0, min(self.max_scroll, y))
        if instant:
            self.y = self.target
            self._apply()
            return
        if self._scroll_loop is None:
            self._scroll_loop = self.E.frame(self._scroll_step, owner=self)

    def _scroll_step(self, dt, now):
        prev = self.y
        k = 1 - pow(0.000005, dt)        # ~ 18% per 16ms frame: responsive, still smooth
        self.y += (self.target - self.y) * k
        if abs(self.target - self.y) < 0.6:
            self.y = self.target
        self.velocity = (self.y - prev) / max(dt, 1e-3)
        self._apply()
        if self.y == self.target:
            self.velocity = 0.0
            self._scroll_loop = None
            return False
        return True

    def _apply(self):
        yi = int(round(self.y))
        dy = yi - self.applied
        if dy == 0:
            return
        self.cv.yview_scroll(dy, "units")
        self.applied = yi
        self.cv.move("hud", 0, dy)
        for fn in self.hud_listeners:
            fn(dy)
        for tag, f in self.parallax:
            self.cv.move(tag, 0, dy * f)
        for fn in self.scroll_listeners:
            fn(yi)
        self._update_progress()
        self._check_reveals()
        self._frame_n = getattr(self, "_frame_n", 0) + 1
        if self.mouse[0] >= 0 and (self._frame_n % 3 == 0 or self.y == self.target):
            self._hit_update(*self.mouse)

    def add_parallax(self, tag, factor):
        self.parallax.append((tag, factor))

    # ================================================================== #
    #  reveals
    # ================================================================== #
    def reveal_at(self, y, fn, offset=90):
        self.reveals.append([y + offset, fn, False])

    def _check_reveals(self):
        bottom = self.applied + self.H
        fired = False
        for r in self.reveals:
            if not r[2] and r[0] <= bottom:
                r[2] = True
                fired = True
                try:
                    r[1]()
                except tk.TclError:
                    pass
        if fired:
            self.raise_hud()

    def reveal_all(self):
        for r in self.reveals:
            if not r[2]:
                r[2] = True
                r[1]()
        self.raise_hud()

    def raise_hud(self):
        self.cv.tag_raise("hud")
        self.cv.tag_raise("modal")

    def visible(self, y1, y2):
        return y2 >= self.applied and y1 <= self.applied + self.H

    # ================================================================== #
    #  zones (hover / click / drag)
    # ================================================================== #
    def zone(self, bbox, **kw):
        z = Zone(bbox, **kw)
        self.zones.append(z)
        return z

    def remove_zone(self, z):
        if z in self.zones:
            self.zones.remove(z)
        if self.hover is z:
            self.hover = None

    def _hit(self, x, y):
        cy = y + self.applied
        best = None
        modal = self.modal is not None
        for z in self.zones:
            if modal and z.z < 100:
                continue
            if z.active is not None and not z.active():
                continue
            x1, y1, x2, y2 = z.box()
            py = y if z.hud else cy
            if x1 <= x <= x2 and y1 <= py <= y2:
                if best is None or z.z >= best.z:
                    best = z
        return best

    def _set_hover(self, z):
        if z is self.hover:
            return
        old, self.hover = self.hover, z
        if old is not None:
            old.hovered = False
        if z is not None:
            z.hovered = True
        if old is not None and old.leave:
            old.leave()
        if z is not None and z.enter:
            z.enter()
        self.cv.configure(cursor=(z.cursor if z else ""))

    def _hit_update(self, x, y):
        if self.pressed is not None and self.dragging:
            return
        self._set_hover(self._hit(x, y))

    def _on_motion(self, e):
        self.mouse = (e.x, e.y)
        self._hit_update(e.x, e.y)

    def _on_press(self, e):
        self.cv.focus_set()
        z = self._hit(e.x, e.y)
        self.pressed = z
        self.press_xy = (e.x, e.y)
        self.dragging = False
        if z is not None and z.press:
            z.press(e.x, e.y)

    def _on_drag(self, e):
        z = self.pressed
        if z is None:
            return
        dx = e.x - self.press_xy[0]
        if not self.dragging and abs(dx) > 6 and z.drag:
            self.dragging = True
        if self.dragging and z.drag:
            z.drag(e.x, e.y)

    def _on_release(self, e):
        z = self.pressed
        self.pressed = None
        if z is None:
            return
        if self.dragging:
            self.dragging = False
            if z.release:
                z.release(e.x, e.y)
            self._hit_update(e.x, e.y)
            return
        if z.release:
            z.release(e.x, e.y)
        if z.click and self._hit(e.x, e.y) is z:
            z.click()

    # ================================================================== #
    #  embedded tk widgets (Entry etc.)
    # ================================================================== #
    def add_window(self, x, y, widget, **kw):
        wid = self.cv.create_window(x, y, window=widget, **kw)
        self.windows.append(wid)
        self.win_want[wid] = True
        return wid

    def set_window(self, wid, on):
        self.win_want[wid] = on
        if self.modal is None:
            self.cv.itemconfigure(wid, state="normal" if on else "hidden")

    def show_windows(self, on):
        for w in self.windows:
            try:
                vis = on and self.win_want.get(w, True)
                self.cv.itemconfigure(w, state="normal" if vis else "hidden")
            except tk.TclError:
                pass

    # ================================================================== #
    #  HUD: progress bar, back-to-top, fox
    # ================================================================== #
    def _build_hud(self):
        cv = self.cv
        self._prog = cv.create_rectangle(0, 0, 0, 4, fill=theme.ACCENT, outline="", tags=("hud",))
        if self.max_scroll > 0:
            self._build_top_button()
        lines = __import__("ak1.data", fromlist=["FOX"]).FOX.get(self.fox_lines, [])
        if lines:
            from .fox import Fox
            self.fox = Fox(self, self.W - 92, self.H - 8, scale=0.82, hud=True, side="left",
                           lines=lines, bg=self.bg)
            self.fox.enter_y = 220
            fx = self.fox
            self.zone(lambda: (fx.bbox()[0], fx.bbox()[1] - self.applied, fx.bbox()[2], fx.bbox()[3] - self.applied),
                      click=fx.poke, hud=True, z=50)

    def _build_top_button(self):
        cv = self.cv
        x, y, r = 40, self.H - 40, 24
        t = ("hud", "totop")
        self._top_c = cv.create_oval(x - r, y - r, x + r, y + r, fill=theme.INK, outline=theme.INK, tags=t)
        self._top_a = cv.create_text(x, y - 1, text="↑", font=F("heavy", 18), fill=theme.BONE, tags=t)
        cv.itemconfigure("totop", state="hidden")
        self._top_shown = False

        def enter():
            cv.itemconfigure(self._top_c, fill=theme.ACCENT, outline=theme.ACCENT)
        def leave():
            cv.itemconfigure(self._top_c, fill=theme.INK, outline=theme.INK)
        self.zone((x - r, y - r, x + r, y + r), click=lambda: self.scroll_to(0), enter=enter, leave=leave,
                  hud=True, z=40, active=lambda: self._top_shown)

    def _update_progress(self):
        ms = self.max_scroll
        p = self.applied / ms if ms else 0
        cv = self.cv
        cv.coords(self._prog, 0, self.applied, self.W * p, self.applied + 4)
        show = self.applied > self.H * 0.8
        if hasattr(self, "_top_c") and show != self._top_shown:
            self._top_shown = show
            cv.itemconfigure("totop", state="normal" if show else "hidden")
            if show:
                y0 = self.applied + self.H - 40
                cv.coords(self._top_c, 16, y0 - 24, 64, y0 + 24)
                cv.coords(self._top_a, 40, y0 - 1)
                # pop in
                from .anim import move
                cv.move("totop", 0, 60)
                move(self.E, cv, "totop", 0, -60, duration=500, easing="outBack", owner=self)

    def fox_say(self, kind):
        import random
        from .data import FOX
        if self.fox and FOX.get(kind):
            self.fox.hop()
            self.fox.say(random.choice(FOX[kind]))
