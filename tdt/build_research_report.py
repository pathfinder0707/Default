"""Assemble the structured research review from every stage's JSON."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "research_template.html")
OUT = os.path.join(HERE, "..", "tdt-research-review.html")
STAGES = {"research": "RESEARCH.json", "sweep": "SWEEP.json",
          "hold": "HOLD.json", "base": "ALL.json"}


def main():
    data = {}
    for key, fn in STAGES.items():
        path = os.path.join(HERE, fn)
        if not os.path.exists(path):
            raise SystemExit("missing %s -- run the pipeline first" % fn)
        data[key] = json.load(open(path))

    # the sweep's verdicts are computed by build_sweep_report; recompute here so
    # this report does not depend on that one having been run
    from build_sweep_report import verdict_of
    from statistics import NormalDist
    fin = data["sweep"]["finalists"]
    t_crit = NormalDist().inv_cdf(1 - (0.05 / max(1, len(fin))) / 2)
    for fi in fin:
        fi["verdict"] = verdict_of(fi, data["sweep"].get("controls", {}), t_crit)

    html = open(TPL).read().replace(
        "{{DATA}}", json.dumps(data, separators=(",", ":"), default=float))
    if "{{" in html:
        raise SystemExit("unsubstituted token: {{%s" % html.split("{{")[1][:40])
    with open(OUT, "w") as fh:
        fh.write(html)
    print("wrote %s (%.0f KB)" % (os.path.abspath(OUT), os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
