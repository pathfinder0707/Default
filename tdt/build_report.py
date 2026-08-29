"""Build the self-contained TDT report from ALL.json.

Trims the payload to what the page draws -- the raw leg indices are large and
nothing in the report reads them -- then substitutes it into the template.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ALL.json")
TPL = os.path.join(HERE, "report_template.html")
OUT = os.path.join(HERE, "..", "tdt-report.html")

STAT = ("n", "win_rate", "exp_r", "exp_pts", "total_r", "pf", "t", "max_dd_r",
        "p_target", "p_stop", "p_timeout", "med_bars", "sd_r")


def slim_stats(s):
    return {k: s[k] for k in STAT if k in s}


def slim_group(rows):
    return [dict({"value": r.get("value")}, **slim_stats(r)) for r in rows or []]


def slim(d):
    bt = d["backtest"]
    out = {
        "meta": d["meta"],
        "legs": d["legs"],
        "null": {
            "hazard": {m: {"legs": h["legs"], "rows": h["rows"]}
                       for m, h in d["null"]["hazard"].items()},
            "neighbour": d["null"]["neighbour"],
            "offset": d["null"]["offset"],
        },
        "backtest": {
            "params": bt["params"],
            "sweep": [r for r in bt["sweep"] if r.get("n")],
            "model2": {}, "model3": {},
        },
    }
    for mode, b in bt["model2"].items():
        out["backtest"]["model2"][mode] = {
            "n_signals": b["n_signals"], "stats": slim_stats(b["stats"]),
            "by_key": slim_group(b["by_key"]), "equity": b["equity"]}
    for mode, b in bt["model3"].items():
        out["backtest"]["model3"][mode] = {
            "n_signals": b["n_signals"], "stats": slim_stats(b["stats"]),
            "by_verdict": slim_group(b["by_verdict"]),
            "by_sig": slim_group(b["by_sig"]), "equity": b["equity"]}
    return out


def main():
    if not os.path.exists(SRC):
        raise SystemExit("no %s -- run `python run_all.py` first" % SRC)
    payload = slim(json.load(open(SRC)))
    html = open(TPL).read().replace(
        "{{DATA}}", json.dumps(payload, separators=(",", ":"), default=float))
    if "{{" in html:
        raise SystemExit("unsubstituted token: {{%s" % html.split("{{")[1][:40])
    with open(OUT, "w") as fh:
        fh.write(html)
    tag = " [SYNTHETIC]" if payload["meta"].get("synthetic") else ""
    print("wrote %s (%.0f KB)%s"
          % (os.path.abspath(OUT), os.path.getsize(OUT) / 1024, tag))


if __name__ == "__main__":
    main()
