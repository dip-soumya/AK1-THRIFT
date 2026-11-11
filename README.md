# AK1-THRIFT — Animated Thrift-Store Front-End (Python Tkinter)

A desktop storefront for a thrift store selling **tees, jeans, trousers, jewellery and accessories**,
built entirely with Python's **Tkinter** GUI library (Pillow is used only to prepare images).
Every screen is drawn on a scrollable `tkinter.Canvas` and animated with a small **anime.js-style
animation engine** written in pure Python.

> Academic project — 21CSC203P Advanced Programming Practice, SRM Institute of Science and Technology.

## Run

```bash
pip install -r requirements.txt
python main.py          # or double-click run.bat on Windows
```

Requires Python 3.10+ (Tkinter ships with Python).

## Tkinter at the core

| Tkinter feature | Used for |
|---|---|
| `tk.Tk`, `tk.Frame` | main window, page container |
| `tk.Canvas` | every page: shapes, text, images, scrolling (`yview_scroll`, `scrollregion`) |
| Canvas items — `create_text / image / rectangle / oval / polygon / line / arc / window` | cards, buttons, mascot, badges, payment form |
| `move`, `coords`, `itemconfigure`, `tag_raise`, tags | animation & layering |
| `after()` | 60 fps animation loop (the "engine") |
| `bind` / `bind_all` — `<Motion>`, `<Button-1>`, `<MouseWheel>`, `<Shift-MouseWheel>` | hover, click, drag, smooth & sideways touchpad scrolling |
| `tk.Entry`, `tk.OptionMenu`, `StringVar.trace_add` | review form, promo code, live card-number formatting |
| `tkinter.font` | text measuring for layout and word-wrap |
| `ImageTk.PhotoImage` (Pillow) | product photos inside the canvas |

## Codebase

```
main.py              entry point
ak1/
  app.py             App: window, NavBar, page router + curtain transitions, toast, cart
  anim.py            Engine: animate(), timeline(), stagger(), easings (expo, back, elastic, spring)
  page.py            Page: smooth scrolling, scroll-triggered reveals, parallax, hover/click zones
  widgets.py         Button, Letters, ProductCard, Rail, RevolvingRing, Accordion,
                     ReviewCard, ReviewForm, QuickView, Marquee, RotatingBadge
  fox.py             Fitz — the animated fox mascot (drawn with canvas polygons)
  bake.py            pre-renders static text/blocks to images for fast scrolling
  assets.py          Pillow image pipeline (cover-crop, flip frames, depth levels)
  theme.py / data.py colours, fonts / catalogue, reviews, quotes
  pages/             intro, home, category (tees, jeans, trousers, jewellery,
                     accessories), checkout
assets/              product photos (Unsplash) + fonts (Google Fonts)
```

**Key functions:** `Engine.animate()` tweens any value with an easing curve · `Page.reveal_at()`
fires an animation when a section scrolls into view · `Page.scroll_to()` smooth inertial scroll ·
`App.go()` page change with curtain transition · `App.add_to_cart()` cart + toast ·
`ProductCard.reveal()` 3D flip-in · `RevolvingRing.spin_to()` 3D carousel · `Fox.say()` speech bubble.

## Features

- Intro screen with a live loading counter and revolving wordmark
- Long-scroll home page: every section animates in (revolving letters, flips, fades, parallax)
- Five departments, each with a **Top Trenders** 3D revolving rack, a **Best Sellers** filter row
  and a **Shop All** grid with animated sorting (trending, best sellers, price, rating, newest)
- Quick-view product sheet with sizes, discount and delivery info
- Reviews: star ratings summary, write-a-review form, swipeable review rail
- Checkout styled as a denim back pocket: card (flipping swing-tag card), UPI QR, cash on delivery,
  promo code, animated totals and confetti on success *(demo only — nothing is charged)*
- Fitz the fox mascot with context-aware lines; touchpad and mouse support (incl. sideways swipes)

## Team

- Soumyadip Das — RA2511026010632
- Tanmay Rathi — RA2511026010643
- Shaivi Bohidar — RA2511026010615

Product photos: Unsplash (free licence). Fonts: Google Fonts (SIL OFL). All products and prices are fictional.
