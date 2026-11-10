"""Render the profile README cards into cards/*.svg.

Standard library only. Reads data/portrait.txt and the subset fonts in fonts/.

    python scripts/render_readme_cards.py            # animated
    STATIC=1 python scripts/render_readme_cards.py   # final frame, for screenshots
"""
import base64, json, os, pathlib
from html import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"
METRICS = json.loads((ROOT / "fonts" / "metrics.json").read_text())

# ---- palette: paper, ink, three accents ------------------------------------
PAPER, RULE = "#F6F2EA", "#DCD3C5"
INK, INK2, MUTED = "#1B1916", "#3A3631", "#7A7268"
BLUE, RED, YELLOW, OCHRE = "#2747C9", "#D2452B", "#E3A21A", "#B57C00"

FONT_FACES = {
    "serif-400": ("Instrument Serif", "normal", 400),
    "serif-italic": ("Instrument Serif", "italic", 400),
    "sans-400": ("Geist", "normal", 400),
    "sans-600": ("Geist", "normal", 600),
    "mono-400": ("Geist Mono", "normal", 400),
}
SERIF, SANS, MONO = "'Instrument Serif',Georgia,serif", "Geist,Helvetica,Arial,sans-serif", "'Geist Mono',Menlo,monospace"
ALL_FONTS = ["serif-400", "serif-italic", "sans-400", "mono-400"]


def font_css(*names):
    out = []
    for n in names:
        fam, style, weight = FONT_FACES[n]
        b64 = base64.b64encode((ROOT / "fonts" / f"{n}.woff").read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                   f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(out)


def width(text, font, size):
    m = METRICS[font]
    return sum(m.get(c, 0.55) for c in text) * size


def wrap(text, font, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, font, size) > max_w:
            lines.append(cur); cur = word
        else:
            cur = trial
    return lines + [cur]


BASE_CSS = """
@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.2)}70%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:scale(1)}}
@keyframes swing{0%{opacity:0;transform:translateY(70px) rotate(-7deg)}55%{opacity:1;transform:translateY(-8px) rotate(1.6deg)}78%{transform:translateY(3px) rotate(-.6deg)}100%{opacity:1;transform:none}}
@keyframes ring{0%{opacity:.55;transform:scale(.4)}100%{opacity:0;transform:scale(2.6)}}
@keyframes dot{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes nudge{0%,70%,100%{transform:none}35%{transform:translate(4px,-4px)}}
@keyframes sweep{0%{transform:translateX(-160px)}55%,100%{transform:translateX(1100px)}}
@keyframes flash{0%,100%{opacity:1}}
.fb{transform-box:fill-box;transform-origin:center}
.lft{transform-box:fill-box;transform-origin:left}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def anim(name, dur, delay, extra=""):
    """Inline animation style; empty in STATIC mode."""
    if STATIC:
        return ""
    return f'style="animation:{name} {dur}s {delay:.3f}s {extra} both"'


def nudge(delay):
    return "" if STATIC else f'style="animation:nudge 2.6s {delay:.2f}s infinite"'


def svg(w, h, body, fonts, label=""):
    style = font_css(*fonts) + BASE_CSS + ("*{animation:none!important}" if STATIC else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f"<style>{style}</style>{body}</svg>")


def paper(w, h, r=18, dashed=False):
    if dashed:
        return (f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r}" fill="{PAPER}" stroke="{MUTED}" '
                f'stroke-width="1.5" stroke-dasharray="6 6"/>')
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r}" fill="{PAPER}" stroke="{RULE}" stroke-width="1.5"/>'


def shine(clip_id, x, y, w, h, delay, period=6, color="#FFFFFF", opacity=.55):
    """A diagonal light band that sweeps across whatever clip_id clips."""
    if STATIC:
        return ""
    # the CSS transform would replace a transform attribute, so the skew sits on an inner element
    return (f'<g clip-path="url(#{clip_id})"><g style="animation:sweep {period}s {delay}s ease-in-out infinite both">'
            f'<rect x="{x}" y="{y-40}" width="70" height="{h+80}" fill="{color}" opacity="{opacity}" '
            f'transform="skewX(-20)"/></g></g>')


def count_up(final, x, y, attrs, start, dur=0.9, frames=18):
    """Text that counts from zero to `final`. CSS cannot change text, so each value
    is its own element, shown for one frame. The last one is the resting state, so
    reduced-motion and STATIC show only the final value."""
    if STATIC:
        return f'<text x="{x}" y="{y}" {attrs}>{escape(final)}</text>'
    decimals = len(final.split(".")[1]) if "." in final else 0
    target = float(final.replace(",", ""))
    frames = min(frames, int(target) + 1) if not decimals else frames
    out, step = [], dur / frames
    for i in range(frames):
        v = target * (1 - (1 - i / frames) ** 3)  # ease-out
        s = f"{v:.{decimals}f}" if decimals else f"{int(v)}"
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0" '
                   f'style="animation:flash {step:.3f}s {start + i*step:.3f}s linear">{s}</text>')
    out.append(f'<text x="{x}" y="{y}" {attrs} style="animation:fade .01s {start+dur:.3f}s both">{escape(final)}</text>')
    return "".join(out)


# ---- 1. hero ------------------------------------------------------------------
def hero():
    W, H = 840, 480
    rows = (ROOT / "data" / "portrait.txt").read_text().split("\n")
    fs, lh = 4.3, 5.16
    pw = max(map(len, rows)) * 0.6 * fs
    px, py = W - pw - 44, (H - len(rows) * lh) / 2 + 6
    portrait = "".join(
        f'<text xml:space="preserve" x="{px:.1f}" y="{py + i*lh:.2f}" {anim("fade", .25, .35 + i*.014)}>{escape(r)}</text>'
        for i, r in enumerate(rows))
    b = [paper(W, H),
         f'<g font-family="{MONO}" font-size="{fs}" fill="{INK}" style="white-space:pre">{portrait}</g>',
         f'<text x="48" y="74" font-family="{MONO}" font-size="11" fill="{MUTED}" letter-spacing="1.5" {anim("up", .6, .05)}>GITHUB / ANGADTATHGIR</text>',
         f'<g font-family="{SERIF}" font-size="92" fill="{INK}">'
         f'<text x="44" y="178" {anim("up", .8, .15)}>Angad</text>'
         f'<text x="44" y="258" font-style="italic" {anim("up", .8, .3)}>Tathgir</text></g>',
         f'<clipPath id="nm"><text x="44" y="258" font-family="{SERIF}" font-size="92" font-style="italic">Tathgir</text></clipPath>',
         shine("nm", 30, 180, 320, 90, 1.4, 5, BLUE, .9),
         f'<rect x="48" y="290" width="56" height="2" fill="{INK}" {anim("fade", .4, .6)}/>',
         f'<g font-family="{SANS}" font-size="16" fill="{INK2}">'
         f'<text x="48" y="328" {anim("up", .6, .65)}>Penn Engineering, class of 2030.</text>'
         f'<text x="48" y="352" {anim("up", .6, .75)}>Forecasting models, racing robots, a lot of probability.</text></g>',
         f'<g {anim("up", .6, .9)}>'
         f'<circle cx="54" cy="408" r="4.5" fill="{BLUE}" style="{"" if STATIC else "animation:dot 2s 1.5s infinite"}"/>'
         + ("" if STATIC else f'<circle cx="54" cy="408" r="4.5" fill="none" stroke="{BLUE}" class="fb" style="animation:ring 2s 1.5s infinite both"/>')
         + f'<text x="68" y="413" font-family="{SANS}" font-size="14" fill="{INK}">Now building <tspan font-weight="600">Tokenback</tspan>'
         f'<tspan fill="{MUTED}"> · private for now</tspan></text></g>']
    return svg(W, H, "".join(b), ["serif-400", "serif-italic", "sans-400", "sans-600", "mono-400"],
               label="Angad Tathgir: Penn Engineering 2030, forecasting models and racing robots")


# ---- 2. by the numbers ------------------------------------------------------
NUMBERS = [
    ("3rd", "", BLUE, ["SIMSO WORLD FINALS,", "GOLD, 3RD GLOBALLY"]),
    ("AIME", "", BLUE, ["QUALIFIER"]),
    ("1st", "", BLUE, ["IN THE WORLD, WATERLOO", "AVOGADRO CHEMISTRY"]),
    ("Top 5%", "", BLUE, ["AMC 12, WORLDWIDE"]),
    ("Top 3%", "", RED, ["IN THE WORLD, WATERLOO", "SIR ISAAC NEWTON PHYSICS"]),
    ("Diana", "", YELLOW, ["AWARD, ECOBINRECYCLE", "+ MERCEDES-BENZ", "BE-VISIONEERS FELLOW"]),
    ("15", "+", YELLOW, ["BADMINTON MEDALS,", "STATE AND NATIONAL"]),
    ("NSE", "", YELLOW, ["COGENCIS INTERN,", "FUND ANALYTICS, 2025"]),
]


def numbers():
    W, cols = 840, 4
    cw, ch, x0, y0 = (840 - 96) / cols, 116, 48, 92
    H = int(y0 + ch * 2 + 14)
    cells = []
    for i, (big, unit, color, label) in enumerate(NUMBERS):
        x, y = x0 + (i % cols) * cw, y0 + (i // cols) * ch
        t = 0.3 + i * 0.09
        big_attrs = f'font-family="{SERIF}" font-size="44" fill="{INK}"'
        big_el = count_up(big, x, y + 44, big_attrs, t + .1, .6) if big.isdigit() else f'<text x="{x}" y="{y+44}" {big_attrs}>{escape(big)}</text>'
        unit_el = (f'<text x="{x + width(big, "serif-400", 44) + 2:.1f}" y="{y+44}" font-family="{SERIF}" font-style="italic" '
                   f'font-size="30" fill="{MUTED}">{escape(unit)}</text>') if unit else ""
        cells.append(
            f'<g {anim("up", .6, t)}>{big_el}{unit_el}'
            f'<rect x="{x}" y="{y+56}" width="26" height="3" rx="1.5" fill="{color}" class="lft" {anim("grow", .5, t + .35)}/>'
            + "".join(f'<text x="{x}" y="{y + 78 + j*14}" font-family="{MONO}" font-size="10" fill="{MUTED}" letter-spacing=".6">{escape(l)}</text>'
                      for j, l in enumerate(label)) + "</g>")
    b = [paper(W, H),
         f'<text x="{x0}" y="56" font-family="{SERIF}" font-size="30" fill="{INK}" {anim("up", .6, .1)}>'
         f'By the numbers, <tspan font-style="italic" fill="{BLUE}">away from the keyboard</tspan></text>',
         f'<line x1="{x0}" x2="{W-x0}" y1="{y0 + ch - 8}" y2="{y0 + ch - 8}" stroke="{RULE}"/>',
         "".join(cells)]
    return svg(W, H, "".join(b), ALL_FONTS, label="By the numbers: competition maths, research, robotics")


# ---- 3. three world tiles ---------------------------------------------------
TILES = [
    ("quant", "QUANT", BLUE, "296", "", ["World Cup matches forecast", "out-of-sample, walk-forward"], 0.0, True),
    ("build", "BUILD", RED, "7539", "", ["Captain, FRC Team Elev8. Won 2", "regionals in 2025 as alliance", "captain, a first for India."], 0.15, False),
    ("research", "RESEARCH", YELLOW, "IEEE", "", ["Xplore paper: Heusler alloys", "for solid-state magnetic cooling"], 0.3, False),
]


def tile(key, kicker, color, number, unit, lines, d0, linked):
    W, H = 270, 300
    t0 = 0.2 + d0
    ink_on = "#FFFFFF" if color != YELLOW else INK
    num_attrs = f'font-family="{SERIF}" font-size="76" fill="{ink_on}"'
    unit_x = 28 + width(number, "serif-400", 76) + 4
    b = [f'<g class="fb" {anim("swing", 1.0, t0)}>',
         f'<clipPath id="t{key}"><rect x="0" y="0" width="{W}" height="{H}" rx="18"/></clipPath>',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="18" fill="{color}"/>',
         "" if STATIC else f'<circle cx="{W-34}" cy="34" r="12" fill="none" stroke="{ink_on}" stroke-width="1.5" class="fb" style="animation:ring 2.4s {t0+1:.2f}s infinite both"/>',
         f'<circle cx="{W-34}" cy="34" r="5" fill="{ink_on}"/>',
         f'<text x="28" y="44" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{ink_on}">{kicker}</text>',
         count_up(number, 28, 168, num_attrs, t0 + 0.55) if number.replace(".", "").isdigit()
         else f'<text x="28" y="168" {num_attrs} class="fb" {anim("pop", .5, t0 + .55)}>{escape(number)}</text>',
         f'<text x="{unit_x:.1f}" y="168" font-family="{SERIF}" font-style="italic" font-size="40" fill="{ink_on}" opacity=".85">{unit}</text>' if unit else "",
         f'<g font-family="{SANS}" font-size="14.5" fill="{ink_on}" opacity=".92">'
         + "".join(f'<text x="28" y="{214 + i*20}">{escape(l)}</text>' for i, l in enumerate(lines)) + "</g>",
         (f'<g class="fb" {nudge(t0 + 1.4)}><text x="{W-30}" y="{H-24}" text-anchor="end" '
          f'font-family="{SANS}" font-size="20" fill="{ink_on}">↗</text></g>') if linked else "",
         shine(f"t{key}", 0, 0, W, H, t0 + 1.6, 7, "#FFFFFF", .22),
         "</g>"]
    return svg(W, H, "".join(b), ALL_FONTS, label=f"{kicker}: {number}{unit} {' '.join(lines)}")


# ---- 4. public project cards ----------------------------------------------
PROJECTS = [
    ("wc2026", "World Cup 2026 model", BLUE, "Forecasts for every match, with each parameter fitted by MLE and tested walk-forward.",
     [("0.9396", "log loss, fitted Elo"), ("296", "matches out-of-sample"), ("49,547", "internationals fitted")], "Python"),
    ("roboracer", "LiDAR racing node", RED, "ROS 2 wall and gap following for the AutoDRIVE RoboRacer, with speed from scan matching.",
     [("6.104 s", "fastest lap, with odometry"), ("6.180 s", "fastest lap, LiDAR only"), ("0", "contacts in 31 laps")], "Python · ROS 2"),
    ("shapes", "Background-agnostic shape detection", YELLOW, "Finds shapes in streamed video by texture, not colour, then places each one in 3D.",
     [("0.969", "IoU on grass"), ("0.957", "IoU on gravel"), ("~54 fps", "at 19 ms a frame")], "Python · OpenCV"),
]


def project(key, title, color, desc, stats, lang, i):
    W, H = 840, 150
    t0 = 0.2 + i * 0.15
    stat_col = OCHRE if color == YELLOW else color
    b = [f'<g {anim("up", .7, t0)}>', paper(W, H),
         f'<rect x="1" y="1" width="8" height="{H-2}" rx="4" fill="{color}"/>',
         f'<text x="36" y="48" font-family="{SERIF}" font-size="30" fill="{INK}">{escape(title)}</text>',
         f'<text x="36" y="76" font-family="{SANS}" font-size="14.5" fill="{INK2}">{escape(desc)}</text>',
         f'<text x="{W-36}" y="44" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}" letter-spacing="1">{escape(lang.upper())}</text>']
    for j, (big, small) in enumerate(stats):
        x = 36 + j * 220
        b.append(f'<g {anim("up", .5, t0 + .35 + j*.1)}><text x="{x}" y="118" font-family="{SERIF}" font-size="26" fill="{stat_col}">{escape(big)}</text>'
                 f'<text x="{x}" y="136" font-family="{MONO}" font-size="10" fill="{MUTED}" letter-spacing=".8">{escape(small.upper())}</text></g>')
    b.append(f'<g class="fb" {nudge(t0 + 1.2)}><text x="{W-36}" y="124" text-anchor="end" font-family="{SANS}" font-size="22" fill="{INK}">↗</text></g></g>')
    return svg(W, H, "".join(b), ALL_FONTS, label=f"{title}: {desc}")


# ---- 5. private / offline projects, two per row ----------------------------
PRIVATE = [
    ("frc", "FRC 7539 robot code", RED, "TEAM REPO · PRIVATE",
     "Team Elev8's 2025 REEFSCAPE robot: swerve drive, arm, ground intake, L2 and L3 scoring, climb.",
     [("20", "commands + subsystems"), ("Java", "WPILib, Phoenix 6")]),
    ("per", "Torque delivery widget", BLUE, "2026 · PRIVATE",
     "Telemetry view of torque asked for vs delivered on a 766 s endurance run, with each shortfall given a cause.",
     [("100%", "of shortfall: 49 mph limit"), ("58", "unit tests")]),
    ("drone", "Drone controller", YELLOW, "2024 · PRIVATE",
     "ESP8266 firmware that flies a Pluto drone over MSP and TCP: arm, take off, steer, land.",
     [("8", "RC channels per frame"), ("C++", "ESP8266, MSP")]),
    ("tokenback", "Tokenback", INK, "PRIVATE",
     "In progress.", []),
]


def private_card(key, title, color, tag, desc, stats, i, W=410):
    H = 214 if W == 410 else 196
    t0 = 0.2 + i * 0.12
    stat_col = OCHRE if color == YELLOW else color
    lines = wrap(desc, "sans-400", 13.5, W - 60)
    b = [f'<g {anim("up", .7, t0)}>', paper(W, H, dashed=True),
         f'<circle cx="34" cy="38" r="5" fill="{color}"/>',
         f'<text x="48" y="42" font-family="{MONO}" font-size="10" fill="{MUTED}" letter-spacing="1">{escape(tag)}</text>',
         f'<text x="28" y="82" font-family="{SERIF}" font-size="28" fill="{INK}">{escape(title)}</text>',
         f'<g font-family="{SANS}" font-size="13.5" fill="{INK2}">'
         + "".join(f'<text x="28" y="{108 + j*19}">{escape(l)}</text>' for j, l in enumerate(lines)) + "</g>"]
    for j, (big, small) in enumerate(stats):
        x = 28 + j * 180
        b.append(f'<g {anim("up", .5, t0 + .35 + j*.1)}><text x="{x}" y="{H-36}" font-family="{SERIF}" font-size="24" fill="{stat_col}">{escape(big)}</text>'
                 f'<text x="{x}" y="{H-20}" font-family="{MONO}" font-size="9.5" fill="{MUTED}" letter-spacing=".6">{escape(small.upper())}</text></g>')
    b.append("</g>")
    return svg(W, H, "".join(b), ALL_FONTS, label=f"{title}: {desc}")


def main():
    CARDS.mkdir(exist_ok=True)
    for old in CARDS.glob("*.svg"):
        old.unlink()
    out = {"hero": hero(), "numbers": numbers()}
    for t in TILES:
        out[t[0]] = tile(*t)
    for i, p in enumerate(PROJECTS):
        out[f"project-{p[0]}"] = project(*p, i)
    for i, p in enumerate(PRIVATE):
        out[f"private-{p[0]}"] = private_card(*p, i)
    for name, s in out.items():
        (CARDS / f"{name}.svg").write_text(s)
    print(f"rendered {len(out)} cards{' (static)' if STATIC else ''} -> {CARDS}")


if __name__ == "__main__":
    main()
