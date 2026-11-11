"""
bake.py  -  pre-render static canvas content into images with Pillow.

Why: on Windows every visible Tk canvas item costs ~50us to repaint, and a scroll repaints the
whole viewport every frame. A product card was ~25 items (texts, star polygons, pills...),
a review card ~20. Baking the static parts into ONE image per block cuts the item count 4-20x,
which is what makes scrolling smooth. Text is drawn at 2x and downsampled for crisp anti-aliasing.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

from . import theme

SS = 2  # supersampling factor
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
_FILES = {
    ("display", False): "Anton-Regular.ttf", ("display", True): "Anton-Regular.ttf",
    ("heavy", False): "ArchivoBlack-Regular.ttf", ("heavy", True): "ArchivoBlack-Regular.ttf",
    ("mono", False): "SpaceMono-Regular.ttf", ("mono", True): "SpaceMono-Bold.ttf",
    ("type", False): "CourierPrime-Regular.ttf", ("type", True): "CourierPrime-Bold.ttf",
    ("serif", False): "DMSerifDisplay-Regular.ttf", ("serif", True): "DMSerifDisplay-Regular.ttf",
}
_WIN_FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_fonts = {}
_cache = {}


def font(kind, px, bold=False):
    key = (kind, int(px), bold)
    f = _fonts.get(key)
    if f is not None:
        return f
    try:
        if kind in ("body", "bodyb"):
            f = ImageFont.truetype(os.path.join(_WIN_FONTS, "bahnschrift.ttf"), int(px))
            try:
                f.set_variation_by_name("SemiBold" if (kind == "bodyb" or bold) else "Regular")
            except Exception:  # noqa: BLE001
                pass
        else:
            f = ImageFont.truetype(os.path.join(_FONT_DIR, _FILES[(kind, bold)]), int(px))
    except Exception:  # noqa: BLE001
        try:
            f = ImageFont.truetype("arial.ttf", int(px))
        except Exception:  # noqa: BLE001
            f = ImageFont.load_default()
    _fonts[key] = f
    return f


def _star(cx, cy, R):
    pts = []
    for k in range(10):
        a = math.radians(-90 + 36 * k)
        r = R if k % 2 == 0 else R * 0.46
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def stars(d, x, cy, rating, size, on=theme.STAR, off=theme.LINE, gap=3):
    """5 stars (with half stars) - coordinates already in supersampled space."""
    for i in range(5):
        cx = x + size + i * (size * 2 + gap)
        pts = _star(cx, cy, size)
        d.polygon(pts, fill=on if rating >= i + 0.75 else off)
        if i + 0.25 <= rating < i + 0.75:
            d.polygon(pts[5:] + [pts[0]], fill=on)
    return size * 10 + gap * 4


def _down(im, w, h):
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)


def truncate(f, text, maxw):
    if f.getlength(text) <= maxw:
        return text
    while len(text) > 3 and f.getlength(text + "\u2026") > maxw:
        text = text[:-1]
    return text.rstrip() + "\u2026"


def wrap(f, text, maxw):
    words, out, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


# --------------------------------------------------------------------------- #
#  product card pieces
# --------------------------------------------------------------------------- #
def pill(text, fill, fg=theme.INK, outline=None, px=10):
    """Small label pill (condition / NEW IN / BEST SELLER #1...)."""
    key = ("pill", text, fill, fg, outline, px)
    im = _cache.get(key)
    if im is None:
        f = font("mono", px * SS, True)
        w = int(f.getlength(text) / SS) + 18
        h = 24
        big = Image.new("RGB", (w * SS, h * SS), fill)
        d = ImageDraw.Draw(big)
        if outline:
            d.rectangle([0, 0, w * SS - 1, h * SS - 1], outline=outline, width=SS)
        d.text((w * SS / 2, h * SS / 2), text, font=f, fill=fg, anchor="mm")
        im = _cache[key] = _down(big, w, h)
    return im


def decorate(photo, p, rank=None, best=None, badge_fg=theme.LIME):
    """Bake the condition pill, NEW IN/SALE badge and rank badge onto the product photo."""
    from .data import BADGE_COL
    im = photo.copy()
    im.paste(pill(p["cond"], theme.ACCENT if p["cond"] == "VINTAGE GEM" else theme.LIME), (12, 12))
    if p.get("badge"):
        im.paste(pill(p["badge"], BADGE_COL.get(p["badge"], theme.LIME)), (12, 42))
    if rank or best:
        label = f"#{rank} TRENDING" if rank else f"BEST SELLER #{best}"
        pl = pill(label, theme.INK, badge_fg, outline=theme.BONE)
        im.paste(pl, (12, im.height - 36))
    return im


def card_info(p, w, pal):
    """Name, tags, price, MRP, discount, stars + rating -> one image (w x 118)."""
    key = ("info", p["id"], w, pal["bg"], pal["fg"], pal["accent"])
    im = _cache.get(key)
    if im is not None:
        return im
    H = 118
    big = Image.new("RGB", (w * SS, H * SS), pal["bg"])
    d = ImageDraw.Draw(big)
    S = SS
    nf = font("heavy", 15 * S)
    d.text((0, 14 * S), truncate(nf, p["name"], (w - 4) * S), font=nf, fill=pal["fg"], anchor="la")
    tf = font("mono", 10 * S)
    d.text((0, 41 * S), "  \u00b7  ".join(p["tags"]), font=tf, fill=pal["muted"], anchor="la")
    pf = font("display", 28 * S)
    price = theme.rupee(p["price"])
    d.text((0, 58 * S), price, font=pf, fill=pal["fg"], anchor="la")
    x = pf.getlength(price) + 10 * S
    mf = font("mono", 12 * S)
    mrp = theme.rupee(p["mrp"])
    d.text((x, 66 * S), mrp, font=mf, fill=pal["muted"], anchor="la")
    mw = mf.getlength(mrp)
    asc = mf.getmetrics()[0]
    d.line([(x, 66 * S + asc * 0.62), (x + mw, 66 * S + asc * 0.62)], fill=pal["muted"], width=S)
    off = round(100 * (1 - p["price"] / p["mrp"]))
    d.text((x + mw + 4 * S, 66 * S), f"-{off}%", font=font("mono", 12 * S, True), fill=pal["accent"], anchor="la")
    sw = stars(d, 0, 108 * S, p["rating"], 7 * S, off=pal["line"], gap=3 * S)
    d.text((sw + 8 * S, 108 * S), f"{p['rating']}  ({p['reviews']})", font=tf, fill=pal["muted"], anchor="lm")
    im = _cache[key] = _down(big, w, H)
    return im


def fade_frames(im, bg, n=6):
    """Pre-blended frames from bg -> image (for fade-ins of baked blocks)."""
    solid = Image.new("RGB", im.size, bg)
    return [Image.blend(solid, im, (i + 1) / n) for i in range(n)]


# --------------------------------------------------------------------------- #
#  review card
# --------------------------------------------------------------------------- #
def review_card(r, w, h, pal, page_bg):
    key = ("review", r["name"], r["title"], r["text"][:40], w, h, pal["bg"], pal["accent"])
    im = _cache.get(key)
    if im is not None:
        return im
    S = SS
    W2, H2 = (w + 8) * S, (h + 8) * S
    big = Image.new("RGB", (W2, H2), page_bg)
    d = ImageDraw.Draw(big)
    d.rectangle([6 * S, 6 * S, (w + 6) * S, (h + 6) * S], fill=pal["accent"])
    d.rectangle([0, 0, w * S, h * S], fill=pal["card"], outline=pal["fg"], width=2 * S)
    stars(d, 22 * S, 34 * S, r["stars"], 9 * S, off=pal["line"], gap=3 * S)
    d.text(((w - 22) * S, 34 * S), r.get("date", "just now").upper(), font=font("mono", 10 * S), fill=pal["muted"],
           anchor="rm")
    d.text((24 * S, 58 * S), r["title"].upper(), font=font("heavy", 17 * S), fill=pal["fg"], anchor="la")
    bf = font("body", 15 * S)
    rows = wrap(bf, "\u201c" + r["text"] + "\u201d", (w - 48) * S)[:4]
    for i, row in enumerate(rows):
        d.text((24 * S, (92 + i * 19) * S), row, font=bf, fill=pal["fg"], anchor="la")
    d.line([(24 * S, (h - 62) * S), ((w - 24) * S, (h - 62) * S)], fill=pal["line"], width=S)
    d.ellipse([24 * S, (h - 50) * S, 60 * S, (h - 14) * S], fill=pal["accent"])
    initials = "".join(s[0] for s in r["name"].split()[:2]).upper()
    d.text((42 * S, (h - 32) * S), initials, font=font("heavy", 12 * S), fill=theme.INK, anchor="mm")
    d.text((72 * S, (h - 42) * S), f"{r['name']}  \u00b7  {r['city']}", font=font("bodyb", 14 * S), fill=pal["fg"],
           anchor="lm")
    d.text((72 * S, (h - 22) * S), "VERIFIED  \u00b7  " + r["product"].upper(), font=font("mono", 9 * S),
           fill=pal["muted"], anchor="lm")
    im = _cache[key] = _down(big, w + 8, h + 8)
    return im
