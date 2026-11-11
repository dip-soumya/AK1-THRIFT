"""
anim.py  -  a tiny anime.js-style animation engine for Tkinter.

anime.js ideas mirrored here:
  * one shared requestAnimationFrame-like ticker driving every tween
  * animate({duration, delay, easing, loop, direction, begin, update, complete})
  * Penner easings + outElastic / spring / outBack
  * stagger(step, from='first'|'center'|'last')
  * timeline().add(..., offset='-=200').play()
  * helpers to tween canvas positions, colours and numbers
"""
import math
import time
import tkinter as tk
import traceback


# --------------------------------------------------------------------------- #
#  Easings
# --------------------------------------------------------------------------- #
def _bounce_out(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def elastic_out(amplitude=1.0, period=0.45):
    a = max(1.0, amplitude)
    p = period
    s = p / (2 * math.pi) * math.asin(1 / a)

    def f(t):
        if t <= 0 or t >= 1:
            return 1.0 if t >= 1 else 0.0
        return a * 2 ** (-10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
    return f


def back_out(s=1.70158):
    return lambda t: 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def spring(mass=1.0, stiffness=100.0, damping=10.0, settle=1.6):
    """anime.js spring(mass, stiffness, damping) mapped onto t in [0,1]."""
    w0 = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    wd = w0 * math.sqrt(max(1e-6, 1 - zeta * zeta))

    def f(t):
        if t >= 1:
            return 1.0
        T = t * settle
        if zeta < 1:
            return 1 - math.exp(-zeta * w0 * T) * (math.cos(wd * T) + (zeta * w0 / wd) * math.sin(wd * T))
        return 1 - (1 + w0 * T) * math.exp(-w0 * T)
    return f


EASINGS = {
    "linear": lambda t: t,
    "inQuad": lambda t: t * t,
    "outQuad": lambda t: 1 - (1 - t) * (1 - t),
    "inOutQuad": lambda t: 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2,
    "inCubic": lambda t: t ** 3,
    "outCubic": lambda t: 1 - (1 - t) ** 3,
    "inOutCubic": lambda t: 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2,
    "outQuart": lambda t: 1 - (1 - t) ** 4,
    "inOutQuart": lambda t: 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2,
    "outQuint": lambda t: 1 - (1 - t) ** 5,
    "inExpo": lambda t: 0.0 if t == 0 else 2 ** (10 * t - 10),
    "outExpo": lambda t: 1.0 if t >= 1 else 1 - 2 ** (-10 * t),
    "inOutExpo": lambda t: (0.0 if t <= 0 else 1.0 if t >= 1 else
                            2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2),
    "outSine": lambda t: math.sin(t * math.pi / 2),
    "inOutSine": lambda t: -(math.cos(math.pi * t) - 1) / 2,
    "inBack": lambda t: 2.70158 * t ** 3 - 1.70158 * t ** 2,
    "outBack": back_out(),
    "outBackSoft": back_out(1.1),
    "outBackHard": back_out(2.6),
    "outElastic": elastic_out(1, 0.45),
    "outElasticSoft": elastic_out(1, 0.75),
    "outBounce": _bounce_out,
    "spring": spring(),
    "springSoft": spring(1, 80, 14),
}


def ease(name_or_fn):
    if callable(name_or_fn):
        return name_or_fn
    return EASINGS.get(name_or_fn, EASINGS["outExpo"])


# --------------------------------------------------------------------------- #
#  Colour + number helpers
# --------------------------------------------------------------------------- #
def hex_rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def rgb_hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))


_mix_cache = {}


def mix(c1, c2, t):
    """Linear colour interpolation (t is clamped, so overshooting easings are safe)."""
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    key = (c1, c2, round(t, 3))
    v = _mix_cache.get(key)
    if v is None:
        a, b = hex_rgb(c1), hex_rgb(c2)
        v = rgb_hex(*(a[i] + (b[i] - a[i]) * t for i in range(3)))
        if len(_mix_cache) > 20000:
            _mix_cache.clear()
        _mix_cache[key] = v
    return v


def lerp(a, b, t):
    return a + (b - a) * t


def stagger(step, start=0, from_="first"):
    """anime.stagger() - returns f(index, total) -> delay in ms."""
    def f(i, total):
        if from_ == "center":
            d = abs(i - (total - 1) / 2)
        elif from_ == "last":
            d = total - 1 - i
        else:
            d = i
        return start + d * step
    return f


# --------------------------------------------------------------------------- #
#  Engine
# --------------------------------------------------------------------------- #
class Tween:
    __slots__ = ("eng", "dur", "update", "ease", "start", "complete", "begin", "loop",
                 "direction", "owner", "iter", "began", "dead")

    def __init__(self, eng, duration, update, easing, delay, complete, begin, loop, direction, owner):
        self.eng = eng
        self.dur = max(0.0, duration / 1000.0)
        self.update = update
        self.ease = ease(easing)
        self.start = eng.now() + delay / 1000.0
        self.complete = complete
        self.begin = begin
        self.loop = loop
        self.direction = direction
        self.owner = owner
        self.iter = 0
        self.began = False
        self.dead = False

    def cancel(self):
        self.dead = True

    def _reversed(self):
        if self.direction == "reverse":
            return True
        return self.direction == "alternate" and self.iter % 2 == 1

    def step(self, now):
        if self.dead:
            return False
        if self.owner is not None and not getattr(self.owner, "alive", True):
            return False
        if now < self.start:
            return True
        if not self.began:
            self.began = True
            if self.begin:
                self.begin()
        t = 1.0 if self.dur == 0 else (now - self.start) / self.dur
        if t >= 1.0:
            final = 0.0 if self._reversed() else 1.0
            if self.update:
                self.update(self.ease(final) if final else self.ease(0.0))
            self.iter += 1
            if self.loop is True or (isinstance(self.loop, int) and self.iter < self.loop):
                self.start += self.dur
                if now - self.start > self.dur:      # fell far behind: resync
                    self.start = now
                return True
            if self.complete:
                self.complete()
            return False
        p = 1.0 - t if self._reversed() else t
        if self.update:
            self.update(self.ease(p))
        return True


class FrameLoop:
    """Persistent per-frame callback: fn(dt, now) -> False to stop."""
    __slots__ = ("fn", "owner", "dead", "last")

    def __init__(self, fn, owner, now):
        self.fn, self.owner, self.dead, self.last = fn, owner, False, now

    def cancel(self):
        self.dead = True

    def step(self, now):
        if self.dead or (self.owner is not None and not getattr(self.owner, "alive", True)):
            return False
        dt = min(0.05, now - self.last)
        self.last = now
        return self.fn(dt, now) is not False


class Engine:
    """Shared ticker. Everything that moves in the app goes through here."""

    def __init__(self, root, fps=60):
        self.root = root
        self.period = 1.0 / fps
        self.next_due = 0.0
        self.tweens = []
        self.loops = []
        self._job = None
        self._ticking = False
        self.frame_time = 0.0

    @staticmethod
    def now():
        return time.perf_counter()

    # -- public API -------------------------------------------------------- #
    def animate(self, duration=800, update=None, easing="outExpo", delay=0, complete=None,
                begin=None, loop=1, direction="normal", owner=None):
        tw = Tween(self, duration, update, easing, delay, complete, begin, loop, direction, owner)
        self.tweens.append(tw)
        self._wake()
        return tw

    def tween(self, a, b, setter, **kw):
        """Tween a number from a to b, calling setter(value)."""
        return self.animate(update=lambda e: setter(a + (b - a) * e), **kw)

    def frame(self, fn, owner=None):
        lp = FrameLoop(fn, owner, self.now())
        self.loops.append(lp)
        self._wake()
        return lp

    def after(self, ms, fn, owner=None):
        """Owner-aware delayed call (runs through the engine so dead pages are skipped)."""
        return self.animate(duration=0, delay=ms, complete=fn, owner=owner)

    def timeline(self, **defaults):
        return Timeline(self, **defaults)

    # -- ticker ------------------------------------------------------------ #
    def _wake(self):
        if self._job is None and not self._ticking:
            self.next_due = self.now()
            self._job = self.root.after(1, self._tick)

    def _tick(self):
        self._job = None
        self._ticking = True
        try:
            self._run()
        finally:
            self._ticking = False
        if (self.tweens or self.loops) and self._job is None:
            # steady 60 fps cadence: aim for the next frame deadline instead of "now + interval"
            now = self.now()
            self.next_due = max(self.next_due + self.period, now + 0.002)
            if self.next_due - now > self.period:
                self.next_due = now + self.period
            self._job = self.root.after(max(1, int(round((self.next_due - now) * 1000))), self._tick)

    def _run(self):
        now = self.now()
        cur, self.tweens = self.tweens, []
        alive = []
        for tw in cur:
            try:
                if tw.step(now):
                    alive.append(tw)
            except tk.TclError:
                pass
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        self.tweens = alive + self.tweens
        curl, self.loops = self.loops, []
        alivel = []
        for lp in curl:
            try:
                if lp.step(now):
                    alivel.append(lp)
            except tk.TclError:
                pass
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        self.loops = alivel + self.loops
        self.frame_time = self.now() - now


class Timeline:
    """anime.timeline(): sequential tweens with relative offsets ('-=200', '+=100') or absolute ms."""

    def __init__(self, eng, duration=600, easing="outExpo", owner=None):
        self.eng = eng
        self.defaults = dict(duration=duration, easing=easing, owner=owner)
        self.items = []
        self.cursor = 0

    def add(self, update=None, offset=None, **kw):
        opts = dict(self.defaults)
        opts.update(kw)
        if offset is None:
            start = self.cursor
        elif isinstance(offset, str):
            n = float(offset[2:])
            start = self.cursor - n if offset.startswith("-=") else self.cursor + n
        else:
            start = float(offset)
        start = max(0, start)
        opts["delay"] = start + opts.get("delay", 0)
        self.items.append((update, opts))
        self.cursor = max(self.cursor, start + opts["duration"])
        return self

    def call(self, fn, offset=None):
        return self.add(update=None, offset=offset, duration=0, complete=fn)

    def play(self, complete=None):
        tws = [self.eng.animate(update=u, **o) for u, o in self.items]
        if complete:
            self.eng.animate(duration=0, delay=self.cursor, complete=complete,
                             owner=self.defaults.get("owner"))
        return tws


# --------------------------------------------------------------------------- #
#  Canvas helpers (the anime.js "targets" part)
# --------------------------------------------------------------------------- #
def move(eng, cv, tag, dx, dy, **kw):
    """Translate a canvas tag/item by (dx, dy) over time."""
    done = [0.0, 0.0]

    def upd(e):
        nx, ny = dx * e, dy * e
        cv.move(tag, nx - done[0], ny - done[1])
        done[0], done[1] = nx, ny
    return eng.animate(update=upd, **kw)


def color(eng, cv, item, c1, c2, prop="fill", **kw):
    return eng.animate(update=lambda e: cv.itemconfigure(item, **{prop: mix(c1, c2, e)}), **kw)


def coords(eng, cv, item, a, b, **kw):
    """Tween an item's coordinate list from a to b."""
    def upd(e):
        cv.coords(item, *[x + (y - x) * e for x, y in zip(a, b)])
    return eng.animate(update=upd, **kw)


def count(eng, cv, item, a, b, fmt="{:,.0f}", **kw):
    """anime.js number counter -> canvas text."""
    return eng.animate(update=lambda e: cv.itemconfigure(item, text=fmt.format(a + (b - a) * e)), **kw)
