"""Shared page pieces: footer, round arrow buttons, category switcher chips."""
import tkinter as tk

from .. import theme
from ..anim import mix, move
import math

from ..data import BEST_FILTERS, CATS, QUOTES, best_sellers
from ..theme import F
from ..widgets import Button, Letters, ProductCard, section_header

M = 56


def arrows(page, x, y, on_prev, on_next, dark=False, bg=None):
    """Two square arrow buttons, right edge at x."""
    kind = "outline-light" if dark else "outline"
    bg = bg or (theme.INK if dark else page.bg)
    b2 = Button(page, x, y, "→", on_next, kind=kind, arrow=False, w=54, h=54, font=F("heavy", 20),
                anchor="ne", page_bg=bg)
    b1 = Button(page, x - 64, y, "←", on_prev, kind=kind, arrow=False, w=54, h=54, font=F("heavy", 20),
                anchor="ne", page_bg=bg)
    return b1, b2


def category_chips(page, y, current, dark=True):
    """Big switcher row: lets you jump straight to any department."""
    cv = page.cv
    keys = ["tee", "jeans", "trousers", "jewel", "acc"]
    x = M
    f = F("display", 28)
    out = []
    for k in keys:
        c = CATS[k]
        label = c["title"]
        tw = theme.measure(f, label)
        w = tw + 46
        on = k == current
        fill = theme.LIME if on else (theme.INK if dark else page.bg)
        fg = theme.INK if on else (theme.BONE if dark else theme.INK)
        r = cv.create_rectangle(x, y, x + w, y + 60, fill=fill, outline=theme.BONE if dark else theme.INK, width=2)
        t = cv.create_text(x + w / 2, y + 31, text=label, font=f, fill=fg)
        if not on:
            def enter(r=r, t=t):
                cv.itemconfigure(r, fill=theme.ACCENT)
                cv.itemconfigure(t, fill=theme.INK)
                move(page.E, cv, t, 0, -3, duration=160, direction="alternate", loop=2, owner=page)

            def leave(r=r, t=t, fill=fill, fg=fg):
                cv.itemconfigure(r, fill=fill)
                cv.itemconfigure(t, fill=fg)
            page.zone((x, y, x + w, y + 60), click=lambda p=c["page"]: page.app.go(p), enter=enter, leave=leave)
        out.append((r, t))
        x += w + 14
    return 60


def footer(page, y):
    """Big black footer: newsletter, giant wordmark, links, a quote."""
    cv, E, W = page.cv, page.E, page.W
    H0 = 770
    cv.create_rectangle(0, y, W, y + H0, fill=theme.INK, outline="")
    # newsletter
    cv.create_text(M, y + 70, text="JOIN THE DROP LIST", font=F("display", 54), fill=theme.BONE, anchor="nw")
    cv.create_text(M, y + 150, text="FRIDAY DROPS, FIRST DIBS, ZERO SPAM. FITZ PROMISES.", font=F("mono", 12),
                   fill="#9A958B", anchor="nw")
    ent = tk.Entry(page.cv, font=F("body", 17), bg=theme.INK3, fg=theme.BONE, insertbackground=theme.ACCENT,
                   relief="flat", highlightthickness=2, highlightbackground=theme.INK3, highlightcolor=theme.LIME)
    ent.insert(0, "your@email.com")
    ent.bind("<FocusIn>", lambda e: ent.get() == "your@email.com" and ent.delete(0, "end"))
    page.add_window(W - M - 560, y + 76, ent, anchor="nw", width=380, height=54)
    msg = cv.create_text(W - M, y + 150, text="", font=F("mono", 12, "bold"), fill=theme.LIME, anchor="ne")

    def join():
        v = ent.get().strip()
        if "@" not in v or "." not in v.split("@")[-1]:
            cv.itemconfigure(msg, text="THAT EMAIL LOOKS PRE-LOVED. TRY AGAIN.", fill=theme.ACCENT)
            return
        cv.itemconfigure(msg, text="YOU'RE IN. SEE YOU FRIDAY ★", fill=theme.LIME)
        ent.delete(0, "end")
        page.fox_say("added")
    Button(page, W - M, y + 76, "SUBSCRIBE", join, kind="lime", anchor="ne", h=54)
    cv.create_line(M, y + 200, W - M, y + 200, fill=theme.INK3, width=2)
    # link columns
    cols = [("SHOP", [(CATS[k]["title"], CATS[k]["page"]) for k in ("tee", "jeans", "trousers", "jewel", "acc")]
             + [("YOUR BAG", "checkout")]),
            ("HELP", [("SHIPPING", None), ("RETURNS", None), ("SIZE GUIDE", None), ("CARE TIPS", None)]),
            ("AK1", [("OUR STORY", None), ("SUSTAINABILITY", None), ("SELL WITH US", None)])]
    cx = M
    for head, links in cols:
        cv.create_text(cx, y + 236, text=head, font=F("mono", 12, "bold"), fill=theme.ACCENT, anchor="nw")
        for i, (lab, target) in enumerate(links):
            ly = y + 268 + i * 30
            t = cv.create_text(cx, ly, text=lab, font=F("heavy", 15), fill=theme.BONE, anchor="nw")
            if target:
                tw = theme.measure(F("heavy", 15), lab)

                def enter(t=t):
                    cv.itemconfigure(t, fill=theme.LIME)
                    move(E, cv, t, 8, 0, duration=250, easing="outBack", owner=page)

                def leave(t=t):
                    cv.itemconfigure(t, fill=theme.BONE)
                    move(E, cv, t, -8, 0, duration=250, easing="outQuad", owner=page)
                page.zone((cx, ly, cx + tw + 10, ly + 24), click=lambda tg=target: page.app.go(tg),
                          enter=enter, leave=leave)
        cx += 230
    q, a = QUOTES[0]
    cv.create_text(W - M, y + 236, text="“" + q + "”", font=F("serif", 26, "italic"), fill=theme.BONE,
                   anchor="ne", width=440, justify="right")
    cv.create_text(W - M, y + 284, text="— " + a, font=F("mono", 11, "bold"), fill="#9A958B", anchor="ne")
    # giant wordmark
    wf = F("display", 210)
    base = y + H0 + 34
    l1 = Letters(page, M - 6, base, "AK1", wf, theme.ACCENT, theme.INK)
    l2 = Letters(page, M - 6 + l1.w + 28, base, "THRIFT", wf, theme.BONE, theme.INK)
    cv.create_text(W - M, y + H0 - 24, text="© 2026 AK1-THRIFT  ·  ACADEMIC PROJECT  ·  PHOTOS: UNSPLASH",
                   font=F("mono", 10), fill="#77736B", anchor="se")

    def play():
        d = l1.play(mode="revolve", step=70, dur=1100)
        l2.play(delay=200, mode="revolve", step=70, dur=1100)
        _ = d
    page.reveal_at(y + 300, play, offset=40)
    return H0


def best_row(page, y0, cat, pal, accent, bg, fg, header=None, label="BEST SELLERS FOR", mono="mono"):
    """Ranked best-seller row with a filter toggle. Switching filters revolves every card
    (flip out -> swap product -> flip in). Slots with nothing to show flip out to empty."""
    cv, E, W = page.cv, page.E, page.W
    opts = BEST_FILTERS[cat]
    cw = (W - 2 * M - 3 * 24) // 4
    ih = int(cw * 1.2)
    y = y0
    if header:
        num, title, sub = header
        y += 90
        h, _ = section_header(page, y, num, title, sub, bg, fg, accent=accent, mono=mono)
        y += h + 26
    pf = F("heavy", 13)
    px = M
    if label:
        cv.create_text(M, y + 23, text=label, font=F(mono, 13, "bold"), fill=accent, anchor="w")
        px = M + theme.measure(F(mono, 13, "bold"), label) + 24
    dark = bg != theme.PAPER
    on_txt = theme.INK if dark else theme.LIME
    ind_col = accent if dark else theme.INK
    pills = []
    ind = cv.create_rectangle(0, 0, 0, 0, fill=ind_col, outline="")
    for lab, pred in opts:
        w = theme.measure(pf, lab) + 36
        cv.create_rectangle(px, y, px + w, y + 46, outline=accent if dark else theme.INK, width=2)
        t = cv.create_text(px + w / 2, y + 23, text=lab, font=pf, fill=fg)
        pills.append((px, w, t, pred))
        px += w + 8
    cv.tag_raise(ind)
    for p in pills:
        cv.tag_raise(p[2])
    cv.coords(ind, pills[0][0], y, pills[0][0] + pills[0][1], y + 46)
    cv.itemconfigure(pills[0][2], fill=on_txt)
    cy = y + 46 + 44
    for i in range(4):
        cv.create_text(M + i * (cw + 24) + cw - 4, cy - 38, text=f"0{i + 1}", anchor="ne",
                       font=F("display", 54), fill=mix(bg, fg, 0.12))
    slots = [ProductCard(page, p, M + i * (cw + 24), cy, cw, ih, pal, best=i + 1)
             for i, p in enumerate(best_sellers(cat))]
    state = {"k": 0, "ind": (pills[0][0], pills[0][0] + pills[0][1]), "busy": False}
    page.reveal_at(cy, lambda: [c.reveal(i * 130) for i, c in enumerate(slots)], offset=60)

    def resolve(c):
        while c is not None and getattr(c, "swapped", False):
            c = c.replaced_by
        return c

    def unbusy():
        state["busy"] = False

    def choose(k):
        if k == state["k"] or state["busy"]:
            return
        state["k"] = k
        state["busy"] = True
        E.after(650, unbusy, owner=page)
        x0, w, t, pred = pills[k]
        for p in pills:
            cv.itemconfigure(p[2], fill=fg)
        cv.itemconfigure(t, fill=on_txt)
        a, b = state["ind"], (x0, x0 + w)
        state["ind"] = b
        E.animate(600, lambda e: cv.coords(ind, a[0] + (b[0] - a[0]) * e, y, a[1] + (b[1] - a[1]) * e, y + 46),
                  easing="outElasticSoft", owner=page)
        newps = best_sellers(cat, pred)
        for i in range(4):
            cur = resolve(slots[i])
            newp = newps[i] if i < len(newps) else None
            if cur is None and newp is not None:
                nc = ProductCard(page, newp, M + i * (cw + 24), cy, cw, ih, pal, best=i + 1)
                nc.reveal(300 + i * 90)
                slots[i] = nc
            elif cur is not None:
                if newp is not None and cur.p["id"] == newp["id"]:
                    slots[i] = cur
                    continue
                cur.flip_swap(newp, delay=i * 90)
                slots[i] = cur
        page.raise_hud()

    for k, (x0, w, t, pred) in enumerate(pills):
        page.zone((x0, y, x0 + w, y + 46), click=lambda k=k: choose(k))
    return cy + ih + 118 + 30 - y0
