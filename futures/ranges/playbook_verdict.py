"""Second pass: the book's own plans, and the control that explains the rest.

The first pass asked whether the lattice predicts anything and answered mostly
no. This one closes two gaps that were left open.

The first gap is the source material. The book ships five named trade plans and
nine entry modules, and none of them had been run. Testing my own paraphrase of
a framework and reporting that it fails is not the same as testing the
framework, so the plans are scored here as written.

The second gap is more serious. Every null in this repo says "Goldbach adds
nothing", and that has two possible causes with opposite responses: the lattice
is empty, or the measurement is too harsh and would report anything as flat.
Until that is settled, no null here means much. So the same machinery is pointed
at six classic effects that have nothing to do with Goldbach; one of them pays,
which makes the nulls informative; and then the lattice is given the easiest
test it has ever had -- not "be an edge" but "improve an edge that exists".

The last section is the one that reframes everything above it.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CSS = """
/* ---- dumbbell comparison ---- */
.dumb{margin:1.6rem 0}
.dumb svg{display:block;width:100%;height:auto;overflow:visible}
.dumb .ax{stroke:var(--rule);stroke-width:1}
.dumb .zero{stroke:var(--rule-2);stroke-width:1;stroke-dasharray:3 3}
.dumb .conn{stroke:var(--rule-2);stroke-width:2}
.dumb .d1{fill:var(--s1)}
.dumb .d2{fill:var(--s2)}
.dumb .ring{stroke:var(--card);stroke-width:2}
.dumb .rowlab{font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  fill:var(--ink-2)}
.dumb .val{font-family:"IBM Plex Mono",monospace;font-size:9.5px;
  fill:var(--ink-3);font-variant-numeric:tabular-nums}
.dumb .tick{font-family:"IBM Plex Mono",monospace;font-size:9px;fill:var(--ink-3)}
.dumb g.mark:hover circle:not(.ring){r:7}

/* ---- max-statistic strip ---- */
.strip{margin:1.6rem 0}
.strip svg{display:block;width:100%;height:auto;overflow:visible}
.strip .band{fill:var(--sunk)}
.strip .med{stroke:var(--ink-3);stroke-width:2}
.strip .true{stroke:var(--bad);stroke-width:2.5}
.strip .lab{font-family:"IBM Plex Mono",monospace;font-size:9.5px;fill:var(--ink-3)}
.strip .lab.hot{fill:var(--bad)}

.legend{display:flex;gap:1.3rem;flex-wrap:wrap;
  font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--ink-2);
  margin:.2rem 0 1.1rem}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;
  margin-right:.42rem;vertical-align:baseline}

/* ---- shape grid: the long/short pattern in stack.py ---- */
.shape{display:grid;grid-template-columns:auto 1fr 1fr;gap:1px;
  background:var(--rule);border:1px solid var(--rule);margin:1.6rem 0}
.shape > div{background:var(--card);padding:.7rem .9rem}
.shape .hd{font-family:"IBM Plex Mono",monospace;font-size:.65rem;
  font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-3);background:var(--sunk)}
.shape .v{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;
  font-size:1.05rem;font-weight:600}
.shape .v small{display:block;font-size:.62rem;font-weight:500;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-3);margin-top:.3rem}
"""


def pct(x, d=1):
    return "%.*f%%" % (d, x * 100)


def _load(name):
    return json.load(open(os.path.join(HERE, name)))


# ---------------------------------------------------------------------------
def dumbbell(rows, x0, x1, s1_name, s2_name):
    """Two values per row on a shared axis. Rows are (label, v1, v2)."""
    w, rh, pad_l, pad_r = 700.0, 34.0, 132.0, 46.0
    h = len(rows) * rh + 34
    span = w - pad_l - pad_r
    X = lambda v: pad_l + (v - x0) / (x1 - x0) * span

    ticks = []
    t = x0
    while t <= x1 + 1e-9:
        ticks.append(t)
        t += 0.5
    tick_svg = "".join(
        '<line x1="%.1f" y1="14" x2="%.1f" y2="%.1f" class="%s"/>'
        '<text x="%.1f" y="8" text-anchor="middle" class="tick">%+.1f</text>'
        % (X(v), X(v), h - 12, "zero" if abs(v) < 1e-9 else "ax", X(v), v)
        for v in ticks)

    body = []
    for i, (lab, v1, v2) in enumerate(rows):
        y = 26 + i * rh
        lo, hi = (v1, v2) if v1 <= v2 else (v2, v1)
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="end" class="rowlab">%s</text>'
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="conn"/>'
            % (pad_l - 12, y + 4, lab, X(lo), y, X(hi), y))
        for v, cls, nm in ((v2, "d2", s2_name), (v1, "d1", s1_name)):
            body.append(
                '<g class="mark"><title>%s, %s: %+.3f points per trade</title>'
                '<circle cx="%.1f" cy="%.1f" r="5.5" class="ring"/>'
                '<circle cx="%.1f" cy="%.1f" r="5.5" class="%s"/></g>'
                % (lab, nm, v, X(v), y, X(v), y, cls))
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="end" class="val">%+.2f</text>'
            '<text x="%.1f" y="%.1f" class="val">%+.2f</text>'
            % (X(lo) - 10, y + 3.5, lo, X(hi) + 10, y + 3.5, hi))

    return ('<div class="dumb"><div class="legend">'
            '<span><i style="background:var(--s1)"></i>%s</span>'
            '<span><i style="background:var(--s2)"></i>%s</span></div>'
            '<svg viewBox="0 0 %d %d" role="img" aria-label="%s against %s, '
            'net points per trade">%s%s</svg></div>'
            % (s1_name, s2_name, int(w), int(h), s1_name, s2_name,
               tick_svg, "".join(body)))


def maxstrip(true, med, p95, hi):
    """The real best cell against the distribution of random-lattice best cells.

    The whole point is that `true` and `med` land within a tenth of a point of
    each other, which is four pixels apart at this width. Two centred labels
    there overprint, so the pair gets one annotation on a leader line and the
    distribution keeps the axis.
    """
    w, h = 700.0, 104.0
    pad = 14.0
    span = w - pad * 2
    X = lambda v: pad + v / hi * span
    xm = (X(true) + X(med)) / 2.0
    return (
        '<div class="strip"><svg viewBox="0 0 %d %d" role="img" '
        'aria-label="the best real cell, plus %.2f, sits at the median of the '
        'random-lattice distribution, plus %.2f">'
        '<rect x="%.1f" y="54" width="%.1f" height="20" rx="2" class="band"/>'
        '<text x="%.1f" y="90" class="lab">random-lattice best cells</text>'
        '<text x="%.1f" y="90" text-anchor="end" class="lab">95th pct %+.2f</text>'
        '<line x1="%.1f" y1="48" x2="%.1f" y2="80" class="med"/>'
        '<line x1="%.1f" y1="48" x2="%.1f" y2="80" class="true"/>'
        '<line x1="%.1f" y1="44" x2="%.1f" y2="30" class="med"/>'
        '<text x="%.1f" y="24" text-anchor="middle" class="lab hot">'
        'best real cell %+.2f</text>'
        '<text x="%.1f" y="12" text-anchor="middle" class="lab">'
        'median of the random lattices %+.2f</text>'
        '</svg></div>'
        % (int(w), int(h), true, med,
           X(0), X(p95) - X(0),
           pad, w - pad, p95,
           X(med), X(med),
           X(true), X(true),
           xm, xm,
           xm, true,
           xm, med))


# ---------------------------------------------------------------------------
def html():
    plans = _load("plans.json")["243"]
    entry = _load("entry.json")
    closes = _load("closes.json")["243"]
    sess = _load("sessions.json")["RTH 09:30-16:00"]["243"]
    bench = _load("benchmark.json")
    ogb = _load("overnight_gb2.json")
    stack = _load("stack.json")
    drift = _load("drift.json")

    # ---- the five plans, scored symmetrically ---------------------------
    order = ["LIQUIDITY", "FLOW CONTINUATION", "FLOW REJECTION", "REBALANCE",
             "EINSTEIN"]
    plan_rows = "".join(
        '<tr%s><td><b>%s</b></td><td class="num dim">%s</td>'
        '<td class="num dim">%s</td><td class="num big">%s</td>'
        '<td class="num dim">%s</td><td class="num %s">%+.2f</td>'
        '<td class="num dim">%.0f pts</td></tr>'
        % (' class="hi"' if k == "LIQUIDITY" else "", k.title(),
           "{:,}".format(plans[k]["n"]), pct(plans[k]["literal"]),
           pct(plans[k]["sym"]), pct(plans[k]["null"]),
           "pos" if plans[k]["z"] > 0 else "neg", plans[k]["z"],
           plans[k]["mae_med"])
        for k in order)

    # ---- entry modules ---------------------------------------------------
    mods = ["immediate", "htf3", "htf5", "htf15", "htf30", "mss", "cisd",
            "ifvg"]
    ent_rows = []
    n_both = 0
    for R in ("243", "729"):
        for m in mods:
            for mode in ("reversal", "continuation"):
                hi_k = "%s|high|%s" % (m, mode)
                lo_k = "%s|low|%s" % (m, mode)
                if hi_k not in entry[R] or lo_k not in entry[R]:
                    continue
                a, b = entry[R][hi_k], entry[R][lo_k]
                if a["ev_r"] > 0 and b["ev_r"] > 0:
                    n_both += 1
                if R == "243" and mode == "reversal":
                    ent_rows.append(
                        '<tr><td>%s</td><td class="num dim">%s</td>'
                        '<td class="num">%s</td><td class="num %s">%+.3fR</td>'
                        '<td class="num %s">%+.3fR</td></tr>'
                        % (m, "{:,}".format(a["n"] + b["n"]),
                           pct((a["win"] * a["n"] + b["win"] * b["n"])
                               / (a["n"] + b["n"])),
                           "pos" if a["ev_r"] > 0 else "neg", a["ev_r"],
                           "pos" if b["ev_r"] > 0 else "neg", b["ev_r"]))
    ent_rows = "".join(ent_rows)

    # ---- HTF close spread -----------------------------------------------
    cl_rows = "".join(
        '<tr%s><td class="num">%s min</td>'
        '<td class="num big">%+.1fpp</td><td class="num dim">%+.1fpp</td>'
        '<td class="num">%s</td><td class="num">%s</td></tr>'
        % (' class="hi"' if tf == "30" else "", tf,
           closes["%s|spread|high|eq" % tf]["true"] * 100,
           closes["%s|spread|high|eq" % tf]["null"] * 100,
           pct(closes["%s|high|eq|closed_inside" % tf]["p_back"]),
           pct(closes["%s|high|eq|closed_through" % tf]["p_back"]))
        for tf in ("3", "5", "15", "30"))

    # ---- benchmark -------------------------------------------------------
    bn_order = ["overnight", "rth_long", "orb", "pdh_pdl", "gap_follow",
                "gap_fade"]
    bn_rows = "".join(
        '<tr%s><td><b>%s</b></td><td class="num dim">%s</td>'
        '<td class="num">%s</td><td class="num big %s">%+.2f</td>'
        '<td class="num dim">%s</td><td class="num">%.2f</td>'
        '<td class="num dim">[%+.2f, %+.2f]</td></tr>'
        % (' class="hi"' if k == "overnight" else "",
           k.replace("_", " "), "{:,}".format(bench[k]["n"]),
           pct(bench[k]["win"]),
           "pos" if bench[k]["lo"] > 0 else "", bench[k]["net"],
           "{:+,.0f}".format(bench[k]["total"]), bench[k]["pf"],
           bench[k]["lo"], bench[k]["hi"])
        for k in bn_order)

    # ---- overnight conditioned on block position ------------------------
    ms = ogb["maxstat"]
    gb_rows = "".join(
        '<tr%s><td class="num">%s</td><td>%s</td>'
        '<td class="num dim">%s</td><td class="num big">%+.2f</td>'
        '<td class="num dim">[%+.2f, %+.2f]</td>'
        '<td class="num %s">%+.2f</td><td class="num %s">%+.2f</td></tr>'
        % (' class="hi"' if (R, band) == ("729", "40-60") else "", R, band,
           "{:,}".format(ogb[R][band]["n"]), ogb[R][band]["mean"],
           ogb[R][band]["ep_lo"], ogb[R][band]["ep_hi"],
           "pos" if ogb[R][band].get("disc_rel", 0) > 0 else "neg",
           ogb[R][band].get("disc_rel", float("nan")),
           "pos" if ogb[R][band].get("val_rel", 0) > 0 else "neg",
           ogb[R][band].get("val_rel", float("nan")))
        for R in ("729", "2187")
        for band in ("0-10", "10-25", "25-40", "40-60", "60-75", "75-90",
                     "90-100")
        if band in ogb[R])

    # ---- the shape of the stack table -----------------------------------
    def sm(setups):
        v = [stack["243|all|%s|%s" % (t, s)]["true"]
             for t in ("0.75/1.50", "1.00/1.00", "0.75/2.25") for s in setups]
        return sum(v) / len(v)

    shape = (
        '<div class="shape">'
        '<div class="hd"></div><div class="hd">Long setups</div>'
        '<div class="hd">Short setups</div>'
        '<div class="hd">Break through</div>'
        '<div><span class="v pos">%+.2f<small>break up</small></span></div>'
        '<div><span class="v neg">%+.2f<small>break down</small></span></div>'
        '<div class="hd">Reject at line</div>'
        '<div><span class="v pos">%+.2f<small>reject down</small></span></div>'
        '<div><span class="v neg">%+.2f<small>reject up</small></span></div>'
        '</div>'
        % (sm(["break_up"]), sm(["break_dn"]), sm(["reject_dn"]),
           sm(["reject_up"])))

    # ---- drift dumbbell --------------------------------------------------
    drows = []
    for tag in ("0.75/1.50", "1.00/1.00", "0.75/2.25"):
        for side, keys in (("long", ["break_up", "reject_dn"]),
                           ("short", ["break_dn", "reject_up"])):
            sig = sum(stack["243|all|%s|%s" % (tag, k)]["true"]
                      for k in keys) / len(keys)
            ran = drift["%s|%s" % (tag, side)]["mean"]
            drows.append(("%s  %s" % (tag, side), sig, ran))
    chart = dumbbell(drows, -1.5, 1.0, "At a Goldbach level", "Random time")

    lift_long = sum(r[1] - r[2] for r in drows[0::2]) / 3.0
    lift_short = sum(r[1] - r[2] for r in drows[1::2]) / 3.0

    return """
<section id="plans">
  <div class="sec-head"><h2>The book's five plans, as written</h2>
    <span class="eyebrow">Source material</span></div>
  <p>Everything above tests my paraphrase of the framework. That is not the same
  as testing the framework, so the five named plans are scored here exactly as
  the book states them, on R=243.</p>
  <p>The <b>literal</b> column is the book's own criterion. It is not a
  probability you can trade: <span class="chip chip-warn">Rebalance</span> scores
  100%% because the plan sets no invalidation, and over a full day price always
  covers the 18%% of a block between the [41] and [59] lines. A rule that cannot
  lose has not been tested. So each plan is re-scored <b>symmetric</b> &mdash;
  the target raced against an equally distant adverse level &mdash; which is the
  weakest assumption that still makes the number mean something.</p>
  <div class="scroll"><table>
    <caption>five plans, R=243, symmetric race against 20 shifted lattices</caption>
    <thead><tr><th>Plan</th><th class="num">n</th><th class="num">Literal</th>
    <th class="num">Symmetric</th><th class="num">Null</th><th class="num">z</th>
    <th class="num">Median heat</th></tr></thead>
    <tbody>%(plan_rows)s</tbody>
  </table></div>
  <div class="note"><p><strong>Liquidity is the only plan that clears a coin
  flip</strong> &mdash; 59.8%% symmetric against roughly 50%% for the other four
  &mdash; and it is also the only plan in the book that states its own
  invalidation: price through the external GIP [17-83] kills the trade. That is
  not a coincidence. The invalidation is what puts the target close enough to
  reach, and it shows in the heat column, 23 points against 39 to 97.</p>
  <p>But read the null column before getting attached to it. <strong>Even
  Liquidity sits fractionally below its own shifted lattice</strong>, 59.8%%
  against 60.4%%. The 59.8%% is real and it is the best number on this page; it
  comes from the plan's geometry &mdash; a near target and a far stop &mdash;
  and not from where the lines are. Every one of the five scores its own null to
  within about a point.</p></div>
</section>

<section id="modules">
  <div class="sec-head"><h2>Nine ways to enter, none of them positive</h2>
    <span class="eyebrow">Entry modules</span></div>
  <p>Boundary touch, then an entry trigger, then take profit at equilibrium.
  Eight trigger modules &times; two directions &times; two scales &times; both
  sides of the block. The requirement is the same one that has killed every
  candidate on this page: a real effect at a line appears at the block high
  <em>and</em> the block low, because they are mirror images of each other.</p>
  <div class="scroll"><table>
    <caption>R=243 reversal, expectancy in R, block high vs block low</caption>
    <thead><tr><th>Trigger</th><th class="num">n</th><th class="num">Win</th>
    <th class="num">EV at high</th><th class="num">EV at low</th></tr></thead>
    <tbody>%(ent_rows)s</tbody>
  </table></div>
  <p><b>%(n_both)d of 32 pairs</b> were positive on both sides. Not one.</p>
  <div class="note bad"><p><strong>One number here was wrong before it was
  right.</strong> An early run reported average R:R of 635 on a 0.6%% win rate.
  The stop was structural &mdash; beyond the swing extreme &mdash; with no floor
  under it, so on bars where the extreme sat almost at the entry the risk went
  to nearly zero and the ratio exploded. A 0.50 ATR floor on risk removes it,
  and the summary is a median rather than a mean.</p></div>
</section>

<section id="htfclose">
  <div class="sec-head"><h2>The thirty-minute close</h2>
    <span class="eyebrow">Largest measured spread</span></div>
  <p>Price reaches the block boundary. Does the candle close back inside, or
  through? This produced the biggest spread anywhere in the study, and it grows
  monotonically with the timeframe &mdash; which is exactly what a real
  confirmation effect should do.</p>
  <div class="scroll"><table>
    <caption>P(returns to equilibrium) split by where the candle closed, R=243 block high</caption>
    <thead><tr><th class="num">Timeframe</th><th class="num">Spread</th>
    <th class="num">Same, shifted</th><th class="num">Closed inside</th>
    <th class="num">Closed through</th></tr></thead>
    <tbody>%(cl_rows)s</tbody>
  </table></div>
  <div class="note"><p>Read the second column against the third. The spread is
  real and it is large. It is also <strong>the same size on a lattice with no
  Goldbach content in it at all</strong>. What the thirty-minute close tells you
  is whether a push has been rejected &mdash; a fact about the candle, available
  at any line you care to draw. The block boundary contributes
  %(clgap)+.1f percentage points of it.</p></div>
</section>

<section id="benchmark">
  <div class="sec-head"><h2>Can this framework find an edge at all?</h2>
    <span class="eyebrow">Control</span></div>
  <p>Every null on this page says Goldbach adds nothing, and there are two
  reasons that could happen. Either the lattice is empty, or the measurement
  &mdash; the cost model, the entry-bar convention, the day-clustered intervals
  &mdash; is harsh enough to report <em>anything</em> as flat. Those demand
  opposite responses, and until it is settled none of the nulls above mean
  much.</p>
  <p>So the identical machinery is pointed at six classic effects with no level
  in them anywhere.</p>
  <div class="scroll"><table>
    <caption>net points per trade after 0.45 cost, 95%% interval clustered by day</caption>
    <thead><tr><th>Strategy</th><th class="num">n</th><th class="num">Win</th>
    <th class="num">Net</th><th class="num">Total</th><th class="num">PF</th>
    <th class="num">95%% CI</th></tr></thead>
    <tbody>%(bn_rows)s</tbody>
  </table></div>
  <div class="note good"><p><strong>The overnight session clears, and holds in
  both halves</strong> &mdash; %(odisc)+.2f before 2019, %(oval)+.2f after, on
  %(on)s nights. Same cost, same intervals, same execution rules that returned
  flat on every lattice test. <strong>The nulls above are informative, not
  artifacts of over-harsh testing.</strong></p></div>
  <div class="note bad"><p><strong>The first version of this table was
  wrong.</strong> Prior-day high/low reported +27.20 a day, which is not a
  plausible number for a rule that simple. 42%% of sessions <em>open</em> already
  beyond the prior day's level, by a median of 26 points &mdash; price was never
  there during the session, so a fill at the level is impossible, and crediting
  one books the overnight gap as instant profit. Filling at
  <code>max(level, bar open)</code> collapses it to the %(pdh)+.2f above, with an
  interval straddling zero.</p></div>
</section>

<section id="overnightgb">
  <div class="sec-head"><h2>Does the lattice improve the one thing that pays?</h2>
    <span class="eyebrow">The easiest test</span></div>
  <p>This is the fair question the lattice had never been asked. Not <em>be an
  edge from nothing</em>, which is what every test above demanded, but
  <em>improve an edge that already exists</em>. If the framework is a map of
  where price sits in a dealing range, then holding overnight from the range
  middle should differ from holding from its edge. The conditioning value is the
  block position of the RTH close, which is the entry price and is known before
  the trade.</p>
  <div class="scroll"><table>
    <caption>overnight net per night by block position &middot; disc and val are relative to that era's own baseline</caption>
    <thead><tr><th class="num">R</th><th>Block position</th>
    <th class="num">Nights</th><th class="num">Net</th><th class="num">95%% CI</th>
    <th class="num">Disc</th><th class="num">Val</th></tr></thead>
    <tbody>%(gb_rows)s</tbody>
  </table></div>
  <p>Two of twenty-one cells clear the unconditional lower bound. R=729
  equilibrium pays %(bestnet)+.2f a night against %(uncond)+.2f for the trade taken blind. For
  about ten minutes that looked like the answer.</p>
  <h3>Then price the search</h3>
  <p>Twenty-one cells were scanned. One false positive at 95%% is the
  <em>expected</em> count, so the honest test is a max statistic: run the same
  twenty-one-cell search on 400 random lattice offsets, take the best cell each
  one finds, and see where the real best cell falls in that distribution.</p>
  %(strip)s
  <div class="note bad"><p>The best real cell sits <strong>at the median of what
  a random grid produces</strong>. <code>p = %(msp).3f</code>. Scanning
  twenty-one bands across three grids manufactures a ten-point spread by
  construction; Goldbach produced a perfectly average one.</p></div>
  <p>The era columns say the same thing from the other side. The winning cell is
  %(bdisc)+.2f relative to its own period before 2019 and %(bval)+.2f after &mdash; it is not
  finding a block position, it is riding the post-2019 regime shift in the
  overnight edge itself.</p>
  <div class="note"><p>One suspicion turned out to be unfounded and is recorded
  because it changed nothing. The lattice is anchored to absolute price, so a
  R=729 band could plausibly be a multi-week regime rather than a nightly draw,
  which would make every interval here fiction. It is not: membership runs are a
  median of one night, and clustering by episode instead of by day moves the
  bounds by less than a point.</p></div>
</section>

<section id="drift">
  <div class="sec-head"><h2>What the win rates were actually measuring</h2>
    <span class="eyebrow">Resolution</span></div>
  <p>Two filters on this page measured large: the thirty-minute close at
  %(clspread)+.1f percentage points of spread, and quiet arrival at +11.9. Both were only
  ever scored as <em>directional probabilities</em> &mdash; does price reach A
  before B. Neither was ever converted into points with a real stop, and a 61%%
  hit rate is worthless if the winners are half the size of the losers.</p>
  <p>So: stack them, and trade them. A thirty-minute bar straddling a Goldbach
  level, split on where it closed, entered on the next minute with an ATR stop
  and target. Four setups &times; four filters &times; three stop/target pairs
  &times; two scales. <b>Ninety-six cells. None paid on both sides.</b></p>
  <p>But the table had one shape, and it had it everywhere &mdash; under every
  filter, every ratio, both scales:</p>
  %(shape)s
  <p>Never mirror images. Always split by <em>direction</em>. The quiet filter
  did not change the pattern, it doubled it &mdash; quiet bars resolve slowly, so
  they hold longer. That is not what a level looks like. That is what drift
  looks like.</p>
  <h3>The control</h3>
  <p>Same geometry, same horizon, same ATR scaling, fired at 30,000
  <b>random times with no level involved.</b></p>
  %(chart)s
  <div class="note bad"><p>The level is worth <strong>%(liftl)+.2f points to a
  long and %(lifts)+.2f to a short</strong> &mdash; call it %(liftnet)+.2f a
  trade on average, inside the noise and a fraction of the commission. The
  1.1-point gap between the two sides is the index risk premium seen through a
  stop.</p>
  <p><strong>Every high win rate in this study was measuring that gap</strong>,
  through a statistic that cannot see position size.</p></div>
</section>
""" % {
        "plan_rows": plan_rows,
        "ent_rows": ent_rows,
        "n_both": n_both,
        "cl_rows": cl_rows,
        "clgap": (closes["30|spread|high|eq"]["true"]
                  - closes["30|spread|high|eq"]["null"]) * 100,
        "clspread": closes["30|spread|high|eq"]["true"] * 100,
        "bn_rows": bn_rows,
        "odisc": bench["overnight"]["disc"], "oval": bench["overnight"]["val"],
        "on": "{:,}".format(bench["overnight"]["n"]),
        "gb_rows": gb_rows,
        "strip": maxstrip(ms["true"], ms["null_med"], ms["null_p95"], 14.0),
        "msp": ms["p"],
        "shape": shape, "chart": chart,
        "liftl": lift_long, "lifts": lift_short,
        "liftnet": (lift_long + lift_short) / 2.0,
        "pdh": bench["pdh_pdl"]["net"],
        "bestnet": ogb["729"]["40-60"]["mean"],
        "uncond": ogb["uncond"],
        "bdisc": ogb["729"]["40-60"]["disc_rel"],
        "bval": ogb["729"]["40-60"]["val_rel"],
    }
