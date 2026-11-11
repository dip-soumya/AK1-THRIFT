"""
widgets.py  -  canvas-drawn, animated building blocks.

Button          neo-brutalist button with offset shadow, colour tween + arrow nudge
Letters         per-letter type that rises / revolves in (anime.js text staggering)
RotatingBadge   circular text that spins (faster while you scroll)
Marquee         infinite ticker band, speeds up with scroll velocity
ProductCard     flip-in (Y-axis revolve) card with hover lift, quick-view band, wishlist + add
Rail            horizontally sliding row of cards
RevolvingRing   3D carousel - items orbit on an ellipse with depth scale / fade, drag to spin
Accordion       hover-expand editorial strips
quote_block     word-by-word serif quote reveal
section_header  numbered section title with revolving letters + growing rule
Review widgets  stars, review cards, rating summary bars, review form
QuickView       modal product sheet
"""
import math
import random
import tkinter as tk

from PIL import Image, ImageTk

from . import bake, theme
from .anim import mix, move, stagger
from .data import BADGE_COL, CATS
from .theme import F, rupee

LIGHT = dict(bg=theme.PAPER, fg=theme.INK, muted=theme.MUTED, line=theme.LINE, ph="#E3DDD1",
             accent=theme.ACCENT, pill=theme.INK, pill_fg=theme.BONE, card=theme.WHITE)
DARK = dict(bg=theme.INK, fg=theme.BONE, muted="#9A958B", line=theme.INK3, ph=theme.INK3,
            accent=theme.ACCENT, pill=theme.BONE, pill_fg=theme.INK, card=theme.INK2)
CHROMEP = dict(DARK, bg=theme.VOID, fg=theme.CHROME_L, muted=theme.CHROME_D, line="#26282B", ph="#141414",
               accent=theme.CHROME, card="#0D0D0D", badge=theme.CHROME)
GOLDP = CHROMEP   # (old name kept for compatibility)


# --------------------------------------------------------------------------- #
#  geometry helpers
# --------------------------------------------------------------------------- #
def rrect(x1, y1, x2, y2, r):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
            x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]


def star_pts(cx, cy, R, r=None):
    r = r or R * 0.46
    pts = []
    for k in range(10):
        a = math.radians(-90 + 36 * k)
        rad = R if k % 2 == 0 else r
        pts += [cx + rad * math.cos(a), cy + rad * math.sin(a)]
    return pts


def lines(cv, x, y, rows, font, fill, lead=None, tags=(), anchor="nw"):
    """Multi-line display type with tight, magazine-style leading (Tk's default is very loose for Anton)."""
    lead = lead or abs(font[1]) * 1.08
    return [cv.create_text(x, y + i * lead, text=r, font=font, fill=fill, anchor=anchor, tags=tags)
            for i, r in enumerate(rows)]


def stars(cv, x, y, rating, size=12, tags=(), on=theme.STAR, off=theme.LINE, gap=3):
    """Row of 5 stars, left edge at x, vertical centre y. Supports half stars."""
    items = []
    for i in range(5):
        cx = x + size + i * (size * 2 + gap)
        full = star_pts(cx, y, size)
        fill = on if rating >= i + 0.75 else off
        items.append(cv.create_polygon(*full, fill=fill, outline="", tags=tags))
        if i + 0.25 <= rating < i + 0.75:     # half star = left half polygon
            half = [full[k] for k in range(10, 20)] + full[0:2]
            items.append(cv.create_polygon(*half, fill=on, outline="", tags=tags))
    return items, size * 10 + gap * 4


# --------------------------------------------------------------------------- #
#  Button
# --------------------------------------------------------------------------- #
class Button:
    KINDS = {
        # fill, text, hover-fill, hover-text, outline
        "ink": (theme.INK, theme.BONE, theme.ACCENT, theme.INK, theme.INK),
        "accent": (theme.ACCENT, theme.INK, theme.INK, theme.BONE, theme.INK),
        "lime": (theme.LIME, theme.INK, theme.INK, theme.LIME, theme.INK),
        "bone": (theme.BONE, theme.INK, theme.ACCENT, theme.INK, theme.INK),
        "gold": (theme.GOLD, theme.INK, theme.BONE, theme.INK, theme.INK),
        "chrome": (theme.CHROME, theme.INK, theme.CRIMSON, theme.CHROME_L, theme.INK),
    }

    def __init__(self, page, x, y, text, command=None, kind="ink", h=50, font=None, anchor="nw",
                 hud=False, tags=(), arrow=True, z=10, shadow=None, page_bg=None, w=None, pad=26):
        self.page, self.cv, self.E = page, page.cv, page.E
        self.command = command
        self.font = font or F("heavy", 15)
        self.text = text
        self.arrow = arrow
        self.kind = kind
        if kind.startswith("outline"):
            fg = theme.BONE if kind == "outline-light" else theme.INK
            bg = page_bg or page.bg
            self.cols = (bg, fg, fg, bg, fg)
        else:
            self.cols = self.KINDS[kind]
        self.shadow_col = shadow
        tw = theme.measure(self.font, text)
        self.w = w or (tw + pad * 2 + (26 if arrow else 0))
        self.h = h
        if anchor == "center":
            x, y = x - self.w / 2, y - h / 2
        elif anchor == "ne":
            x = x - self.w
        elif anchor == "e":
            x, y = x - self.w, y - h / 2
        elif anchor == "w":
            y = y - h / 2
        self.x, self.y = x, y
        self.tag = f"btn{id(self)}"
        t = (self.tag,) + tuple(tags) + (("hud",) if hud else ())
        cv = self.cv
        self.i_sh = None
        if shadow:
            self.i_sh = cv.create_rectangle(x + 5, y + 5, x + self.w + 5, y + h + 5, fill=shadow, outline="", tags=t)
        self.i_bg = cv.create_rectangle(x, y, x + self.w, y + h, fill=self.cols[0], outline=self.cols[4], width=2, tags=t)
        lx = x + (self.w - (26 if arrow else 0)) / 2 if arrow else x + self.w / 2
        self.i_tx = cv.create_text(lx, y + h / 2 + 1, text=text, font=self.font, fill=self.cols[1], tags=t)
        self.i_ar = None
        if arrow:
            self.i_ar = cv.create_text(x + self.w - pad - 6, y + h / 2, text="→", font=F("heavy", 17),
                                       fill=self.cols[1], tags=t)
        self.hv = 0.0
        self._hv_tw = None
        self._ar_dx = 0.0
        self.enabled = True
        self.zone = page.zone(lambda: (self.x, self.y, self.x + self.w, self.y + self.h), click=self._click,
                              enter=lambda: self._hover(True), leave=lambda: self._hover(False), hud=hud, z=z)

    def _paint(self, h):
        f0, t0, f1, t1, ol = self.cols
        cv = self.cv
        cv.itemconfigure(self.i_bg, fill=mix(f0, f1, h), outline=mix(ol, ol if self.kind.startswith("outline") else ol, h))
        cv.itemconfigure(self.i_tx, fill=mix(t0, t1, h))
        if self.i_ar:
            cv.itemconfigure(self.i_ar, fill=mix(t0, t1, h))
            dx = 7 * h - self._ar_dx
            cv.move(self.i_ar, dx, 0)
            self._ar_dx += dx

    def _hover(self, on):
        if self._hv_tw:
            self._hv_tw.cancel()
        a, b = self.hv, (1.0 if on else 0.0)

        def upd(e):
            self.hv = a + (b - a) * e
            self._paint(self.hv)
        self._hv_tw = self.E.animate(260, upd, easing="outCubic", owner=self.page)
        if self.i_sh is not None:
            off = -3 if on else 3
            move(self.E, self.cv, self.i_bg, off, off, duration=200, easing="outQuad", owner=self.page)
            move(self.E, self.cv, self.i_tx, off, off, duration=200, easing="outQuad", owner=self.page)
            if self.i_ar:
                move(self.E, self.cv, self.i_ar, off, off, duration=200, easing="outQuad", owner=self.page)

    def _click(self):
        if not self.enabled:
            return
        # press squash: quick nudge
        move(self.E, self.cv, self.tag, 0, 3, duration=240, easing="outQuad", direction="alternate", loop=2,
             owner=self.page)
        if self.command:
            self.command()

    def set_text(self, text):
        self.cv.itemconfigure(self.i_tx, text=text)

    def move(self, dx, dy):
        self.cv.move(self.tag, dx, dy)
        self.x += dx
        self.y += dy

    def set_visible(self, on):
        self.cv.itemconfigure(self.tag, state="normal" if on else "hidden")
        self.enabled = on
        self.zone.active = (lambda: True) if on else (lambda: False)

    def pop_in(self, delay=0, dy=24):
        """Fade + rise into place."""
        cv = self.cv
        cv.itemconfigure(self.tag, state="hidden")
        cv.move(self.tag, 0, dy)
        self.y += dy

        def begin():
            cv.itemconfigure(self.tag, state="normal")

        def upd(e, last=[0.0]):
            d = -dy * e - last[0]
            cv.move(self.tag, 0, d)
            self.y += d
            last[0] += d
        self.E.animate(700, upd, delay=delay, easing="outBack", begin=begin, owner=self.page)

    def delete(self):
        self.cv.delete(self.tag)
        self.page.remove_zone(self.zone)


# --------------------------------------------------------------------------- #
#  Letters  (staggered per-letter type)
# --------------------------------------------------------------------------- #
class Letters:
    def __init__(self, page, x, y, text, font, fg, bg, tags=(), tracking=0, align="left"):
        self.page, self.cv, self.E = page, page.cv, page.E
        self.fg, self.bg = fg, bg
        self.items = []
        self.text, self.font, self.tags, self.tracking = text, font, tags, tracking
        widths = [theme.measure(font, ch) + tracking for ch in text]
        self.w = sum(widths) - tracking
        if align == "center":
            x -= self.w / 2
        elif align == "right":
            x -= self.w
        self.x, self.y = x, y
        cx = x
        for ch, w in zip(text, widths):
            if ch != " ":
                it = self.cv.create_text(cx + (w - tracking) / 2, y, text=ch, font=font, fill=bg, anchor="s",
                                         tags=tags)
                self.items.append((it, cx + (w - tracking) / 2, y))
            cx += w
        self.h = theme.line_h(font)
        self.size = abs(font[1])

    def play(self, delay=0, mode="rise", step=42, dur=1000, easing=None, from_="first"):
        st = stagger(step, from_=from_)
        n = len(self.items)
        cv = self.cv
        rise = self.size * 0.7
        for i, (it, x, y) in enumerate(self.items):
            d = delay + st(i, n)
            if mode == "revolve":
                cv.coords(it, x, y + rise * 0.5)
                cv.itemconfigure(it, angle=75)

                def upd(e, it=it, x=x, y=y):
                    cv.coords(it, x, y + rise * 0.5 * (1 - e))
                    # rotation completes in the first 60% (rotated glyphs are the expensive part to draw)
                    cv.itemconfigure(it, angle=75 * max(0.0, 1 - e / 0.6), fill=mix(self.bg, self.fg, e * 1.6))
                self.E.animate(dur, upd, delay=d, easing=easing or "outBack", owner=self.page)
            elif mode == "drop":
                cv.coords(it, x, y - rise)

                def upd(e, it=it, x=x, y=y):
                    cv.coords(it, x, y - rise * (1 - e))
                    cv.itemconfigure(it, fill=mix(self.bg, self.fg, e * 1.5))
                self.E.animate(dur, upd, delay=d, easing=easing or "outBounce", owner=self.page)
            else:
                cv.coords(it, x, y + rise)

                def upd(e, it=it, x=x, y=y):
                    cv.coords(it, x, y + rise * (1 - e))
                    cv.itemconfigure(it, fill=mix(self.bg, self.fg, e * 1.4))
                self.E.animate(dur, upd, delay=d, easing=easing or "outExpo", owner=self.page)
        end = delay + st(n - 1, n) + dur if n else delay
        self.E.after(end + 60, self._merge, owner=self.page)
        return end

    def _merge(self):
        """Once the per-letter animation is over, swap the N glyph items for ONE text item.
        Big display type is expensive to redraw letter-by-letter on every scroll frame."""
        if not self.items or self.tracking:
            return
        cv = self.cv
        first, x0, y0 = self.items[0]
        try:
            cx, cy = cv.coords(first)
        except (ValueError, tk.TclError):
            return
        it = cv.create_text(self.x + (cx - x0), self.y + (cy - y0), text=self.text, font=self.font, fill=self.fg,
                            anchor="sw", tags=self.tags)
        cv.tag_raise(it, first)
        for i, _, _ in self.items:
            cv.delete(i)
        self.items = []

    def wave(self, amp=8, step=60, dur=500):
        """A playful one-off hop through the word (hover effect)."""
        cv = self.cv
        for i, (it, x, y) in enumerate(self.items):
            self.E.animate(dur, lambda e, it=it, x=x, y=y: cv.coords(it, x, y - amp * math.sin(e * math.pi)),
                           delay=i * step, easing="outQuad", owner=self.page)

    def set_fill(self, c):
        for it, _, _ in self.items:
            self.cv.itemconfigure(it, fill=c)


# --------------------------------------------------------------------------- #
#  RotatingBadge
# --------------------------------------------------------------------------- #
class RotatingBadge:
    """Circular spinning text. The ring of letters is ONE pre-rendered transparent image that is
    rotated (frames cached every 2 degrees) - was ~40 rotated text items repainted every frame."""

    STEP = 2  # degrees per cached frame

    def __init__(self, page, cx, cy, r, text, fg, fill=None, center="\u2605", center_fg=None,
                 font=None, speed=0.45, tags=()):
        self.page, self.cv = page, page.cv
        self.cx, self.cy, self.r = cx, cy, r
        self.rot = 0.0
        self.speed = speed
        cv = self.cv
        size = abs((font or F("mono", 13, "bold"))[1])
        self.tag = f"badge{id(self)}"
        t = (self.tag,) + tuple(tags)
        if fill:
            cv.create_oval(cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26, fill=fill, outline="", tags=t)
        self.center = cv.create_text(cx, cy, text=center, font=F("display", int(r * 0.9)),
                                     fill=center_fg or fg, tags=t)
        self.base = self._render_ring(text, fg, size)
        self.frames = {}
        self.item = cv.create_image(cx, cy, image="", tags=t)
        self.scale = 0.0
        self._idx = None
        self._last = 0
        self._show()
        page.E.frame(self._tick, owner=page)

    def _render_ring(self, text, fg, size):
        S = bake.SS
        R = (self.r + size) * S
        D = int(R * 2 + 4 * S)
        ring = Image.new("RGBA", (D, D), (0, 0, 0, 0))
        f = bake.font("mono", size * S, True)
        n = len(text)
        c = D / 2
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            th = -math.pi / 2 + i * 2 * math.pi / n
            g = Image.new("RGBA", (size * 2 * S, size * 2 * S), (0, 0, 0, 0))
            from PIL import ImageDraw
            ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=fg, anchor="mm")
            g = g.rotate(-(math.degrees(th) + 90), resample=Image.BICUBIC, expand=True)
            x = c + self.r * S * math.cos(th) - g.width / 2
            y = c + self.r * S * math.sin(th) - g.height / 2
            ring.alpha_composite(g, (int(x), int(y)))
        return ring.resize((D // S, D // S), Image.LANCZOS)

    def _frame(self, idx):
        ph = self.frames.get(idx)
        if ph is None:
            ph = self.frames[idx] = ImageTk.PhotoImage(
                self.base.rotate(-idx * self.STEP, resample=Image.BICUBIC))
        return ph

    def _show(self):
        if self.scale <= 0.02:
            self.cv.itemconfigure(self.item, state="hidden")
            return
        self.cv.itemconfigure(self.item, state="normal")
        idx = int(math.degrees(self.rot) // self.STEP) % (360 // self.STEP)
        if abs(self.scale - 1) < 0.002:
            if idx != self._idx:
                self._idx = idx
                self.cv.itemconfigure(self.item, image=self._frame(idx))
            return
        # popping in: scaled (uncached) frame
        im = self.base.rotate(-idx * self.STEP, resample=Image.BILINEAR)
        k = max(0.05, self.scale)
        im = im.resize((max(2, int(im.width * k)), max(2, int(im.height * k))), Image.BILINEAR)
        self._pop_ph = ImageTk.PhotoImage(im)
        self._idx = None
        self.cv.itemconfigure(self.item, image=self._pop_ph)

    def _tick(self, dt, now):
        if not self.page.visible(self.cy - self.r - 200, self.cy + self.r + 200):
            return True
        boost = 1 + min(6, abs(self.page.velocity) / 350)
        self.rot += dt * self.speed * boost
        if now - self._last > 0.03:
            self._last = now
            self._show()
        return True

    def pop(self, delay=0):
        self.page.E.tween(0, 1, lambda v: setattr(self, "scale", v), duration=1300, delay=delay,
                          easing="outElastic", owner=self.page, complete=lambda: setattr(self, "scale", 1.0))
        self.cv.itemconfigure(self.center, angle=0)
        self.page.E.animate(1200, lambda e: self.cv.itemconfigure(self.center, angle=360 * (1 - e)),
                            delay=delay, easing="outExpo", owner=self.page)


# --------------------------------------------------------------------------- #
#  Marquee
# --------------------------------------------------------------------------- #
class Marquee:
    def __init__(self, page, y, h, text, bg, fg, font=None, speed=90, direction=-1, outline=None):
        self.page, self.cv = page, page.cv
        self.y, self.h = y, h
        self.speed, self.dir = speed, direction
        font = font or F("display", int(h * 0.52))
        cv = self.cv
        cv.create_rectangle(-10, y, page.W + 10, y + h, fill=bg, outline=outline or bg, width=2)
        self.tw = theme.measure(font, text)
        n = int(page.W / max(1, self.tw)) + 2
        self.items = [cv.create_text(i * self.tw, y + h / 2 + 1, text=text, font=font, fill=fg, anchor="w")
                      for i in range(n)]
        self.off = 0.0
        self._last = 0
        page.E.frame(self._tick, owner=page)

    def _tick(self, dt, now):
        if not self.page.visible(self.y, self.y + self.h):
            return True
        v = self.page.velocity
        boost = 1 + min(5, abs(v) / 250)
        self.off = (self.off + self.speed * boost * dt) % self.tw
        if now - self._last > 0.016:
            self._last = now
            for i, it in enumerate(self.items):
                x = i * self.tw - self.off if self.dir < 0 else (i - 1) * self.tw + self.off
                self.cv.coords(it, x, self.y + self.h / 2 + 1)
        return True


_DECORATED = {}      # (product, size, badges) -> PIL photo with pills baked in
_DECORATED_TK = {}   # same -> PhotoImage
_INFO_TK = {}


def _info_tk(p, w, pal):
    key = (p["id"], w, pal["bg"], pal["fg"], pal["accent"])
    ph = _INFO_TK.get(key)
    if ph is None:
        ph = _INFO_TK[key] = ImageTk.PhotoImage(bake.card_info(p, w, pal))
    return ph


# --------------------------------------------------------------------------- #
#  ProductCard
# --------------------------------------------------------------------------- #
class ProductCard:
    def __init__(self, page, p, x, y, w, img_h, pal=LIGHT, rank=None, best=None):
        self.page, self.cv, self.E, self.A = page, page.cv, page.E, page.A
        self.p, self.x, self.y, self.w, self.ih = p, x, y, w, img_h
        self.pal = pal
        self.rank, self.best = rank, best
        self.h = img_h + 118
        self.tag = f"card{id(self)}"
        self.revealed = False
        self.lift = 0.0
        self._lift_tw = None
        self.band = 0.0
        self.img_item = None
        self._hv_on = False
        self._build()
        page.warm.append((y, self._prewarm))
        t = page
        self.z_main = t.zone(lambda: (self.x, self.y, self.x + self.w, self.y + self.h),
                             click=self.open, enter=lambda: self._hover(True), leave=self._maybe_leave, z=5)
        hx, hy = lambda: self.x + self.w - 26, lambda: self.y + 26
        self.z_heart = t.zone(lambda: (hx() - 18, hy() - 18, hx() + 18, hy() + 18), click=self.toggle_wish,
                              z=8, enter=lambda: self._hover(True), leave=self._maybe_leave)
        ax, ay = lambda: self.x + self.w - 22, lambda: self.y + img_h + 74
        self.z_add = t.zone(lambda: (ax() - 22, ay() - 22, ax() + 22, ay() + 22), click=self.add,
                            enter=self._add_hover_on, leave=self._add_hover_off, z=8)

    def _maybe_leave(self):
        if not (self.z_main.hovered or self.z_heart.hovered or self.z_add.hovered):
            self._hover(False)

    # ------------------------------------------------------------------ #
    def _build(self):
        """Only the interactive bits are live canvas items; photo badges + the text block are baked."""
        cv, p, pal, x, y, w, ih = self.cv, self.p, self.pal, self.x, self.y, self.w, self.ih
        t = (self.tag, "card")
        bg = pal["bg"]
        self.i_ph = cv.create_rectangle(x, y, x + w, y + ih, fill=pal["ph"], outline="", tags=t)
        # quick-view band (grows on hover)
        self.i_band = cv.create_rectangle(x, y + ih, x + w, y + ih, fill=theme.INK, outline="", state="hidden", tags=t)
        self.i_band_t = cv.create_text(x + w / 2, y + ih - 20, text="QUICK VIEW  \u2192", font=F("heavy", 13),
                                       fill=theme.INK, state="hidden", tags=t)
        # heart
        hx, hy = x + w - 26, y + 26
        self.i_heart_bg = cv.create_oval(hx - 17, hy - 17, hx + 17, hy + 17, fill=theme.WHITE, outline="",
                                         state="hidden", tags=t)
        wished = p["id"] in self.page.app.wish
        self.i_heart = cv.create_text(hx, hy + 1, text="\u2665" if wished else "\u2661", font=F("body", 20),
                                      fill=theme.ACCENT if wished else theme.INK, state="hidden", tags=t)
        self.i_info = None
        self.info_frames = []
        # add button
        ax, ay = x + w - 22, y + ih + 74
        self.i_add = cv.create_oval(ax - 21, ay - 21, ax + 21, ay + 21, fill=bg, outline=bg, width=2, tags=t)
        self.i_add_t = cv.create_text(ax, ay - 1, text="+", font=F("heavy", 20), fill=bg, tags=t)
        self.add_ang = 0.0

    def _prewarm(self):
        self._photo_tk()
        _info_tk(self.p, self.w, self.pal)

    def _photo_pil(self):
        p = self.p
        key = (p["id"], self.w, self.ih, self.rank, self.best, self.pal.get("badge", theme.LIME))
        im = _DECORATED.get(key)
        if im is None:
            base = self.A.cover(p["cat"], p["img"], self.w, self.ih, p["focus"])
            im = _DECORATED[key] = bake.decorate(base, p, self.rank, self.best, self.pal.get("badge", theme.LIME))
        return im, key

    def _photo_tk(self):
        im, key = self._photo_pil()
        ph = _DECORATED_TK.get(key)
        if ph is None:
            ph = _DECORATED_TK[key] = ImageTk.PhotoImage(im)
        return ph

    # ------------------------------------------------------------------ #
    def reveal(self, delay=0, mode="flip"):
        if self.revealed:
            return
        self.revealed = True
        cv, pal = self.cv, self.pal
        p = self.p
        # image: revolve-in (Y axis flip) built from on-demand squashed frames
        base, _ = self._photo_pil()
        cache = {}
        bgph = pal["ph"]
        cx, cy = self.x + self.w / 2, self.y + self.ih / 2
        self.img_item = cv.create_image(cx, cy, image="", tags=(self.tag, "card"))
        cv.tag_raise(self.img_item, self.i_ph)
        holder = {}

        def frame(e):
            if not self.revealed:
                return
            th = (math.pi / 2) * (1 - min(1.0, e))
            k = max(0.02, math.cos(th))
            q = round(k * 6) / 6
            ph = cache.get(q)
            if ph is None:
                fw = max(2, int(self.w * q))
                fh = max(2, int(self.ih * (0.88 + 0.12 * q)))
                im = base.resize((fw, fh), Image.BILINEAR)
                if q < 0.98:
                    im = Image.blend(im, Image.new("RGB", im.size, bgph), (1 - q) * 0.6)
                ph = ImageTk.PhotoImage(im)
                cache[q] = ph
            holder["ph"] = ph
            cv.itemconfigure(self.img_item, image=ph)
            cv.coords(self.img_item, self.x + self.w / 2, self.y + self.ih / 2 - self.lift)

        def done():
            holder["ph"] = self._photo_tk()
            cv.itemconfigure(self.img_item, image=holder["ph"])
            cv.itemconfigure(self.i_ph, state="hidden")
            cache.clear()
            self._order()

        if mode == "flip":
            self.E.animate(900, frame, delay=delay, easing="outBack", complete=done, owner=self.page,
                           begin=lambda: frame(0))
        else:
            self.E.after(delay, done, owner=self.page)

        def show_extras():
            for it in (self.i_heart_bg, self.i_heart):
                cv.itemconfigure(it, state="normal")
            self._order()
        self.E.after(delay + 450, show_extras, owner=self.page)

        # baked text block fades in from the background colour
        def show_info():
            self.info_ph = _info_tk(p, self.w, pal)
            y0 = self.y + self.ih
            self.i_info = cv.create_image(self.x, y0, image=self.info_ph, anchor="nw", tags=(self.tag, "card"))
            cv.tag_lower(self.i_info, self.i_add)
            # wipe: a background-coloured cover slides off to the right (1 temporary item, no new bitmaps)
            cover = cv.create_rectangle(self.x - 1, y0, self.x + self.w + 1, y0 + 118, fill=pal["bg"], outline="",
                                        tags=(self.tag, "card"))
            x0 = self.x

            def upd(e):
                dx = self.x - x0
                cv.coords(cover, x0 + dx + self.w * e, y0, x0 + dx + self.w + 1, y0 + 118)
            self.E.animate(560, upd, easing="inOutCubic", owner=self.page, complete=lambda: cv.delete(cover))
        self.E.after(delay + 250, show_info, owner=self.page)
        self.E.animate(600, lambda e: (cv.itemconfigure(self.i_add, outline=mix(pal["bg"], pal["fg"], e)),
                                       cv.itemconfigure(self.i_add_t, fill=mix(pal["bg"], pal["fg"], e))),
                       delay=delay + 500, owner=self.page)

    def _order(self):
        cv = self.cv
        if self.img_item:
            cv.tag_raise(self.i_band, self.img_item)
        cv.tag_raise(self.i_band_t, self.i_band)
        for it in (self.i_heart_bg, self.i_heart):
            cv.tag_raise(it)
        self.page.raise_hud()

    # ------------------------------------------------------------------ #
    def _hover(self, on):
        if not self.revealed or on == self._hv_on:
            return
        self._hv_on = on
        if self._lift_tw:
            self._lift_tw.cancel()
        a = self.lift
        b = 8.0 if on else 0.0
        cv = self.cv
        ih, x, y, w = self.ih, self.x, self.y, self.w
        cv.itemconfigure(self.i_band_t, state="normal" if on else "hidden")
        cv.itemconfigure(self.i_band, state="normal")

        def upd(e):
            v = a + (b - a) * e
            d = v - self.lift
            self.lift = v
            if self.img_item:
                cv.move(self.img_item, 0, -d)
            for it in (self.i_heart_bg, self.i_heart):
                cv.move(it, 0, -d)
            bh = 44 * (v / 8.0)
            cv.coords(self.i_band, self.x, self.y + ih - bh - self.lift, self.x + w, self.y + ih - self.lift)
            cv.coords(self.i_band_t, self.x + w / 2, self.y + ih - bh / 2 - self.lift)
            cv.itemconfigure(self.i_band_t, fill=mix(theme.INK, theme.LIME, v / 8.0))
            if v <= 0.05:
                cv.itemconfigure(self.i_band, state="hidden")
        self._lift_tw = self.E.animate(380, upd, easing="outCubic", owner=self.page)

    def _add_hover_on(self):
        self._hover(True)
        self._spin_add(1)

    def _add_hover_off(self):
        self._spin_add(0)
        self._maybe_leave()

    def _spin_add(self, on):
        cv, pal = self.cv, self.pal
        cv.itemconfigure(self.i_add, fill=pal["accent"] if on else pal["bg"],
                         outline=pal["accent"] if on else pal["fg"])
        cv.itemconfigure(self.i_add_t, fill=theme.INK if on else pal["fg"])
        a0 = self.add_ang
        a1 = 90.0 if on else 0.0

        def upd(e):
            self.add_ang = a0 + (a1 - a0) * e
            cv.itemconfigure(self.i_add_t, angle=self.add_ang)
        self.E.animate(420, upd, easing="outBack", owner=self.page)

    def toggle_wish(self):
        w = self.page.app.wish
        pid = self.p["id"]
        on = pid not in w
        if on:
            w.add(pid)
        else:
            w.discard(pid)
        cv = self.cv
        cv.itemconfigure(self.i_heart, text="♥" if on else "♡", fill=theme.ACCENT if on else theme.INK)
        hx, hy = self.x + self.w - 26, self.y + 26 - self.lift
        # pop: grow the heart font with an elastic ease
        self.E.animate(700, lambda e: cv.itemconfigure(self.i_heart, font=F("body", int(20 + 14 * math.sin(min(1, e) * math.pi)))),
                       easing="outQuad", owner=self.page)
        if on:
            self.page.app.toast("SAVED TO WISHLIST", self.p, sub="♥  " + self.p["name"])
        _ = (hx, hy)

    def add(self):
        sizes = CATS[self.p["cat"]]["sizes"]
        self.page.app.add_to_cart(self.p, sizes[len(sizes) // 2])
        cv = self.cv
        cv.itemconfigure(self.i_add_t, text="✓")
        self.E.after(1300, lambda: cv.itemconfigure(self.i_add_t, text="+"), owner=self.page)

    def open(self):
        QuickView(self.page, self.p)

    # ------------------------------------------------------------------ #
    def shift(self, dx):
        self.cv.move(self.tag, dx, 0)
        self.x += dx

    def move_to(self, nx, ny, delay=0, dur=900, easing="outExpo"):
        dx, dy = nx - self.x, ny - self.y
        if dx == 0 and dy == 0:
            return
        sx, sy = self.x, self.y
        done = [0.0, 0.0]

        def upd(e):
            ddx, ddy = dx * e - done[0], dy * e - done[1]
            self.cv.move(self.tag, ddx, ddy)
            done[0] += ddx
            done[1] += ddy
            self.x, self.y = sx + done[0], sy + done[1]
        self.E.animate(dur, upd, delay=delay, easing=easing, owner=self.page)

    def flip_swap(self, newp, delay=0):
        """Revolve out -> swap product -> revolve in (used by filter toggles)."""
        cv = self.cv

        def out():
            cv.delete(self.tag)
            for z in (self.z_main, self.z_heart, self.z_add):
                self.page.remove_zone(z)
            nc = None
            if newp is not None:
                nc = ProductCard(self.page, newp, self.x, self.y, self.w, self.ih, self.pal,
                                 rank=self.rank, best=self.best)
                nc.reveal(0)
            self.replaced_by = nc
            self.swapped = True
        # squash current image
        if self.img_item:
            base, _ = self._photo_pil()
            holder = {}

            def upd(e):
                k = max(0.03, math.cos(e * math.pi / 2))
                im = base.resize((max(2, int(self.w * k)), self.ih), Image.BILINEAR)
                holder["ph"] = ImageTk.PhotoImage(im)
                cv.itemconfigure(self.img_item, image=holder["ph"])
            self.E.animate(320, upd, delay=delay, easing="inQuad", complete=out, owner=self.page)
            if self.i_info:
                self.E.after(delay, lambda: cv.itemconfigure(self.i_info, state="hidden"), owner=self.page)
        else:
            self.E.after(delay, out, owner=self.page)


# --------------------------------------------------------------------------- #
#  Rail  (horizontal slider of cards)
# --------------------------------------------------------------------------- #
class Track:
    """Smooth horizontal track shared by the product + review rails.
    Cards glide toward (x0 + i*step - offset). Arrow buttons jump a card at a time; touchpad swipes
    move the offset directly (1:1 feel), rubber-band past the ends, then snap to the nearest card."""

    def __init__(self, page, cards, x0, step, visible, y1, y2):
        self.page, self.cards, self.x0, self.step, self.visible = page, cards, x0, step, visible
        self.off = 0.0
        self.loop = None
        self.last_swipe = 0.0
        page.hzone(lambda: (0, y1, page.W, y2), self.swipe)

    @property
    def max_off(self):
        return max(0, (len(self.cards) - self.visible) * self.step)

    def _kick(self):
        if self.loop is None:
            self.loop = self.page.E.frame(self._tick, owner=self.page)

    def _tick(self, dt, now):
        base = 1 - pow(0.00003, dt)                 # ~15% per frame
        lead = self.off / self.step
        moving = False
        for i, c in enumerate(self.cards):
            d = self.x0 + i * self.step - self.off - c.x
            if abs(d) > 0.6:
                lag = 1 - 0.06 * min(abs(i - lead), 5)  # far cards trail a little -> elastic wave
                c.shift(d * base * lag)
                moving = True
            elif d:
                c.shift(d)
        if not moving:
            self.loop = None
            return False
        return True

    def go(self, index):
        n_max = self.max_off / self.step if self.step else 0
        index = max(0, min(n_max, index))
        self.off = index * self.step
        self._kick()

    def slide(self, d):
        cur = round(self.off / self.step)
        tgt = cur + d
        if tgt < 0 or tgt * self.step > self.max_off + 1:
            # rubber-band bump at the ends
            self.off = cur * self.step + 46 * d
            self._kick()
            self.page.E.after(170, lambda: self.go(cur), owner=self.page)
            return
        self.go(tgt)

    def swipe(self, dx):
        o = self.off + dx
        if o < 0 or o > self.max_off:               # resist past the ends
            o = self.off + dx * 0.35
            o = max(-140, min(self.max_off + 140, o))
        self.off = o
        self._kick()
        self.last_swipe = self.page.E.now()
        self.page.E.after(170, self._settle, owner=self.page)

    def _settle(self):
        if self.page.E.now() - self.last_swipe >= 0.16:
            self.go(round(self.off / self.step))


class Rail:
    def __init__(self, page, products, x, y, w, img_h, gap=24, visible=4, pal=LIGHT, ranks=False):
        self.page = page
        self.cards = []
        self.step = w + gap
        self.visible = visible
        for i, p in enumerate(products):
            self.cards.append(ProductCard(page, p, x + i * self.step, y, w, img_h, pal,
                                          rank=(i + 1) if ranks else None))
        self.h = self.cards[0].h if self.cards else 0
        self.track = Track(page, self.cards, x, self.step, visible, y, y + self.h)

    def reveal(self, delay=0):
        for i, c in enumerate(self.cards):
            c.reveal(delay + (i if i < self.visible + 1 else self.visible) * 110)

    def slide(self, d):
        self.track.slide(d)


# --------------------------------------------------------------------------- #
#  RevolvingRing  (3D carousel)
# --------------------------------------------------------------------------- #
class RevolvingRing:
    def __init__(self, page, products, cx, base_y, rx, img_w, img_h, bg, levels=14, lift=70,
                 on_front=None, speed=0.22):
        self.page, self.cv, self.E, self.A = page, page.cv, page.E, page.A
        self.products = products
        self.n = len(products)
        self.cx, self.base_y, self.rx = cx, base_y, rx
        self.iw, self.ih = img_w, img_h
        self.L = levels
        self.lift = lift
        self.min_scale = 0.40
        self.on_front = on_front
        self.speed = speed
        self.rot = 0.0
        self.spin_tw = None
        self.drag_from = None
        self.hovering = False
        self.front = -1
        self.order = []
        self.scale = 0.0          # intro "unfold" from the centre
        self.active = False
        self.tag = f"ring{id(self)}"
        cv = self.cv
        cv.create_oval(cx - rx - img_w * 0.3, base_y - 26, cx + rx + img_w * 0.3, base_y + 26,
                       outline=mix(bg, theme.BONE, 0.22), dash=(3, 7), width=2, tags=(self.tag,))
        self.frames = [self.A.depth_levels(p["cat"], p["img"], img_w, img_h, levels, p["focus"], bg,
                                           self.min_scale) for p in products]
        self.items = [cv.create_image(cx, base_y, image=self.frames[i][0], anchor="s", state="hidden",
                                      tags=(self.tag,)) for i in range(self.n)]
        self.boxes = [(0, 0, 0, 0)] * self.n
        self.zone = page.zone(lambda: (cx - rx - img_w, base_y - img_h - lift, cx + rx + img_w, base_y + 10),
                              click=self._click, press=self._press, drag=self._drag, release=self._release,
                              enter=lambda: setattr(self, "hovering", True),
                              leave=lambda: setattr(self, "hovering", False), z=6, cursor="hand2")
        self._last = 0
        self.swipe_t = 0.0
        page.hzone(lambda: (cx - rx - img_w, base_y - img_h - lift, cx + rx + img_w, base_y + 10), self.swipe)
        page.E.frame(self._tick, owner=page)

    def swipe(self, dx):
        """Touchpad sideways swipe spins the ring; it snaps to the nearest piece when you stop."""
        if not self.active:
            return
        if self.spin_tw:
            self.spin_tw.cancel()
            self.spin_tw = None
        self.rot -= dx * 0.0034
        self.swipe_t = self.E.now()
        self.E.after(220, self._swipe_settle, owner=self.page)

    def _swipe_settle(self):
        if self.E.now() - self.swipe_t >= 0.2 and self.drag_from is None:
            n = self.n
            self.spin_to(int(round(-self.rot / (2 * math.pi / n)) % n), dur=800)

    def start(self, delay=0):
        def go():
            self.active = True
            for it in self.items:
                self.cv.itemconfigure(it, state="normal")
            self.E.tween(0, 1, lambda v: setattr(self, "scale", v), duration=1600, easing="outExpo",
                         owner=self.page)
            self.E.tween(self.rot + math.pi * 1.5, self.rot, lambda v: setattr(self, "rot", v), duration=2000,
                         easing="outExpo", owner=self.page)
        self.E.after(delay, go, owner=self.page)

    def _layout(self):
        cv = self.cv
        n = self.n
        depth = []
        for i in range(n):
            a = self.rot + i * 2 * math.pi / n
            d = (math.cos(a) + 1) / 2
            x = self.cx + self.rx * math.sin(a) * self.scale
            y = self.base_y - (1 - d) * self.lift
            lvl = int(round(d * (self.L - 1)))
            s = self.min_scale + (1 - self.min_scale) * lvl / (self.L - 1)
            cv.itemconfigure(self.items[i], image=self.frames[i][lvl])
            cv.coords(self.items[i], x, y)
            w2, h = self.iw * s / 2, self.ih * s
            self.boxes[i] = (x - w2, y - h, x + w2, y)
            depth.append((d, i))
        depth.sort()
        order = [i for _, i in depth]
        if order != self.order:
            self.order = order
            for i in order:
                cv.tag_raise(self.items[i])
            self.page.raise_hud()
        front = order[-1]
        if front != self.front:
            self.front = front
            if self.on_front:
                self.on_front(self.products[front])

    def _tick(self, dt, now):
        if not self.active:
            return True
        vis = self.page.visible(self.base_y - self.ih - self.lift - 40, self.base_y + 40)
        if not vis:
            return True
        if self.spin_tw is None and self.drag_from is None and not self.hovering and now - self.swipe_t > 0.6:
            self.rot -= self.speed * dt
        if now - self._last > 0.022:
            self._last = now
            self._layout()
        return True

    def spin_to(self, i, dur=1100):
        n = self.n
        target = -i * 2 * math.pi / n
        cur = self.rot
        k = round((cur - target) / (2 * math.pi))
        target += k * 2 * math.pi
        if self.spin_tw:
            self.spin_tw.cancel()

        def fin():
            self.spin_tw = None
        self.spin_tw = self.E.tween(cur, target, lambda v: setattr(self, "rot", v), duration=dur,
                                    easing="outExpo", owner=self.page, complete=fin)

    def step(self, d):
        self.spin_to((self.front + d) % self.n)

    def _hit_item(self, x, y):
        cy = y + self.page.applied
        for i in reversed(self.order):
            x1, y1, x2, y2 = self.boxes[i]
            if x1 <= x <= x2 and y1 <= cy <= y2:
                return i
        return None

    def _click(self):
        mx, my = self.page.mouse
        i = self._hit_item(mx, my)
        if i is None:
            return
        if i == self.front:
            QuickView(self.page, self.products[i])
        else:
            self.spin_to(i)

    def _press(self, x, y):
        self.drag_from = (x, self.rot)
        if self.spin_tw:
            self.spin_tw.cancel()
            self.spin_tw = None

    def _drag(self, x, y):
        if self.drag_from:
            x0, r0 = self.drag_from
            self.rot = r0 + (x - x0) * 0.006

    def _release(self, x, y):
        self.drag_from = None
        # snap to nearest item
        n = self.n
        i = round(-self.rot / (2 * math.pi / n)) % n
        self.spin_to(int(i), dur=900)


# --------------------------------------------------------------------------- #
#  Accordion  (hover-expand editorial strips)
# --------------------------------------------------------------------------- #
class Accordion:
    def __init__(self, page, products, x, y, total_w, h, collapsed=128, gap=10, pal=DARK):
        self.page, self.cv, self.E, self.A = page, page.cv, page.E, page.A
        self.ps = products
        self.n = len(products)
        self.x, self.y, self.tw, self.h = x, y, total_w, h
        self.c, self.gap = collapsed, gap
        self.e = total_w - collapsed * (self.n - 1) - gap * (self.n - 1)
        self.widths = [float(self.e if i == 0 else collapsed) for i in range(self.n)]
        self.active = 0
        self.tws = []
        self.lru = {}
        self.pal = pal
        self.shown = False
        cv = self.cv
        self.tag = f"acc{id(self)}"
        self.imgs, self.vlabels, self.vbg, self.nums = [], [], [], []
        for i, p in enumerate(products):
            self.imgs.append(cv.create_image(x, y, anchor="nw", state="hidden", tags=(self.tag,)))
            self.vbg.append(cv.create_rectangle(0, 0, 0, 0, fill=theme.INK, outline="", state="hidden", tags=(self.tag,)))
            self.vlabels.append(cv.create_text(0, 0, text=p["name"].upper(), angle=90, anchor="w",
                                               font=F("display", 22), fill=theme.BONE, state="hidden", tags=(self.tag,)))
            self.nums.append(cv.create_text(0, 0, text=f"0{i + 1}", anchor="nw", font=F("mono", 12, "bold"),
                                            fill=theme.INK, state="hidden", tags=(self.tag,)))
        # info block for the active strip
        self.info_bg = cv.create_rectangle(0, 0, 0, 0, fill=theme.INK, outline="", state="hidden", tags=(self.tag,))
        self.info_name = cv.create_text(0, 0, text="", anchor="nw", font=F("display", 34), fill=theme.BONE,
                                        state="hidden", tags=(self.tag,))
        self.info_sub = cv.create_text(0, 0, text="", anchor="nw", font=F("mono", 12), fill=theme.LIME,
                                       state="hidden", tags=(self.tag,))
        self.offs = [0.0] * self.n
        self.dirty = False
        for i in range(self.n):
            page.zone(lambda i=i: self._box(i), enter=lambda i=i: self.set_active(i),
                      click=lambda i=i: QuickView(self.page, self.ps[i]), z=6)
        self.swipe_acc = 0.0
        page.hzone((x, y, x + total_w, y + h), self.swipe)
        page.E.frame(self._tick, owner=page)

    def swipe(self, dx):
        self.swipe_acc += dx
        if abs(self.swipe_acc) >= 70:
            step = 1 if self.swipe_acc > 0 else -1
            self.swipe_acc = 0.0
            self.set_active(max(0, min(self.n - 1, self.active + step)))

    def _box(self, i):
        x = self.x + sum(self.widths[:i]) + self.gap * i
        return (x, self.y, x + self.widths[i], self.y + self.h)

    def _img(self, i, w):
        q = max(16, int(w // 16 * 16))
        key = (i, q)
        ph = self.lru.get(key)
        if ph is None:
            p = self.ps[i]
            base = self.A.cover(p["cat"], p["img"], int(self.e), self.h, p["focus"])
            x0 = (int(self.e) - q) // 2
            ph = ImageTk.PhotoImage(base.crop((x0, 0, x0 + q, self.h)))
            if len(self.lru) > 160:
                self.lru.pop(next(iter(self.lru)))
            self.lru[key] = ph
        return ph, q

    def _tick(self, dt, now):
        if self.dirty and self.page.visible(self.y - 40, self.y + self.h + 40):
            self.dirty = False
            self.layout()
        return True

    def layout(self):
        cv = self.cv
        x = self.x
        vf = F("display", 22)
        for i in range(self.n):
            w = self.widths[i]
            off = self.offs[i]
            ph, q = self._img(i, w)
            cv.itemconfigure(self.imgs[i], image=ph)
            cv.coords(self.imgs[i], x + off + (w - q) / 2, self.y)
            openness = (w - self.c) / (self.e - self.c)
            st = "normal" if (openness < 0.35 and self.shown and off < 2) else "hidden"
            tw = theme.measure(vf, self.ps[i]["name"].upper())
            cv.itemconfigure(self.vbg[i], state=st)
            cv.itemconfigure(self.vlabels[i], state=st)
            cv.coords(self.vbg[i], x + 12, self.y + self.h - tw - 40, x + 50, self.y + self.h - 12)
            cv.coords(self.vlabels[i], x + 31, self.y + self.h - 26)
            cv.coords(self.nums[i], x + off + 14, self.y + 14)
            cv.itemconfigure(self.nums[i], fill=theme.BONE if openness < 0.5 else theme.LIME)
            if i == self.active:
                ib = (x + 18, self.y + self.h - 108, x + w - 18, self.y + self.h - 18)
                cv.coords(self.info_bg, *ib)
                cv.coords(self.info_name, ib[0] + 20, ib[1] + 12)
                cv.coords(self.info_sub, ib[0] + 22, ib[1] + 60)
                vis = openness > 0.85 and self.shown
                for it in (self.info_bg, self.info_name, self.info_sub):
                    cv.itemconfigure(it, state="normal" if vis else "hidden")
            x += w + self.gap
        cv.tag_raise(self.info_bg)
        cv.tag_raise(self.info_name)
        cv.tag_raise(self.info_sub)
        self.page.raise_hud()

    def reveal(self, delay=0):
        """Strips slide in from the right one by one, then the first one blooms open."""
        cv = self.cv
        cv.itemconfigure(self.tag, state="hidden")
        self.widths = [float(self.c)] * self.n
        self.offs = [float(self.tw)] * self.n

        def go():
            self.shown = True
            for i in range(self.n):
                cv.itemconfigure(self.imgs[i], state="normal")
                cv.itemconfigure(self.nums[i], state="normal")

            def mk(i):
                def upd(v):
                    self.offs[i] = v
                    self.dirty = True
                return upd
            for i in range(self.n):
                self.E.tween(self.tw - i * 40, 0, mk(i), duration=1200, delay=i * 110, easing="outExpo",
                             owner=self.page)
            self.E.after(650, lambda: self.set_active(0, force=True), owner=self.page)
        self.E.after(delay, go, owner=self.page)
        self._update_info()
        self.dirty = True

    def _update_info(self):
        p = self.ps[self.active]
        self.cv.itemconfigure(self.info_name, text=p["name"].upper())
        self.cv.itemconfigure(self.info_sub, text=f"{rupee(p['price'])}   ·   {'  /  '.join(p['tags'])}   ·   VIEW →")

    def set_active(self, i, force=False):
        if (i == self.active and not force) or not self.shown:
            return
        self.active = i
        self._update_info()
        for t in self.tws:
            t.cancel()
        start = list(self.widths)
        target = [float(self.e if k == i else self.c) for k in range(self.n)]

        def upd(e):
            self.widths = [a + (b - a) * e for a, b in zip(start, target)]
            self.dirty = True
        self.tws = [self.E.animate(750, upd, easing="outExpo", owner=self.page)]


# --------------------------------------------------------------------------- #
#  quote + section header
# --------------------------------------------------------------------------- #
def quote_block(page, y, quote, author, bg, fg, accent=theme.ACCENT, size=56, width=None):
    cv, E = page.cv, page.E
    W = page.W
    width = width or W - 260
    font = F("serif", size, "italic")
    lines = theme.wrap(font, quote, width)
    lh = theme.line_h(font)
    top = y + 70
    cv.create_rectangle(0, y, W, y + 140 + lh * len(lines) + 60, fill=bg, outline="")
    qm = cv.create_text(W / 2, y + 40, text="“", font=F("serif", 150), fill=bg)
    words = []
    for li, line in enumerate(lines):
        ws = line.split(" ")
        sp = theme.measure(font, " ")
        lw = theme.measure(font, line)
        x = (W - lw) / 2
        for w in ws:
            ww = theme.measure(font, w)
            it = cv.create_text(x, top + li * lh + lh, text=w, font=font, fill=bg, anchor="sw")
            words.append((it, x, top + li * lh + lh, li))
            x += ww + sp
    by = top + lh * len(lines) + 34
    au = cv.create_text(W / 2, by, text="—  " + author, font=F("mono", 14, "bold"), fill=bg)
    rule = cv.create_rectangle(W / 2, by + 26, W / 2, by + 29, fill=accent, outline="")
    total = by + 60 - y

    def play():
        E.animate(900, lambda e: (cv.itemconfigure(qm, fill=mix(bg, accent, e)),
                                  cv.coords(qm, W / 2, y + 40 + 30 * (1 - e))), easing="outBack", owner=page)
        for i, (it, x, yy, _li) in enumerate(words):
            def upd(e, it=it, x=x, yy=yy):
                cv.coords(it, x, yy + 36 * (1 - e))
                cv.itemconfigure(it, fill=mix(bg, fg, e * 1.3))
            E.animate(950, upd, delay=150 + i * 70, easing="outExpo", owner=page)
        d = 150 + len(words) * 70 + 200
        E.animate(700, lambda e: cv.itemconfigure(au, fill=mix(bg, fg, e)), delay=d, owner=page)

        def merge():
            # one text item per line instead of one per word (cheaper to repaint while scrolling)
            for li, line in enumerate(lines):
                ws = [w for w in words if w[3] == li]
                if not ws:
                    continue
                first = ws[0]
                cv.create_text(first[1], first[2], text=line, font=font, fill=fg, anchor="sw")
                for w in ws:
                    cv.delete(w[0])
        E.after(d + 800, merge, owner=page)
        E.animate(900, lambda e: cv.coords(rule, W / 2 - 60 * e, by + 26, W / 2 + 60 * e, by + 29), delay=d,
                  easing="outExpo", owner=page)
    page.reveal_at(y + 40, play)
    return total


def section_header(page, y, num, title, sub, bg, fg, view=None, accent=theme.ACCENT, M=56, size=96, mono="mono"):
    cv, E = page.cv, page.E
    W = page.W
    n_it = cv.create_text(M, y + 4, text=f"({num})", font=F(mono, 14, "bold"), fill=bg, anchor="nw")
    font = F("display", size)
    let = Letters(page, M, y + 30 + theme.line_h(font) - 8, title, font, fg, bg)
    sy = y + 30 + theme.line_h(font)
    s_it = cv.create_text(M, sy, text=sub, font=F(mono, 14 if mono == "type" else 13, "bold" if mono == "type" else ""),
                          fill=bg, anchor="nw")
    rule = cv.create_rectangle(M, sy + 40, M, sy + 42, fill=fg, outline="")
    btn = None
    if view:
        text, cmd = view
        btn = Button(page, W - M, sy - 30, text, cmd, kind="outline-light" if fg != theme.INK else "outline",
                     anchor="ne", page_bg=bg, h=48)
        btn.set_visible(False)
    h = sy + 56 - y

    def play():
        E.animate(500, lambda e: cv.itemconfigure(n_it, fill=mix(bg, accent, e)), owner=page)
        let.play(delay=80, mode="revolve", step=55, dur=1000)
        E.animate(700, lambda e: cv.itemconfigure(s_it, fill=mix(bg, theme.MUTED if fg == theme.INK else
                                                                 (theme.CHROME_D if bg == theme.VOID else "#A39E94"), e)),
                  delay=500, owner=page)
        E.animate(1400, lambda e: cv.coords(rule, M, sy + 40, M + (W - 2 * M) * e, sy + 42), delay=300,
                  easing="inOutExpo", owner=page)
        if btn:
            btn.set_visible(True)
            btn.pop_in(delay=600)
    page.reveal_at(y, play, offset=60)
    return h, let


# --------------------------------------------------------------------------- #
#  Reviews
# --------------------------------------------------------------------------- #
class ReviewCard:
    def __init__(self, page, r, x, y, w, h, pal=LIGHT):
        self.page, self.cv = page, page.cv
        self.x, self.y, self.w, self.h = x, y, w, h
        self.tag = f"rev{id(self)}"
        t = (self.tag,)
        cv = self.cv
        # the whole card (shadow, stars, title, quote, avatar...) is ONE baked image -> 1 canvas item, not ~20
        self.ph = ImageTk.PhotoImage(bake.review_card(r, w, h, pal, pal["bg"]))
        cv.create_image(x, y, image=self.ph, anchor="nw", tags=t)
        cv.itemconfigure(self.tag, state="hidden")

    def reveal(self, delay=0):
        cv, E = self.cv, self.page.E
        cv.move(self.tag, 0, 60)

        def begin():
            cv.itemconfigure(self.tag, state="normal")
        move(E, cv, self.tag, 0, -60, duration=900, delay=delay, easing="outExpo", begin=begin, owner=self.page)

    def shift(self, dx):
        self.cv.move(self.tag, dx, 0)
        self.x += dx


class ReviewRail:
    def __init__(self, page, reviews, x, y, w=380, h=270, gap=26, pal=LIGHT):
        self.page = page
        self.x, self.y, self.w, self.h, self.gap = x, y, w, h, gap
        self.pal = pal
        self.cards = [ReviewCard(page, r, x + i * (w + gap), y, w, h, pal) for i, r in enumerate(reviews)]
        vis = max(1, int((page.W - x) // (w + gap)))
        self.track = Track(page, self.cards, x, w + gap, vis, y, y + h + 10)

    def reveal(self, delay=0):
        for i, c in enumerate(self.cards):
            c.reveal(delay + min(i, 4) * 120)

    def slide(self, d):
        self.track.slide(d)

    def insert(self, r):
        """New review lands at the front; everybody else glides right."""
        nc = ReviewCard(self.page, r, self.x - self.track.off, self.y, self.w, self.h, self.pal)
        self.cards.insert(0, nc)
        self.track.go(0)
        nc.reveal(250)
        self.page.raise_hud()


def rating_summary(page, x, y, cat, avg, total, pal=LIGHT):
    from .data import RATING_DIST
    cv, E = page.cv, page.E
    big = cv.create_text(x, y, text="0.0", font=F("display", 110), fill=pal["fg"], anchor="nw")
    cv.create_text(x + 4, y + 150, text=f"FROM {total:,} VERIFIED REVIEWS", font=F("mono", 12, "bold"),
                   fill=pal["muted"], anchor="nw")
    st_items, _ = stars(cv, x, y + 186, 0, size=13, off=pal["line"])
    bars = []
    bx, bw = x + 280, 300
    for i, pct in enumerate(RATING_DIST[cat]):
        yy = y + 18 + i * 34
        cv.create_text(bx, yy, text=f"{5 - i}★", font=F("mono", 12, "bold"), fill=pal["fg"], anchor="w")
        cv.create_rectangle(bx + 44, yy - 6, bx + 44 + bw, yy + 6, fill=pal["line"], outline="")
        b = cv.create_rectangle(bx + 44, yy - 6, bx + 44, yy + 6, fill=pal["accent"], outline="")
        lab = cv.create_text(bx + 54 + bw, yy, text="0%", font=F("mono", 11), fill=pal["muted"], anchor="w")
        bars.append((b, lab, pct, yy))

    def play():
        E.animate(1600, lambda e: cv.itemconfigure(big, text=f"{avg * e:.1f}"), easing="outExpo", owner=page)
        for k, it in enumerate(st_items):
            E.animate(300, lambda e, it=it: cv.itemconfigure(it, fill=mix(pal["line"], theme.STAR, e)),
                      delay=300 + k * 140, owner=page)
        for i, (b, lab, pct, yy) in enumerate(bars):
            def upd(e, b=b, lab=lab, pct=pct, yy=yy):
                cv.coords(b, bx + 44, yy - 6, bx + 44 + bw * pct / 100 * e, yy + 6)
                cv.itemconfigure(lab, text=f"{pct * e:.0f}%")
            E.animate(1400, upd, delay=200 + i * 120, easing="outExpo", owner=page)
    page.reveal_at(y, play)
    return 230


class ReviewForm:
    """Inline 'write a review' form: name entry, hover star picker, comment box, submit."""

    def __init__(self, page, x, y, w, on_submit, products, pal=LIGHT):
        self.page, self.cv, self.E = page, page.cv, page.E
        self.on_submit = on_submit
        self.rating = 0
        self.hover_r = 0
        cv = self.cv
        self.h = 330
        dark = pal["bg"] != theme.PAPER
        fbg = theme.INK3 if dark else theme.WHITE
        ffg = theme.BONE if dark else theme.INK
        cv.create_rectangle(x + 6, y + 6, x + w + 6, y + self.h + 6, fill=pal["accent"], outline="")
        cv.create_rectangle(x, y, x + w, y + self.h, fill=pal["card"], outline=pal["fg"], width=2)
        cv.create_text(x + 26, y + 26, text="WRITE A REVIEW", font=F("display", 34), fill=pal["fg"], anchor="nw")
        cv.create_text(x + 26, y + 76, text="TELL THE NEXT OWNER WHAT THEY'RE IN FOR.", font=F("mono", 11),
                       fill=pal["muted"], anchor="nw")
        # stars picker
        self.star_items = []
        sx, sy = x + 26, y + 124
        for i in range(5):
            it = cv.create_polygon(*star_pts(sx + 18 + i * 42, sy, 17), fill=pal["line"], outline="")
            self.star_items.append(it)
            cx = sx + 18 + i * 42
            page.zone((cx - 20, sy - 20, cx + 20, sy + 20), click=lambda i=i: self.set_rating(i + 1),
                      enter=lambda i=i: self._hover(i + 1), leave=lambda: self._hover(0), z=9)
        self.pal = pal
        self.r_label = cv.create_text(sx + 230, sy, text="TAP A STAR", font=F("mono", 11, "bold"),
                                      fill=pal["muted"], anchor="w")
        ent_kw = dict(font=F("body", 15), bg=fbg, fg=ffg, insertbackground=theme.ACCENT, relief="flat",
                      highlightthickness=2, highlightbackground=pal["line"], highlightcolor=theme.ACCENT)
        self.name_var = tk.StringVar()
        self.e_name = tk.Entry(page.cv, textvariable=self.name_var, **ent_kw)
        cv.create_text(x + 26, y + 160, text="NAME", font=F("mono", 10, "bold"), fill=pal["muted"], anchor="nw")
        page.add_window(x + 26, y + 178, self.e_name, anchor="nw", width=(w - 78) // 2, height=40)
        self.prod_var = tk.StringVar(value=products[0]["name"])
        cv.create_text(x + 26 + (w - 78) // 2 + 26, y + 160, text="PRODUCT", font=F("mono", 10, "bold"),
                       fill=pal["muted"], anchor="nw")
        om = tk.OptionMenu(page.cv, self.prod_var, *[p["name"] for p in products])
        om.configure(font=F("body", 13), bg=fbg, fg=ffg, activebackground=theme.ACCENT, relief="flat",
                     highlightthickness=2, highlightbackground=pal["line"], bd=0, indicatoron=False, anchor="w")
        om["menu"].configure(font=F("body", 13), bg=theme.WHITE, fg=theme.INK, activebackground=theme.ACCENT)
        page.add_window(x + 26 + (w - 78) // 2 + 26, y + 178, om, anchor="nw", width=(w - 78) // 2, height=40)
        cv.create_text(x + 26, y + 228, text="YOUR TAKE", font=F("mono", 10, "bold"), fill=pal["muted"], anchor="nw")
        self.e_text = tk.Entry(page.cv, **ent_kw)
        page.add_window(x + 26, y + 246, self.e_text, anchor="nw", width=w - 52 - 190, height=48)
        self.btn = Button(page, x + w - 26, y + 246, "POST IT", self.submit, kind="accent", anchor="ne", h=48,
                          shadow=theme.INK if not dark else None)
        self.msg = cv.create_text(x + w - 26, y + 26, text="", font=F("mono", 11, "bold"), fill=theme.ACCENT, anchor="ne")
        self.x, self.y, self.w = x, y, w

    def _paint(self, n):
        for i, it in enumerate(self.star_items):
            self.cv.itemconfigure(it, fill=theme.STAR if i < n else self.pal["line"])

    def _hover(self, n):
        self.hover_r = n
        self._paint(n or self.rating)

    def set_rating(self, n):
        self.rating = n
        self._paint(n)
        labels = ["", "NOT FOR ME", "IT'S OKAY", "PRETTY GOOD", "LOVE IT", "OBSESSED"]
        self.cv.itemconfigure(self.r_label, text=labels[n], fill=theme.ACCENT)
        it = self.star_items[n - 1]
        sx = self.x + 26 + 18 + (n - 1) * 42
        sy = self.y + 124

        def upd(e):
            r = 17 + 9 * math.sin(e * math.pi)
            self.cv.coords(it, *star_pts(sx, sy, r))
        self.E.animate(500, upd, easing="outQuad", owner=self.page)

    def _error(self, text):
        cv = self.cv
        cv.itemconfigure(self.msg, text=text)
        move(self.E, cv, self.msg, 10, 0, duration=70, direction="alternate", loop=6, easing="linear", owner=self.page)

    def submit(self):
        name = self.name_var.get().strip()
        text = self.e_text.get().strip()
        if not self.rating:
            return self._error("PICK A STAR RATING FIRST")
        if not name:
            return self._error("WHO ARE YOU? (NAME)")
        if len(text) < 4:
            return self._error("SAY A LITTLE MORE")
        self.cv.itemconfigure(self.msg, text="")
        r = dict(name=name, city="AK1 Community", stars=self.rating, title=["", "Not for me", "It's okay", "Pretty good",
                                                                             "Love it", "Obsessed"][self.rating],
                 text=text, product=self.prod_var.get(), date="just now")
        self.name_var.set("")
        self.e_text.delete(0, "end")
        self.rating = 0
        self._paint(0)
        self.cv.itemconfigure(self.r_label, text="THANK YOU ♥", fill=theme.ACCENT)
        self.on_submit(r)


# --------------------------------------------------------------------------- #
#  QuickView modal
# --------------------------------------------------------------------------- #
class QuickView:
    def __init__(self, page, p):
        if page.modal is not None:
            return
        self.page, self.cv, self.E, self.A = page, page.cv, page.E, page.A
        self.p = p
        page.modal = self
        page.show_windows(False)
        if page.fox:
            page.fox.hush()
        cv = self.cv
        W, H = page.W, page.H
        top = page.applied
        self.tag = f"qv{id(self)}"
        t = (self.tag, "modal", "hud")
        self.zones = []
        self.dim = cv.create_rectangle(0, top, W, top + H, fill=theme.INK, outline="", stipple="gray50",
                                       tags=("modal", "hud", self.tag + "dim"))
        pw, ph = min(980, W - 120), min(600, H - 80)
        px, py = (W - pw) / 2, top + (H - ph) / 2
        self.box = (px, py, pw, ph)
        cv.create_rectangle(px + 10, py + 10, px + pw + 10, py + ph + 10, fill=theme.ACCENT, outline="", tags=t)
        cv.create_rectangle(px, py, px + pw, py + ph, fill=theme.PAPER, outline=theme.INK, width=3, tags=t)
        iw = int(ph * 0.74)
        self.ph = self.A.tk_cover(p["cat"], p["img"], iw, ph, p["focus"])
        self.img = cv.create_image(px, py, image=self.ph, anchor="nw", tags=t)
        cat = CATS[p["cat"]]
        rx = px + iw + 40
        rw = pw - iw - 80
        crumb = f"AK1 / {cat['title']} / {p['sub']}" if p.get("sub") else f"AK1 / {cat['title']} / {p['cond']}"
        cv.create_text(rx, py + 36, text=crumb + (f"  ·  {p['badge']}" if p.get("badge") else ""),
                       font=F("mono", 11, "bold"),
                       fill=theme.ACCENT, anchor="nw", tags=t)
        nf = F("display", 46)
        nlines = theme.wrap(nf, p["name"].upper(), rw)
        lines(cv, rx, py + 58, nlines, nf, theme.INK, tags=t)
        yy = py + 58 + 50 * len(nlines) + 26
        pf = F("display", 40)
        cv.create_text(rx, yy, text=rupee(p["price"]), font=pf, fill=theme.INK, anchor="nw", tags=t)
        pw2 = theme.measure(pf, rupee(p["price"]))
        off = round(100 * (1 - p["price"] / p["mrp"]))
        cv.create_text(rx + pw2 + 14, yy + 14, text=f"{rupee(p['mrp'])}", font=F("mono", 14) + ("overstrike",),
                       fill=theme.MUTED, anchor="nw", tags=t)
        cv.create_text(rx + pw2 + 14, yy + 34, text=f"YOU SAVE {off}%", font=F("mono", 12, "bold"),
                       fill=theme.ACCENT, anchor="nw", tags=t)
        yy += 70
        _, sw = stars(cv, rx, yy, p["rating"], size=9, tags=t)
        cv.create_text(rx + sw + 10, yy, text=f"{p['rating']} / 5  ·  {p['reviews']} REVIEWS  ·  {p['sold']:,} SOLD",
                       font=F("mono", 11), fill=theme.MUTED, anchor="w", tags=t)
        yy += 26
        df = F("body", 16)
        dl = theme.wrap(df, p["desc"], rw)
        cv.create_text(rx, yy, text="\n".join(dl), font=df, fill=theme.INK, anchor="nw", tags=t)
        yy += theme.line_h(df) * len(dl) + 18
        if p.get("gender"):
            g = {"M": "FOR HIM", "W": "FOR HER", "U": "UNISEX"}[p["gender"]]
            cv.create_text(rx, yy, text=g + "  ·  " + "  /  ".join(p["tags"]), font=F("mono", 11, "bold"),
                           fill=theme.MUTED, anchor="nw", tags=t)
        else:
            cv.create_text(rx, yy, text="  /  ".join(p["tags"]), font=F("mono", 11, "bold"), fill=theme.MUTED,
                           anchor="nw", tags=t)
        yy += 30
        # size pills
        self.size = cat["sizes"][len(cat["sizes"]) // 2]
        self.pills = {}
        sx = rx
        for s in cat["sizes"]:
            sf = F("heavy", 13)
            w = max(48, theme.measure(sf, s) + 26)
            r = cv.create_rectangle(sx, yy, sx + w, yy + 40, fill=theme.PAPER, outline=theme.INK, width=2, tags=t)
            tx = cv.create_text(sx + w / 2, yy + 20, text=s, font=sf, fill=theme.INK, tags=t)
            self.pills[s] = (r, tx)
            self.zones.append(page.zone((sx, yy - top, sx + w, yy + 40 - top), click=lambda s=s: self.pick(s),
                                        hud=True, z=110))
            sx += w + 8
        self.pick(self.size, anim=False)
        yy += 64
        self.btn = Button(page, rx, yy, f"ADD TO BAG  ·  {rupee(p['price'])}", self.add, kind="ink", h=56,
                          tags=("modal", self.tag), hud=True, z=110, shadow=theme.ACCENT)
        self.btn.zone.bbox = lambda: (self.btn.x, self.btn.y - page.applied, self.btn.x + self.btn.w,
                                      self.btn.y + self.btn.h - page.applied)
        import datetime
        eta = (datetime.date.today() + datetime.timedelta(days=5)).strftime("%d %b").upper()
        perks = [f"▸ GET IT BY {eta}",
                 "✔ FREE COD & SHIPPING   ✔ 7-DAY RETURN & EXCHANGE   ✔ SHIPS IN 48 HRS"]
        for i, line in enumerate(perks):
            cv.create_text(rx, yy + 72 + i * 20, text=line, font=F("mono", 10, "bold"),
                           fill=theme.ACCENT if i == 0 else theme.MUTED, anchor="nw", tags=t)
        # close X
        cx, cy = px + pw - 30, py + 30
        self.x_c = cv.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill=theme.INK, outline="", tags=t)
        self.x_t = cv.create_text(cx, cy, text="✕", font=F("heavy", 14), fill=theme.BONE, tags=t)
        self.x_ang = 0

        def xh(on):
            cv.itemconfigure(self.x_c, fill=theme.ACCENT if on else theme.INK)
            self.E.animate(400, lambda e: cv.itemconfigure(self.x_t, angle=(90 * e if on else 90 * (1 - e))),
                           easing="outBack", owner=page)
        self.zones.append(page.zone((cx - 20, cy - 20 - top, cx + 20, cy + 20 - top), click=self.close,
                                    enter=lambda: xh(True), leave=lambda: xh(False), hud=True, z=120))
        self.zones.append(page.zone((0, 0, W, H), click=self._outside, hud=True, z=100, cursor=""))
        self.zones.append(self.btn.zone)
        page.app.root.bind("<Escape>", lambda e: self.close())
        cv.tag_raise("modal")
        # entrance: panel rises with overshoot, image wipes in
        cv.move(self.tag, 0, 60)
        cv.itemconfigure(self.dim, state="hidden")
        move(self.E, cv, self.tag, 0, -60, duration=650, easing="outBack", owner=page)
        self.E.after(10, lambda: cv.itemconfigure(self.dim, state="normal"), owner=page)
        self.curtain = cv.create_rectangle(px, py, px + iw, py + ph, fill=theme.ACCENT, outline="", tags=t)
        cv.move(self.curtain, 0, 60)
        move(self.E, cv, self.curtain, 0, -60, duration=650, easing="outBack", owner=page)
        self.E.animate(800, lambda e: cv.coords(self.curtain, px, py + ph * e, px + iw, py + ph), delay=300,
                       easing="inOutExpo", owner=page)

    def _outside(self):
        mx, my = self.page.mouse
        px, py, pw, ph = self.box
        py -= self.page.applied
        if not (px <= mx <= px + pw and py <= my <= py + ph):
            self.close()

    def pick(self, s, anim=True):
        self.size = s
        for k, (r, tx) in self.pills.items():
            on = k == s
            self.cv.itemconfigure(r, fill=theme.INK if on else theme.PAPER)
            self.cv.itemconfigure(tx, fill=theme.LIME if on else theme.INK)
        if anim:
            r, tx = self.pills[s]
            move(self.E, self.cv, tx, 0, -4, duration=160, direction="alternate", loop=2, owner=self.page)

    def add(self):
        self.page.app.add_to_cart(self.p, self.size)
        self.btn.set_text("ADDED  ✓")
        self.E.after(500, self.close, owner=self.page)

    def close(self):
        if self.page.modal is not self:
            return
        page = self.page
        for z in self.zones:
            page.remove_zone(z)
        page.app.root.bind("<Escape>", lambda e: None)
        cv = self.cv

        def fin():
            self.btn.delete()
            cv.delete(self.tag)
            cv.delete(self.tag + "dim")
            page.modal = None
            page.show_windows(True)
        cv.itemconfigure(self.dim, state="hidden")
        move(self.E, cv, self.tag, 0, page.H, duration=450, easing="inBack", complete=fin, owner=page)
