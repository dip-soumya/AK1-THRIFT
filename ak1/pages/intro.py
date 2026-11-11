"""INTRO - splash: revolving wordmark, real preload counter, Fitz says hello."""
import random

from .. import theme
from ..anim import mix, move
from ..data import FOX, QUOTES
from ..fox import Fox
from ..page import Page
from ..theme import F
from ..widgets import Button, Letters, RotatingBadge


class IntroPage(Page):
    key = "intro"
    title = "AK1"
    bg = theme.INK
    fox_lines = "none"

    def build(self):
        cv, W, H = self.cv, self.W, self.H
        self.content_h = H
        cv.create_rectangle(0, 0, W, H, fill=theme.INK, outline="")
        for gx in range(0, W, 80):
            cv.create_line(gx, 0, gx, H, fill="#141414")
        q, a = QUOTES[2]
        self.q1 = cv.create_text(56, 56, text="“" + q + "”", font=F("serif", 24, "italic"), fill=theme.INK,
                                 anchor="nw", width=520)
        self.q2 = cv.create_text(58, 130, text="— " + a, font=F("mono", 11, "bold"), fill=theme.INK, anchor="nw")
        self.badge = RotatingBadge(self, W - 150, 150, 74, "EST. 2026 • PRE-LOVED • AK1 THRIFT • ",
                                   theme.INK, fill=theme.LIME, center="★", font=F("mono", 12, "bold"), speed=0.7)
        wf = F("display", 230)
        base = H * 0.60
        a_w = theme.measure(wf, "AK1")
        t_w = theme.measure(wf, "THRIFT")
        gap = 34
        x0 = (W - (a_w + gap + t_w)) / 2
        self.l1 = Letters(self, x0, base, "AK1", wf, theme.ACCENT, theme.INK)
        self.l2 = Letters(self, x0 + a_w + gap, base, "THRIFT", wf, theme.BONE, theme.INK)
        self.tag = cv.create_text(W / 2, base - 30, text="P R E - L O V E D   ·   R E - W O R N   ·   R E - D E F I N E D",
                                  font=F("mono", 14, "bold"), fill=theme.INK)
        # loading counter
        self.count = cv.create_text(W - 56, H - 40, text="000", font=F("display", 110), fill=theme.INK, anchor="se")
        self.count_lab = cv.create_text(W - 56, H - 30, text="LOADING THE RACKS", font=F("mono", 11, "bold"),
                                        fill=theme.INK, anchor="ne")
        self.bar = cv.create_rectangle(0, H - 6, 0, H, fill=theme.ACCENT, outline="")
        self.p_target = 0.0
        self.p_shown = 0.0
        self.loaded = False
        self.btn = Button(self, W / 2, base + 52, "ENTER THE STORE", self.app.enter_store, kind="accent",
                          anchor="center", shadow=theme.BONE, h=64, font=F("display", 26), w=360)
        self.btn.set_visible(False)
        self.fox = Fox(self, 150, H - 6, scale=1.45, hud=False, side="right", lines=FOX["intro"], bg=theme.INK)
        self.fox.enter_y = 260
        fx = self.fox
        self.zone(lambda: fx.bbox(), click=fx.poke, z=50)
        self.app.root.bind("<Return>", lambda e: self.loaded and self.app.enter_store())

    def finalize(self):
        self.cv.configure(scrollregion=(0, 0, self.W, self.H))

    def on_enter(self):
        cv, E = self.cv, self.E
        self.l1.play(delay=200, mode="revolve", step=90, dur=1200)
        self.l2.play(delay=480, mode="revolve", step=90, dur=1200)
        E.animate(900, lambda e: cv.itemconfigure(self.tag, fill=mix(theme.INK, theme.LIME, e)), delay=1300, owner=self)
        E.animate(1200, lambda e: (cv.itemconfigure(self.q1, fill=mix(theme.INK, theme.BONE, e)),
                                   cv.itemconfigure(self.q2, fill=mix(theme.INK, "#8a857b", e))), delay=600, owner=self)
        E.animate(700, lambda e: (cv.itemconfigure(self.count, fill=mix(theme.INK, theme.BONE, e)),
                                  cv.itemconfigure(self.count_lab, fill=mix(theme.INK, "#8a857b", e))), delay=300,
                  owner=self)
        self.badge.pop(delay=700)
        self.fox.enter(delay=900, frm=260)
        E.after(1900, lambda: self.fox.say(random.choice(FOX["intro"][:2]), hold=7000), owner=self)
        E.frame(self._count_tick, owner=self)
        self.queue = self.A.all_images()
        self.total = max(1, len(self.queue))
        E.after(400, self._load_some, owner=self)

    def _load_some(self):
        for _ in range(3):
            if not self.queue:
                break
            cat, pid = self.queue.pop(0)
            self.A.pil(cat, pid)
        self.p_target = 1 - len(self.queue) / self.total
        if self.queue:
            self.E.after(1, self._load_some, owner=self)

    def _count_tick(self, dt, now):
        cv = self.cv
        self.p_shown += (self.p_target - self.p_shown) * min(1, dt * 5)
        if self.p_target >= 1 and self.p_shown > 0.995:
            self.p_shown = 1.0
        cv.itemconfigure(self.count, text=f"{int(self.p_shown * 100):03d}")
        cv.coords(self.bar, 0, self.H - 6, self.W * self.p_shown, self.H)
        if self.p_shown >= 1.0 and not self.loaded:
            self.loaded = True
            cv.itemconfigure(self.count_lab, text="RACKS READY — PRESS ENTER")
            self.btn.set_visible(True)
            self.btn.pop_in(delay=0, dy=40)
            move(self.E, cv, self.btn.tag, 0, -6, duration=900, delay=900, loop=True, direction="alternate",
                 easing="inOutSine", owner=self)
            return False
        return True
