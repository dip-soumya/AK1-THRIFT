"""CATEGORY pages - TEES / JEANS / TROUSERS / JEWELLERY / ACCESSORIES.

  banner  ->  department switcher  ->  TOP TRENDERS revolving ring
  ->  SHOP ALL grid with animated sort (FLIP: cards glide to their new slots)
  ->  REVIEWS: rating summary, write-a-review form, review rail
"""
import random

from .. import theme
from ..anim import mix, move
from ..data import BEST_FILTERS, CATS, QUOTES, REVIEWS, SORTS, by_cat, trending
from ..page import Page
from ..theme import F, rupee
from ..widgets import (CHROMEP, DARK, LIGHT, Button, Letters, ProductCard, QuickView, ReviewForm, ReviewRail,
                       RevolvingRing, RotatingBadge, quote_block, rating_summary, section_header)
from .common import M, arrows, best_row, category_chips, footer


class CategoryPage(Page):
    cat = "tee"
    bg = theme.PAPER
    pal = LIGHT
    ring_bg = theme.INK
    accent = theme.ACCENT
    quote_i = 2
    mono = "mono"          # small-print font ("type" = typewriter on the chrome pages)
    best_sub = ""

    @property
    def fox_lines(self):
        return self.cat

    def build(self):
        self.c = CATS[self.cat]
        y = 0
        y += self.banner(y)
        y += self.trenders(y)
        y += self.extra(y)
        y += self.shop_all(y)
        y += self.reviews(y)
        y += quote_block(self, y, *QUOTES[self.quote_i], bg=self.bg, fg=self.pal["fg"], accent=self.accent)
        y += footer(self, y)
        self.content_h = y

    @property
    def chrome(self):
        return self.accent == theme.CHROME

    def extra(self, y0):
        """Ranked BEST SELLERS row with a filter toggle that revolves the cards."""
        if self.cat not in BEST_FILTERS:
            return 0
        return best_row(self, y0, self.cat, self.pal, self.accent, self.bg, self.pal["fg"],
                        header=("★", "BEST SELLERS", self.best_sub), label="FILTER", mono=self.mono)

    # ------------------------------------------------------------------ #
    def banner(self, y0):
        cv, E, W = self.cv, self.E, self.W
        h = 560
        cat, img, focus = self.c["banner"]
        ph = self.A.tk_cover(cat, img, W, h + 160, focus, dim=0.45, dim_to=theme.INK)
        cv.create_rectangle(0, y0, W, y0 + h, fill=theme.INK, outline="")
        cv.create_image(0, y0 - 80, image=ph, anchor="nw", tags=("banpar",))
        self.add_parallax("banpar", 0.35)
        cur = cv.create_rectangle(0, y0, W, y0 + h, fill=self.accent, outline="")
        crumb = cv.create_text(M, y0 + 54, text=f"AK1 / SHOP / {self.c['long']}", font=F(self.mono, 14, "bold"),
                               fill=theme.INK, anchor="nw")
        tf = F("display", 230)
        title = Letters(self, M - 6, y0 + h - 70, self.c["title"], tf, theme.BONE, theme.INK, tags=("tpar",))
        self.add_parallax("tpar", -0.12)
        n = len(by_cat(self.cat))
        tag = cv.create_text(M, y0 + h - 44, text=f"{self.c['tagline']}   ·   {n} PIECES   ·   NEW DROP FRIDAY",
                             font=F(self.mono, 14 if self.chrome else 13, "bold"), fill=theme.INK, anchor="w")
        badge = RotatingBadge(self, W - M - 90, y0 + 130, 70, "TOP TRENDERS • THIS WEEK • AK1 • ",
                              theme.INK, fill=theme.CHROME if self.chrome else theme.LIME,
                              center="✦", font=F("mono", 12, "bold"))

        def play():
            E.animate(1100, lambda e: cv.coords(cur, 0, y0, W, y0 + h * (1 - e)), easing="inOutExpo", owner=self)
            title.play(delay=350, mode="revolve", step=70, dur=1100)
            E.animate(700, lambda e: cv.itemconfigure(crumb, fill=mix(theme.INK, theme.CHROME if self.chrome else theme.LIME, e)),
                      delay=600, owner=self)
            E.animate(700, lambda e: cv.itemconfigure(tag, fill=mix(theme.INK, theme.BONE, e)), delay=900, owner=self)
            badge.pop(delay=900)
        self.reveal_at(y0, play, offset=0)
        # department switcher (separate buttons that land on each area)
        sy = y0 + h
        cv.create_rectangle(0, sy, W, sy + 110, fill=theme.INK, outline="")
        cv.create_text(W - M, sy + 55, text="JUMP TO →", font=F("mono", 12, "bold"), fill="#77736B", anchor="e")
        category_chips(self, sy + 25, self.cat, dark=True)
        return h + 110

    # ------------------------------------------------------------------ #
    def trenders(self, y0):
        cv, E, W = self.cv, self.E, self.W
        bg = self.ring_bg
        band = cv.create_rectangle(0, y0, W, y0 + 10, fill=bg, outline="")
        y = y0 + 80
        h, _ = section_header(self, y, "01", "TOP TRENDERS", "WHAT EVERYONE'S ADDING TO BAG RIGHT NOW  ·  DRAG TO SPIN",
                              bg, theme.BONE, accent=self.accent, mono=self.mono)
        y += h + 30
        iw, ih = 310, 410
        base = y + ih + 90
        cap_y = base + 56
        rank = cv.create_text(W / 2, cap_y - 6, text="", font=F("mono", 12, "bold"), fill=self.accent)
        name = cv.create_text(W / 2, cap_y + 26, text="", font=F("display", 44), fill=theme.BONE)
        sub = cv.create_text(W / 2, cap_y + 74, text="", font=F(self.mono, 14, "bold"),
                             fill=theme.CHROME if self.chrome else theme.LIME)
        tops = trending(self.cat, 7)
        self.front = tops[0]

        def on_front(p):
            self.front = p
            cv.itemconfigure(rank, text=f"#{tops.index(p) + 1} TRENDING  ·  {p['sold']:,} SOLD")
            cv.itemconfigure(name, text=p["name"].upper())
            cv.itemconfigure(sub, text=f"{rupee(p['price'])}   ·   ★ {p['rating']}   ·   {p['cond']}")
            E.animate(450, lambda e: (cv.itemconfigure(name, fill=mix(bg, theme.BONE, e)),
                                      cv.coords(name, W / 2, cap_y + 26 + 14 * (1 - e))), easing="outCubic", owner=self)
        ring = RevolvingRing(self, tops, W / 2, base, 460, iw, ih, bg, on_front=on_front)
        self.reveal_at(y + 60, lambda: ring.start(0), offset=0)
        by = cap_y + 112
        Button(self, W / 2 - 10, by, "QUICK VIEW", lambda: QuickView(self, self.front), kind="outline-light",
               anchor="ne", page_bg=bg)
        Button(self, W / 2 + 10, by, "ADD TO BAG", lambda: self.app.add_to_cart(
            self.front, self.c["sizes"][len(self.c["sizes"]) // 2]), kind="chrome" if self.chrome else "lime")
        Button(self, M, cap_y - 10, "←", lambda: ring.step(-1), kind="outline-light", arrow=False, w=64, h=64,
               font=F("heavy", 22), page_bg=bg)
        Button(self, W - M, cap_y - 10, "→", lambda: ring.step(1), kind="outline-light", arrow=False, w=64, h=64,
               font=F("heavy", 22), anchor="ne", page_bg=bg)
        band_h = by + 50 + 90 - y0
        cv.coords(band, 0, y0, W, y0 + band_h)
        return band_h

    # ------------------------------------------------------------------ #
    def shop_all(self, y0):
        cv, E, W = self.cv, self.E, self.W
        pal = self.pal
        cv.create_rectangle(0, y0, W, y0 + 10, fill=self.bg, outline="")
        y = y0 + 90
        h, _ = section_header(self, y, "02", "SHOP ALL", "SORT IT YOUR WAY  ·  CARDS GLIDE TO THEIR NEW SPOT",
                              self.bg, pal["fg"], accent=self.accent, mono=self.mono)
        y += h + 26
        # sort pills with a sliding indicator
        cv.create_text(M, y + 22, text="SORT BY", font=F("mono", 12, "bold"), fill=self.accent, anchor="w")
        pf = F("heavy", 13)
        px = M + 96
        pills = []
        ind = cv.create_rectangle(0, 0, 0, 0, fill=pal["fg"], outline="")
        for lab, key in SORTS:
            w = theme.measure(pf, lab) + 36
            cv.create_rectangle(px, y, px + w, y + 44, outline=pal["fg"], width=2)
            t = cv.create_text(px + w / 2, y + 22, text=lab, font=pf, fill=pal["fg"])
            pills.append([px, w, t, key, lab])
            px += w + 8
        cv.tag_raise(ind)
        for p in pills:
            cv.tag_raise(p[2])
        self.sort_count = cv.create_text(W - M, y + 22, text="", font=F("mono", 12), fill=pal["muted"], anchor="e")
        y += 44 + 34
        cols = 4
        gap = 24
        cw = (W - 2 * M - gap * (cols - 1)) // cols
        ih = int(cw * 1.25)
        prods = sorted(by_cat(self.cat), key=SORTS[0][1])
        cards = []
        row_h = ih + 118 + 40
        for i, p in enumerate(prods):
            r, c = divmod(i, cols)
            cards.append(ProductCard(self, p, M + c * (cw + gap), y + r * row_h, cw, ih, pal))
        rows = (len(prods) + cols - 1) // cols
        for r in range(rows):
            def rv(r=r):
                for k, card in enumerate(cards[r * cols:(r + 1) * cols]):
                    card.reveal(k * 110)
            self.reveal_at(y + r * row_h, rv, offset=80)
        state = {"k": 0, "order": list(cards)}

        def slots(i):
            r, c = divmod(i, cols)
            return M + c * (cw + gap), y + r * row_h

        def set_ind(k, anim=True):
            x0, w, t, key, lab = pills[k]
            for p in pills:
                cv.itemconfigure(p[2], fill=pal["fg"])
            cv.itemconfigure(t, fill=pal["bg"] if pal["fg"] != theme.INK else theme.LIME)
            a = cv.coords(ind) or [x0, y, x0, y]
            if not anim or a == [0, 0, 0, 0]:
                cv.coords(ind, x0, y - 44 - 34, x0 + w, y - 34)
                return
            b = [x0, y - 78, x0 + w, y - 34]
            E.animate(650, lambda e: cv.coords(ind, *[u + (v - u) * e for u, v in zip(a, b)]),
                      easing="outElasticSoft", owner=self)
            cv.itemconfigure(self.sort_count, text=f"{len(cards)} PIECES  ·  SORTED BY {lab}")

        def do_sort(k):
            if k == state["k"]:
                return
            state["k"] = k
            set_ind(k)
            keyf = pills[k][3]
            order = sorted(cards, key=lambda cd: keyf(cd.p))
            for cd in cards:
                if not cd.revealed:
                    cd.reveal(0, mode="instant")
            for i, cd in enumerate(order):
                nx, ny = slots(i)
                cd.move_to(nx, ny, delay=i * 22, dur=1000, easing="inOutExpo")
            state["order"] = order
            self.raise_hud()

        for k, p in enumerate(pills):
            x0, w = p[0], p[1]
            self.zone((x0, y - 78, x0 + w, y - 34), click=lambda k=k: do_sort(k))
        self.do_sort = do_sort
        self.grid_y = y
        cv.itemconfigure(self.sort_count, text=f"{len(cards)} PIECES  ·  SORTED BY {pills[0][4]}")
        set_ind(0, anim=False)
        return y + rows * row_h + 40 - y0

    # ------------------------------------------------------------------ #
    def reviews(self, y0):
        cv, W = self.cv, self.W
        pal = self.pal
        y = y0 + 60
        h, _ = section_header(self, y, "03", "REVIEWS", "REAL PEOPLE. REAL OPINIONS. REAL GOOD TASTE.", self.bg, pal["fg"],
                              accent=self.accent, mono=self.mono)
        y += h + 40
        revs = REVIEWS[self.cat]
        total = sum(p["reviews"] for p in by_cat(self.cat))
        avg = round(sum(p["rating"] * p["reviews"] for p in by_cat(self.cat)) / max(1, total), 1)
        rating_summary(self, M, y, self.cat, avg, total, pal)
        fw = W - 2 * M - 700
        rail_holder = {}

        def submitted(r):
            rail_holder["rail"].insert(r)
            self.fox_say("review")
        ReviewForm(self, W - M - fw, y - 10, fw, submitted, trending(self.cat), pal)
        y += 360
        rail = ReviewRail(self, revs, M, y, w=390, h=280, pal=pal)
        rail_holder["rail"] = rail
        self.reveal_at(y, rail.reveal, offset=60)
        y += 280 + 30
        arrows(self, W - M, y, lambda: rail.slide(-1), lambda: rail.slide(1), dark=pal["fg"] != theme.INK, bg=self.bg)
        return y + 54 + 40 - y0


class TeesPage(CategoryPage):
    key = "tees"
    title = "TEES"
    cat = "tee"
    quote_i = 2


class JeansPage(CategoryPage):
    """Denim wall inspired by Bofrike: baggy fits named by their wash, waist-mapped sizes."""
    key = "jeans"
    title = "JEANS"
    cat = "jeans"
    quote_i = 3
    ring_bg = theme.DENIM_D
    best_sub = "WHAT NEVER STAYS ON THE RACK  ·  FILTER FOR HIM OR FOR HER"


class TrousersPage(CategoryPage):
    """Bofrike-style bottoms: sweeping wide legs, pleats, bubble linen and dark graphic baggies."""
    key = "trousers"
    title = "TROUSERS"
    cat = "trousers"
    quote_i = 4
    ring_bg = "#1F1A14"
    best_sub = "WIDE-LEG, PLEATED, PRINTED OR UTILITY  ·  PICK YOUR SILHOUETTE"


class JewelleryPage(CategoryPage):
    """Chrome-gothic jewellery inspired by Spoiled Duckie: black, silver, typewriter type."""
    key = "jewellery"
    title = "JEWELLERY"
    cat = "jewel"
    bg = theme.VOID
    pal = CHROMEP
    ring_bg = "#0F0F11"
    accent = theme.CHROME
    mono = "type"
    quote_i = 9
    best_sub = "THE PIECES THAT NEVER STAY IN THE CABINET"


class AccessoriesPage(CategoryPage):
    """New department, also Spoiled-Duckie-led: shades, caps, chrome buckles, watches, charms."""
    key = "accessories"
    title = "ACCESSORIES"
    cat = "acc"
    bg = theme.VOID
    pal = CHROMEP
    ring_bg = "#121214"
    accent = theme.CHROME
    mono = "type"
    quote_i = 10
    best_sub = "CAPS, SHADES, BUCKLES, WATCHES & CHARMS  ·  FILTER BY WHAT'S MISSING FROM YOUR FIT"
