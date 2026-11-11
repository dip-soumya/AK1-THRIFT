"""
fox.py  -  FITZ, the AK1 mascot. A sharp-dressed fox in a black blazer, lime tie and
sunglasses pushed up on his head - drawn 100% with tkinter canvas primitives.

Alive-ness (all on the shared anime engine):
  idle bob, tail wag, random blinks, ear twitches, talking mouth + raised brows,
  jump on click, pop-in neo-brutalist speech bubble with a typewriter effect.
"""
import math
import random

from . import theme
from .anim import mix
from .theme import F

FUR = "#EE7A2E"
FUR_D = "#C8581A"
CREAM = "#FFF3E2"
EAR_IN = "#3B2016"
LAPEL = "#2A2A2A"
LENS = "#1B1B1B"


def _rot(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


class Fox:
    # local geometry: origin = bottom-centre of the fox, y grows downward (negative = up)
    TAIL = [(22, -8), (44, -12), (60, -30), (66, -58), (60, -84), (50, -70), (46, -50), (36, -30), (22, -20)]
    TIP = [(54, -66), (60, -86), (68, -62), (62, -56)]
    BODY = [(-40, 0), (-39, -40), (-34, -54), (-20, -62), (20, -62), (34, -54), (39, -40), (40, 0)]
    SHIRT = [(-13, -62), (13, -62), (0, -24)]
    LAP_L = [(-13, -62), (-25, -57), (-4, -24)]
    LAP_R = [(13, -62), (25, -57), (4, -24)]
    KNOT = [(-5, -60), (5, -60), (3.5, -53), (-3.5, -53)]
    BLADE = [(-3.5, -53), (3.5, -53), (7.5, -27), (0, -18), (-7.5, -27)]
    POCKET = [(19, -40), (31, -40), (28, -47), (24, -44), (21, -48)]
    EAR_L = [(-40, -108), (-33, -152), (-11, -126)]
    EAR_LI = [(-34, -115), (-31, -141), (-18, -125)]
    HEAD = [(-28, -130), (28, -130), (46, -100), (27, -78), (0, -56), (-27, -78), (-46, -100)]
    MUZZLE = [(-44, -98), (-20, -88), (0, -92), (20, -88), (44, -98), (25, -76), (0, -57), (-25, -76)]

    def __init__(self, page, x, y, scale=0.9, hud=True, side="left", lines=None, bg=theme.PAPER):
        self.page = page
        self.cv = page.cv
        self.E = page.E
        self.s = scale
        self.ox, self.oy = x, y
        self.side = side
        self.lines = list(lines or [])
        random.shuffle(self.lines)
        self.line_i = 0
        self.bg = bg
        self.tag = f"fox{id(self)}"
        self.tags = (self.tag, "hud") if hud else (self.tag,)
        self.bob = 0.0
        self.jump = 0.0
        self.wag = 0.0
        self.ear = 0.0
        self.blink = 1.0
        self.talking = False
        self.mouth_open = False
        self.next_blink = 0
        self.bubble = None
        self.typing = None
        self.enter_y = 0.0
        self._last_render = 0
        self._build()
        if hud:
            page.hud_listeners.append(self._on_shift)
        self.E.frame(self._tick, owner=page)

    # ------------------------------------------------------------------ #
    def _on_shift(self, dy):
        self.oy += dy

    def T(self, pts, dy=0.0):
        s, ox, oy = self.s, self.ox, self.oy + (self.bob + self.jump + self.enter_y + dy) * self.s
        out = []
        for x, y in pts:
            out += [ox + x * s, oy + y * s]
        return out

    def _build(self):
        cv, t = self.cv, self.tags
        P = lambda fill, smooth=False, outline="": cv.create_polygon(0, 0, 0, 0, 0, 0, fill=fill, outline=outline,
                                                                     smooth=smooth, tags=t)
        self.i_tail = P(FUR, True)
        self.i_tip = P(CREAM, True)
        self.i_earl, self.i_earli = P(FUR), P(EAR_IN)
        self.i_earr, self.i_earri = P(FUR), P(EAR_IN)
        self.i_body = P(theme.INK)
        self.i_shirt = P(theme.WHITE)
        self.i_lapl, self.i_lapr = P(LAPEL), P(LAPEL)
        self.i_blade, self.i_knot = P(theme.LIME), P(theme.LIME)
        self.i_s1 = cv.create_line(0, 0, 0, 0, fill=theme.INK, width=max(1, 1.6 * self.s), tags=t)
        self.i_s2 = cv.create_line(0, 0, 0, 0, fill=theme.INK, width=max(1, 1.6 * self.s), tags=t)
        self.i_pocket = P(theme.ACCENT)
        self.i_head = P(FUR, True)
        self.i_muzzle = P(CREAM, True)
        self.i_glass_l = cv.create_oval(0, 0, 0, 0, fill=LENS, outline=theme.GOLD, width=max(1, 1.6 * self.s), tags=t)
        self.i_glass_r = cv.create_oval(0, 0, 0, 0, fill=LENS, outline=theme.GOLD, width=max(1, 1.6 * self.s), tags=t)
        self.i_bridge = cv.create_line(0, 0, 0, 0, fill=theme.GOLD, width=max(1, 2 * self.s), tags=t)
        self.i_shine_l = cv.create_line(0, 0, 0, 0, fill="#6b6b6b", width=max(1, 1.5 * self.s), tags=t)
        self.i_shine_r = cv.create_line(0, 0, 0, 0, fill="#6b6b6b", width=max(1, 1.5 * self.s), tags=t)
        self.i_eye_l = cv.create_oval(0, 0, 0, 0, fill=theme.INK, outline="", tags=t)
        self.i_eye_r = cv.create_oval(0, 0, 0, 0, fill=theme.INK, outline="", tags=t)
        self.i_gl_l = cv.create_oval(0, 0, 0, 0, fill=theme.WHITE, outline="", tags=t)
        self.i_gl_r = cv.create_oval(0, 0, 0, 0, fill=theme.WHITE, outline="", tags=t)
        self.i_brow_l = cv.create_line(0, 0, 0, 0, fill=theme.INK, width=max(1, 2.6 * self.s), capstyle="round", tags=t)
        self.i_brow_r = cv.create_line(0, 0, 0, 0, fill=theme.INK, width=max(1, 2.6 * self.s), capstyle="round", tags=t)
        self.i_nose = cv.create_oval(0, 0, 0, 0, fill=theme.INK, outline="", tags=t)
        self.i_mouth = cv.create_line(0, 0, 0, 0, 0, 0, fill=theme.INK, width=max(1, 1.8 * self.s),
                                      smooth=True, capstyle="round", tags=t)
        self.i_mouth_o = cv.create_oval(0, 0, 0, 0, fill="#5A1A10", outline="", state="hidden", tags=t)
        self._render(force=True)

    def _oval(self, item, cx, cy, rx, ry):
        p = self.T([(cx - rx, cy - ry), (cx + rx, cy + ry)])
        self.cv.coords(item, *p)

    def _render(self, force=False):
        cv = self.cv
        tail = _rot(self.TAIL, 24, -14, self.wag)
        tip = _rot(self.TIP, 24, -14, self.wag)
        cv.coords(self.i_tail, *self.T(tail))
        cv.coords(self.i_tip, *self.T(tip))
        el = _rot(self.EAR_L, -25, -118, -self.ear)
        eli = _rot(self.EAR_LI, -25, -118, -self.ear)
        er = [(-x, y) for x, y in _rot(self.EAR_L, -25, -118, self.ear * 0.4)]
        eri = [(-x, y) for x, y in _rot(self.EAR_LI, -25, -118, self.ear * 0.4)]
        cv.coords(self.i_earl, *self.T(el))
        cv.coords(self.i_earli, *self.T(eli))
        cv.coords(self.i_earr, *self.T(er))
        cv.coords(self.i_earri, *self.T(eri))
        if force:
            cv.coords(self.i_body, *self.T(self.BODY))
        else:
            cv.coords(self.i_body, *self.T(self.BODY))
        cv.coords(self.i_shirt, *self.T(self.SHIRT))
        cv.coords(self.i_lapl, *self.T(self.LAP_L))
        cv.coords(self.i_lapr, *self.T(self.LAP_R))
        cv.coords(self.i_knot, *self.T(self.KNOT))
        cv.coords(self.i_blade, *self.T(self.BLADE))
        cv.coords(self.i_s1, *self.T([(-5, -46), (5, -41)]))
        cv.coords(self.i_s2, *self.T([(-6, -36), (6, -31)]))
        cv.coords(self.i_pocket, *self.T(self.POCKET))
        # head bobs a touch more than the body -> feels alive
        hb = math.sin(self.bob * 0.9) * 0.6
        cv.coords(self.i_head, *self.T(self.HEAD, hb))
        cv.coords(self.i_muzzle, *self.T(self.MUZZLE, hb))
        self._oval(self.i_glass_l, -13, -121 + hb, 9, 7.5)
        self._oval(self.i_glass_r, 13, -121 + hb, 9, 7.5)
        cv.coords(self.i_bridge, *self.T([(-4, -122 + hb), (4, -122 + hb)]))
        cv.coords(self.i_shine_l, *self.T([(-17, -124 + hb), (-13, -127 + hb)]))
        cv.coords(self.i_shine_r, *self.T([(9, -124 + hb), (13, -127 + hb)]))
        ry = 5.8 * self.blink
        self._oval(self.i_eye_l, -15, -100 + hb, 4.4, ry)
        self._oval(self.i_eye_r, 15, -100 + hb, 4.4, ry)
        gs = 1.4 if self.blink > 0.5 else 0
        self._oval(self.i_gl_l, -13.6, -102 + hb, gs, gs)
        self._oval(self.i_gl_r, 16.4, -102 + hb, gs, gs)
        by = -3 if self.talking else 0
        cv.coords(self.i_brow_l, *self.T([(-21, -109 + by + hb), (-9, -107 + by * 0.4 + hb)]))
        cv.coords(self.i_brow_r, *self.T([(9, -107 + by * 0.4 + hb), (21, -109 + by + hb)]))
        self._oval(self.i_nose, 0, -71 + hb, 5.2, 3.8)
        cv.coords(self.i_mouth, *self.T([(-5, -66 + hb), (0, -64 + hb), (5, -66 + hb)]))
        if self.mouth_open:
            cv.itemconfigure(self.i_mouth_o, state="normal")
            self._oval(self.i_mouth_o, 0, -63.5 + hb, 3.4, 3)
        else:
            cv.itemconfigure(self.i_mouth_o, state="hidden")

    # ------------------------------------------------------------------ #
    def _tick(self, dt, now):
        self.bob = math.sin(now * 2.6) * 2.2
        self.wag = math.sin(now * 3.9) * 9 + math.sin(now * 1.3) * 3
        if self.next_blink == 0:
            self.next_blink = now + random.uniform(1.5, 4)
        if now > self.next_blink:
            k = (now - self.next_blink) / 0.16
            if k >= 1:
                self.blink = 1.0
                self.next_blink = now + random.uniform(2.2, 5.2)
                if random.random() < 0.35:
                    self.E.animate(420, lambda e: setattr(self, "ear", math.sin(e * math.pi * 2) * 12),
                                   easing="linear", owner=self.page)
            else:
                self.blink = max(0.12, abs(1 - 2 * k))
        if self.talking:
            self.mouth_open = int(now * 11) % 2 == 0
        else:
            self.mouth_open = False
        gap = 0.07 if self.page._scroll_loop is not None else 0.028   # relax while the page scrolls
        if now - self._last_render >= gap:
            self._last_render = now
            self._render()

    # ------------------------------------------------------------------ #
    def bbox(self):
        s = self.s
        return (self.ox - 48 * s, self.oy - 156 * s, self.ox + 70 * s, self.oy)

    def enter(self, delay=0, frm=180):
        """Slide up from below with a springy overshoot."""
        self.enter_y = frm
        self.E.tween(frm, 0, lambda v: setattr(self, "enter_y", v), duration=1100, delay=delay,
                     easing="outElastic", owner=self.page)

    def hop(self):
        tl = self.E.timeline(owner=self.page)
        tl.add(lambda e: setattr(self, "jump", -26 * e), duration=170, easing="outQuad")
        tl.add(lambda e: setattr(self, "jump", -26 * (1 - e)), duration=560, easing="outBounce")
        tl.play()

    def next_line(self):
        if not self.lines:
            return ""
        line = self.lines[self.line_i % len(self.lines)]
        self.line_i += 1
        return line

    def poke(self):
        self.hop()
        self.say(self.next_line())

    # ------------------------------------------------------------------ #
    #  speech bubble
    # ------------------------------------------------------------------ #
    def say(self, text, hold=None, maxw=290):
        if not text:
            return
        self.hush(instant=True)
        cv, s = self.cv, self.s
        font = F("bodyb", 16)
        lines = theme.wrap(font, text, maxw)
        lh = theme.line_h(font)
        pad = 16
        w = max(theme.measure(font, ln) for ln in lines) + pad * 2
        w = max(w, 120)
        h = len(lines) * lh + pad * 2 + 18
        # bubble geometry relative to the fox origin (so HUD scrolling never breaks it)
        if self.side == "left":
            tip = (-50 * s, -104 * s)
            bx2 = tip[0] - 16
            bx1 = bx2 - w
        else:
            tip = (50 * s, -110 * s)
            bx1 = tip[0] + 16
            bx2 = bx1 + w
        by2 = tip[1] + 22
        by1 = by2 - h
        b = dict(rel=(bx1, by1, bx2, by2), tip=tip, items=[], text=text, lines=lines, font=font, lh=lh, pad=pad)
        tg = self.tags + (self.tag + "b",)
        b["shadow"] = cv.create_polygon(0, 0, 0, 0, 0, 0, fill=theme.ACCENT, outline="", smooth=True, tags=tg)
        b["shape"] = cv.create_polygon(0, 0, 0, 0, 0, 0, fill=theme.WHITE, outline=theme.INK,
                                       width=2, smooth=True, tags=tg)
        self.bubble = b
        self.page.raise_hud()

        def upd(e):
            if self.bubble is not b:
                return
            self._bubble_shape(b, e)
        self.E.animate(420, upd, easing="outBack", owner=self.page, complete=lambda: self._type(b, hold))
        self._bubble_shape(b, 0.05)

    def _bubble_pts(self, rel, tip, k, off=0.0):
        x1, y1, x2, y2 = rel
        tx, ty = tip
        # scale around tip
        X = lambda x: tx + (x - tx) * k + off
        Y = lambda y: ty + (y - ty) * k + off
        r = 14
        x1, x2, y1, y2 = X(x1), X(x2), Y(y1), Y(y2)
        if self.side == "left":
            tail = [(x2, Y(ty - 18)), (tx + off, ty + off), (x2, Y(ty - 4))]
        else:
            tail = [(x1, Y(ty - 4)), (tx + off, ty + off), (x1, Y(ty - 18))]
        pts = [(x1 + r, y1), (x1 + r, y1), (x2 - r, y1), (x2 - r, y1), (x2, y1), (x2, y1 + r), (x2, y1 + r)]
        if self.side == "left":
            pts += [(x2, Y(ty - 18)), (x2, Y(ty - 18)), (tx + off, ty + off), (tx + off, ty + off),
                    (x2, Y(ty - 4)), (x2, Y(ty - 4))]
        pts += [(x2, y2 - r), (x2, y2 - r), (x2, y2), (x2 - r, y2), (x2 - r, y2), (x1 + r, y2), (x1 + r, y2),
                (x1, y2), (x1, y2 - r), (x1, y2 - r)]
        if self.side != "left":
            pts += [(x1, Y(ty - 4)), (x1, Y(ty - 4)), (tx + off, ty + off), (tx + off, ty + off),
                    (x1, Y(ty - 18)), (x1, Y(ty - 18))]
        pts += [(x1, y1 + r), (x1, y1 + r), (x1, y1)]
        _ = tail
        out = []
        ox, oy = self.ox, self.oy + (self.enter_y) * self.s
        for x, y in pts:
            out += [ox + x, oy + y]
        return out

    def _bubble_shape(self, b, e):
        k = max(0.02, e)
        try:
            self.cv.coords(b["shadow"], *self._bubble_pts(b["rel"], b["tip"], k, off=5))
            self.cv.coords(b["shape"], *self._bubble_pts(b["rel"], b["tip"], k))
        except Exception:  # noqa: BLE001
            pass

    def _type(self, b, hold):
        if self.bubble is not b:
            return
        cv = self.cv
        x1, y1, _, _ = b["rel"]
        ox, oy = self.ox, self.oy + self.enter_y * self.s
        tg = self.tags + (self.tag + "b",)
        lab = cv.create_text(ox + x1 + b["pad"], oy + y1 + 12, text="FITZ ▸", anchor="nw",
                             font=F("mono", 11, "bold"), fill=theme.ACCENT, tags=tg)
        txt = cv.create_text(ox + x1 + b["pad"], oy + y1 + 30, text="", anchor="nw",
                             font=b["font"], fill=theme.INK, tags=tg)
        b["items"] += [lab, txt]
        full = "\n".join(b["lines"])
        n = len(full)
        self.talking = True

        def upd(e):
            if self.bubble is not b:
                return
            cv.itemconfigure(txt, text=full[:int(n * e + 0.5)])

        def done():
            if self.bubble is b:
                self.talking = False
                self.E.after(hold or (2600 + 38 * n), lambda: self.hush(b), owner=self.page)
        self.typing = self.E.animate(max(400, n * 28), upd, easing="linear", owner=self.page, complete=done)

    def hush(self, b=None, instant=False):
        b = b or self.bubble
        if b is None or (self.bubble is not b and not instant):
            return
        if self.bubble is b:
            self.bubble = None
        self.talking = False
        if self.typing:
            self.typing.cancel()
        cv = self.cv
        if instant:
            for i in [b["shadow"], b["shape"]] + b["items"]:
                cv.delete(i)
            return
        for i in b["items"]:
            cv.delete(i)

        def upd(e):
            self._bubble_shape(b, 1 - e)

        def fin():
            cv.delete(b["shadow"])
            cv.delete(b["shape"])
        self.E.animate(220, upd, easing="inBack", owner=self.page, complete=fin)
