"""CHECKOUT - 'Pay from your back pocket'.

Left : your bag (qty steppers, swipe-out remove, promo code, live animated totals, eco meter)
Right: a stitched denim back-pocket holding the payment methods
       CARD -> a kraft-paper swing tag that IS your card (flips to the back for CVV)
       UPI  -> generated QR with a scanning laser
       CASH -> a hanger with a price tag
Pay  -> 'stitching your order' spinner -> confetti made of tiny tees -> order confirmed
(Demo only. Nothing is charged and nothing leaves this computer.)
"""
import math
import random
import tkinter as tk

from .. import theme
from ..anim import mix, move
from ..data import CATS, FOX
from ..page import Page
from ..theme import F, rupee
from ..widgets import Button, Letters, lines, rrect
from .common import M, footer

WATER = {"tee": 2700, "jeans": 7500, "trousers": 5000, "jewel": 300, "acc": 400}
KRAFT = "#E8D9BC"
COPPER = "#B87333"


class CheckoutPage(Page):
    key = "checkout"
    title = "CHECKOUT"
    bg = theme.PAPER
    fox_lines = "checkout"

    def build(self):
        self.promo = False
        self.method = "card"
        self.shown = {}
        self.vals = {}
        y = self.header(0)
        self.body_y = y
        h_left = self.bag(y)
        h_right = self.pocket(y)
        y += max(h_left, h_right) + 80
        y += footer(self, y)
        self.content_h = y
        self.recalc(anim=False)

    # ================================================================== #
    def header(self, y0):
        cv, E, W = self.cv, self.E, self.W
        h = 300
        cv.create_rectangle(0, y0, W, y0 + h, fill=theme.INK, outline="")
        crumb = cv.create_text(M, y0 + 50, text="AK1 / BAG / PAY", font=F("mono", 13, "bold"), fill=theme.INK,
                               anchor="nw")
        t = Letters(self, M - 4, y0 + h - 40, "CHECKOUT", F("display", 170), theme.BONE, theme.INK)
        steps = ["01  BAG", "02  DETAILS", "03  PAY"]
        sx = W - M
        items = []
        for s in reversed(steps):
            it = cv.create_text(sx, y0 + 60, text=s, font=F("mono", 12, "bold"), fill=theme.INK, anchor="ne")
            sx -= theme.measure(F("mono", 12, "bold"), s) + 40
            items.append(it)

        def play():
            t.play(mode="revolve", step=60, dur=1000)
            E.animate(600, lambda e: cv.itemconfigure(crumb, fill=mix(theme.INK, theme.LIME, e)), delay=300, owner=self)
            for i, it in enumerate(reversed(items)):
                E.animate(500, lambda e, it=it, i=i: cv.itemconfigure(it, fill=mix(theme.INK, theme.LIME if i == 2 else "#8a857b", e)),
                          delay=500 + i * 150, owner=self)
        self.reveal_at(y0, play, offset=0)
        return h

    # ================================================================== #
    #  LEFT - the bag
    # ================================================================== #
    def bag(self, y0):
        cv, E = self.cv, self.E
        x = M
        self.lw = lw = 640
        y = y0 + 70
        self.bag_title = cv.create_text(x, y, text="YOUR BAG", font=F("display", 52), fill=theme.INK, anchor="nw")
        self.bag_count = cv.create_text(x + 260, y + 18, text="", font=F("mono", 13, "bold"), fill=theme.ACCENT,
                                        anchor="nw")
        y += 90
        cv.create_line(x, y, x + lw, y, fill=theme.INK, width=2)
        self.rows = []
        self.row_h = 140
        cart = self.app.cart
        for i, item in enumerate(cart):
            self.rows.append(self._row(item, x, y + i * self.row_h, i))
        self.rows_y = y
        n = max(1, len(cart))
        sy = y + n * self.row_h + 30
        # empty state
        self.empty_tag = "emptystate"
        cv.create_text(x, y + 30, text="NOTHING HERE YET.", font=F("display", 44), fill=theme.INK, anchor="nw",
                       tags=(self.empty_tag,))
        cv.create_text(x, y + 96, text=random.choice(FOX["empty"]).upper(), font=F("mono", 12, "bold"),
                       fill=theme.MUTED, anchor="nw", tags=(self.empty_tag,))
        self.empty_btn = Button(self, x + lw, y + 30, "GO THRIFTING", lambda: self.app.go("home"), kind="accent",
                                anchor="ne", shadow=theme.INK)
        self._set_empty(len(cart) == 0)
        # summary (tagged so it can glide up when rows are removed)
        self.sum_tag = "summary"
        self.summary(x, sy, lw)
        return sy + 560 - y0

    def _set_empty(self, on):
        self.cv.itemconfigure(self.empty_tag, state="normal" if on else "hidden")
        self.empty_btn.set_visible(on)

    def _row(self, item, x, y, i):
        cv, E = self.cv, self.E
        p = item["p"]
        tag = f"row{id(item)}"
        t = (tag,)
        ph = self.A.tk_cover(p["cat"], p["img"], 92, 116, p["focus"])
        cv.create_image(x, y + 12, image=ph, anchor="nw", tags=t)
        cv.create_text(x + 116, y + 18, text=p["name"].upper(), font=F("heavy", 17), fill=theme.INK, anchor="nw",
                       tags=t)
        cv.create_text(x + 116, y + 46, text=f"SIZE {item['size']}  ·  {p['cond']}  ·  {CATS[p['cat']]['title']}",
                       font=F("mono", 11), fill=theme.MUTED, anchor="nw", tags=t)
        price = cv.create_text(x + self.lw, y + 16, text=rupee(p["price"] * item["qty"]), font=F("display", 30),
                               fill=theme.INK, anchor="ne", tags=t)
        cv.create_text(x + self.lw, y + 62, text=rupee(p["mrp"] * item["qty"]), font=F("mono", 11) + ("overstrike",),
                       fill=theme.MUTED, anchor="ne", tags=t)
        # qty stepper
        qy = y + 80
        row = {"item": item, "tag": tag, "y": y, "price": price, "zones": []}
        bx = x + 116

        def box(xx, label, cb):
            r = cv.create_rectangle(xx, qy, xx + 36, qy + 36, fill=theme.PAPER, outline=theme.INK, width=2, tags=t)
            tt = cv.create_text(xx + 18, qy + 18, text=label, font=F("heavy", 16), fill=theme.INK, tags=t)

            def enter():
                cv.itemconfigure(r, fill=theme.INK)
                cv.itemconfigure(tt, fill=theme.LIME)

            def leave():
                cv.itemconfigure(r, fill=theme.PAPER)
                cv.itemconfigure(tt, fill=theme.INK)
            row["zones"].append(self.zone(lambda: (xx, row["y"] + 80, xx + 36, row["y"] + 116), click=cb,
                                          enter=enter, leave=leave))
        box(bx, "−", lambda: self.qty(row, -1))
        row["qty"] = cv.create_text(bx + 58, qy + 18, text=str(item["qty"]), font=F("display", 22), fill=theme.INK,
                                    tags=t)
        box(bx + 80, "+", lambda: self.qty(row, 1))
        rm = cv.create_text(x + self.lw, qy + 18, text="✕  REMOVE", font=F("mono", 11, "bold"), fill=theme.ACCENT,
                            anchor="e", tags=t)
        rw = theme.measure(F("mono", 11, "bold"), "✕  REMOVE")
        row["zones"].append(self.zone(lambda: (x + self.lw - rw, row["y"] + 86, x + self.lw, row["y"] + 112),
                                      click=lambda: self.remove(row),
                                      enter=lambda: cv.itemconfigure(rm, fill=theme.INK),
                                      leave=lambda: cv.itemconfigure(rm, fill=theme.ACCENT)))
        cv.create_line(x, y + self.row_h, x + self.lw, y + self.row_h, fill=theme.LINE, width=1, tags=t)
        # entrance: slide from the left, staggered
        cv.move(tag, -80, 0)
        cv.itemconfigure(tag, state="hidden")
        E.after(200 + i * 110, lambda: cv.itemconfigure(tag, state="normal"), owner=self)
        move(E, cv, tag, 80, 0, duration=900, delay=200 + i * 110, easing="outExpo", owner=self)
        return row

    def qty(self, row, d):
        item = row["item"]
        nq = item["qty"] + d
        if nq <= 0:
            return self.remove(row)
        if nq > 5:
            self.fox_say("added")
            return
        item["qty"] = nq
        cv = self.cv
        cv.itemconfigure(row["qty"], text=str(nq))
        cv.itemconfigure(row["price"], text=rupee(item["p"]["price"] * nq))
        it = row["qty"]
        self.E.animate(400, lambda e: cv.itemconfigure(it, font=F("display", int(22 + 10 * math.sin(e * math.pi)))),
                       owner=self)
        self.app.nav.set_count(sum(i["qty"] for i in self.app.cart))
        self.recalc()

    def remove(self, row):
        cv, E = self.cv, self.E
        if row not in self.rows:
            return
        idx = self.rows.index(row)
        self.rows.remove(row)
        if row["item"] in self.app.cart:
            self.app.cart.remove(row["item"])
        for z in row["zones"]:
            self.remove_zone(z)
        move(E, cv, row["tag"], -self.W, 0, duration=600, easing="inBack", owner=self,
             complete=lambda: cv.delete(row["tag"]))
        for k, r in enumerate(self.rows[idx:]):
            r["y"] -= self.row_h
            move(E, cv, r["tag"], 0, -self.row_h, duration=800, delay=250 + k * 60, easing="outExpo", owner=self)
        if self.rows:
            move(E, cv, self.sum_tag, 0, -self.row_h, duration=800, delay=300, easing="outExpo", owner=self)
            self.sum_y -= self.row_h
        else:
            E.after(450, lambda: self._set_empty(True), owner=self)
            self.fox_say("empty")
        self.app.nav.set_count(sum(i["qty"] for i in self.app.cart))
        self.recalc()

    # ------------------------------------------------------------------ #
    def summary(self, x, y, w):
        cv = self.cv
        t = (self.sum_tag,)
        self.sum_y = y
        cv.create_text(x, y, text="PROMO CODE", font=F("mono", 11, "bold"), fill=theme.MUTED, anchor="nw", tags=t)
        self.promo_var = tk.StringVar()
        ent = tk.Entry(self.cv, textvariable=self.promo_var, font=F("mono", 15, "bold"), bg=theme.WHITE, fg=theme.INK,
                       insertbackground=theme.ACCENT, relief="flat", highlightthickness=2,
                       highlightbackground=theme.INK, highlightcolor=theme.ACCENT)
        self.promo_win = self.add_window(x, y + 22, ent, anchor="nw", width=w - 170, height=50, tags=t)
        self.promo_btn = Button(self, x + w, y + 22, "APPLY", self.apply_promo, kind="ink", anchor="ne", h=50,
                                tags=t)
        self.promo_msg = cv.create_text(x, y + 84, text="HINT: FOXES LOVE A GOOD DEAL.", font=F("mono", 10),
                                        fill=theme.MUTED, anchor="nw", tags=t)
        y += 124
        lines = [("subtotal", "SUBTOTAL"), ("savings", "THRIFT SAVINGS vs. RETAIL"), ("promo", "PROMO  THRIFTY10"),
                 ("delivery", "DELIVERY"), ("cod", "CASH HANDLING")]
        self.sum_items = {}
        for i, (k, lab) in enumerate(lines):
            yy = y + i * 34
            a = cv.create_text(x, yy, text=lab, font=F("mono", 13, "bold"), fill=theme.INK, anchor="nw", tags=t)
            b = cv.create_text(x + w, yy, text="", font=F("mono", 13, "bold"),
                               fill=theme.ACCENT if k in ("savings", "promo") else theme.INK, anchor="ne", tags=t)
            self.sum_items[k] = (a, b)
        y += len(lines) * 34 + 10
        cv.create_line(x, y, x + w, y, fill=theme.INK, width=3, tags=t)
        cv.create_text(x, y + 26, text="TOTAL", font=F("display", 44), fill=theme.INK, anchor="nw", tags=t)
        self.total_item = cv.create_text(x + w, y + 14, text="", font=F("display", 64), fill=theme.INK, anchor="ne",
                                         tags=t)
        y += 120
        # eco meter
        cv.create_rectangle(x, y, x + w, y + 92, fill=theme.LIME, outline=theme.INK, width=2, tags=t)
        self.eco_txt = cv.create_text(x + 20, y + 18, text="", font=F("heavy", 15), fill=theme.INK, anchor="nw", tags=t)
        self.eco_track = cv.create_rectangle(x + 20, y + 56, x + w - 20, y + 70, fill=theme.WHITE, outline=theme.INK,
                                             width=2, tags=t)
        self.eco_bar = cv.create_rectangle(x + 20, y + 56, x + 20, y + 70, fill=theme.INK, outline="", tags=t)
        self.eco_geo = (x + 20, y + 56, x + w - 20, y + 70)

    def apply_promo(self):
        code = self.promo_var.get().strip().upper()
        cv = self.cv
        if code == "THRIFTY10":
            self.promo = True
            cv.itemconfigure(self.promo_msg, text="✔ THRIFTY10 APPLIED  ·  EXTRA 10% OFF", fill=theme.ACCENT)
            self.fox_say("promo_ok")
        else:
            cv.itemconfigure(self.promo_msg, text="✕ NOT A CODE. (THE FOX KNOWS ONE...)", fill=theme.ACCENT)
            move(self.E, cv, self.promo_msg, 8, 0, duration=60, loop=6, direction="alternate", owner=self)
            self.fox_say("promo_bad")
        self.recalc()

    def totals(self):
        cart = self.app.cart
        sub = sum(i["p"]["price"] * i["qty"] for i in cart)
        sav = sum((i["p"]["mrp"] - i["p"]["price"]) * i["qty"] for i in cart)
        promo = round(sub * 0.10) if (self.promo and sub) else 0
        delivery = 0 if (sub - promo >= 1499 or sub == 0) else 99
        cod = 49 if (self.method == "cash" and sub) else 0
        water = sum(WATER[i["p"]["cat"]] * i["qty"] for i in cart)
        return dict(subtotal=sub, savings=sav, promo=promo, delivery=delivery, cod=cod,
                    total=sub - promo + delivery + cod, water=water, n=sum(i["qty"] for i in cart))

    def recalc(self, anim=True):
        cv, E = self.cv, self.E
        T = self.totals()
        old = self.vals or {k: 0 for k in T}
        self.vals = T
        fmt = {"subtotal": lambda v: rupee(v), "savings": lambda v: "−" + rupee(v), "promo": lambda v: "−" + rupee(v),
               "delivery": lambda v: "FREE" if v == 0 else rupee(v), "cod": lambda v: rupee(v)}
        for k, (a, b) in self.sum_items.items():
            show = not (k == "promo" and not self.promo) and not (k == "cod" and self.method != "cash")
            cv.itemconfigure(a, fill=theme.INK if show else theme.LINE)
            if not show:
                cv.itemconfigure(b, text="—")
                continue
            if T[k] == old.get(k) or not anim:
                cv.itemconfigure(b, text=fmt[k](T[k]))
            else:
                a0, b0, f = old.get(k, 0), T[k], fmt[k]
                E.animate(900, lambda e, b=b, a0=a0, b0=b0, f=f: cv.itemconfigure(b, text=f(a0 + (b0 - a0) * e)),
                          easing="outExpo", owner=self)
        a0, b0 = old["total"], T["total"]
        E.animate(1100 if anim else 1, lambda e: cv.itemconfigure(self.total_item, text=rupee(a0 + (b0 - a0) * e)),
                  easing="outExpo", owner=self)
        if anim and a0 != b0:
            move(E, cv, self.total_item, 0, -8, duration=200, direction="alternate", loop=2, owner=self)
        n = T["n"]
        cv.itemconfigure(self.bag_count, text=f"{n} PIECE{'S' if n != 1 else ''}")
        cv.itemconfigure(self.eco_txt, text=f"THIS ORDER SAVES ~{T['water']:,} LITRES OF WATER")
        frac = min(1.0, T["water"] / 30000)
        cur = cv.coords(self.eco_bar)
        tr = cv.coords(self.eco_track)
        w0 = (cur[2] - cur[0]) if cur else 0

        def eco(e):
            x1, y1, x2, y2 = cv.coords(self.eco_track)
            cv.coords(self.eco_bar, x1, y1, x1 + w0 + ((x2 - x1) * frac - w0) * e, y2)
        E.animate(1200 if anim else 1, eco, easing="outExpo", owner=self)
        _ = tr
        if hasattr(self, "pay_btn"):
            self.pay_btn.set_text(f"PAY {rupee(T['total'])}" if n else "BAG IS EMPTY")

    # ================================================================== #
    #  RIGHT - the denim back pocket
    # ================================================================== #
    def pocket(self, y0):
        cv, E, W = self.cv, self.E, self.W
        px = M + self.lw + 70
        pw = W - M - px
        py = y0 + 70
        ph = 950
        self.px, self.py, self.pw = px, py, pw
        tip = py + ph
        shape = [px, py, px + pw, py, px + pw, py + ph - 140, px + pw / 2, tip, px, py + ph - 140]
        # denim body + twill + shadow pre-rendered ONCE with Pillow (was ~170 canvas lines redrawn every scroll frame)
        self._pocket_ph = self._pocket_image(pw, ph)
        cv.create_image(px - 2, py - 2, image=self._pocket_ph, anchor="nw")
        # stitching
        for inset, col in ((14, theme.STITCH), (24, theme.STITCH)):
            pts = [px + inset, py + 44 if inset == 14 else py + 54, px + pw - inset, py + 44 if inset == 14 else py + 54,
                   px + pw - inset, py + ph - 140 - inset * 0.4, px + pw / 2, tip - inset * 1.25,
                   px + inset, py + ph - 140 - inset * 0.4, px + inset, py + 44 if inset == 14 else py + 54]
            cv.create_line(pts, fill=col, width=2, dash=(7, 5))
        cv.create_line(px + 10, py + 16, px + pw - 10, py + 16, fill=theme.STITCH, width=2, dash=(7, 5))
        cv.create_line(px + 10, py + 26, px + pw - 10, py + 26, fill=theme.STITCH, width=2, dash=(7, 5))
        # arcuate (the iconic back-pocket stitch)
        ay = py + ph - 115
        for off in (0, 12):
            cv.create_line(px + 60, ay - 40 + off, px + pw / 4, ay + 10 + off, px + pw / 2, ay - 30 + off,
                           px + 3 * pw / 4, ay + 10 + off, px + pw - 60, ay - 40 + off,
                           smooth=True, fill=theme.STITCH, width=3)
        # rivets
        for rx in (px + 14, px + pw - 14):
            cv.create_oval(rx - 8, py + 8, rx + 8, py + 24, fill=COPPER, outline="#7a4a1f", width=2)
            cv.create_oval(rx - 3, py + 13, rx + 3, py + 19, fill="#D99A5B", outline="")
        # leather patch
        lpx = px + pw - 150
        cv.create_rectangle(lpx, py + 46, lpx + 112, py + 96, fill="#8B5A2B", outline="#5E3A18", width=2)
        cv.create_rectangle(lpx + 5, py + 51, lpx + 107, py + 91, outline="#C08A52", dash=(3, 3))
        cv.create_text(lpx + 56, py + 71, text="AK1 · 26", font=F("heavy", 16), fill="#F3D9B5")
        self.ptitle = lines(cv, px + 40, py + 44, ["PAY FROM YOUR", "BACK POCKET."], F("display", 36), theme.BONE)
        # method tabs (fabric labels)
        ty = py + 156
        tabs = [("card", "CARD"), ("upi", "UPI"), ("cash", "CASH ON DELIVERY")]
        tf = F("heavy", 14)
        tx = px + 40
        self.tabs = {}
        self.tab_ind = cv.create_rectangle(0, 0, 0, 0, fill=theme.LIME, outline="")
        for key, lab in tabs:
            w = theme.measure(tf, lab) + 40
            r = cv.create_rectangle(tx, ty, tx + w, ty + 44, fill=theme.BONE, outline=theme.INK, width=2)
            cv.create_rectangle(tx + 4, ty + 4, tx + w - 4, ty + 40, outline=theme.STITCH, dash=(4, 3))
            t = cv.create_text(tx + w / 2, ty + 22, text=lab, font=tf, fill=theme.INK)
            self.tabs[key] = (tx, w, r, t)
            self.zone((tx, ty, tx + w, ty + 44), click=lambda k=key: self.set_method(k))
            tx += w + 10
        cv.tag_raise(self.tab_ind)
        for k, (tx_, w, r, t) in self.tabs.items():
            cv.tag_raise(t)
        self.tab_y = ty
        x0, w0 = self.tabs["card"][0], self.tabs["card"][1]
        cv.coords(self.tab_ind, x0, ty, x0 + w0, ty + 44)
        cy = ty + 76
        self.content_y = cy
        self.method_windows = {"card": [], "upi": [], "cash": []}
        self.build_card(cy)
        self.build_upi(cy)
        self.build_cash(cy)
        self._show_method("card", anim=False)
        # pay button
        by = py + 722
        self.pay_btn = Button(self, px + pw / 2, by, "PAY", self.pay, kind="lime", anchor="center", h=66,
                              w=pw - 120, shadow=theme.INK, font=F("display", 28))
        cv.create_text(px + pw / 2, by + 56, text="\U0001F512  DEMO CHECKOUT  ·  NOTHING IS CHARGED", font=F("mono", 10, "bold"),
                       fill="#C9D4E6")
        return ph + 120

    def _pocket_image(self, pw, ph):
        """Denim back-pocket: drop shadow, indigo body, diagonal twill, seam outline."""
        from PIL import Image, ImageDraw, ImageTk
        pad = 2
        W, H = pw + 16 + pad, ph + 16 + pad
        im = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(im)
        shape = [(pad, pad), (pad + pw, pad), (pad + pw, pad + ph - 140), (pad + pw / 2, pad + ph),
                 (pad, pad + ph - 140)]
        d.polygon([(x + 10, y + 10) for x, y in shape], fill=theme.INK)
        denim = Image.new("RGB", (W, H), theme.DENIM)
        dd = ImageDraw.Draw(denim)
        for k in range(-H, W + H, 9):
            dd.line([(k, 0), (k - H, H)], fill="#34527d", width=1)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(shape, fill=255)
        im.paste(denim, (0, 0), mask)
        d.line(shape + [shape[0]], fill=theme.DENIM_D, width=4, joint="curve")
        return ImageTk.PhotoImage(im)

    # ------------------------------------------------------------------ #
    def _win(self, method, x, y, widget, **kw):
        wid = self.add_window(x, y, widget, **kw)
        self.method_windows[method].append(wid)
        return wid

    def _entry(self, **kw):
        e = tk.Entry(self.cv, font=F("mono", 15, "bold"), bg=theme.BONE, fg=theme.INK, insertbackground=theme.ACCENT,
                     relief="flat", highlightthickness=2, highlightbackground=theme.DENIM_D,
                     highlightcolor=theme.LIME, **kw)
        return e

    def build_card(self, y):
        cv = self.cv
        px, pw = self.px, self.pw
        tw, th = 420, 236
        x1 = px + (pw - tw) / 2
        y1 = y + 4
        x2, y2 = x1 + tw, y1 + th
        cx, cyy = (x1 + x2) / 2, (y1 + y2) / 2
        self.tag_c = (cx, cyy)
        T = "m_card"
        self.flip_items = {"common": [], "front": [], "back": []}

        def add(group, item, text=False):
            self.flip_items[group].append((item, cv.coords(item), text))
            return item
        body = [x1 + 40, y1, x2 - 16, y1, x2, y1 + 16, x2, y2 - 16, x2 - 16, y2, x1 + 40, y2, x1, y2 - 40, x1, y1 + 40]
        add("common", cv.create_polygon([v + 6 for v in body], fill="#1a2a44", outline="", tags=(T,)))
        add("common", cv.create_polygon(body, fill=KRAFT, outline="#B9A47E", width=2, tags=(T,)))
        add("common", cv.create_oval(x1 + 18, cyy - 10, x1 + 38, cyy + 10, fill=theme.DENIM, outline="#B9A47E", width=2,
                                     tags=(T,)))
        # string to the rivet
        self.string = cv.create_line(x1 + 28, cyy, x1 - 30, cyy - 70, px + 14, self.py + 16, smooth=True,
                                     fill=theme.BONE, width=2, tags=(T,))
        # FRONT
        add("front", cv.create_text(x1 + 60, y1 + 26, text="AK1 PAY", font=F("heavy", 18), fill=theme.INK, anchor="nw",
                                    tags=(T,)), True)
        add("front", cv.create_rectangle(x1 + 60, y1 + 66, x1 + 108, y1 + 100, fill=theme.GOLD, outline="#8a6d34",
                                         tags=(T,)))
        for k in range(3):
            add("front", cv.create_line(x1 + 60, y1 + 75 + k * 9, x1 + 108, y1 + 75 + k * 9, fill="#8a6d34", tags=(T,)))
        add("front", cv.create_text(x2 - 62, y1 + 30, text="♥ RE-WORN", font=F("mono", 10, "bold"), fill=theme.ACCENT,
                                    anchor="n", tags=(T,)), True)
        # barcode
        rnd = random.Random(7)
        bx = x2 - 108
        while bx < x2 - 22:
            w = rnd.choice((1, 2, 3))
            add("front", cv.create_rectangle(bx, y1 + 66, bx + w, y1 + 104, fill=theme.INK, outline="", tags=(T,)))
            bx += w + rnd.choice((2, 3))
        self.t_num = add("front", cv.create_text(x1 + 60, y1 + 140, text="••••  ••••  ••••  ••••",
                                                 font=F("mono", 21, "bold"), fill=theme.INK, anchor="w", tags=(T,)), True)
        add("front", cv.create_text(x1 + 60, y1 + 176, text="CARD HOLDER", font=F("mono", 9), fill="#7d6b4b", anchor="nw",
                                    tags=(T,)), True)
        self.t_name = add("front", cv.create_text(x1 + 60, y1 + 192, text="YOUR NAME", font=F("mono", 14, "bold"),
                                                  fill=theme.INK, anchor="nw", tags=(T,)), True)
        add("front", cv.create_text(x2 - 30, y1 + 176, text="EXPIRES", font=F("mono", 9), fill="#7d6b4b", anchor="ne",
                                    tags=(T,)), True)
        self.t_exp = add("front", cv.create_text(x2 - 30, y1 + 192, text="MM/YY", font=F("mono", 14, "bold"),
                                                 fill=theme.INK, anchor="ne", tags=(T,)), True)
        # BACK
        add("back", cv.create_rectangle(x1 + 40, y1 + 30, x2, y1 + 76, fill=theme.INK, outline="", tags=(T,)))
        add("back", cv.create_rectangle(x1 + 60, y1 + 100, x2 - 120, y1 + 140, fill=theme.WHITE, outline="#B9A47E",
                                        tags=(T,)))
        for k in range(8):
            add("back", cv.create_line(x1 + 64 + k * 26, y1 + 138, x1 + 84 + k * 26, y1 + 102, fill="#E3D6BE", tags=(T,)))
        add("back", cv.create_rectangle(x2 - 108, y1 + 100, x2 - 30, y1 + 140, fill=theme.WHITE, outline=theme.ACCENT,
                                        width=2, tags=(T,)))
        self.t_cvv = add("back", cv.create_text(x2 - 69, y1 + 120, text="CVV", font=F("mono", 15, "bold"),
                                                fill=theme.INK, tags=(T,)), True)
        add("back", cv.create_text(x1 + 60, y1 + 166, text="THANK YOU FOR THRIFTING.\nTHIS TAG IS 100% RECYCLED. LIKE YOUR STYLE.",
                                   font=F("mono", 9), fill="#7d6b4b", anchor="nw", tags=(T,)), True)
        for it, _, _ in self.flip_items["back"]:
            cv.itemconfigure(it, state="hidden")
        self.face = "front"
        self.flip_tw = None
        # entries
        ey = y2 + 30
        lx = px + 40
        fw = pw - 80
        lab = lambda xx, yy, s: cv.create_text(xx, yy, text=s, font=F("mono", 10, "bold"), fill="#C9D4E6", anchor="nw",
                                               tags=(T,))
        lab(lx, ey, "CARD NUMBER")
        self.v_num = tk.StringVar()
        self.e_num = self._entry(textvariable=self.v_num)
        self._win("card", lx, ey + 18, self.e_num, anchor="nw", width=fw, height=46)
        ey += 82
        w1 = int(fw * 0.5)
        w2 = int((fw - w1 - 20) / 2)
        lab(lx, ey, "NAME ON CARD")
        lab(lx + w1 + 10, ey, "EXPIRY")
        lab(lx + w1 + w2 + 20, ey, "CVV")
        self.v_name, self.v_exp, self.v_cvv = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.e_name = self._entry(textvariable=self.v_name)
        self.e_exp = self._entry(textvariable=self.v_exp)
        self.e_cvv = self._entry(textvariable=self.v_cvv, show="•")
        self._win("card", lx, ey + 18, self.e_name, anchor="nw", width=w1, height=46)
        self._win("card", lx + w1 + 10, ey + 18, self.e_exp, anchor="nw", width=w2, height=46)
        self._win("card", lx + w1 + w2 + 20, ey + 18, self.e_cvv, anchor="nw", width=w2, height=46)
        self.card_err = cv.create_text(px + pw / 2, ey + 82, text="", font=F("mono", 11, "bold"), fill=theme.LIME,
                                       tags=(T,))
        self._guard = False
        self.v_num.trace_add("write", lambda *a: self._fmt_num())
        self.v_exp.trace_add("write", lambda *a: self._fmt_exp())
        self.v_cvv.trace_add("write", lambda *a: self._fmt_cvv())
        self.v_name.trace_add("write", lambda *a: cv.itemconfigure(self.t_name, text=(self.v_name.get().upper()[:22] or "YOUR NAME")))
        self.e_cvv.bind("<FocusIn>", lambda e: self.flip("back"))
        self.e_cvv.bind("<FocusOut>", lambda e: self.flip("front"))
        for e in (self.e_num, self.e_name, self.e_exp):
            e.bind("<FocusIn>", lambda ev: self.flip("front"), add="+")

    def _set(self, var, val):
        self._guard = True
        var.set(val)
        self._guard = False

    def _fmt_num(self):
        if self._guard:
            return
        d = "".join(c for c in self.v_num.get() if c.isdigit())[:16]
        s = " ".join(d[i:i + 4] for i in range(0, len(d), 4))
        self._set(self.v_num, s)
        self.e_num.icursor("end")
        shown = (d + "•" * (16 - len(d)))
        self.cv.itemconfigure(self.t_num, text="  ".join(shown[i:i + 4] for i in range(0, 16, 4)))

    def _fmt_exp(self):
        if self._guard:
            return
        d = "".join(c for c in self.v_exp.get() if c.isdigit())[:4]
        s = d if len(d) <= 2 else d[:2] + "/" + d[2:]
        self._set(self.v_exp, s)
        self.e_exp.icursor("end")
        self.cv.itemconfigure(self.t_exp, text=s or "MM/YY")

    def _fmt_cvv(self):
        if self._guard:
            return
        d = "".join(c for c in self.v_cvv.get() if c.isdigit())[:3]
        self._set(self.v_cvv, d)
        self.cv.itemconfigure(self.t_cvv, text=("•" * len(d)) or "CVV")

    def flip(self, face):
        """Revolve the swing tag around its vertical axis (scale-x through 0, swap faces)."""
        if face == self.face or self.method != "card":
            return
        if self.flip_tw:
            self.flip_tw.cancel()
        cv = self.cv
        cx = self.tag_c[0]
        old = self.face
        self.face = face
        st = {"swapped": False}

        def apply(k, grp_show):
            for g in ("common", grp_show):
                for it, base, is_text in self.flip_items[g]:
                    if is_text:
                        cv.itemconfigure(it, state="normal" if k > 0.92 else "hidden")
                        cv.coords(it, cx + (base[0] - cx) * k, base[1])
                    else:
                        cv.coords(it, *[cx + (v - cx) * k if i % 2 == 0 else v for i, v in enumerate(base)])

        def upd(e):
            k = abs(math.cos(e * math.pi))
            k = max(0.02, k)
            if e >= 0.5 and not st["swapped"]:
                st["swapped"] = True
                for it, _, _ in self.flip_items[old]:
                    cv.itemconfigure(it, state="hidden")
                for it, _, is_text in self.flip_items[face]:
                    if not is_text:
                        cv.itemconfigure(it, state="normal")
            apply(k, face if st["swapped"] else old)
        self.flip_tw = self.E.animate(700, upd, easing="inOutCubic", owner=self)

    # ------------------------------------------------------------------ #
    def build_upi(self, y):
        cv = self.cv
        px, pw = self.px, self.pw
        T = "m_upi"
        qs = 220
        qx, qy = px + 40, y + 4
        cv.create_rectangle(qx - 12, qy - 12, qx + qs + 12, qy + qs + 12, fill=theme.WHITE, outline=theme.INK, width=2,
                            tags=(T,))
        n = 29
        m = qs / n
        rnd = random.Random(2026)

        def finder(fx, fy):
            cv.create_rectangle(qx + fx * m, qy + fy * m, qx + (fx + 7) * m, qy + (fy + 7) * m, fill=theme.INK,
                                outline="", tags=(T,))
            cv.create_rectangle(qx + (fx + 1) * m, qy + (fy + 1) * m, qx + (fx + 6) * m, qy + (fy + 6) * m,
                                fill=theme.WHITE, outline="", tags=(T,))
            cv.create_rectangle(qx + (fx + 2) * m, qy + (fy + 2) * m, qx + (fx + 5) * m, qy + (fy + 5) * m,
                                fill=theme.INK, outline="", tags=(T,))
        for i in range(n):
            for j in range(n):
                if (i < 8 and j < 8) or (i >= n - 8 and j < 8) or (i < 8 and j >= n - 8):
                    continue
                if rnd.random() < 0.47:
                    cv.create_rectangle(qx + i * m, qy + j * m, qx + (i + 1) * m, qy + (j + 1) * m, fill=theme.INK,
                                        outline="", tags=(T,))
        finder(0, 0)
        finder(n - 7, 0)
        finder(0, n - 7)
        # fox-orange centre logo
        c = qx + qs / 2
        cv.create_rectangle(c - 22, qy + qs / 2 - 22, c + 22, qy + qs / 2 + 22, fill=theme.WHITE, outline="", tags=(T,))
        cv.create_text(c, qy + qs / 2, text="AK1", font=F("display", 18), fill=theme.ACCENT, tags=(T,))
        self.scan = cv.create_line(qx - 8, qy, qx + qs + 8, qy, fill=theme.ACCENT, width=3, tags=(T,))
        self.scan_geo = (qx, qy, qs)
        self.scan_tw = None
        rx = qx + qs + 40
        rw = px + pw - 40 - rx
        lines(cv, rx, qy, ["SCAN WITH", "ANY UPI APP"], F("display", 30), theme.BONE, tags=(T,))
        cv.create_text(rx, qy + 96, text="OR ENTER YOUR UPI ID", font=F("mono", 10, "bold"), fill="#C9D4E6", anchor="nw",
                       tags=(T,))
        self.v_upi = tk.StringVar()
        e = self._entry(textvariable=self.v_upi)
        self._win("upi", rx, qy + 116, e, anchor="nw", width=rw, height=46)
        self.upi_msg = cv.create_text(rx, qy + 176, text="", font=F("mono", 11, "bold"), fill=theme.LIME, anchor="nw",
                                      width=rw, tags=(T,))
        cv.create_text(px + 40, qy + qs + 34, text="PAYEE: ak1thrift@upi  ·  AK1 THRIFT STORE", font=F("mono", 11, "bold"),
                       fill=theme.BONE, anchor="nw", tags=(T,))
        cv.create_text(px + 40, qy + qs + 60, text="QR is decorative — this is a demo. Type any id like name@bank.",
                       font=F("body", 13), fill="#C9D4E6", anchor="nw", tags=(T,))

    def _scan_start(self):
        if self.scan_tw:
            self.scan_tw.cancel()
        qx, qy, qs = self.scan_geo
        cv = self.cv
        self.scan_tw = self.E.animate(1500, lambda e: cv.coords(self.scan, qx - 8, qy + qs * e, qx + qs + 8, qy + qs * e),
                                      easing="inOutSine", loop=True, direction="alternate", owner=self)

    def build_cash(self, y):
        cv = self.cv
        px, pw = self.px, self.pw
        T = "m_cash"
        cx = px + pw / 2
        hy = y + 20
        # hanger
        cv.create_line(cx, hy + 40, cx, hy + 22, cx + 10, hy + 8, cx + 22, hy + 14, cx + 18, hy + 30, smooth=True,
                       fill=theme.BONE, width=5, tags=(T,))
        cv.create_line(cx - 150, hy + 120, cx, hy + 40, cx + 150, hy + 120, cx - 150, hy + 120, fill=theme.BONE,
                       width=5, joinstyle="round", tags=(T,))
        # price tag swinging from the hanger bar
        tx, ty = cx + 60, hy + 120
        cv.create_line(tx, ty, tx + 20, ty + 40, fill=theme.BONE, width=2, tags=(T, "cashtag"))
        cv.create_polygon(tx + 4, ty + 40, tx + 120, ty + 40, tx + 120, ty + 104, tx + 4, ty + 104, tx - 10, ty + 72,
                          fill=KRAFT, outline="#B9A47E", width=2, tags=(T, "cashtag"))
        cv.create_text(tx + 62, ty + 62, text="+₹49", font=F("display", 24), fill=theme.INK, tags=(T, "cashtag"))
        cv.create_text(tx + 62, ty + 88, text="HANDLING", font=F("mono", 9, "bold"), fill="#7d6b4b", tags=(T, "cashtag"))
        lines(cv, px + 40, hy + 150, ["PAY WHEN", "IT LANDS."], F("display", 44), theme.BONE, tags=(T,))
        cv.create_text(px + 40, hy + 290, text="EXACT CHANGE MAKES FITZ VERY HAPPY.\nTRUST ISSUES? TOTALLY VALID. WE GET IT.",
                       font=F("mono", 11, "bold"), fill="#C9D4E6", anchor="nw", tags=(T,))

    def _show_method(self, m, anim=True):
        cv, E = self.cv, self.E
        old = self.method
        self.method = m
        for k in ("card", "upi", "cash"):
            on = k == m
            if not anim or k in (m, old):
                cv.itemconfigure("m_" + k, state="normal" if on else "hidden")
            for wid in self.method_windows[k]:
                self.set_window(wid, on)
        if m == "card":
            for it, _, _ in self.flip_items["back" if self.face == "front" else "front"]:
                cv.itemconfigure(it, state="hidden")
        if m == "upi":
            self._scan_start()
        if anim:
            cv.move("m_" + m, 50, 0)
            move(E, cv, "m_" + m, -50, 0, duration=700, easing="outExpo", owner=self)
            if m == "cash":
                # swing the price tag like a pendulum
                cv.move("cashtag", 0, 0)
        x0, w = self.tabs[m][0], self.tabs[m][1]
        a = cv.coords(self.tab_ind)
        b = [x0, self.tab_y, x0 + w, self.tab_y + 44]
        if anim:
            E.animate(600, lambda e: cv.coords(self.tab_ind, *[u + (v - u) * e for u, v in zip(a, b)]),
                      easing="outElasticSoft", owner=self)
        else:
            cv.coords(self.tab_ind, *b)
        for k, (tx, tw, r, t) in self.tabs.items():
            cv.itemconfigure(t, fill=theme.INK)

    def set_method(self, m):
        if m == self.method:
            return
        if self.face == "back":
            self.face = "back"
        self._show_method(m)
        self.recalc()
        if m == "cash":
            self.fox_say("checkout")

    # ================================================================== #
    #  PAY
    # ================================================================== #
    def _err(self, msg):
        cv = self.cv
        if self.method == "card":
            cv.itemconfigure(self.card_err, text=msg)
            move(self.E, cv, self.card_err, 10, 0, duration=60, loop=6, direction="alternate", owner=self)
        elif self.method == "upi":
            cv.itemconfigure(self.upi_msg, text=msg)
        move(self.E, cv, self.pay_btn.tag, 12, 0, duration=60, loop=6, direction="alternate", owner=self)
        if self.fox:
            self.fox.hop()
            self.fox.say(random.choice(FOX["error"]))

    def pay(self):
        T = self.totals()
        if not T["n"]:
            move(self.E, self.cv, self.pay_btn.tag, 12, 0, duration=60, loop=6, direction="alternate", owner=self)
            self.fox_say("empty")
            return
        if self.method == "card":
            num = self.v_num.get().replace(" ", "")
            exp = self.v_exp.get()
            if len(num) != 16:
                return self._err("CARD NUMBER NEEDS 16 DIGITS")
            if len(self.v_name.get().strip()) < 2:
                return self._err("WHOSE CARD IS IT? (NAME)")
            if len(exp) != 5 or not (1 <= int(exp[:2] or 0) <= 12):
                return self._err("EXPIRY SHOULD LOOK LIKE 08/29")
            if len(self.v_cvv.get()) != 3:
                return self._err("CVV IS THE 3 DIGITS ON THE BACK")
            self.cv.itemconfigure(self.card_err, text="")
        elif self.method == "upi":
            v = self.v_upi.get().strip()
            if "@" not in v or len(v) < 4:
                return self._err("UPI ID LOOKS LIKE name@bank")
        self.processing()

    def processing(self):
        cv, E = self.cv, self.E
        self.modal = "busy"
        self.show_windows(False)
        top = self.applied
        W, H = self.W, self.H
        t = ("busy", "hud", "modal")
        cv.create_rectangle(0, top, W, top + H, fill=theme.INK, outline="", stipple="gray50", tags=t)
        cx, cy = W / 2, top + H / 2
        cv.create_oval(cx - 70, cy - 110, cx + 70, cy + 30, fill=theme.INK, outline=theme.INK3, width=10, tags=t)
        arc = cv.create_arc(cx - 70, cy - 110, cx + 70, cy + 30, start=90, extent=100, style="arc",
                            outline=theme.LIME, width=10, tags=t)
        msg = cv.create_text(cx, cy + 80, text="STITCHING YOUR ORDER...", font=F("display", 34), fill=theme.BONE, tags=t)
        msgs = ["STITCHING YOUR ORDER...", "CHECKING THE SEAMS...", "FOLDING WITH LOVE...", "ALMOST THERE..."]
        E.animate(900, lambda e: cv.itemconfigure(arc, start=90 - 360 * e, extent=60 + 120 * math.sin(e * math.pi)),
                  loop=True, easing="inOutSine", owner=self)
        for i, m in enumerate(msgs[1:]):
            E.after(700 * (i + 1), lambda m=m: cv.itemconfigure(msg, text=m), owner=self)
        E.after(2800, self.success, owner=self)

    def success(self):
        cv, E = self.cv, self.E
        cv.delete("busy")
        T = self.totals()
        self.app.cart.clear()
        self.app.nav.set_count(0)
        top = self.applied
        W, H = self.W, self.H
        t = ("done", "hud", "modal")
        cv.create_rectangle(0, top, W, top + H, fill=theme.INK, outline="", tags=t)
        oid = "AK1-" + "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        l1 = Letters(self, W / 2, top + H / 2 - 40, "ORDER", F("display", 140), theme.BONE, theme.INK, tags=t,
                     align="center")
        l2 = Letters(self, W / 2, top + H / 2 + 110, "CONFIRMED.", F("display", 140), theme.LIME, theme.INK, tags=t,
                     align="center")
        l1.play(mode="revolve", step=60)
        l2.play(delay=300, mode="revolve", step=60)
        info = cv.create_text(W / 2, top + H / 2 + 150, text=f"ORDER {oid}  ·  {rupee(T['total'])} PAID  ·  "
                                                              f"~{T['water']:,} L OF WATER SAVED",
                              font=F("mono", 14, "bold"), fill=theme.INK, tags=t)
        E.animate(800, lambda e: cv.itemconfigure(info, fill=mix(theme.INK, theme.BONE, e)), delay=900, owner=self)
        b = Button(self, W / 2, top + H / 2 + 190, "KEEP THRIFTING", lambda: self.app.go("home"), kind="accent",
                   anchor="n", tags=t, z=120, shadow=theme.BONE, h=56)
        b.x -= b.w / 2
        cv.move(b.tag, -b.w / 2, 0)
        b.zone.z = 150
        self.confetti(top)
        # Fitz gets the last word, pinned above the overlay
        if self.fox:
            self.fox.hop()
            self.fox.say(random.choice(FOX["paid"]))
            cv.tag_raise(self.fox.tag)
        self.modal = "done"
        self.zone((0, 0, W, H), hud=True, z=110, cursor="")

    def confetti(self, top):
        cv, E, W = self.cv, self.E, self.W
        tee = [(-6, -5), (-2, -7), (2, -7), (6, -5), (9, -1), (5, 1), (5, 8), (-5, 8), (-5, 1), (-9, -1)]
        rect = [(-4, -7), (4, -7), (4, 7), (-4, 7)]
        cols = [theme.ACCENT, theme.LIME, theme.GOLD, theme.BONE, theme.DENIM_L, theme.STITCH]
        parts = []
        for i in range(90):
            shape = tee if i % 3 == 0 else rect
            s = random.uniform(1.2, 2.4) if shape is tee else random.uniform(0.8, 1.4)
            it = cv.create_polygon(0, 0, 0, 0, 0, 0, fill=random.choice(cols), outline="", tags=("done", "hud", "modal"))
            parts.append(dict(it=it, pts=shape, s=s, x=W / 2 + random.uniform(-80, 80), y=top + self.H * 0.42,
                              vx=random.uniform(-650, 650), vy=random.uniform(-1050, -350),
                              a=random.uniform(0, 6.28), va=random.uniform(-9, 9)))
        clock = {"t": 0}

        def step(dt, now):
            clock["t"] += dt
            for p in parts:
                p["vy"] += 1500 * dt
                p["vx"] *= (1 - 0.9 * dt)
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["a"] += p["va"] * dt
                ca, sa = math.cos(p["a"]), math.sin(p["a"])
                flat = abs(math.cos(p["a"] * 0.7))       # 3D tumble
                co = []
                for x, y in p["pts"]:
                    x *= p["s"] * flat
                    y *= p["s"]
                    co += [p["x"] + x * ca - y * sa, p["y"] + x * sa + y * ca]
                cv.coords(p["it"], *co)
            if clock["t"] > 4.5:
                for p in parts:
                    cv.delete(p["it"])
                return False
            return True
        E.frame(step, owner=self)
