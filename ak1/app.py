"""
app.py  -  window, navigation bar, curtain page transitions, toasts and the bag.
"""
import ctypes
import os
import random
import sys
import tkinter as tk
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont, ImageTk

from . import theme
from .anim import Engine, mix, move
from .assets import Assets
from .data import FOX
from .theme import F, rupee
from .widgets import Letters

NAV_H = 72


# --------------------------------------------------------------------------- #
#  Nav bar
# --------------------------------------------------------------------------- #
class NavBar(tk.Canvas):
    LINKS = [("HOME", "home"), ("TEES", "tees"), ("JEANS", "jeans"), ("TROUSERS", "trousers"),
             ("JEWELLERY", "jewellery"), ("ACCESSORIES", "accessories")]

    def __init__(self, app):
        super().__init__(app.root, height=NAV_H, bg=theme.INK, highlightthickness=0, bd=0)
        self.app = app
        self.E = app.anim
        self.alive = True
        W = app.W
        lf = F("display", 34)
        self.create_text(28, NAV_H / 2 + 1, text="AK1", font=lf, fill=theme.ACCENT, anchor="w", tags=("logo",))
        aw = theme.measure(lf, "AK1")
        self.create_text(28 + aw + 6, NAV_H / 2 + 1, text="THRIFT", font=lf, fill=theme.BONE, anchor="w",
                         tags=("logo",))
        self.create_text(28 + aw + 6 + theme.measure(lf, "THRIFT") + 12, NAV_H / 2 - 9, text="®",
                         font=F("mono", 10), fill=theme.MUTED, anchor="w", tags=("logo",))
        self.hits = []
        f = F("heavy", 13)
        widths = [theme.measure(f, t) for t, _ in self.LINKS]
        total = sum(widths) + 38 * (len(widths) - 1)
        x = (W - total) / 2 + 30
        self.items = {}
        for (label, key), w in zip(self.LINKS, widths):
            it = self.create_text(x, NAV_H / 2, text=label, font=f, fill=theme.BONE, anchor="w")
            self.items[key] = (it, x, w)
            self.hits.append(((x - 10, 0, x + w + 10, NAV_H), key, it))
            x += w + 38
        self.ul = self.create_rectangle(0, NAV_H - 16, 0, NAV_H - 12, fill=theme.LIME, outline="")
        self.ul_pos = None
        # bag
        bx = W - 30
        self.bag_w = 150
        self.bag_bg = self.create_rectangle(bx - self.bag_w, 14, bx, NAV_H - 14, fill=theme.BONE, outline="")
        self.bag_t = self.create_text(bx - self.bag_w + 22, NAV_H / 2, text="BAG", font=F("heavy", 14), fill=theme.INK,
                                      anchor="w")
        self.cnt_c = self.create_oval(bx - 52, NAV_H / 2 - 17, bx - 18, NAV_H / 2 + 17, fill=theme.ACCENT, outline="")
        self.cnt_t = self.create_text(bx - 35, NAV_H / 2, text="0", font=F("heavy", 14), fill=theme.INK)
        self.hits.append(((bx - self.bag_w, 14, bx, NAV_H - 14), "checkout", None))
        self.hits.append(((20, 0, 300, NAV_H), "home", None))
        self.hover = None
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<Button-1>", self._click)

    def _hit(self, x, y):
        for (x1, y1, x2, y2), key, it in self.hits:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key, it
        return None

    def _set_hover(self, h):
        if h == self.hover:
            return
        if self.hover:
            key, it = self.hover
            if it is not None:
                self.itemconfigure(it, fill=theme.BONE)
            elif key == "checkout":
                self.itemconfigure(self.bag_bg, fill=theme.BONE)
        self.hover = h
        if h:
            key, it = h
            if it is not None:
                self.itemconfigure(it, fill=theme.ACCENT)
                move(self.E, self, it, 0, -4, duration=140, direction="alternate", loop=2, owner=self)
            elif key == "checkout":
                self.itemconfigure(self.bag_bg, fill=theme.LIME)
        self.configure(cursor="hand2" if h else "")

    def _motion(self, e):
        self._set_hover(self._hit(e.x, e.y))

    def _click(self, e):
        h = self._hit(e.x, e.y)
        if h:
            self.app.go(h[0])

    def set_active(self, key):
        if key not in self.items:
            target = (0, 0)
        else:
            it, x, w = self.items[key]
            target = (x, x + w)
        a = self.ul_pos or (target[0] + (target[1] - target[0]) / 2,) * 2
        self.ul_pos = target

        def upd(e):
            self.coords(self.ul, a[0] + (target[0] - a[0]) * e, NAV_H - 16, a[1] + (target[1] - a[1]) * e, NAV_H - 12)
        self.E.animate(800, upd, easing="outElasticSoft", owner=self)
        for k, (it, x, w) in self.items.items():
            self.itemconfigure(it, font=F("heavy", 13))

    def set_count(self, n, bump=False):
        self.itemconfigure(self.cnt_t, text=str(n))
        if bump:
            bx, cy = self.app.W - 65, NAV_H / 2

            def upd(e):
                r = 17 + 9 * (1 - e)
                self.coords(self.cnt_c, bx - r, cy - r, bx + r, cy + r)
            self.E.animate(900, upd, easing="outElastic", owner=self)
            self.E.animate(600, lambda e: self.itemconfigure(self.bag_bg, fill=mix(theme.LIME, theme.BONE, e)),
                           owner=self)


# --------------------------------------------------------------------------- #
#  App
# --------------------------------------------------------------------------- #
class App:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:  # noqa: BLE001
                pass
        try:
            # 1 ms timer resolution: Tk's after() otherwise snaps to ~15.6 ms on Windows -> jittery frames
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:  # noqa: BLE001
            pass
        theme.register_fonts(os.path.join(root_dir, "assets", "fonts"))
        self.root = root = tk.Tk()
        root.withdraw()
        theme.init_fonts(root)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.W = min(1400, sw - 40)
        self.Hf = min(900, sh - 90)
        root.geometry(f"{self.W}x{self.Hf}+{(sw - self.W) // 2}+{max(0, (sh - self.Hf) // 2 - 20)}")
        root.resizable(False, False)
        root.title("AK1-THRIFT  —  second hand, first class")
        root.configure(bg=theme.INK)
        self._icon()
        self.anim = Engine(root)
        self.assets = Assets(root_dir)
        self.cart = []
        self.wish = set()
        self.page = None
        self.busy = False
        self.nav = NavBar(self)
        self.stage = tk.Frame(root, bg=theme.INK, highlightthickness=0, bd=0)
        self.stage.pack(side="bottom", fill="both", expand=True)
        self.stage_h = self.Hf
        self.toast_cv = None
        self.toast_tw = []
        root.bind_all("<MouseWheel>", self._wheel)
        for k, d in (("<Down>", 140), ("<Up>", -140), ("<Next>", "pg"), ("<Prior>", "-pg"), ("<space>", "pg")):
            root.bind(k, lambda e, d=d: self._key(e, d))
        root.bind("<Home>", lambda e: self._key(e, "home"))
        root.bind("<End>", lambda e: self._key(e, "end"))
        root.bind("<Escape>", lambda e: None)
        self.pages = self._registry()
        self._show_intro()
        root.deiconify()
        try:
            root.attributes("-alpha", 0.0)
            self.anim.tween(0, 1, lambda v: root.attributes("-alpha", v), duration=700, easing="outQuad")
        except tk.TclError:
            pass

    def _registry(self):
        from .pages.category import AccessoriesPage, JeansPage, JewelleryPage, TeesPage, TrousersPage
        from .pages.checkout import CheckoutPage
        from .pages.home import HomePage
        from .pages.intro import IntroPage
        return {"intro": IntroPage, "home": HomePage, "tees": TeesPage, "jeans": JeansPage,
                "trousers": TrousersPage, "jewellery": JewelleryPage, "accessories": AccessoriesPage,
                "checkout": CheckoutPage}

    def _icon(self):
        try:
            fp = os.path.join(self.root_dir, "assets", "fonts", "Anton-Regular.ttf")
            im = Image.new("RGB", (64, 64), theme.ACCENT)
            d = ImageDraw.Draw(im)
            f = ImageFont.truetype(fp, 34)
            d.text((32, 34), "AK1", font=f, fill=theme.INK, anchor="mm")
            self._icon_ph = ImageTk.PhotoImage(im)
            self.root.iconphoto(True, self._icon_ph)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    def _wheel(self, e):
        if self.page is None or self.busy:
            return
        if e.state & 0x0001:
            # Tk reports a touchpad's sideways swipe (WM_MOUSEHWHEEL) as Shift+MouseWheel:
            # route it to the slider under the pointer instead of scrolling the page down
            self.page.on_hwheel(e)
        else:
            self.page.on_wheel(e)

    def _key(self, e, d):
        p = self.page
        if p is None or self.busy or p.modal is not None:
            return
        if isinstance(self.root.focus_get(), tk.Entry) and d in ("home", "end", "pg") and e.keysym != "Next":
            return
        if d == "pg":
            p.scroll_by(p.H * 0.85)
        elif d == "-pg":
            p.scroll_by(-p.H * 0.85)
        elif d == "home":
            p.scroll_to(0)
        elif d == "end":
            p.scroll_to(p.max_scroll)
        else:
            p.scroll_by(d)

    # ------------------------------------------------------------------ #
    def _mount(self, key, **kw):
        if self.page is not None:
            self.page.teardown()
        cls = self.pages[key]
        page = cls(self, **kw)
        page.build()
        page.finalize()
        page.pack(fill="both", expand=True)
        self.page = page
        return page

    def _show_intro(self):
        self.stage_h = self.Hf
        page = self._mount("intro")
        self.root.after(250, page.on_enter)

    def enter_store(self):
        if self.busy or self.page is None or self.page.key != "intro":
            return
        self.root.unbind("<Return>")
        self.go("home", _first=True)

    def go(self, key, _first=False, **kw):
        if self.busy:
            return
        if self.page is not None and self.page.key == key:
            self.page.scroll_to(0)
            return
        self.busy = True
        if self.page is not None and self.page.fox:
            self.page.fox.hush(instant=True)
        root = self.root
        Wf, Hf = self.W, self.Hf
        title = self.pages[key].title
        a = tk.Canvas(root, bg=theme.ACCENT, highlightthickness=0, bd=0)
        b = tk.Canvas(root, bg=theme.INK, highlightthickness=0, bd=0)
        dummy = SimpleNamespace(cv=b, E=self.anim, alive=True)

        def rise(c, e):
            h = max(1, int(Hf * e))
            c.place(x=0, y=Hf - h, width=Wf, height=h)

        def lift(c, e):
            h = max(1, int(Hf * (1 - e)))
            c.place(x=0, y=0, width=Wf, height=h)
            if e >= 1:
                c.place_forget()

        rise(a, 0.0)
        rise(b, 0.0)
        self.anim.animate(480, lambda e: rise(a, e), easing="inOutExpo")
        self.anim.animate(480, lambda e: rise(b, e), delay=90, easing="inOutExpo", complete=lambda: swap())

        def swap():
            if _first:
                self.nav.pack(side="top", fill="x", before=self.stage)
                self.stage_h = self.Hf - NAV_H
            root.update_idletasks()
            try:
                page = self._mount(key, **kw)
            except Exception:  # noqa: BLE001 - never leave the curtain stuck
                import traceback
                traceback.print_exc()
                page = self._mount("home") if key != "home" else self.page
            self.nav.set_active(key)
            root.update_idletasks()
            # title letters in the curtain
            f = F("display", 170)
            L = Letters(dummy, Wf / 2, Hf / 2 + 110, title, f, theme.BONE, theme.INK, align="center")
            sub = b.create_text(Wf / 2, Hf / 2 + 140, text=random.choice(
                ["SECOND HAND. FIRST CLASS.", "PRE-LOVED. RE-WORN.", "BUY LESS. CHOOSE WELL.", "WEAR IT LOUD."]),
                font=F("mono", 14, "bold"), fill=theme.INK)
            end = L.play(mode="revolve", step=34, dur=520)
            self.anim.animate(500, lambda e: b.itemconfigure(sub, fill=mix(theme.INK, theme.LIME, e)), delay=150)
            self.anim.animate(560, lambda e: lift(b, e), delay=end + 40, easing="inOutExpo")
            self.anim.animate(560, lambda e: lift(a, e), delay=end + 130, easing="inOutExpo",
                              complete=lambda: done(page))

        def done(page):
            dummy.alive = False
            a.destroy()
            b.destroy()
            self.busy = False
            if page is not None:
                page.on_enter()

    # ------------------------------------------------------------------ #
    def add_to_cart(self, p, size):
        for it in self.cart:
            if it["p"]["id"] == p["id"] and it["size"] == size:
                it["qty"] += 1
                break
        else:
            self.cart.append(dict(p=p, size=size, qty=1))
        n = sum(i["qty"] for i in self.cart)
        self.nav.set_count(n, bump=True)
        self.toast("ADDED TO BAG", p, sub=f"{p['name']}  ·  SIZE {size}  ·  {rupee(p['price'])}")
        if self.page is not None and random.random() < 0.6:
            self.page.fox_say("added")

    def toast(self, title, p=None, sub=""):
        root = self.root
        for t in self.toast_tw:
            t.cancel()
        if self.toast_cv is not None:
            self.toast_cv.destroy()
        w, h = 400, 96
        c = tk.Canvas(root, width=w, height=h, bg=theme.INK, highlightthickness=0, bd=0)
        self.toast_cv = c
        c.create_rectangle(0, 0, w, h, outline=theme.LIME, width=4)
        x = 16
        if p is not None:
            ph = self.assets.tk_cover(p["cat"], p["img"], 56, 70, p["focus"])
            c._ph = ph
            c.create_image(14, 13, image=ph, anchor="nw")
            x = 84
        c.create_text(x, 22, text="✔  " + title, font=F("heavy", 15), fill=theme.LIME, anchor="nw")
        c.create_text(x, 52, text=sub, font=F("mono", 10), fill=theme.BONE, anchor="nw", width=w - x - 12)
        bar = c.create_rectangle(0, h - 4, w, h, fill=theme.ACCENT, outline="")
        X0, X1 = self.W + 10, self.W - w - 24
        Y = NAV_H + 18

        def slide(v):
            if c.winfo_exists():
                c.place(x=int(v), y=Y)
        self.toast_tw = [
            self.anim.tween(X0, X1, slide, duration=650, easing="outBack"),
            self.anim.animate(2600, lambda e: c.winfo_exists() and c.coords(bar, 0, h - 4, w * (1 - e), h),
                              delay=300, easing="linear"),
            self.anim.tween(X1, X0, slide, duration=450, delay=2900, easing="inBack",
                            complete=lambda: c.winfo_exists() and c.destroy()),
        ]

    def run(self):
        try:
            self.root.mainloop()
        finally:
            try:
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:  # noqa: BLE001
                pass
