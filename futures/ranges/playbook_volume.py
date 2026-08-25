"""The volume and fixed-time-hold sections of the playbook.

Two late findings that change the shape of the report. Volume was missing from
the working dataset entirely -- every conditional test before it asked the
"when" question of price alone, which is the same information rearranged. And
the fixed-time hold is the cleanest formulation in the study: no stop, no
target, nothing to tune, so nothing can be manufactured.
"""


def html(D):
    q = D["quiet"]
    vol = {r["cond"]: r for r in D["volume"]}
    part = D["partition"]
    best = max(q["trade"], key=lambda r: r["ev_atr"])

    vq = [("rvol very low (<p20)", "Lowest quintile"),
          ("rvol low (p20-40)", "Second"),
          ("rvol mid (p40-60)", "Middle"),
          ("rvol high (p60-80)", "Fourth"),
          ("rvol very high (>p80)", "Highest quintile")]
    vol_rows = "".join(
        '<tr><td>%s</td><td class="num dim">%s</td><td class="num big">%s</td>'
        '<td class="num %s">%+.2fpp</td></tr>'
        % (lab, "{:,}".format(vol[k]["n_val"]), "%.1f%%" % (vol[k]["val"] * 100),
           "pos" if vol[k]["lift_val"] > 0 else "neg", vol[k]["lift_val"] * 100)
        for k, lab in vq if k in vol)

    p243 = {(r["trade"], r["hold"]): r for r in part["243"]["high"]}
    p243l = {(r["trade"], r["hold"]): r for r in part["243"]["low"]}
    prow = "".join(
        '<tr><td>%s</td><td>%s</td><td class="num dim">%s</td>'
        '<td class="num">%.1f%%</td><td class="num %s">%+.2f</td>'
        '<td class="num %s">%+.2f</td><td class="num %s">%+.2f</td>'
        '<td class="num dim">%.0f</td><td class="num dim">%.0f</td>'
        '<td class="num dim">%.1f</td><td class="num dim">%.1f</td></tr>'
        % (side, r["trade"], "{:,}".format(r["n"]), r["win"] * 100,
           "pos" if r["mean_pts"] > 0 else "neg", r["mean_pts"],
           "pos" if r["net_pts"] > 0 else "neg", r["net_pts"],
           "pos" if r["med_pts"] > 0 else "neg", r["med_pts"],
           r["best"], r["worst"], r["mfe_mean"], r["mae_mean"])
        for side, tbl in (("High", p243), ("Low", p243l))
        for r in [tbl[("fade", 60)], tbl[("follow", 60)]])

    ncells = sum(len(part[R][p]) for R in part for p in part[R])

    return """
<div class="col">
<section id="volume">
  <div class="sec-head"><h2>The input I was missing</h2>
    <span class="chip chip-warn">Corrected</span></div>
  <p>Every conditional test above asks the "when" question of price alone
  &mdash; zone, session, volatility, break depth, sweep, confluence. All of it
  derived from OHLC, which means all of it is the same information rearranged.
  <b>Volume was in the source data and was dropped when this study's working
  dataset was built.</b> Sixteen years of it. That was not a limit of the data;
  it was an error in the pipeline, and it is the obvious place for an answer to
  hide: volume is what separates a sweep that gets absorbed from one that runs.</p>
  <p>Rebuilt, the raw conditional table is the most dramatic in the study.
  Rejection rate by the touch bar's volume against its own trailing typical:</p>
</section>
</div>

<div class="scroll"><table>
  <caption>Touch rejection by relative volume &mdash; validation half, 2019&ndash;2026</caption>
  <thead><tr><th>Volume at the touch</th><th class="num">Touches</th>
    <th class="num">Rejects</th><th class="num">vs baseline</th></tr></thead>
  <tbody>%(vol_rows)s</tbody>
</table></div>

<div class="col">
  <p>Monotone across all five, and the discovery and validation lifts correlate
  at <b>+0.982</b>. A climax bar with a heavy approach rejects only 16.6%%.</p>
  <div class="note bad">
    <p><strong>Most of it is not real.</strong> Volume and touch-bar range
    correlate at 0.45, and the break test marks an immediate break when the
    touch bar itself pushes half an ATR past the level. So "high volume breaks
    levels" is largely <em>"wide bars break levels"</em>, which is close to
    tautological. Binned by range, volume adds &minus;0.02pp, +0.68pp and
    &minus;1.92pp across the middle three bins &mdash; nothing.</p>
  </div>
  <p>One cell survives, and it is the first thing in this study to clear a coin
  flip. Measured <b>purely forward</b>, with the touch bar excluded from both
  sides so no mechanical component remains:</p>
  <div class="note good">
    <p><strong>Quiet arrival &mdash; a small bar on low volume &mdash; rejects
    55.4%% of the time</strong>, against a forward baseline of 47.1%%.
    57,024 events across 4,335 days, 95%% CI [55.0, 55.9], discovery 51.9 and
    validation 56.1.</p>
    <p>The mirrored cell (small bar, <em>high</em> volume) does not validate
    &mdash; 25.5%% in discovery against 55.3%% in validation on 2,020 events
    &mdash; and is discarded rather than reported.</p>
  </div>
  <div class="note key">
    <p><strong>A number this report was quoting is wrong.</strong> The 39.3%%
    touch-rejection headline was substantially touch-bar mechanics. Excluding
    that bar the baseline is <b>47.1%%</b>, so arrivals at these levels sit much
    nearer a coin flip than "three in five push through" implied.</p>
  </div>
</div>

<div class="col">
<section id="stack">
  <div class="sec-head"><h2>Does the quiet filter belong to Goldbach?</h2>
    <span class="chip chip-bad">No &mdash; but it stacks</span></div>
</section>
  <p>No. Under the filter the true lattice rejects <b>%(qtrue)s</b> against
  <b>%(qnull)s</b> for shifted lattices. <b>The filter is worth +11.87
  percentage points; the lattice inside it is worth +0.39.</b> Price drifting
  quietly into any line tends to turn there.</p>
  <p>It does stack with the one level-identity result, though, and in the right
  direction &mdash; the two survivors of this study are roughly independent:</p>
  <ul>
    <li>Everything: <b>39.3%%</b></li>
    <li>Block boundary or midpoint: <b>41.6%%</b></li>
    <li>Quiet arrival: <b>51.0%%</b></li>
    <li><b>Quiet arrival at a boundary or midpoint: %(qgrid)s</b> (%(qgridn)s events)</li>
  </ul>
  <p>And for the first time something pays. Fading a quiet arrival with a
  <b>1.00 ATR target against a 0.50 ATR stop</b> returns <b>%(bestev)+.4f ATR</b>,
  day-clustered CI [%(bestlo)+.4f, %(besthi)+.4f] &mdash; the only interval in
  this study that excludes zero. The positive region is coherent rather than one
  lucky cell: everything with target above stop pays, everything at a quarter-ATR
  target does not.</p>
  <div class="note bad">
    <p><strong>It does not validate, and the failure is the interesting part.</strong>
    Split at 2019 the discovery half is negative for <em>every</em> bracket. By
    era the chosen bracket runs &minus;0.104, +0.008, +0.055, +0.067 &mdash; a
    monotone trend, not a stable edge.</p>
    <p>The suspect was the volume normalisation, since 2010 NQ traded 35
    contracts a minute with 28%% of minutes under ten. It is not: a range-only
    filter, ATR-normalised and era-neutral by construction, shows the same shape
    (&minus;0.225, +0.020, +0.078, +0.071). What it does show is that the early
    era selects a different animal &mdash; the filter passes <b>8.7%%</b> of
    touches in 2010&ndash;2014 against <b>2.9%%</b> since, because back then a
    one-tick bar was 0.19 ATR and "quiet" meant nothing traded at all.</p>
    <p>Positive and consistent across 2015&ndash;2026 over three consecutive
    periods and 14,575 events; strongly negative in a regime whose
    microstructure makes the filter mean something else. <b>A candidate, not an
    edge.</b> The honest test is forward.</p>
  </div>
</div>

<div class="col">
<section id="clock">
  <div class="sec-head"><h2>Trade the partition on a clock</h2>
    <span class="chip chip-bad">Flat</span></div>
  <p>The cleanest formulation in the study, and worth saying why: with a
  fixed-time exit there is no bracket to tune, no win-rate dial, and no
  entry-bar convention on the exit side. Nothing can be manufactured by choosing
  where to put a stop, because there is no stop. Price arrives at the block high
  or low from at least 1 ATR away, the trade is taken with or against it, and it
  is closed 15, 30, 45 or 60 minutes later whatever has happened.</p>
</section>
</div>

<div class="scroll"><table>
  <caption>R=243, 60-minute hold, no stop and no target</caption>
  <thead><tr><th>Partition</th><th>Trade</th><th class="num">n</th>
    <th class="num">Win</th><th class="num">Mean</th><th class="num">Net</th>
    <th class="num">Median</th><th class="num">Best</th><th class="num">Worst</th>
    <th class="num">MFE avg</th><th class="num">MAE avg</th></tr></thead>
  <tbody>%(prow)s</tbody>
</table></div>

<div class="col">
  <p><b>%(ncells)d cells across three block sizes. None has a day-clustered 95%%
  interval on net points that excludes zero.</b> Three things in the table are
  worth keeping anyway.</p>
  <div class="note key">
    <p><strong>Fading the low partition wins more often than it loses and still
    loses money.</strong> 52.2%% win rate, median <b>+1.25 points</b>, mean
    <b>&minus;0.45</b>. Many small wins, fewer bigger losses &mdash; and every
    low-partition fade cell at every block size shows that same
    positive-median, negative-mean profile. That is exactly what a system that
    feels like it works looks like from the inside.</p>
  </div>
  <p><b>The excursions say a stop would have hurt.</b> Over a 60-minute hold the
  trade averages about 40 points in your favour and 40 against, whichever side
  you take. Price swings roughly two ATR both ways inside the hour before
  settling near where it started, so any stop tighter than that is hit by noise
  on trades that finish flat. And the worst single trade reaches
  <b>&minus;1,234 points</b> &mdash; the tail a no-stop rule actually carries.</p>
  <div class="note bad">
    <p><strong>The apparent structure is drift.</strong> At R=81 over 60 minutes
    the four cells read fade-high &minus;0.78, follow-high +0.78, fade-low
    +0.12, follow-low &minus;0.12: the two <em>long</em> cells positive, the two
    <em>short</em> cells negative, exact mirrors, over a sample in which NQ rose
    eighteen-fold.</p>
    <p>Against the unconditional 60-minute drift of +0.35 points from any random
    bar the excess collapses. Against shifted lattices, all %(ncells)d cells span
    <b>&minus;1.19 to +1.19 points with a mean of +0.000</b>.</p>
  </div>
  <p>One asymmetry is not drift: arriving at the high and going long beats
  arriving at the low and going long, +1.03 against &minus;0.80 excess at
  R=243. Continuation on top of drift &mdash; and shifted lattices reproduce it,
  so it belongs to price near any line rather than to these.</p>
</div>
""" % {
        "vol_rows": vol_rows, "prow": prow, "ncells": ncells,
        "qtrue": "%.2f%%" % (q["lattice"]["quiet"] * 100),
        "qnull": "%.2f%%" % (q["lattice"]["quiet_null"] * 100),
        "qgrid": "%.1f%%" % (q["stack"]["quiet_grid"] * 100),
        "qgridn": "{:,}".format(q["stack"]["n"]),
        "bestev": best["ev_atr"], "bestlo": best["lo"], "besthi": best["hi"],
    }
