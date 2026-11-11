"""
One-time asset fetcher for AK1-THRIFT.

Downloads the product / model photography (Unsplash, free licence) and the
display fonts (Google Fonts, OFL) into ./assets so the app runs fully offline.
Run:  python tools/fetch_assets.py
"""
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "assets", "img")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

UNSPLASH = "https://images.unsplash.com/photo-{id}?w={w}&q=80&fm=jpg&fit=crop"

PHOTOS = {
    "tee": [
        "1521572163474-6864f9cf17ab", "1622445275992-e7efb32d2257",
        "1627225925683-1da7021732ea", "1678872844677-d650b788709b",
        "1586583903558-bf4ae02b9f29", "1780566759964-e101fe4a3d8c",
        "1775234576197-b916f4115679", "1593726891090-b4c6bc09c819",
        "1780565595413-16c7bc95af74", "1629253463418-d13efa2256de",
        "1618453292459-53424b66bb6a", "1790337214565-7e95d5fb06b3",
        "1589902860314-e910697dea18", "1623113527253-ea2025c15738",
        "1622519407650-3df9883f76a5",
    ],
    "jeans": [
        "1742980511651-b845fa826f33", "1697677791984-5bb30a8a6a25",
        "1628519662791-c13362859149", "1745177111188-d2e5be3eaf0c",
        "1684791323250-81e2edf64906", "1696063972714-f594427ff452",
        "1739358930012-48f9e65cbc1a", "1790610810108-23f5f3068fc2",
        "1784708299503-629069930594", "1788546451800-516b7be9615b",
        "1748594641483-00b6639385a1", "1664817514365-d411ea570c91",
        "1762164130276-021d7c91cd89", "1746591847545-33d872de8411",
        "1774413511100-54f34b2912e5", "1746633521036-59a481e231f6",
        "1725203663920-257760e77aff", "1767899390509-892ad3978dfa",
    ],
    "trousers": [
        "1535530705774-695729778c55", "1687276154823-66f9cba2e484",
        "1716470435412-731a739f9bf8", "1678274342617-09c13eefab9f",
        "1670855822901-5786604e9c40", "1715624133436-d3d449d126ea",
        "1739730976324-2205cb312e37", "1744535814652-9cd3a3dea348",
        "1548883354-7622d03aca27", "1789110854083-e4752bded644",
        "1781510524875-fdea332501be", "1653587106660-4908e9a7bae7",
        "1623596305214-19f21cbf48ee", "1700176353429-5ee7a3105e97",
        "1579920896716-51bfb40ec2a0", "1728088734937-973546275483",
        "1718431672925-5ed7773cce80", "1691407981600-62ebb537a0f2",
        "1768289222386-93b3e854cf31", "1783012687000-26e994270984",
    ],
    "jewel": [
        "1701684431307-b943ffce2e10", "1514739950730-cf1039cbf25d",
        "1652536157585-c87809f64a6b", "1786052336938-d97aeb946fe5",
        "1728313934473-c322f86854b4", "1676485261309-784d67817972",
        "1770722452017-3e4136bf335f", "1558419841-b74c7d4a903e",
        "1735480166478-910de1391b1c", "1789938632462-56704ef437a1",
        "1656010280162-772358d9f4ed", "1786835568749-fb106bc6a263",
        "1714747453609-1cb3acaccf62", "1635190010609-8dcb53c17d3e",
        "1786835568294-d0834d85503c", "1659095141570-be8b9aff59ce",
        "1628785517892-dbcd2f2719ed", "1724937721130-c9a9a4ee477e",
        "1640027659402-c0268b22ddf8", "1786341430358-24fac3b2267d",
        "1566405599386-7f42dde888ce", "1656109801168-699967cf3ba9",
        "1721808085017-38b92dd4f400", "1763130782823-346bba485ec9",
        "1728781627377-5917ab37a47d", "1791041709357-132e8aa60d1f",
    ],
    "acc": [
        "1521369909029-2afed882baee", "1568246621541-5704b4f0bbf2",
        "1678721938524-1a3ee398de2a", "1788546451826-8c8197e11091",
        "1759350075133-d8dab3dcafc3", "1785088561462-9c64357fe174",
        "1772521222853-949a4af568e8", "1787261446883-a82727ca36f3",
        "1789774821474-d10687425ccd", "1752056611077-38328eb8464b",
        "1623808241776-a989707b4c36", "1618677426050-9e4391b7125e",
        "1606196480513-96a7b0d4133a", "1524805444758-089113d48a6d",
        "1791118088116-26727995ada5", "1759406069569-efb854b3410b",
        "1635423760085-e10fceef0756", "1693834084392-fa61a52a81c0",
        "1613405091285-2c3ece70ff2e", "1758445445126-72b4424e1d7b",
        "1727154085760-134cc942246e", "1653773991823-636f90ecd5c5",
        "1642615392063-6b61bf7f1305", "1586772483952-c75dadcf7678",
    ],
    "hero": [
        "1613915617430-8ab0fd7c6baf", "1612731486606-2614b4d74921",
        "1603189343302-e603f7add05a", "1759630814559-f9fffe187384",
        "1619161519929-befcb28d6384", "1637536701306-3214e9cec64a",
        "1587115924362-622c3fa065bd", "1758613654186-6ce234bf94ab",
        "1507553532144-b9df5e38c8d1", "1572251328767-e59f06f13ba1",
        "1670092473608-47d146ea71b4", "1645561305502-63a9ba09ab09",
        "1770012117468-9b1ee7aba977",
    ],
}

GF = "https://github.com/google/fonts/raw/main/ofl/"
FONTS = {
    "Anton-Regular.ttf": GF + "anton/Anton-Regular.ttf",
    "ArchivoBlack-Regular.ttf": GF + "archivoblack/ArchivoBlack-Regular.ttf",
    "DMSerifDisplay-Regular.ttf": GF + "dmserifdisplay/DMSerifDisplay-Regular.ttf",
    "DMSerifDisplay-Italic.ttf": GF + "dmserifdisplay/DMSerifDisplay-Italic.ttf",
    "SpaceMono-Regular.ttf": GF + "spacemono/SpaceMono-Regular.ttf",
    "SpaceMono-Bold.ttf": GF + "spacemono/SpaceMono-Bold.ttf",
    "CourierPrime-Regular.ttf": GF + "courierprime/CourierPrime-Regular.ttf",
    "CourierPrime-Bold.ttf": GF + "courierprime/CourierPrime-Bold.ttf",
}

UA = {"User-Agent": "Mozilla/5.0 (AK1-THRIFT academic project)"}


def _get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return dest, "cached"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest, "ok"
    except Exception as e:  # noqa: BLE001
        return dest, f"FAILED ({e})"


def main():
    jobs = []
    for cat, ids in PHOTOS.items():
        os.makedirs(os.path.join(IMG_DIR, cat), exist_ok=True)
        w = 1400 if cat == "hero" else 800
        for pid in ids:
            jobs.append((UNSPLASH.format(id=pid, w=w), os.path.join(IMG_DIR, cat, pid + ".jpg")))
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, url in FONTS.items():
        jobs.append((url, os.path.join(FONT_DIR, name)))

    with ThreadPoolExecutor(max_workers=8) as ex:
        for dest, status in ex.map(lambda j: _get(*j), jobs):
            print(f"{status:>8}  {os.path.relpath(dest, ROOT)}")
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
