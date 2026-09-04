"""Build the sweep report from SWEEP.json.

Adds the two things the sweep itself deliberately does not decide: the
significance bar, and whether each finalist cleared it. Kept here rather than
in sweep.py so the search cannot be tempted to grade itself.
"""
import json
import os
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "SWEEP.json")
TPL = os.path.join(HERE, "sweep_template.html")
OUT = os.path.join(HERE, "..", "tdt-sweep-report.html")


def verdict_of(f, controls, t_crit):
    """A finalist passes only by clearing the bar AND beating the control.

    Beating zero is not enough: the fade-every-leg control already has an edge,
    so a configuration that merely matches it has found the trade structure,
    not the counting.
    """
    te = f.get("test")
    if not te or not te.get("n"):
        return "no test trades"
    ctrl = controls.get(f["control_key"] + "|test")
    if te["exp_r"] <= 0:
        return "loses out of sample"
    if abs(te["t"]) <= t_crit:
        return "below the bar"
    if ctrl and te["exp_r"] <= ctrl["exp_r"]:
        return "no better than control"
    return "passes"


def main():
    if not os.path.exists(SRC):
        raise SystemExit("no %s -- run `python sweep.py` first" % SRC)
    d = json.load(open(SRC))
    hold_path = os.path.join(HERE, "HOLD.json")
    d["hold_study"] = json.load(open(hold_path)) if os.path.exists(hold_path) else None
    finals = d["finalists"]
    n_fin = max(1, len(finals))
    alpha = 0.05 / n_fin
    t_crit = NormalDist().inv_cdf(1 - alpha / 2)

    for f in finals:
        f["verdict"] = verdict_of(f, d.get("controls", {}), t_crit)

    d["meta"]["finalists_n"] = len(finals)
    d["meta"]["bonferroni_alpha"] = alpha
    d["meta"]["t_threshold"] = t_crit

    html = open(TPL).read().replace(
        "{{DATA}}", json.dumps(d, separators=(",", ":"), default=float))
    if "{{" in html:
        raise SystemExit("unsubstituted token: {{%s" % html.split("{{")[1][:40])
    with open(OUT, "w") as fh:
        fh.write(html)

    passed = [f for f in finals if f["verdict"] == "passes"]
    print("wrote %s (%.0f KB)" % (os.path.abspath(OUT), os.path.getsize(OUT) / 1024))
    print("bar: |t| > %.2f on test (Bonferroni over %d finalists), and must beat control"
          % (t_crit, len(finals)))
    print("%d of %d readings passed" % (len(passed), len(finals)))
    for f in sorted(finals, key=lambda x: -(x["test"]["t"] if x.get("test") else -99)):
        c, te, tr = f["config"], f.get("test"), f["train"]
        print("  %-9s %-2d %-7s %-4s k=%d %-8s rr=%-4s | train %+0.4fR t=%+5.2f n=%-5d"
              " | test %s | %s"
              % (c["signal"], c["key"], c["polarity"], c["tf"], c["k"], c["mode"],
                 c["rr"], tr["exp_r"], tr["t"], tr["n"],
                 ("%+0.4fR t=%+5.2f n=%-5d" % (te["exp_r"], te["t"], te["n"]))
                 if te else "none", f["verdict"]))


if __name__ == "__main__":
    main()
