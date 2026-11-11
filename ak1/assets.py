"""
assets.py  -  Pillow image pipeline (cover-crop, caching, flip frames, depth levels).

Tkinter does the drawing; Pillow only prepares bitmaps:
  * cover()        object-fit: cover with a focus point
  * flip_frames()  horizontally squashed frames -> fake 3D "revolve" (card flip)
  * depth_levels() scaled + darkened copies for the revolving 3D carousel
  * zoom_frames()  slightly zoomed crops for hover-zoom tiles
"""
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps, ImageTk

from . import theme


class Assets:
    def __init__(self, root_dir):
        self.root = root_dir
        self.img_dir = os.path.join(root_dir, "assets", "img")
        self.font_dir = os.path.join(root_dir, "assets", "fonts")
        self._pil = {}
        self._cover = {}
        self._tk = {}

    # ------------------------------------------------------------------ #
    def path(self, cat, pid):
        return os.path.join(self.img_dir, cat, pid + ".jpg")

    def all_images(self):
        out = []
        if os.path.isdir(self.img_dir):
            for cat in sorted(os.listdir(self.img_dir)):
                d = os.path.join(self.img_dir, cat)
                for f in sorted(os.listdir(d)):
                    if f.endswith(".jpg"):
                        out.append((cat, f[:-4]))
        return out

    def pil(self, cat, pid):
        key = (cat, pid)
        im = self._pil.get(key)
        if im is None:
            p = self.path(cat, pid)
            try:
                im = Image.open(p)
                im = ImageOps.exif_transpose(im).convert("RGB")
            except Exception:  # noqa: BLE001  -> offline / missing: draw a placeholder
                im = self._placeholder(cat, pid)
            self._pil[key] = im
        return im

    def _placeholder(self, cat, pid):
        im = Image.new("RGB", (600, 800), theme.INK3)
        d = ImageDraw.Draw(im)
        for i in range(0, 1400, 28):
            d.line([(i, 0), (i - 800, 800)], fill=theme.INK2, width=10)
        try:
            f = ImageFont.truetype(os.path.join(self.font_dir, "Anton-Regular.ttf"), 120)
        except Exception:  # noqa: BLE001
            f = ImageFont.load_default()
        d.text((40, 560), cat.upper(), fill=theme.ACCENT, font=f)
        return im

    # ------------------------------------------------------------------ #
    def cover(self, cat, pid, w, h, focus=0.4, gray=False, dim=0.0, dim_to=theme.INK):
        """object-fit: cover. focus = vertical focus (0 top .. 1 bottom)."""
        w, h = max(1, int(w)), max(1, int(h))
        key = (cat, pid, w, h, round(focus, 2), gray, round(dim, 3), dim_to)
        im = self._cover.get(key)
        if im is not None:
            return im
        src = self.pil(cat, pid)
        sw, sh = src.size
        scale = max(w / sw, h / sh)
        cw, ch = min(sw, w / scale), min(sh, h / scale)
        x0 = max(0.0, (sw - cw) / 2)
        y0 = max(0.0, (sh - ch) * focus)
        im = src.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
        if gray:
            im = ImageOps.grayscale(im).convert("RGB")
            im = ImageEnhance.Contrast(im).enhance(1.15)
        if dim > 0:
            im = Image.blend(im, Image.new("RGB", im.size, dim_to), dim)
        self._cover[key] = im
        return im

    def tk(self, pil_img, key=None):
        if key is not None and key in self._tk:
            return self._tk[key]
        ph = ImageTk.PhotoImage(pil_img)
        if key is not None:
            self._tk[key] = ph
        return ph

    def tk_cover(self, cat, pid, w, h, focus=0.4, **fx):
        key = ("cover", cat, pid, int(w), int(h), round(focus, 2), tuple(sorted(fx.items())))
        if key in self._tk:
            return self._tk[key]
        return self.tk(self.cover(cat, pid, w, h, focus, **fx), key)

    # ------------------------------------------------------------------ #
    def flip_frames(self, cat, pid, w, h, focus=0.4, n=9, bg=theme.PAPER):
        """Frames for a Y-axis revolve: width = w*cos(theta) with a slight perspective shade.
        Returns [(photo, width)] from edge-on to full-face. Not cached (cheap + transient)."""
        base = self.cover(cat, pid, w, h, focus)
        out = []
        for i in range(n):
            th = (math.pi / 2) * (1 - i / (n - 1))
            k = math.cos(th)
            fw = max(2, int(w * k))
            fh = max(2, int(h * (0.9 + 0.1 * k)))
            im = base.resize((fw, fh), Image.BILINEAR)
            shade = (1 - k) * 0.55
            if shade > 0.01:
                im = Image.blend(im, Image.new("RGB", im.size, bg), shade)
            out.append((ImageTk.PhotoImage(im), fw, fh))
        return out

    def depth_levels(self, cat, pid, w, h, levels=10, focus=0.4, bg=theme.INK, min_scale=0.42):
        """Scaled + darkened copies used by the 3D revolving ring."""
        key = ("depth", cat, pid, w, h, levels, bg, min_scale)
        if key in self._tk:
            return self._tk[key]
        base = self.cover(cat, pid, w, h, focus)
        out = []
        for l in range(levels):
            d = l / (levels - 1)
            s = min_scale + (1 - min_scale) * d
            im = base.resize((max(2, int(w * s)), max(2, int(h * s))), Image.BILINEAR)
            fade = (1 - d) * 0.62
            if fade > 0.01:
                im = Image.blend(im, Image.new("RGB", im.size, bg), fade)
            out.append(ImageTk.PhotoImage(im))
        self._tk[key] = out
        return out

    def zoom_frames(self, cat, pid, w, h, focus=0.4, n=6, zoom=1.12, gray_first=False):
        key = ("zoom", cat, pid, w, h, n, zoom, gray_first)
        if key in self._tk:
            return self._tk[key]
        big = self.cover(cat, pid, int(w * zoom), int(h * zoom), focus)
        out = []
        for i in range(n):
            z = 1 + (zoom - 1) * i / (n - 1)
            cw, ch = big.width / z, big.height / z
            bx, by = max(0.0, (big.width - cw) / 2), max(0.0, (big.height - ch) / 2)
            im = big.resize((w, h), Image.BILINEAR, box=(bx, by, bx + cw, by + ch))
            if gray_first:
                g = ImageOps.grayscale(im).convert("RGB")
                im = Image.blend(g, im, i / (n - 1))
            out.append(ImageTk.PhotoImage(im))
        self._tk[key] = out
        return out

    def strip(self, cat, pid, full_w, h, w, focus=0.5, step=6):
        """Centre crop of a full-width image at width w (for the accordion gallery)."""
        w = max(step, int(round(w / step) * step))
        w = min(w, full_w)
        key = ("strip", cat, pid, full_w, h, w, round(focus, 2))
        if key in self._tk:
            return self._tk[key]
        base = self.cover(cat, pid, full_w, h, focus)
        x0 = (full_w - w) // 2
        ph = ImageTk.PhotoImage(base.crop((x0, 0, x0 + w, h)))
        self._tk[key] = ph
        return ph

    # ------------------------------------------------------------------ #
    def text_image(self, text, font_file, size, fill, bg=None, pad=4):
        """Render text with Pillow (used for the app icon / big outlined type)."""
        f = ImageFont.truetype(os.path.join(self.font_dir, font_file), size)
        l, t, r, b = f.getbbox(text)
        im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), bg or (0, 0, 0, 0))
        ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill)
        return im
