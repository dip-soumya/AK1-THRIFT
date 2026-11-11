"""
AK1-THRIFT  -  run me:   python main.py

A thrift-store storefront GUI built with tkinter (+ Pillow for image prep),
with anime.js-style motion: staggered/revolving type, a 3D revolving rack,
flip-in cards, scroll-triggered reveals, parallax, curtain page transitions
and Fitz - the fox in a tie.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    img_dir = os.path.join(HERE, "assets", "img")
    if not os.path.isdir(img_dir) or not os.listdir(img_dir):
        print("Assets missing - downloading photos & fonts once (needs internet)...")
        from tools import fetch_assets
        fetch_assets.main()
    from ak1.app import App
    App(HERE).run()


if __name__ == "__main__":
    main()
