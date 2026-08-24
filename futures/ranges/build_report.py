"""Build the GB-Ranges backtest report from ALL.json."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "ALL.json")))
OUT = os.path.join(HERE, "..", "gb-ranges-report.html")

LEVEL_NAME = {
    0: "range extreme", 3: "internal rng liq", 7: "LLOD", 11: "internal rng liq",
    17: "GIP", 23: "flow outer", 29: "flow middle", 35: "flow inner",
    41: "ext rebalance liq", 47: "int rebalance liq", 50: "equilibrium",
    53: "int rebalance liq", 59: "ext rebalance liq", 65: "flow inner",
    71: "flow middle", 77: "flow outer", 83: "GIP", 89: "internal rng liq",
    93: "LLOD", 97: "internal rng liq",
}
LAYER_OF = {
    0: "liq", 3: "liq", 7: "liq", 11: "liq", 89: "liq", 93: "liq", 97: "liq",
    17: "gip", 83: "gip",
    23: "flow", 29: "flow", 35: "flow", 65: "flow", 71: "flow", 77: "flow",
    41: "reb", 47: "reb", 50: "reb", 53: "reb", 59: "reb",
}
LAYER_LABEL = {"liq": "liquidity", "flow": "flow", "reb": "rebalance", "gip": "GIP"}


# ---------------------------------------------------------------- graphics
def phase_strip(nulls, true_val, width=560, height=54):
    """Rug plot: where the true lattice sits among its 59 shifted twins."""
    lo = min(min(nulls), true_val)
    hi = max(max(nulls), true_val)
    pad = (hi - lo) * 0.18 or 1e-6
    lo, hi = lo - pad, hi + pad
    span = hi - lo

    def x(v):
        return 26 + (v - lo) / span * (width - 52)

    mu = sum(nulls) / len(nulls)
    var = sum((v - mu) ** 2 for v in nulls) / (len(nulls) - 1)
    sd = var ** 0.5
    band = ""
    if sd > 0:
        x1, x2 = x(mu - 3 * sd), x(mu + 3 * sd)
        x1, x2 = max(26, x1), min(width - 26, x2)
        band = ('<rect x="%.1f" y="14" width="%.1f" height="24" rx="2" '
                'class="strip-band"/>' % (x1, max(0.0, x2 - x1)))

    ticks = "".join(
        '<line x1="%.1f" y1="18" x2="%.1f" y2="34" class="strip-null"/>' % (x(v), x(v))
        for v in nulls
    )
    tx = x(true_val)
    marker = ('<line x1="%.1f" y1="10" x2="%.1f" y2="42" class="strip-true"/>'
              '<circle cx="%.1f" cy="10" r="3" class="strip-dot"/>' % (tx, tx, tx))
    axis = '<line x1="26" y1="46" x2="%d" y2="46" class="strip-axis"/>' % (width - 26)
    labs = ('<text x="26" y="53" class="strip-lab">%.4f</text>'
            '<text x="%d" y="53" class="strip-lab" text-anchor="end">%.4f</text>'
            % (lo, width - 26, hi))
    return ('<svg viewBox="0 0 %d %d" class="strip" role="img" '
            'aria-label="true lattice against 59 shifted lattices">%s%s%s%s%s</svg>'
            % (width, height, band, ticks, marker, axis, labs))


def sigma_bar(z, width=150, cap=4.0):
    """Small signed sigma indicator with the +/-3 threshold marked."""
    zc = max(-cap, min(cap, z))
    mid = width / 2
    x = mid + zc / cap * (mid - 8)
    thr = mid + 3.0 / cap * (mid - 8)
    thr2 = mid - 3.0 / cap * (mid - 8)
    cls = "sig-hit" if abs(z) >= 3 else "sig-noise"
    return ('<svg viewBox="0 0 %d 18" class="sigbar" role="img" aria-label="z = %.2f">'
            '<rect x="%.1f" y="6" width="%.1f" height="6" rx="3" class="sig-track"/>'
            '<line x1="%.1f" y1="3" x2="%.1f" y2="15" class="sig-thr"/>'
            '<line x1="%.1f" y1="3" x2="%.1f" y2="15" class="sig-thr"/>'
            '<line x1="%.1f" y1="2" x2="%.1f" y2="16" class="sig-zero"/>'
            '<circle cx="%.1f" cy="9" r="4" class="%s"/></svg>'
            % (width, z, 8.0, width - 16.0, thr, thr, thr2, thr2, mid, mid, x, cls))


def grid_heat(cells):
    """48-cell robustness grid, coloured by |z| against the phase null."""
    Rs = [81, 243, 729, 2187]
    ks = [3, 5, 10, 20]
    tols = [0.25, 0.5, 1.0]
    cw, ch, gx, gy = 44, 26, 74, 40
    W = gx + len(ks) * len(tols) * cw + 16
    H = gy + len(Rs) * ch + 34
    parts = []
    for ti, k in enumerate(ks):
        cx = gx + ti * len(tols) * cw + len(tols) * cw / 2
        parts.append('<text x="%.1f" y="20" class="hm-hd" text-anchor="middle">k=%d</text>'
                     % (cx, k))
        for tj, tol in enumerate(tols):
            x = gx + (ti * len(tols) + tj) * cw + cw / 2
            parts.append('<text x="%.1f" y="34" class="hm-sub" text-anchor="middle">%.2f</text>'
                         % (x, tol))
    for ri, R in enumerate(Rs):
        y = gy + ri * ch
        parts.append('<text x="64" y="%.1f" class="hm-hd" text-anchor="end">%d</text>'
                     % (y + 17, R))
        for ti, k in enumerate(ks):
            for tj, tol in enumerate(tols):
                c = next((c for c in cells if c["R"] == R and c["k"] == k
                          and abs(c["tol"] - tol) < 1e-9), None)
                if c is None:
                    continue
                z = c["z_phase"]
                x = gx + (ti * len(tols) + tj) * cw
                op = min(abs(z) / 3.0, 1.0) * 0.8 + 0.06
                cls = "hm-pos" if z >= 0 else "hm-neg"
                parts.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="2" '
                             'class="%s" opacity="%.3f"/>'
                             % (x + 1, y + 1, cw - 2, ch - 2, cls, op))
                parts.append('<text x="%.1f" y="%.1f" class="hm-val" text-anchor="middle">'
                             '%+.1f</text>' % (x + cw / 2, y + 17, z))
    parts.append('<text x="74" y="%d" class="hm-sub">block size R (rows) &#183; '
                 'swing strength k &#183; tolerance in pp (columns) &#183; '
                 'value is z against the phase null</text>' % (H - 8))
    return ('<svg viewBox="0 0 %d %d" class="heat" role="img" '
            'aria-label="48-cell robustness grid">%s</svg>' % (W, H, "".join(parts)))


# ---------------------------------------------------------------- fragments
def verdict_row(label, detail, z):
    return ('<tr><th scope="row">%s</th><td class="dim">%s</td>'
            '<td class="num">%+.2f</td><td>%s</td></tr>'
            % (label, detail, z, sigma_bar(z)))


def build():
    p = D["h1"]["primary"]
    grid = D["h1"]["grid"]
    rx = D["reaction"]
    st = D["structure"]
    pw = D["power"]
    meta = D["meta"]

    allz = [z for c in grid for z in (c["z_occ"], c["z_phase"], c["z_levelset"])]
    grid_max = max(allz, key=abs)
    grid_over3 = sum(1 for z in allz if abs(z) > 3)
    # the pre-registration required clearing +3 against EVERY null, not any one
    grid_survive = sum(1 for c in grid
                       if min(c["z_occ"], c["z_phase"], c["z_levelset"]) > 3)
    round_best = max(st["round"], key=lambda r: abs(r["z_phase"]))

    # --- the three tests added after the framework was described as traded ---
    resp = D["respect"]
    ms = D["majorswing"]
    su = D["setup"]
    ms_z = [r["z"] for r in ms]
    su_win = sorted(x["win"] for x in su)
    su_ev = sorted(x["ev_R"] for x in su)
    su_best = max(su, key=lambda x: x["z"])
    ms_ext = [r for r in ms if r["R"] == 2187 and r["zone"] == "EXT_97_100"]
    ms_r81 = [r for r in ms if r["R"] == 81]

    resp_rows = "".join(
        '<tr><td class="num">%d</td><td class="num">%s</td>'
        '<td class="num">%.1f pts</td><td class="num">%.1f pts</td>'
        '<td class="num">%+.1f%%</td><td class="num">%+.2f</td></tr>'
        % (d["R"], "{:,}".format(d["n"]), d["median_pen"]["true"] * d["R"],
           d["median_pen"]["null_mean"] * d["R"],
           (d["median_pen"]["true"] / d["median_pen"]["null_mean"] - 1) * 100,
           d["median_pen"]["z_signed"])
        for d in resp)

    ms_rows = "".join(
        '<tr><td>%s</td><td class="num dim">%s</td><td class="num">%.4f</td>'
        '<td class="num">%.4f</td><td class="num">%+.1f%%</td>'
        '<td class="num">%.4f</td><td class="num">%+.2f</td></tr>'
        % (r["swing"], "{:,}".format(r["n"]), r["rate"], r["null_mean"],
           (r["rate"] / r["null_mean"] - 1) * 100, r["occ_rate"], r["z_occ_adj"])
        for r in ms_ext)

    # headline verdict table
    rx60 = next(r for r in rx if r["R"] == 2187 and r["M"] == 60)
    sweep2187 = next(s for s in st["sweep"] if s["R"] == 2187)
    dwell_reb = next(d for d in st["dwell"] if d["R"] == 2187 and d["layer"] == "rebalance")
    dwell_best = max(st["dwell"], key=lambda d: abs(d["z_phase"]))

    strongest = max(grid, key=lambda c: max(abs(c["z_occ"]), abs(c["z_phase"]),
                                            abs(c["z_levelset"])))
    vrows = "".join([
        verdict_row("Swings land on levels",
                    "%s swings, R=2187, tol &#177;0.5pp" % "{:,}".format(p["n_swings"]),
                    p["z_phase"]),
        verdict_row("&#8230; best of all 60 phases",
                    "phase-agnostic &#8212; does any lattice origin work?", p["z_adjmax"]),
        verdict_row("Levels produce a reaction",
                    "%s deduplicated touches, 60&#8209;minute horizon"
                    % "{:,}".format(rx60["n"]), rx60["z_phase"]),
        verdict_row("Block edges sweep and reject",
                    "%s boundary crossings, R=2187" % "{:,}".format(sweep2187["n"]),
                    sweep2187["z_phase"]),
        verdict_row("Price lingers in rebalance",
                    "share of closes inside [41&#8211;59]", dwell_reb["z_phase"]),
        verdict_row("Round decimals, same test",
                    "the control &#8212; every %d points" % round_best["R"],
                    round_best["z_phase"]),
        verdict_row("Strongest of %d grid tests" % len(allz),
                    "R=%d, k=%d, tol %.2fpp &#8212; but fails the other two nulls"
                    % (strongest["R"], strongest["k"], strongest["tol"]), grid_max),
    ])

    # per-level reaction table, 60-minute horizon, both block sizes
    r729 = next(r for r in rx if r["R"] == 729 and r["M"] == 60)
    lvl_rows = []
    for pct in [0, 3, 7, 11, 17, 23, 29, 35, 41, 47, 50, 53, 59, 65, 71, 77, 83, 89, 93, 97]:
        a = r729["by_level"].get(str(pct), {})
        b = rx60["by_level"].get(str(pct), {})
        ra = a.get("reject_rate")
        rb = b.get("reject_rate")
        lay = LAYER_OF[pct]
        lvl_rows.append(
            '<tr><td class="lv"><span class="chip chip-%s">%d</span></td>'
            '<td class="dim">%s</td>'
            '<td class="num">%s</td><td class="num">%s</td>'
            '<td class="num">%s</td><td class="num">%s</td></tr>'
            % (lay, pct, LEVEL_NAME[pct],
               "%d" % a.get("n", 0), "%.3f" % ra if ra is not None else "&#8212;",
               "%d" % b.get("n", 0), "%.3f" % rb if rb is not None else "&#8212;")
        )
    lvl_rows = "".join(lvl_rows)

    # reaction summary across horizons
    rx_rows = "".join(
        '<tr><td class="num">%d</td><td class="num">%d min</td>'
        '<td class="num">%s</td><td class="num">%.4f</td><td class="num">%.4f</td>'
        '<td class="num">%+.2f</td><td class="num dim">%d/60</td></tr>'
        % (r["R"], r["M"], "{:,}".format(r["n"]), r["reject_rate"],
           r["null_mean"], r["z_phase"], r["rank"])
        for r in rx
    )

    dwell_rows = "".join(
        '<tr><td class="num">%d</td><td><span class="chip chip-%s">%s</span></td>'
        '<td class="num dim">%.0f%%</td><td class="num">%.4f</td>'
        '<td class="num">%.4f</td><td class="num">%+.2f</td></tr>'
        % (d["R"],
           {"liquidity_lo": "liq", "liquidity_hi": "liq", "flow_lo": "flow",
            "flow_hi": "flow", "rebalance": "reb"}[d["layer"]],
           d["layer"].replace("_", " "), d["width"] * 100,
           d["dwell"], d["null_mean"], d["z_phase"])
        for d in st["dwell"]
    )

    sweep_rows = "".join(
        '<tr><td class="num">%d</td><td class="num">%s</td><td class="num">%.4f</td>'
        '<td class="num">%.4f</td><td class="num">%+.2f</td></tr>'
        % (s["R"], "{:,}".format(s["n"]), s["rate"], s["null_mean"], s["z_phase"])
        for s in st["sweep"]
    )
    round_rows = "".join(
        '<tr><td class="num">every %d pts</td><td class="num">%s</td>'
        '<td class="num">%.4f</td><td class="num">%.4f</td><td class="num">%+.2f</td></tr>'
        % (r["R"], "{:,}".format(r["n"]), r["rate"], r["null_mean"], r["z_phase"])
        for r in st["round"]
    )

    pw_h1 = "".join(
        '<tr><td class="num">%.1f%%</td><td class="num">%.4f</td>'
        '<td class="num">%+.2f</td><td>%s</td></tr>'
        % (r["frac"] * 100, r["rate"], r["z_phase"], sigma_bar(r["z_phase"]))
        for r in pw["h1"]
    )
    pw_rx = "".join(
        '<tr><td class="num">+%.1f pp</td><td class="num">%.4f</td>'
        '<td class="num">%+.2f</td><td>%s</td></tr>'
        % (r["lift"] * 100, r["rate"], r["z_phase"], sigma_bar(r["z_phase"]))
        for r in pw["reaction"]
    )

    strip_h1 = phase_strip(p["phase_rates"][1:], p["phase_rates"][0])
    strip_rx = phase_strip(rx60["null_rates"], rx60["reject_rate"])
    strip_sw = phase_strip(sweep2187["null_rates"], sweep2187["rate"])
    heat = grid_heat(grid)

    html = render(dict(
        bars="{:,}".format(meta["bars"]),
        sessions="{:,}".format(meta["sessions"]),
        start=meta["start"], end=meta["end"],
        px_lo="{:,.0f}".format(meta["px_lo"]), px_hi="{:,.0f}".format(meta["px_hi"]),
        vrows=vrows,
        n_swings="{:,}".format(p["n_swings"]),
        rate="%.4f" % p["rate"], cov="%.4f" % p["coverage"],
        occ="%.4f" % p["occ_rate"],
        z_occ="%+.2f" % p["z_occ"], z_phase="%+.2f" % p["z_phase"],
        z_lset="%+.2f" % p["z_levelset"],
        z_adjmax="%+.2f" % p["z_adjmax"], phase_rank=p["phase_rank"],
        lset_rank="{:,}".format(p["levelset_rank"]),
        adjmax_rank="{:,}".format(p["adjmax_rank"]),
        strip_h1=strip_h1, strip_rx=strip_rx, strip_sw=strip_sw, heat=heat,
        grid_max="%+.2f" % grid_max,
        grid_over3=grid_over3, grid_survive=grid_survive,
        n_grid_z=len(allz),
        z_uniform="%+.2f" % p["z_uniform"],
        round_best_R=round_best["R"], round_best_z="%+.2f" % round_best["z_phase"],
        resp_rows=resp_rows, ms_rows=ms_rows,
        ms_cells=len(ms), ms_zlo="%+.2f" % min(ms_z), ms_zhi="%+.2f" % max(ms_z),
        ms_r81_lo="%+.2f" % min(r["z"] for r in ms_r81),
        ms_r81_hi="%+.2f" % max(r["z"] for r in ms_r81),
        su_cells=len(su),
        su_medwin="%.3f" % su_win[len(su_win) // 2],
        su_medev="%+.3f" % su_ev[len(su_ev) // 2],
        su_best_z="%+.2f" % su_best["z"], su_best_ev="%+.3f" % su_best["ev_R"],
        su_best_win="%.3f" % su_best["win"],
        su_best_desc="R=%d, %s, after a %s" % (su_best["R"],
                                               su_best["zone"].replace("_", " "),
                                               su_best["ctx"]),
        rx_rows=rx_rows, lvl_rows=lvl_rows,
        dwell_rows=dwell_rows, sweep_rows=sweep_rows, round_rows=round_rows,
        pw_h1=pw_h1, pw_rx=pw_rx,
        rx60_n="{:,}".format(rx60["n"]), rx60_rate="%.4f" % rx60["reject_rate"],
        rx60_null="%.4f" % rx60["null_mean"], rx60_sd="%.4f" % rx60["null_sd"],
        rx60_z="%+.2f" % rx60["z_phase"],
        sw_rate="%.4f" % sweep2187["rate"], sw_null="%.4f" % sweep2187["null_mean"],
        sw_z="%+.2f" % sweep2187["z_phase"],
        dwell_best_layer=dwell_best["layer"].replace("_", " "),
        dwell_best_z="%+.2f" % dwell_best["z_phase"],
    ))
    with open(OUT, "w") as fh:
        fh.write(html)
    print("wrote %s (%.1f KB)" % (OUT, os.path.getsize(OUT) / 1024))


def render(vals):
    """Token substitution: {{name}} -> value. Avoids %-escaping every CSS percent."""
    html = open(os.path.join(HERE, "report_template.html")).read()
    for k, v in vals.items():
        if isinstance(v, float):
            s = "%.4f" % v if abs(v) < 1 else "%+.2f" % v
        else:
            s = str(v)
        html = html.replace("{{%s}}" % k, s)
    leftover = [t for t in html.split("{{")[1:]]
    if leftover:
        raise SystemExit("unsubstituted token: {{%s" % leftover[0][:40])
    return html

if __name__ == "__main__":
    build()
