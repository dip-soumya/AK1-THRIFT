"""
theme.py  -  palette + typography for AK1-THRIFT.

Fonts (Google Fonts, OFL) are registered *privately* for this process on
Windows via GDI AddFontResourceEx, so nothing gets installed system-wide.
  Anton            -> giant condensed display headlines
  Archivo Black    -> heavy sub-heads / buttons
  DM Serif Display -> italic fashion quotes
  Space Mono       -> price tags, labels, editorial micro-copy
"""
import os
import sys
import tkinter.font as tkfont

# ---- palette ------------------------------------------------------------- #
INK = "#0E0E0E"
INK2 = "#181818"
INK3 = "#262626"
BONE = "#EEE9DF"
PAPER = "#F7F4EE"
WHITE = "#FFFFFF"
ACCENT = "#FF4A1C"     # signal orange-red (also Fitz's fur family)
ACCENT_D = "#D93A10"
LIME = "#D4FF2E"       # acid lime pop
GOLD = "#C9A45F"
GOLD_L = "#E6CF9C"
MUTED = "#8C877D"
MUTED_D = "#5C5952"
LINE = "#D8D2C5"
DENIM = "#2E4A72"
DENIM_D = "#22385A"
DENIM_L = "#3F6496"
STITCH = "#F2A93B"
STAR = "#FFB321"
# chrome / gothic jewellery + accessories palette
VOID = "#050505"
CHROME = "#C9CDD3"
CHROME_L = "#ECEEF1"
CHROME_D = "#7E848C"
CRIMSON = "#C8102E"

FONT_FILES = [
    "Anton-Regular.ttf", "ArchivoBlack-Regular.ttf",
    "DMSerifDisplay-Regular.ttf", "DMSerifDisplay-Italic.ttf",
    "SpaceMono-Regular.ttf", "SpaceMono-Bold.ttf",
    "CourierPrime-Regular.ttf", "CourierPrime-Bold.ttf",
]

_FAMILY = {
    "display": ["Anton", "Impact", "Bahnschrift Condensed", "Arial Black"],
    "heavy": ["Archivo Black", "Arial Black", "Segoe UI Black"],
    "serif": ["DM Serif Display", "Georgia", "Times New Roman"],
    "mono": ["Space Mono", "Consolas", "Courier New"],
    "type": ["Courier Prime", "Courier New", "Consolas"],
    "body": ["Bahnschrift", "Segoe UI", "Helvetica"],
    "bodyb": ["Bahnschrift SemiBold", "Segoe UI Semibold", "Helvetica"],
}
FAMILY = {}
_font_cache = {}


def register_fonts(font_dir):
    """Load bundled TTFs for this process only (Windows). Call before tk.Tk()."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        FR_PRIVATE = 0x10
        for f in FONT_FILES:
            p = os.path.join(font_dir, f)
            if os.path.exists(p):
                ctypes.windll.gdi32.AddFontResourceExW(p, FR_PRIVATE, 0)
    except Exception:  # noqa: BLE001
        pass


def init_fonts(root):
    fams = {f.lower() for f in tkfont.families(root)}
    for kind, options in _FAMILY.items():
        FAMILY[kind] = next((o for o in options if o.lower() in fams), options[-1])


def F(kind, size, *styles):
    """Pixel-sized font tuple, e.g. F('display', 96)."""
    return (FAMILY.get(kind, "Segoe UI"), -int(size)) + tuple(styles)


def measure(font, text):
    key = font
    f = _font_cache.get(key)
    if f is None:
        fam, size = font[0], font[1]
        f = tkfont.Font(family=fam, size=size,
                        weight="bold" if "bold" in font[2:] else "normal",
                        slant="italic" if "italic" in font[2:] else "roman")
        _font_cache[key] = f
    return f.measure(text)


def line_h(font):
    measure(font, "x")
    return _font_cache[font].metrics("linespace")


def wrap(font, text, width):
    """Greedy word-wrap using real glyph metrics. Returns list of lines."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if measure(font, trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rupee(n):
    s = f"{int(round(n)):,}"
    return "₹" + s
