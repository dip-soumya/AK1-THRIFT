"""HOME - one long scroll story. Every section loads in as you reach it."""
import math

from .. import theme
from ..anim import mix, move
from ..data import CATS, MARQUEE, PRODUCTS, QUOTES, REVIEWS, by_cat, trending
from ..page import Page
from ..theme import F, rupee
from ..widgets import (CHROMEP, DARK, LIGHT, Accordion, Button, Letters, Marquee, ProductCard, QuickView,
                       Rail, RevolvingRing, ReviewRail, RotatingBadge, quote_block, section_header, stars)
from .common import M, arrows, best_row, footer


class HomePage(Page):
    key = "home"
    title = "HOME"
    bg = theme.PAPER
    fox_lines = "home"

    def build(self):
        y = 0
        y += self.hero(y)
        y += self.marquees(y)
        y += self.tiles(y)
        y += quote_block(self, y, *QUOTES[0], bg=theme.PAPER, fg=theme.INK)
        self.tees_y = y
        y += self.tees(y)
        y += self.jeans(y)
        y += quote_block(self, y, *QUOTES[1], bg=theme.BONE, fg=theme.INK, accent=theme.INK)
        y += self.trousers(y)
        y += self.jewellery(y)
        y += self.accessories(y)
        y += self.stats(y)
        y += self.reviews(y)
        y += footer(self, y)
        self.content_h = y

    # ------------------------------------------------------------------ #
    def hero(self, y0):
        cv, E, W, H = self.cv, self.E, self.W, self.H
        h = max(700, H)
        cv.create_rectangle(0, y0, W, y0 + h, fill=theme.INK, outline="")
        # faint grid lines (editorial feel)
        for gx in range(M, W, (W - 2 * M) // 6):
            cv.create_line(gx, y0, gx, y0 + h, fill="#161616")
        # collage
        iw, ih = 420, min(590, h - 120)
        mx = W - M - iw - 30
        my = y0 + 70
        im1 = self.A.tk_cover("hero", "1637536701306-3214e9cec64a", iw, ih, 0.25, gray=True)
        i1 = cv.create_image(mx, my, image=im1, anchor="nw", tags=("par1",))
        c1 = cv.create_rectangle(mx, my, mx + iw, my + ih, fill=theme.ACCENT, outline="", tags=("par1",))
        sw, sh = 260, 340
        sx, sy = mx - 190, my + ih - sh + 50
        im2 = self.A.tk_cover("hero", "1670092473608-47d146ea71b4", sw, sh, 0.35)
        cv.create_rectangle(sx + 10, sy + 10, sx + sw + 10, sy + sh + 10, fill=theme.LIME, outline="", tags=("par2",))
        i2 = cv.create_image(sx, sy, image=im2, anchor="nw", tags=("par2",))
        c2 = cv.create_rectangle(sx, sy, sx + sw + 10, sy + sh + 10, fill=theme.INK, outline="", tags=("par2",))
        tagc = cv.create_text(sx, sy + sh + 30, text="FIG. 02 — SATURDAY FITS, SANTA MONICA", anchor="nw",
                              font=F("mono", 10), fill=theme.INK, tags=("par2",))
        self.add_parallax("par1", 0.18)
        self.add_parallax("par2", 0.38)
        badge = RotatingBadge(self, mx + iw - 8, my + 26, 64, "SECOND HAND • FIRST CLASS • AK1 THRIFT • ",
                              theme.INK, fill=theme.ACCENT, center="★", font=F("mono", 12, "bold"),
                              tags=("par1",))
        # headline
        kick = cv.create_text(M, y0 + 72, text="AK1—THRIFT  /  EST. 2026  /  VOL. 07 — AUTUMN DROP",
                              font=F("mono", 13, "bold"), fill=theme.INK, anchor="nw", tags=("par0",))
        hf = F("display", 150)
        lh = 150
        b1 = y0 + 120 + lh * 1.25
        l1 = Letters(self, M - 4, b1, "SECOND", hf, theme.BONE, theme.INK, tags=("par0",))
        l1b = Letters(self, M - 4 + l1.w + 30, b1, "HAND.", hf, theme.ACCENT, theme.INK, tags=("par0",))
        b2 = b1 + lh * 1.08
        l2 = Letters(self, M - 4, b2, "FIRST", hf, theme.BONE, theme.INK, tags=("par0",))
        l2b = Letters(self, M - 4 + l2.w + 30, b2, "CLASS.", hf, theme.LIME, theme.INK, tags=("par0",))
        self.add_parallax("par0", -0.08)
        # cycling word
        cy = b2 + 34
        cf = F("heavy", 30)
        lead = cv.create_text(M, cy, text="THE ONE STOP FOR", font=cf, fill=theme.INK, anchor="nw")
        lw = theme.measure(cf, "THE ONE STOP FOR ")
        self.cyc_words = ["TEES.", "BAGGY FITS.", "WIDE LEGS.", "CROSS PENDANTS.", "CHROME BUCKLES.", "SECOND CHANCES."]
        self.cyc_i = 0
        self.cyc_item = cv.create_text(M + lw, cy, text=self.cyc_words[0], font=cf, fill=theme.INK, anchor="nw")
        self.cyc_pos = (M + lw, cy)
        para = cv.create_text(M, cy + 56, width=520, anchor="nw", fill=theme.INK, font=F("body", 17),
                              text="Hand-picked, pre-loved fashion - cleaned, steamed and styled for its second life. "
                                   "New drops every Friday. No two pieces alike.")
        b_shop = Button(self, M, cy + 136, "SHOP THE DROP", lambda: self.scroll_to(self.tees_y - 20),
                        kind="accent", shadow=theme.BONE, h=56)
        b_jew = Button(self, M + b_shop.w + 22, cy + 136, "JEWELLERY", lambda: self.app.go("jewellery"),
                       kind="outline-light", h=56, page_bg=theme.INK)
        for b in (b_shop, b_jew):
            b.set_visible(False)
        scr = cv.create_text(W / 2, y0 + h - 30, text="SCROLL  ↓", font=F("mono", 12, "bold"), fill=theme.INK)

        def play():
            E.animate(700, lambda e: cv.itemconfigure(kick, fill=mix(theme.INK, theme.LIME, e)), owner=self)
            d = l1.play(delay=100, mode="revolve", step=55, dur=1000)
            l1b.play(delay=380, mode="revolve", step=55, dur=1000)
            l2.play(delay=520, mode="revolve", step=55, dur=1000)
            l2b.play(delay=800, mode="revolve", step=55, dur=1000)
            # curtains wipe off the images
            E.animate(1200, lambda e: cv.coords(c1, mx, my, mx + iw, my + ih * (1 - e)), delay=300,
                      easing="inOutExpo", owner=self)
            E.animate(1100, lambda e: cv.coords(c2, sx, sy + (sh + 10) * e, sx + sw + 10, sy + sh + 10), delay=700,
                      easing="inOutExpo", owner=self)
            E.animate(600, lambda e: cv.itemconfigure(tagc, fill=mix(theme.INK, "#77736B", e)), delay=1500, owner=self)
            badge.pop(delay=1100)
            for i, it in enumerate((lead, self.cyc_item, para)):
                E.animate(800, lambda e, it=it: cv.itemconfigure(it, fill=mix(theme.INK, theme.BONE if it != self.cyc_item else theme.ACCENT, e)),
                          delay=1100 + i * 120, owner=self)
            for i, b in enumerate((b_shop, b_jew)):
                b.set_visible(True)
                b.pop_in(delay=1400 + i * 120)
            E.animate(900, lambda e: cv.itemconfigure(scr, fill=mix(theme.INK, "#9A958B", e)), delay=1800, owner=self)
            move(E, cv, scr, 0, 8, duration=700, delay=2000, loop=True, direction="alternate",
                 easing="inOutSine", owner=self)
            E.after(2600, self._cycle, owner=self)
            _ = d
        self.reveal_at(y0, play, offset=0)
        return h

    def _cycle(self):
        cv, E = self.cv, self.E
        it = self.cyc_item
        x, y = self.cyc_pos

        def out(e):
            cv.coords(it, x, y - 26 * e)
            cv.itemconfigure(it, fill=mix(theme.ACCENT, theme.INK, e))

        def swap():
            self.cyc_i = (self.cyc_i + 1) % len(self.cyc_words)
            cv.itemconfigure(it, text=self.cyc_words[self.cyc_i])

            def inn(e):
                cv.coords(it, x, y + 26 * (1 - e))
                cv.itemconfigure(it, fill=mix(theme.INK, theme.ACCENT, e))
            E.animate(600, inn, easing="outBack", owner=self)
        E.animate(380, out, easing="inQuad", complete=swap, owner=self)
        E.after(2300, self._cycle, owner=self)

    # ------------------------------------------------------------------ #
    def marquees(self, y0):
        Marquee(self, y0, 84, MARQUEE, theme.ACCENT, theme.INK, speed=95)
        Marquee(self, y0 + 84, 44, "PRE-LOVED  /  RE-WORN  /  RE-DEFINED  /  " * 3, theme.INK, theme.BONE,
                font=F("mono", 15, "bold"), speed=60, direction=1)
        return 128

    # ------------------------------------------------------------------ #
    def tiles(self, y0):
        cv, E, W = self.cv, self.E, self.W
        backing = cv.create_rectangle(0, y0, W, y0 + 10, fill=theme.PAPER, outline="")   # hides hero parallax overflow
        y = y0 + 90
        h, _ = section_header(self, y, "00", "SHOP BY OBSESSION", "FIVE DEPARTMENTS. ZERO BASICS. CLICK ONE.",
                              theme.PAPER, theme.INK)
        y += h + 28
        n, gap = 5, 18
        tw = (W - 2 * M - gap * (n - 1)) // n
        th = 440
        spec = [("tee", "1622445275992-e7efb32d2257", 0.3), ("jeans", "1628519662791-c13362859149", 0.55),
                ("trousers", "1653587106660-4908e9a7bae7", 0.55), ("jewel", "1789938632462-56704ef437a1", 0.35),
                ("acc", "1653773991823-636f90ecd5c5", 0.3)]
        for i, (cat, img, focus) in enumerate(spec):
            x = M + i * (tw + gap)
            c = CATS[cat]
            frames = self.A.zoom_frames(cat, img, tw, th, focus, n=7, zoom=1.14, gray_first=True)
            t = f"tile{i}"
            im = cv.create_image(x, y, image=frames[0], anchor="nw", tags=(t,))
            cur = cv.create_rectangle(x, y, x + tw, y + th, fill=theme.INK, outline="", tags=(t,))
            lab_bg = cv.create_rectangle(x, y + th - 86, x + tw, y + th, fill=theme.INK, outline="", tags=(t,))
            lsz = 40
            while theme.measure(F("display", lsz), c["title"]) > tw - 84 and lsz > 22:
                lsz -= 2
            lab = cv.create_text(x + 18, y + th - 44, text=c["title"], font=F("display", lsz), fill=theme.BONE,
                                 anchor="w", tags=(t,))
            cnt = cv.create_text(x + tw - 20, y + th - 44, text=f"{len(by_cat(cat))} →", font=F("mono", 14, "bold"),
                                 fill=theme.LIME, anchor="e", tags=(t,))
            cv.create_rectangle(x + 12, y + 12, x + 50, y + 38, fill=theme.INK, outline="", tags=(t,))
            num = cv.create_text(x + 31, y + 25, text=f"0{i + 1}", font=F("mono", 12, "bold"), fill=theme.LIME,
                                 tags=(t,))
            state = {"z": 0.0, "tw": None}

            def hover(on, frames=frames, im=im, lab_bg=lab_bg, lab=lab, cnt=cnt, state=state, x=x):
                if state["tw"]:
                    state["tw"].cancel()
                a, b = state["z"], (1.0 if on else 0.0)

                def upd(e):
                    state["z"] = a + (b - a) * e
                    k = int(round(state["z"] * (len(frames) - 1)))
                    cv.itemconfigure(im, image=frames[k])
                    cv.itemconfigure(lab_bg, fill=mix(theme.INK, theme.ACCENT, state["z"]))
                    cv.itemconfigure(lab, fill=mix(theme.BONE, theme.INK, state["z"]))
                    cv.itemconfigure(cnt, fill=mix(theme.LIME, theme.INK, state["z"]))
                state["tw"] = E.animate(450, upd, easing="outCubic", owner=self)
                cv.itemconfigure(cnt, angle=0)
                if on:
                    E.animate(500, lambda e: cv.itemconfigure(cnt, angle=-20 * math.sin(e * math.pi)),
                              easing="outQuad", owner=self)

            self.zone((x, y, x + tw, y + th), click=lambda p=c["page"]: self.app.go(p),
                      enter=lambda h=hover: h(True), leave=lambda h=hover: h(False))

            def play(cur=cur, x=x, t=t, i=i):
                E.animate(1000, lambda e: cv.coords(cur, x, y + th * e, x + tw, y + th), delay=100 + i * 140,
                          easing="inOutExpo", owner=self, complete=lambda: cv.delete(cur))
                _ = num
            self.reveal_at(y, play, offset=40)
        cv.coords(backing, 0, y0, W, y + th + 40)
        return (y + th + 40) - y0

    # ------------------------------------------------------------------ #
    def tees(self, y0):
        W = self.W
        y = y0 + 60
        h, _ = section_header(self, y, "01", "TEES THAT TALK", "TOP TRENDING THIS WEEK  ·  BOXY, BAND, BABY & BACK-PRINT",
                              theme.PAPER, theme.INK, view=("VIEW ALL TEES", lambda: self.app.go("tees")))
        y += h + 30
        cw = (W - 2 * M - 3 * 24) // 4
        ih = int(cw * 1.25)
        rail = Rail(self, trending("tee", 9), M, y, cw, ih, ranks=True)
        self.reveal_at(y, rail.reveal, offset=60)
        y += rail.h + 26
        b1, b2 = arrows(self, W - M, y, lambda: rail.slide(-1), lambda: rail.slide(1))
        self.cv.create_text(M, y + 27, text="←  SLIDE FOR MORE  →", font=F("mono", 11, "bold"),
                            fill=theme.MUTED, anchor="w")
        return y + 54 + 70 - y0

    # ------------------------------------------------------------------ #
    def jeans(self, y0):
        cv, E, W = self.cv, self.E, self.W
        band = cv.create_rectangle(0, y0, W, y0 + 10, fill=theme.INK, outline="")
        y = y0 + 90
        h, _ = section_header(self, y, "02", "DENIM ON ROTATION", "BAGGY FIT, NAMED BY THE WASH  ·  DRAG TO SPIN  ·  CLICK THE FRONT PIECE",
                              theme.INK, theme.BONE, view=("VIEW ALL JEANS", lambda: self.app.go("jeans")))
        y += h + 40
        iw, ih = 320, 430
        base = y + ih + 90
        cap_y = base + 56
        name = cv.create_text(W / 2, cap_y, text="", font=F("display", 46), fill=theme.BONE)
        sub = cv.create_text(W / 2, cap_y + 50, text="", font=F("mono", 13, "bold"), fill=theme.LIME)
        self.ring_front = None

        def on_front(p):
            self.ring_front = p
            cv.itemconfigure(name, text=p["name"].upper())
            cv.itemconfigure(sub, text=f"{rupee(p['price'])}   ·   ★ {p['rating']}   ·   {'  /  '.join(p['tags'])}")
            E.animate(450, lambda e: (cv.itemconfigure(name, fill=mix(theme.INK, theme.BONE, e)),
                                      cv.coords(name, W / 2, cap_y + 14 * (1 - e))), easing="outCubic", owner=self)
        ring = RevolvingRing(self, trending("jeans", 8), W / 2, base, 470, iw, ih, theme.INK, on_front=on_front)
        self.reveal_at(y + 100, lambda: ring.start(0), offset=0)
        by = cap_y + 92
        bq = Button(self, W / 2 - 10, by, "QUICK VIEW", lambda: self.ring_front and QuickView(self, self.ring_front),
                    kind="outline-light", anchor="ne", page_bg=theme.INK)
        ba = Button(self, W / 2 + 10, by, "ADD TO BAG", lambda: self.ring_front and self.app.add_to_cart(
            self.ring_front, CATS["jeans"]["sizes"][2]), kind="lime")
        Button(self, M, cap_y - 20, "←", lambda: ring.step(-1), kind="outline-light", arrow=False, w=64, h=64,
               font=F("heavy", 22), page_bg=theme.INK)
        Button(self, W - M, cap_y - 20, "→", lambda: ring.step(1), kind="outline-light", arrow=False, w=64, h=64,
               font=F("heavy", 22), anchor="ne", page_bg=theme.INK)
        _ = (bq, ba)
        band_h = by + 50 + 100 - y0
        cv.coords(band, 0, y0, W, y0 + band_h)
        return band_h

    # ------------------------------------------------------------------ #
    def trousers(self, y0):
        W = self.W
        y = y0 + 90
        h, _ = section_header(self, y, "03", "TROUSERS, REWORKED", "HOVER A STRIP  ·  FLAMES, SWEEPS, PLEATS & PARACHUTES",
                              theme.PAPER, theme.INK, view=("VIEW ALL TROUSERS", lambda: self.app.go("trousers")))
        y += h + 34
        acc = Accordion(self, trending("trousers", 5), M, y, W - 2 * M, 500, collapsed=140)
        self.reveal_at(y, acc.reveal, offset=80)
        return y + 500 + 100 - y0

    # ------------------------------------------------------------------ #
    def jewellery(self, y0):
        """Chrome & crosses - gothic silver, inspired by Spoiled Duckie."""
        cv, E, W = self.cv, self.E, self.W
        pal = CHROMEP
        band = cv.create_rectangle(0, y0, W, y0 + 10, fill=theme.VOID, outline="")
        y = y0 + 90
        h, _ = section_header(self, y, "04", "CHROME & CROSSES", "GOTHIC SILVER JEWELLERY  ·  FOR HIM, HER & EVERYONE BETWEEN",
                              theme.VOID, theme.CHROME_L, view=("SHOP JEWELLERY", lambda: self.app.go("jewellery")),
                              accent=theme.CHROME, mono="type")
        y += h + 30
        bw, bh = W - 2 * M, 440
        ban = self.A.tk_cover("jewel", "1791041709357-132e8aa60d1f", bw, bh, 0.5)
        cv.create_image(M, y, image=ban, anchor="nw")
        cur = cv.create_rectangle(M, y, M + bw, y + bh, fill=theme.CHROME, outline="")
        box = cv.create_rectangle(M + 30, y + bh - 170, M + 540, y + bh - 30, fill=theme.VOID, outline=theme.CHROME_D)
        t1 = cv.create_text(M + 56, y + bh - 150, text="SILVER. CROSSES. STARS.", font=F("display", 40),
                            fill=theme.VOID, anchor="nw")
        t2 = cv.create_text(M + 56, y + bh - 86, text="Cathedral rings, rosaries, ear cuffs and cursed\n"
                                                    "little trinkets. One-word names, no rules.",
                            font=F("type", 15, "bold"), fill=theme.VOID, anchor="nw")

        def play_banner(by=y):
            E.animate(1300, lambda e: cv.coords(cur, M + bw * e, by, M + bw, by + bh), easing="inOutExpo", owner=self,
                      complete=lambda: cv.delete(cur))
            E.animate(700, lambda e: cv.itemconfigure(t1, fill=mix(theme.VOID, theme.CHROME_L, e)), delay=900, owner=self)
            E.animate(700, lambda e: cv.itemconfigure(t2, fill=mix(theme.VOID, theme.CHROME, e)), delay=1050, owner=self)
            _ = box
        self.reveal_at(y, play_banner, offset=60)
        y += bh + 50
        y += best_row(self, y, "jewel", pal, theme.CHROME, theme.VOID, theme.CHROME_L, header=None,
                      label="BEST SELLERS FOR", mono="type")
        band_h = y + 80 - y0
        cv.coords(band, 0, y0, W, y0 + band_h)
        return band_h

    # ------------------------------------------------------------------ #
    def accessories(self, y0):
        """The chrome cabinet - the new accessories department."""
        cv, E, W = self.cv, self.E, self.W
        bg = "#0B0B0C"
        band = cv.create_rectangle(0, y0, W, y0 + 10, fill=bg, outline="")
        Marquee(self, y0, 56, "SHADES  /  CAPS  /  BEANIES  /  CHROME BUCKLES  /  WALLET CHAINS  /  WATCHES  /  CLAW CLIPS  /  BAG CHARMS  /  ",
                theme.CHROME, theme.VOID, font=F("type", 20, "bold"), speed=70, direction=1)
        y = y0 + 56 + 90
        h, _ = section_header(self, y, "05", "THE CHROME CABINET",
                              "NEW: ACCESSORIES  ·  THE PUNCTUATION AT THE END OF A FIT",
                              bg, theme.CHROME_L, view=("SHOP ACCESSORIES", lambda: self.app.go("accessories")),
                              accent=theme.CHROME, mono="type")
        y += h + 30
        cw = (W - 2 * M - 3 * 24) // 4
        ih = int(cw * 1.2)
        pal = dict(CHROMEP, bg=bg)
        rail = Rail(self, trending("acc", 10), M, y, cw, ih, pal=pal, ranks=True)
        self.reveal_at(y, rail.reveal, offset=60)
        y += rail.h + 26
        cv.create_text(M, y + 27, text="←  SLIDE THE CABINET  →", font=F("type", 13, "bold"),
                       fill=theme.CHROME_D, anchor="w")
        arrows(self, W - M, y, lambda: rail.slide(-1), lambda: rail.slide(1), dark=True, bg=bg)
        band_h = y + 54 + 90 - y0
        cv.coords(band, 0, y0 + 56, W, y0 + band_h)
        return band_h

    # ------------------------------------------------------------------ #
    def stats(self, y0):
        cv, E, W = self.cv, self.E, self.W
        h = 330
        cv.create_rectangle(0, y0, W, y0 + h, fill=theme.LIME, outline="")
        data = [(12480, "{:,.0f}+", "PIECES REHOMED"), (33.7, "{:.1f}M", "LITRES OF WATER SAVED"),
                (4.8, "{:.1f}★", "AVERAGE RATING"), (0, "{:.0f}", "LANDFILL GUILT")]
        cw = (W - 2 * M) / 4
        items = []
        for i, (val, fmt, lab) in enumerate(data):
            x = M + i * cw
            if i:
                cv.create_line(x, y0 + 70, x, y0 + h - 70, fill=theme.INK, width=2)
            n = cv.create_text(x + 26, y0 + 80, text=fmt.format(0), font=F("display", 84), fill=theme.INK, anchor="nw")
            cv.create_text(x + 30, y0 + 222, text=lab, font=F("mono", 12, "bold"), fill=theme.INK, anchor="nw")
            items.append((n, val, fmt))

        def play():
            for i, (n, val, fmt) in enumerate(items):
                E.animate(2200, lambda e, n=n, val=val, fmt=fmt: cv.itemconfigure(n, text=fmt.format(val * e)),
                          delay=i * 160, easing="outExpo", owner=self)
                cv.move(n, 0, 30)
                move(E, cv, n, 0, -30, duration=900, delay=i * 160, easing="outBack", owner=self)
        self.reveal_at(y0, play, offset=80)
        return h

    # ------------------------------------------------------------------ #
    def reviews(self, y0):
        W = self.W
        y = y0 + 100
        h, _ = section_header(self, y, "06", "WORD ON THE STREET", "4.8 ★ FROM 6,200+ VERIFIED THRIFTERS",
                              theme.PAPER, theme.INK)
        y += h + 34
        mixed = []
        for k in ("tee", "jeans", "acc", "jewel", "trousers"):
            mixed += REVIEWS[k][:2]
        rail = ReviewRail(self, mixed, M, y, w=390, h=280)
        self.reveal_at(y, rail.reveal, offset=60)
        y += 280 + 30
        arrows(self, W - M, y, lambda: rail.slide(-1), lambda: rail.slide(1))
        return y + 54 + 110 - y0
