"""Build the desk-reference playbook from ALL.json.

The companion report answers "is the lattice real?". This one answers the
question a trader actually has in front of a chart: given a setup I can name in
real time, what happens next and how often. Same event set, same nulls, but
organised by what you would do rather than by what was hypothesised.
"""
import json
import os

import playbook_paths as pp
import playbook_volume as pv
import playbook_clock as pc

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "ALL.json")))
OUT = os.path.join(HERE, "..", "..", "gb-playbook.html")

ATR26 = 16.99          # 2026 median RTH 1-minute ATR, in points
COST = D["edge81"]["cost_pts"]

CSS = """
:root{
  --ground:#EDEEF1;
  --card:#FFFFFF;
  --sunk:#E3E5EA;
  --ink:#16191D;
  --ink-2:#474F59;
  --ink-3:#6F7883;
  --rule:#D5D8DE;
  --rule-2:#BFC4CD;
  --accent:#1B6E72;
  --accent-soft:#D6E7E7;
  --good:#2E6B4C;
  --good-soft:#DBEAE1;
  --warn:#8A6416;
  --warn-soft:#F0E6CF;
  --bad:#9C3B36;
  --bad-soft:#F1DCDA;
  --shadow:0 1px 2px rgba(22,25,29,.05),0 6px 20px rgba(22,25,29,.05);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#111417;
    --card:#181C21;
    --sunk:#1F242A;
    --ink:#E6E9EC;
    --ink-2:#AEB6BF;
    --ink-3:#7C858F;
    --rule:#2A3037;
    --rule-2:#3B434C;
    --accent:#57C4C7;
    --accent-soft:#16383A;
    --good:#6FBE93;
    --good-soft:#16301F;
    --warn:#D6AC5A;
    --warn-soft:#332912;
    --bad:#DB8A84;
    --bad-soft:#331A19;
    --shadow:0 1px 2px rgba(0,0,0,.45),0 8px 26px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --ground:#111417;
  --card:#181C21;
  --sunk:#1F242A;
  --ink:#E6E9EC;
  --ink-2:#AEB6BF;
  --ink-3:#7C858F;
  --rule:#2A3037;
  --rule-2:#3B434C;
  --accent:#57C4C7;
  --accent-soft:#16383A;
  --good:#6FBE93;
  --good-soft:#16301F;
  --warn:#D6AC5A;
  --warn-soft:#332912;
  --bad:#DB8A84;
  --bad-soft:#331A19;
  --shadow:0 1px 2px rgba(0,0,0,.45),0 8px 26px rgba(0,0,0,.35);
}

*{box-sizing:border-box}
body{
  margin:0;padding:0 20px 110px;
  background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16.5px;line-height:1.6;-webkit-font-smoothing:antialiased;
}
.wrap{max-width:1060px;margin:0 auto}
.col{max-width:66ch}

h1,h2,h3{font-family:"Archivo","Helvetica Neue",Arial,sans-serif;
         text-wrap:balance;margin:0;letter-spacing:-.015em}
h1{font-size:clamp(2.3rem,6vw,3.9rem);font-weight:700;line-height:1.02}
h2{font-size:clamp(1.35rem,2.7vw,1.8rem);font-weight:600;line-height:1.15}
h3{font-size:1.02rem;font-weight:600;line-height:1.3;margin-top:2.2rem}
p{margin:0 0 1.05rem}
b,strong{font-weight:600}

.eyebrow{
  font-family:"IBM Plex Mono",monospace;font-size:.68rem;font-weight:500;
  letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3);
}

/* ---- masthead ---- */
header.mast{padding:70px 0 26px;border-bottom:2px solid var(--ink)}
header.mast .eyebrow{margin-bottom:1.4rem}
.lede{font-size:1.15rem;color:var(--ink-2);max-width:58ch;margin-top:1.4rem}
.mast-meta{display:flex;flex-wrap:wrap;gap:.35rem 2rem;margin-top:1.8rem;
  font-family:"IBM Plex Mono",monospace;font-size:.74rem;color:var(--ink-3)}
.mast-meta b{color:var(--ink-2);font-weight:500}

/* ---- verdict chips ---- */
.chip{
  display:inline-block;font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  padding:.2rem .55rem;border-radius:2px;white-space:nowrap;
}
.chip-good{background:var(--good-soft);color:var(--good)}
.chip-bad{background:var(--bad-soft);color:var(--bad)}
.chip-warn{background:var(--warn-soft);color:var(--warn)}
.chip-acc{background:var(--accent-soft);color:var(--accent)}

/* ---- the ladder: headline stat rows ---- */
.ladder{display:flex;flex-direction:column;gap:0;margin:34px 0 8px;
  border-top:1px solid var(--rule-2)}
.rung{display:grid;grid-template-columns:minmax(140px,190px) 1fr auto;
  gap:1.2rem 1.6rem;align-items:baseline;
  padding:20px 4px;border-bottom:1px solid var(--rule)}
.rung .fig{font-family:"IBM Plex Mono",monospace;font-weight:600;
  font-size:clamp(1.7rem,4vw,2.5rem);line-height:1;color:var(--accent);
  font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.rung .fig small{display:block;font-size:.62rem;font-weight:500;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin-top:.5rem}
.rung .claim{color:var(--ink-2);font-size:.95rem}
.rung .claim b{color:var(--ink)}
.rung.neg .fig{color:var(--bad)}

/* ---- sections ---- */
section{padding-top:56px}
section > h2{padding-bottom:.65rem;border-bottom:1px solid var(--rule);
  margin-bottom:.4rem}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;
  gap:1rem;flex-wrap:wrap;margin-bottom:1.4rem}
.sec-head .eyebrow{margin:0}

/* ---- tables ---- */
.scroll{overflow-x:auto;margin:1.5rem 0;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:520px;
  background:var(--card)}
caption{caption-side:top;text-align:left;font-family:"IBM Plex Mono",monospace;
  font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-3);padding:0 .8rem .55rem}
th,td{text-align:left;padding:.52rem .8rem;border-bottom:1px solid var(--rule)}
thead th{font-family:"IBM Plex Mono",monospace;font-size:.65rem;font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3);
  border-bottom:1px solid var(--rule-2);white-space:nowrap;vertical-align:bottom}
tbody tr:last-child td{border-bottom:none}
td.num,th.num{font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums;white-space:nowrap}
td.big{font-weight:600;color:var(--ink)}
.dim{color:var(--ink-3)}
.neg{color:var(--bad)}
.pos{color:var(--good)}
tbody tr.hi{background:var(--sunk)}

/* break-even bar */
.bebar{display:block;width:132px;height:16px}
.be-track{fill:var(--sunk)}
.be-fill-lo{fill:var(--bad)}
.be-fill-hi{fill:var(--good)}
.be-thr{stroke:var(--ink);stroke-width:1.5}
.be-lab{font-family:"IBM Plex Mono",monospace;font-size:7.5px;fill:var(--ink-3)}

/* ---- callouts ---- */
.note{border-left:3px solid var(--rule-2);padding:.15rem 0 .15rem 1.15rem;
  margin:1.5rem 0;color:var(--ink-2)}
.note.key{border-left-color:var(--accent)}
.note.bad{border-left-color:var(--bad)}
.note.good{border-left-color:var(--good)}
.note p:last-child{margin-bottom:0}
.note strong{color:var(--ink)}

.card{background:var(--card);border:1px solid var(--rule);border-radius:3px;
  padding:22px 24px;box-shadow:var(--shadow);margin:1.6rem 0}

ul,ol{padding-left:1.15rem;margin:0 0 1.05rem}
li{margin-bottom:.45rem}
code{font-family:"IBM Plex Mono",monospace;font-size:.86em;
  background:var(--sunk);padding:.1em .36em;border-radius:2px}

/* checklist */
.check{list-style:none;padding:0;margin:1.2rem 0;
  display:flex;flex-direction:column;gap:0;border-top:1px solid var(--rule)}
.check li{display:grid;grid-template-columns:2.1rem 1fr;gap:.9rem;
  padding:.85rem .2rem;margin:0;border-bottom:1px solid var(--rule)}
.check .n{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
  font-weight:600;color:var(--accent);padding-top:.22rem}

hr.end{border:none;border-top:2px solid var(--ink);margin:72px 0 0}
footer{padding-top:20px;font-family:"IBM Plex Mono",monospace;
  font-size:.71rem;color:var(--ink-3);line-height:1.7}

a{color:var(--accent)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);
  outline-offset:2px}

@media (max-width:680px){
  body{font-size:16px;padding:0 15px 70px}
  header.mast{padding-top:46px}
  .rung{grid-template-columns:1fr;gap:.5rem;padding:16px 2px}
  .rung .fig small{margin-top:.3rem}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def pct(x, d=1):
    return "%.*f%%" % (d, x * 100)


def bebar(win, breakeven, hi=0.55):
    """Win rate against the rate it must clear to break even."""
    w = 132.0
    x = lambda v: min(max(v / hi, 0.0), 1.0) * (w - 2) + 1
    cls = "be-fill-hi" if win >= breakeven else "be-fill-lo"
    return (
        '<svg viewBox="0 0 %d 16" class="bebar" role="img" '
        'aria-label="win rate %s against break-even %s">'
        '<rect x="1" y="5" width="%.1f" height="6" rx="1" class="be-track"/>'
        '<rect x="1" y="5" width="%.1f" height="6" rx="1" class="%s"/>'
        '<line x1="%.1f" y1="2" x2="%.1f" y2="14" class="be-thr"/>'
        "</svg>"
        % (int(w), pct(win), pct(breakeven), w - 2, x(win) - 1, cls,
           x(breakeven), x(breakeven))
    )


def build():
    br = D["baserate"]
    e = D["edge81"]
    pen = e["penetration"]
    pol = [r for r in D["polarity"] if r["label"] == "all"]
    siz = D["sizing"]

    st = {(r["cond"], r["rr"]): r for r in e["structure"]}
    st_all = [st[("ALL", rr)] for rr in (1.0, 1.5, 2.0, 3.0)]
    grid_all = [r for r in e["rows"] if r["cond"] == "ALL"]

    # ---- ladder ----------------------------------------------------------
    r81 = next(x for x in br["retest"] if x["R"] == 81)
    t81 = next(x for x in br["touch"] if x["R"] == 81)
    s2 = st[("ALL", 2.0)]
    ladder = "".join([
        '<div class="rung"><div class="fig">%s<small>break &rarr; retest</small></div>'
        '<div class="claim">A level that breaks and runs a full ATR past comes back '
        'to be touched again within two hours. <b>Plan the second entry; do not '
        'chase the first.</b></div><div><span class="chip chip-good">Usable</span></div></div>'
        % pct(r81["rates"]["120"], 1),
        '<div class="rung"><div class="fig">%s<small>median penetration</small></div>'
        '<div class="claim">How far price pushes past the level on the retest bar, '
        'in ATR. <b>A stop closer than 0.75 ATR beyond the line sits inside the '
        'level\'s own noise.</b></div><div><span class="chip chip-good">Usable</span></div></div>'
        % ("%.2f" % pen["percentiles"]["50"]),
        '<div class="rung neg"><div class="fig">%s<small>vs %s needed at 2R</small></div>'
        '<div class="claim">Win rate on the retest trade entered properly, with the '
        'stop beyond the retest bar\'s wick. <b>Below break-even at every ratio '
        'tighter than 3R.</b></div><div><span class="chip chip-bad">Not an edge</span></div></div>'
        % (pct(s2["p"]), pct(1 / (1 + 2.0))),
        '<div class="rung neg"><div class="fig">%s<small>touch &rarr; reject</small></div>'
        '<div class="claim">Arriving from at least 1 ATR away, price turns rather '
        'than pushes through only two times in five. <b>A blind limit fade at the '
        'line loses.</b></div><div><span class="chip chip-warn">Watch out</span></div></div>'
        % pct(t81["p"]),
    ])

    # ---- retest availability --------------------------------------------
    retest_rows = "".join(
        '<tr><td class="num">%d</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
        % (r["R"], "{:,}".format(r["n"]), pct(r["rates"]["60"]),
           pct(r["rates"]["120"]), pct(r["rates"]["240"]))
        for r in br["retest"])

    # ---- penetration / stop placement -----------------------------------
    pen_rows = "".join(
        '<tr%s><td class="num">%.2f ATR</td><td class="num dim">%.0f pts</td>'
        '<td class="num big">%s</td><td class="num dim">%s</td></tr>'
        % (' class="hi"' if float(s) == 0.75 else "", float(s), float(s) * ATR26,
           pct(v), "survives" if v > .75 else "too tight")
        for s, v in sorted(pen["stop_survival"].items(), key=lambda kv: float(kv[0])))
    pctl_rows = "".join(
        '<tr><td class="num">p%s</td><td class="num big">%.2f ATR</td>'
        '<td class="num dim">%.1f pts</td></tr>'
        % (q, v, v * ATR26)
        for q, v in sorted(pen["percentiles"].items(), key=lambda kv: float(kv[0])))

    # ---- the trade -------------------------------------------------------
    st_rows = "".join(
        '<tr><td class="num">%.1fR</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num">%s</td>'
        '<td class="num dim">%s</td><td class="num %s">%+.3fR</td>'
        '<td>%s</td></tr>'
        % (r["rr"], "{:,}".format(r["n"]), pct(r["p"]),
           pct(1 / (1 + r["rr"])), pct(r["null_p"]),
           "neg" if r["ev_r"] < 0 else "pos", r["ev_r"],
           bebar(r["p"], 1 / (1 + r["rr"])))
        for r in st_all)

    grid_rows = "".join(
        '<tr><td class="num">%.2f / %.2f</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num dim">%s</td>'
        '<td class="num %s">%+.3f</td><td class="num %s">%+.2f</td></tr>'
        % (r["tgt"], r["stop"], "{:,}".format(r["n"]), pct(r["p"]),
           pct(r["null_p"]), "neg" if r["ev_atr"] < 0 else "pos", r["ev_atr"],
           "neg" if r["ev_atr"] * ATR26 - COST < 0 else "pos",
           r["ev_atr"] * ATR26 - COST)
        for r in grid_all)

    # ---- conditions ------------------------------------------------------
    COND_ORDER = [
        ("zone=EXT", "Range extreme 97&ndash;100 / 0&ndash;3"),
        ("zone=EQ", "Equilibrium 47&ndash;53"),
        ("zone=FV", "Flow middle 29 / 71"),
        ("zone=GIP", "Inversion point 17 / 83"),
        ("zone=LLOD", "Last line of defense 7 / 93"),
        ("sweep=yes", "After an aligned liquidity sweep"),
        ("sweep=no", "&hellip; without one"),
        ("htf_conf=yes", "Also a level on the R=729 lattice"),
        ("htf_conf=no", "&hellip; R=81 only"),
        ("exc_1_1.5", "Shallow break, 1&ndash;1.5 ATR"),
        ("exc_1.5_2.5", "Medium break, 1.5&ndash;2.5 ATR"),
        ("exc_2.5+", "Deep break, over 2.5 ATR"),
        ("sess=NYopen", "New York open hour"),
        ("sess=RTHrest", "Rest of the NY session"),
        ("sess=London", "London"),
        ("sess=Asia", "Asia"),
        ("vol_low", "Quiet tape"),
        ("vol_high", "Fast tape"),
        ("dir=long", "Long, at broken resistance"),
        ("dir=short", "Short, at broken support"),
    ]
    base2 = st[("ALL", 2.0)]["p"]
    cond_rows = "".join(
        '<tr><td>%s</td><td class="num dim">%s</td><td class="num big">%s</td>'
        '<td class="num dim">%s</td><td class="num %s">%+.1fpp</td></tr>'
        % (label, "{:,}".format(st[(k, 2.0)]["n"]), pct(st[(k, 2.0)]["p"]),
           pct(st[(k, 2.0)]["null_p"]),
           "neg" if st[(k, 2.0)]["p"] < base2 else "pos",
           (st[(k, 2.0)]["p"] - base2) * 100)
        for k, label in COND_ORDER if (k, 2.0) in st)

    # ---- touch -----------------------------------------------------------
    touch_rows = "".join(
        '<tr><td class="num">%d</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num">%s</td>'
        '<td class="num pos">%+.2fpp</td><td class="num pos">%+.2f</td></tr>'
        % (r["R"], "{:,}".format(r["n"]), pct(r["p"], 2), pct(r["null"], 2),
           (r["p"] - r["null"]) * 100, r["z"])
        for r in br["touch"])
    pol_rows = "".join(
        '<tr><td class="num">%d</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num">%s</td>'
        '<td class="num %s">%+.2fpp</td><td class="num">%d / 20</td></tr>'
        % (r["R"], "{:,}".format(r["n"]), pct(r["hold_rate"], 2),
           pct(r["null_mean"], 2),
           "pos" if r["hold_rate"] > r["null_mean"] else "neg",
           (r["hold_rate"] - r["null_mean"]) * 100, r["rank"])
        for r in pol)

    # ---- multi-scale / level identity -------------------------------------
    lvl = sorted(D["levels"]["levels"], key=lambda r: -r["reject"])
    lvl_rows = "".join(
        '<tr%s><td class="num">%d</td><td>%s</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num dim">[%.3f, %.3f]</td>'
        '<td>%s</td></tr>'
        % (' class="hi"' if r["structural"] else "", r["pct"], r["name"],
           "{:,}".format(r["n"]), pct(r["reject"], 2), r["lo"], r["hi"],
           '<span class="chip chip-acc">any grid</span>' if r["structural"] else "")
        for r in lvl)

    conf_rows = "".join(
        '<tr><td class="num">%d</td><td class="num dim">%s</td>'
        '<td class="num big">%s</td><td class="num">%s</td>'
        '<td class="num %s">%+.2fpp</td><td class="num %s">%+.2f</td></tr>'
        % (r["confluence"], "{:,}".format(r["n"]), pct(r["reject"], 2),
           pct(r["null_mean"], 2),
           "pos" if r["reject"] > r["null_mean"] else "neg",
           (r["reject"] - r["null_mean"]) * 100,
           "pos" if r["z"] > 0 else "neg", r["z"])
        for r in D["confluence"])

    lt = {(r["band"], r["rr"]): r for r in D["lvltrade"]}
    lt_rows = "".join(
        '<tr><td class="num">%.1fR</td><td class="num dim">%s</td>'
        '<td class="num">%s</td><td class="num">%s</td>'
        '<td class="num %s">%+.3fR</td><td class="num %s">%+.3fR</td></tr>'
        % (rm, pct(1 / (1 + rm)),
           pct(lt[("boundary + EQ", rm)]["p"]), pct(lt[("the other 18", rm)]["p"]),
           "neg" if lt[("boundary + EQ", rm)]["ev_r"] < 0 else "pos",
           lt[("boundary + EQ", rm)]["ev_r"],
           "neg" if lt[("the other 18", rm)]["ev_r"] < 0 else "pos",
           lt[("the other 18", rm)]["ev_r"])
        for rm in (1.0, 1.5, 2.0, 3.0))

    om = D["levels"]["omnibus"]
    sv = D["levels"]["structural_vs_gb"]
    db = D["controls"]["day_boot"]
    nest_z = [r["z"] for r in D["nest"]]

    # ---- sizing ----------------------------------------------------------
    siz_rows = "".join(
        '<tr%s><td class="num">%d</td><td class="num dim">%.1f pts</td>'
        '<td class="num dim">%.0f pts</td><td class="num">%.1f</td>'
        '<td class="num %s">%.2f</td><td class="num">%.1f</td></tr>'
        % (' class="hi"' if r["year"] == 2026 else "", r["year"], r["bar"],
           r["rth_range"], r["blocks_81"],
           "neg" if r["zone81_bars"] < 0.5 else "", r["zone81_bars"],
           r["zone729_bars"])
        for r in siz)

    n_ret = "{:,}".format(e["n_true"])
    risk_pts = st_all[0]["risk_atr"] * ATR26

    html = HEAD + """
<div class="wrap">

<header class="mast">
  <div class="eyebrow">NQ futures &middot; 1-minute &middot; 2010&ndash;2026 &middot; %(nret)s retests</div>
  <h1>Goldbach<br>Base Rates</h1>
  <p class="lede">What actually happens at a PO3 level, stated as frequencies you
  can put in a plan. Two of these numbers are worth trading around. The rest are
  here so you stop paying for the ones that aren't.</p>
  <div class="mast-meta">
    <span><b>4,778,135</b> bars</span>
    <span><b>4,885</b> trading days</span>
    <span>price <b>1,722</b>&ndash;<b>30,976</b></span>
    <span><b>6</b> shifted-lattice nulls per cell</span>
  </div>
</header>

<div class="ladder">%(ladder)s</div>

<div class="col">

<section id="event">
  <div class="sec-head"><h2>What counts as an event</h2>
    <span class="eyebrow">Definitions</span></div>
  <p>Every number on this page comes from one event chain, applied to all twenty
  Goldbach levels of the R=81 block and mirrored for both directions:</p>
  <ol>
    <li><b>Break.</b> A close crosses the level.</li>
    <li><b>Excursion.</b> Price then travels at least <b>1 ATR</b> beyond it, and
    this must complete on a bar <em>before</em> the return.</li>
    <li><b>Retest.</b> Price comes back to touch the level, within 240 bars.</li>
    <li><b>Resolution.</b> The trade is scored against ATR-scaled barriers, from
    the bar <em>after</em> entry.</li>
  </ol>
  <p>Barriers are ATR-scaled throughout because price ran from 1,722 to 30,976
  across the sample &mdash; a fixed point target would measure the era, not the
  setup.</p>

  <div class="note bad">
    <p><strong>Two artifacts had to be removed first, and both flattered the
    setup badly.</strong></p>
    <p>The excursion flag was originally updated <em>before</em> the return was
    tested, which let a single wide bar count as break, excursion and retest at
    once. <b>54%% of events qualified that way</b>, each already a full ATR onside
    at its supposed entry &mdash; and no order could have been resting at the
    level, because the filter that selects the setup is only known once that bar
    has closed.</p>
    <p>The entry bar was also scored symmetrically. A long fills at the level
    <em>because</em> that bar traded down to it, so the bar's high happened
    before the fill and counting it as profit is look-ahead, while its low is
    real heat. The entry bar can now stop you out but cannot pay you.</p>
    <p>Together they were worth <b>+0.19 ATR per trade of pure fiction</b>: the
    baseline went from a 59.4%% win rate and 17 profitable years out of 17, to
    47.7%% and none. Anything below is post-correction.</p>
  </div>
</section>

<section id="availability">
  <div class="sec-head"><h2>You will get a second entry</h2>
    <span class="chip chip-good">Usable</span></div>
  <p>The single most valuable number here, and the one least sensitive to how the
  test is built &mdash; it involves no barriers, no fills and no assumptions about
  execution. Just: does price come back?</p>
</section>
</div>

<div class="scroll"><table>
  <caption>After a break that runs 1 ATR, does the level get retested?</caption>
  <thead><tr><th class="num">Block</th><th class="num">Breaks</th>
    <th class="num">Within 60 min</th><th class="num">120 min</th>
    <th class="num">240 min</th></tr></thead>
  <tbody>%(retest_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note good">
    <p><strong>Do not chase the break.</strong> Four times in five the level
    comes back to you inside two hours, and the rate barely moves across block
    sizes &mdash; it is a property of how price moves, not of this lattice, which
    is exactly why you can rely on it.</p>
    <p>The corollary matters as much: the one time in six that price never comes
    back is the move you would have caught by chasing. Sizing has to survive
    missing those.</p>
  </div>
</div>

<div class="col">
<section id="risk">
  <div class="sec-head"><h2>Where the stop has to go</h2>
    <span class="chip chip-good">Usable</span></div>
  <p>The retest bar does not stop politely at the line &mdash; it pushes through
  it. That penetration distribution is what sets the stop, and it is the
  arithmetic behind every losing result further down this page.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Penetration past the level on the retest bar</caption>
  <thead><tr><th class="num">Percentile</th><th class="num">In ATR</th>
    <th class="num">At 2026 volatility</th></tr></thead>
  <tbody>%(pctl_rows)s</tbody>
</table></div>

<div class="scroll"><table>
  <caption>How often a stop at each distance survives the entry bar</caption>
  <thead><tr><th class="num">Stop beyond the level</th>
    <th class="num">At 2026 volatility</th><th class="num">Survives</th>
    <th class="num">&nbsp;</th></tr></thead>
  <tbody>%(pen_rows)s</tbody>
</table></div>

<div class="col">
  <p>Median penetration is <b>%(pen50).2f ATR</b>. At a 2026 one-minute ATR of
  %(atr26).2f points that is <b>%(pen50pts).1f points</b> of routine push-through
  on a level you thought was holding.</p>
  <div class="note key">
    <p><strong>0.75 ATR is the practical floor.</strong> Below it you are stopped
    by noise more than one time in five before the trade has done anything; at
    0.25 ATR you are stopped <b>%(stop25)s</b> of the time on the entry bar
    alone.</p>
  </div>
</div>

%(paths_html)s

<div class="col">
<section id="trade">
  <div class="sec-head"><h2>The trade itself</h2>
    <span class="chip chip-bad">Not an edge</span></div>
  <p>Entered the way you would actually take it: at the <b>close of the retest
  bar</b>, once the penetration is visible, with the stop just beyond that bar's
  extreme. Median risk is <b>%(risk).2f ATR</b>, about %(riskpts).1f points at
  current volatility. The black tick on each bar is the win rate that ratio needs
  to break even.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Structure entry &mdash; close of retest bar, stop beyond the wick</caption>
  <thead><tr><th class="num">Target</th><th class="num">Trades</th>
    <th class="num">Win rate</th><th class="num">Break-even</th>
    <th class="num">Shifted lattices</th><th class="num">Expectancy</th>
    <th class="num">Actual vs break-even</th></tr></thead>
  <tbody>%(st_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note bad">
    <p><strong>Read the win rate against the column beside it.</strong> At 1R the
    trade needs 50.0%% and returns %(w1)s. At 3R it needs 25.0%% and returns
    %(w3)s &mdash; a martingale to three decimal places, before a cent of
    cost.</p>
    <p>The shifted-lattice column is the same procedure run on lattices whose
    origin has been moved. It tracks the true lattice to within 0.3 percentage
    points at every ratio. Whatever this is measuring, it is not Goldbach.</p>
  </div>
  <p>The blind version &mdash; a resting limit at the line with fixed ATR
  brackets, no waiting for the bar to close &mdash; is worse, and worse in an
  instructive way. Wide stops buy a high hit rate that costs more than it
  returns:</p>
</div>

<div class="scroll"><table>
  <caption>Limit at the level &mdash; fixed ATR target and stop</caption>
  <thead><tr><th class="num">Target / stop</th><th class="num">Trades</th>
    <th class="num">Win rate</th><th class="num">Shifted lattices</th>
    <th class="num">Expectancy</th><th class="num">Net points, 2026</th></tr></thead>
  <tbody>%(grid_rows)s</tbody>
</table></div>

<div class="col">
  <p>The 0.50/3.00 row is the trap in miniature: an <b>82.6%%</b> win rate, and it
  loses money on every one of the 4,885 days in this sample. A high hit rate is
  not an edge; it is a choice about the shape of the distribution.</p>
</div>

<div class="col">
<section id="conditions">
  <div class="sec-head"><h2>Does any filter rescue it?</h2>
    <span class="chip chip-bad">Not an edge</span></div>
  <p>This is where a real effect would hide &mdash; the setup is not supposed to
  work everywhere, only in context. Every condition below is knowable at the
  moment of entry, scored at 2R, where break-even is 33.3%%.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Structure entry at 2R, by condition &mdash; baseline %(base2)s</caption>
  <thead><tr><th>Condition</th><th class="num">Trades</th>
    <th class="num">Win rate</th><th class="num">Shifted lattices</th>
    <th class="num">vs baseline</th></tr></thead>
  <tbody>%(cond_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note bad">
    <p><strong>Nothing moves it.</strong> The four named zones land within 0.3
    percentage points of each other. An aligned liquidity sweep is worth less
    than a point. Confluence with the higher-timeframe R=729 lattice is worth
    nothing at all.</p>
    <p>The one condition that clearly does move the number is the New York open
    hour &mdash; and it moves it <em>down</em>, by nearly three points. That is
    the hour with the widest bars, so the structure stop is placed furthest from
    entry and the 2R target furthest away again.</p>
  </div>
</div>

<div class="col">
<section id="touch">
  <div class="sec-head"><h2>Reject or break?</h2>
    <span class="chip chip-warn">Watch out</span></div>
  <p>The plainest question, and the one your screen-time intuition is answering.
  Price arrives at a level having come from at least 1 ATR away. Scored as a fade
  filled at the line, with the arriving bar's push past it counted as heat
  against you.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>First touch &mdash; does price turn or go through?</caption>
  <thead><tr><th class="num">Block</th><th class="num">Touches</th>
    <th class="num">Rejects</th><th class="num">Shifted lattices</th>
    <th class="num">Edge</th><th class="num">z</th></tr></thead>
  <tbody>%(touch_rows)s</tbody>
</table></div>

<div class="col">
  <p>Roughly <b>three arrivals in five push through</b> rather than turn. Read
  that as an execution fact rather than a market law: a half-ATR bracket sits
  inside the penetration distribution from earlier, so the number describes what
  happens to an order resting on the line, not what price "wants" to do.</p>
  <p>The polarity claim &mdash; broken resistance becoming support &mdash; lands
  in the same place. Taking the retest as support with a symmetric half-ATR
  bracket:</p>
</div>

<div class="scroll"><table>
  <caption>Does a broken level hold on the retest?</caption>
  <thead><tr><th class="num">Block</th><th class="num">Retests</th>
    <th class="num">Holds</th><th class="num">Shifted lattices</th>
    <th class="num">Edge</th><th class="num">Rank</th></tr></thead>
  <tbody>%(pol_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note key">
    <p><strong>And here the lattice finally shows something real.</strong> The
    true phase beats its shifted twins on the touch test at all three block
    sizes, same sign, z +3.89, +4.87 and +2.57 &mdash; and on the retest test it
    ranks first of twenty phases at three of four block sizes. Two independent
    statistics, consistent direction. That is not noise.</p>
    <p>It is also <b>about a third of a percentage point</b>. The base rate it
    sits on is ten points underwater, and one point of round-trip cost at current
    volatility is worth twenty times more than the effect. It is real, and it is
    not a trade.</p>
  </div>
</div>

<div class="col">
<section id="scales">
  <div class="sec-head"><h2>All eight scales at once</h2>
    <span class="chip chip-acc">Real, doesn't pay</span></div>
  <p>Everything above takes one block size at a time. The tool on the chart
  does not &mdash; it shows all eight PO3 scales together, and the reported
  experience is that some levels work and others do nothing. Scale agreement is
  the obvious candidate for what separates them, and unlike most confluence
  stories it is exactly computable, because the blocks nest: 729 = 3 &times; 243
  = 9 &times; 81.</p>
  <p>First, the lattice itself. Every one of the eight rows in the tool's table
  reproduces from <code>floor(price / R) &times; R</code> to the point &mdash;
  3, 9, 27, 81, 243, 729, 2187 and 6561. That is worth stating plainly: the
  levels are exactly what this study has been testing all along, so the null
  results are about the levels themselves, not about a bad reconstruction.</p>
  <p>Major swings do not cluster where scales agree: 11 cells, z from
  %(nestlo)+.2f to %(nesthi)+.2f, nothing close.</p>
  <p>Reaction was a different story. Counting how many of the other five scales
  mark the same price, the rejection rate climbs monotonically &mdash; and
  shifted lattices, which preserve the nesting exactly and move only where it
  sits, stay flat:</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Touch rejection by how many other PO3 scales mark the same price</caption>
  <thead><tr><th class="num">Scales</th><th class="num">Touches</th>
    <th class="num">Rejects</th><th class="num">Shifted lattices</th>
    <th class="num">Edge</th><th class="num">z</th></tr></thead>
  <tbody>%(conf_rows)s</tbody>
</table></div>

<div class="col">
  <p>It survived every confound. Deep confluence is not nearer round numbers
  &mdash; it is slightly further; excluding everything within 10 points of a
  round hundred makes the effect <em>stronger</em>; a round-number map sorts
  touches the opposite way; the small scales carry it rather than proximity to
  a 2187 or 6561 level; it holds in all three eras; and resampling whole days
  puts the advantage at <b>%(dbobs)+.2fpp</b>, 95%% CI
  [%(dblo)+.2f, %(dbhi)+.2f], with every one of 2,000 resamples above zero.</p>
  <div class="note bad">
    <p><strong>Then it dissolved.</strong> Confluence depth is entangled with
    <em>which</em> level you are on: 81 = 3 &times; 27 means some percentages
    are structurally better connected than others. Holding the level fixed and
    comparing high against low confluence within it, the effect is worth
    <b>+0.15 percentage points</b>, and only 12 of 20 levels move the right
    way. It was level identity all along.</p>
  </div>
  <p>Which turns out to be a far bigger effect, and the strongest thing in this
  study. Shuffling the level labels within each trading day &mdash; keeping
  every outcome and all the intraday clustering, changing only which line each
  touch belongs to &mdash; <b>none of 2,000 permutations</b> reached the
  observed spread across the twenty levels. z = <b>%(omz)+.2f</b>.</p>
</div>

<div class="scroll"><table>
  <caption>Every Goldbach level, ranked &mdash; touch rejection rate</caption>
  <thead><tr><th class="num">Level</th><th>Name</th><th class="num">Touches</th>
    <th class="num">Rejects</th><th class="num">95%% CI by day</th>
    <th>&nbsp;</th></tr></thead>
  <tbody>%(lvl_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note key">
    <p><strong>The two lines at the top are the two that any evenly spaced grid
    has.</strong> The block boundary and the midpoint reject <b>%(svst)s</b>
    against <b>%(svgb)s</b> for the eighteen Goldbach percentages &mdash; a gap
    of <b>%(svdiff)+.2f pp</b> with a day-clustered CI of
    [%(svlo)+.2f, %(svhi)+.2f].</p>
    <p>Among the eighteen, dispersion is weak (z +3.52) and does not cohere:
    the named Goldbach Inversion Point at 17/83 is among the <em>weakest</em>
    lines on the board, and mirror pairs that the framework says are equivalent
    agree only to within their error bars.</p>
  </div>
  <p>Your instinct to trade the extreme and the equilibrium is right, and this
  is the first evidence in the study that supports any part of the framework.
  But it is the <b>exact boundary and the exact midpoint</b> doing the work,
  not the 3-point band around them: the 0 line rejects %(l0)s while the 3 line
  rejects only %(l3)s.</p>
  <p>And it still does not pay. Retests at those two lines are, if anything,
  slightly worse than at the other eighteen:</p>
</div>

<div class="scroll"><table>
  <caption>Structure entry &mdash; boundary and midpoint against everything else</caption>
  <thead><tr><th class="num">Target</th><th class="num">Break-even</th>
    <th class="num">Boundary + EQ win</th><th class="num">Other 18 win</th>
    <th class="num">Boundary + EQ EV</th><th class="num">Other 18 EV</th></tr></thead>
  <tbody>%(lt_rows)s</tbody>
</table></div>

<div class="col">
  <p>So the levels are not all alike, and the difference is not luck &mdash;
  but it lives in the grid's own geometry rather than in Goldbach's numbers,
  it is worth about two and a half percentage points of rejection, and it
  does not survive contact with a stop and a target.</p>
</div>

%(vol_html)s

%(clock_html)s

<div class="col">
<section id="sizing">
  <div class="sec-head"><h2>R=81 no longer resolves</h2>
    <span class="chip chip-warn">Watch out</span></div>
  <p>Independent of every result above, this is the finding most likely to be
  costing you money right now. A block is only usable if it is large relative to
  a candle. The 3%% zone &mdash; your 0.97&ndash;1.00 band &mdash; is a fixed 2.43
  points at R=81, forever. The candle is not fixed.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Can you actually see the zone?</caption>
  <thead><tr><th class="num">Year</th><th class="num">Median 1-min bar</th>
    <th class="num">Median RTH range</th><th class="num">81-blocks crossed / day</th>
    <th class="num">3%% zone, in candles &mdash; R=81</th>
    <th class="num">R=729</th></tr></thead>
  <tbody>%(siz_rows)s</tbody>
</table></div>

<div class="col">
  <div class="note bad">
    <p><strong>In 2026 the R=81 zone is 0.15 of one candle.</strong> You are
    marking a band two and a half points wide on a chart whose median minute bar
    is nearly sixteen points, and price crosses almost five whole blocks in a
    session. There is nothing there to react to &mdash; the zone is finer than
    the instrument's own resolution.</p>
    <p>In 2012 that same zone was nearly two candles wide and price crossed a
    third of a block a day. The framework was built when 81 meant something.</p>
  </div>
  <div class="note key">
    <p><strong>R=729 is where 81 used to sit.</strong> Its zone is 21.9 points
    &mdash; about 1.4 candles &mdash; and it covers roughly half a session's
    range. If you want the levels to be things price can plausibly respond to,
    that is the block. R=243 is the floor.</p>
  </div>
</div>

<div class="col">
<section id="cost">
  <div class="sec-head"><h2>The cost hurdle</h2>
    <span class="eyebrow">Arithmetic</span></div>
  <p>Assume %(cost).2f points round trip &mdash; roughly $4 commission plus a tick
  of slippage on the stop exit, with entries and targets as resting limits.
  Against a structure trade risking %(riskpts).1f points, that is
  <b>%(costpct).1f%%</b> of your risk gone before the trade starts.</p>
  <p>To clear it at 2R you need <b>%(need2)s</b> rather than 33.3%%. The measured
  rate is %(w2)s. The gap is not close, and it does not close under any condition
  tested.</p>
</section>

<section id="gap">
  <div class="sec-head"><h2>What this does not cover</h2>
    <span class="eyebrow">Honest limits</span></div>
  <p>Your actual entry is a confirmation signal &mdash; tCISD, an inverted
  fair-value gap, a market-structure shift. The structure entry tested here is
  the closest mechanical proxy for it, but <b>it is not your signal</b>. If the
  edge lives in the confirmation rather than in the level, nothing on this page
  can see it, and I cannot rule that out.</p>
  <p>What this page does establish is narrower and still worth having: the lines
  alone carry no edge. Any edge you have is in the reading, not the grid &mdash;
  which means it is worth knowing whether the reading survives measurement.</p>
  <div class="card">
    <p style="margin-bottom:.6rem"><b>To test that, I need one of two things:</b></p>
    <ul style="margin-bottom:0">
      <li>20&ndash;30 setups you marked yourself, with date and time, so your
      swing-marking can be compared against the detectors used here; or</li>
      <li>a log of 50&ndash;100 actual trades &mdash; entry, stop, target,
      outcome.</li>
    </ul>
  </div>
</section>

<section id="desk">
  <div class="sec-head"><h2>What to do differently</h2>
    <span class="eyebrow">Desk card</span></div>
  <ul class="check">
    <li><span class="n">01</span><span><b>Move to R=729.</b> R=81's zone is below
    the resolution of a 2026 candle. R=243 is the minimum.</span></li>
    <li><span class="n">02</span><span><b>Never chase a break.</b> You get the
    level back %(ret120)s of the time within two hours.</span></li>
    <li><span class="n">03</span><span><b>Stop at least 0.75 ATR beyond the
    line</b>, not at it. Median push-through is %(pen50).2f ATR.</span></li>
    <li><span class="n">04</span><span><b>Stop expecting the zone to add a
    filter.</b> EXT, EQ, FV and GIP perform identically, as does sweep context
    and HTF confluence.</span></li>
    <li><span class="n">05</span><span><b>Trade wider than 2R or not at
    all.</b> Every tighter ratio is below its break-even before costs.</span></li>
    <li><span class="n">06</span><span><b>If you fade one, fade a quiet
    arrival at the boundary or the EQ.</b> Small bar, low volume, at the 0 or
    50 line: 53.9%% rejection, the best combination in sixteen years of data
    &mdash; and a candidate rather than a confirmed edge.</span></li>
    <li><span class="n">07</span><span><b>Treat the levels as a map, not a
    signal.</b> They tell you where you are. They do not tell you what
    happens next.</span></li>
  </ul>
</section>
</div>

<hr class="end">
<footer>
  4,778,135 one-minute bars &middot; 4,885 trading days &middot; 2010-07-07 to 2026-08-06<br>
  CME NQ front-month, unadjusted, rolled by daily volume &middot; America/New_York with DST<br>
  every cell scored against 6 shifted-lattice nulls &middot; no look-ahead: outcomes resolve from the bar after entry
</footer>

</div>
""" % {
        "nret": n_ret, "ladder": ladder,
        "retest_rows": retest_rows, "pen_rows": pen_rows, "pctl_rows": pctl_rows,
        "st_rows": st_rows, "grid_rows": grid_rows, "cond_rows": cond_rows,
        "touch_rows": touch_rows, "pol_rows": pol_rows, "siz_rows": siz_rows,
        "pen50": pen["percentiles"]["50"],
        "pen50pts": pen["percentiles"]["50"] * ATR26,
        "atr26": ATR26,
        "stop25": pct(1 - pen["stop_survival"]["0.25"]),
        "risk": st_all[0]["risk_atr"], "riskpts": risk_pts,
        "w1": pct(st[("ALL", 1.0)]["p"]), "w2": pct(st[("ALL", 2.0)]["p"]),
        "w3": pct(st[("ALL", 3.0)]["p"]),
        "base2": pct(base2),
        "conf_rows": conf_rows, "lvl_rows": lvl_rows, "lt_rows": lt_rows,
        "nestlo": min(nest_z), "nesthi": max(nest_z),
        "dbobs": db["obs"] * 100, "dblo": db["lo"] * 100, "dbhi": db["hi"] * 100,
        "omz": om["z"],
        "svst": pct(sv["structural"], 2), "svgb": pct(sv["goldbach"], 2),
        "svdiff": sv["diff"] * 100, "svlo": sv["lo"] * 100, "svhi": sv["hi"] * 100,
        "l0": pct(next(r["reject"] for r in lvl if r["pct"] == 0), 2),
        "l3": pct(next(r["reject"] for r in lvl if r["pct"] == 3), 2),
        "paths_html": pp.html(D),
        "vol_html": pv.html(D),
        "clock_html": pc.html(D),
        "cost": COST, "costpct": COST / risk_pts * 100,
        "need2": pct((COST / risk_pts + 1) / 3.0),
        "ret120": pct(r81["rates"]["120"]),
    }

    with open(OUT, "w") as fh:
        fh.write(html)
    print("wrote %s (%.1f KB)" % (OUT, os.path.getsize(OUT) / 1024))


HEAD = """<title>Goldbach Base Rates</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>""" + CSS + pp.CSS + pc.CSS + """</style>
"""

if __name__ == "__main__":
    build()
