"""Build the interactive intraday PO3 report from ALL.json."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "po3-intraday-report.html")

KEEP = ("R", "n", "po3", "exp_gross", "sd", "win_rate", "p_target", "p_stop",
        "p_timeout", "pf", "med_bars", "risk_pts", "max_dd", "exp_pts", "t_stat")


def slim(d):
    out = {"meta": d["meta"], "sizing": d["sizing"]}

    out["grid"] = d["strat"]["grid"]
    out["sweep"] = {
        k: [{a: r[a] for a in KEEP if a in r} for r in v if r.get("n", 0) > 0]
        for k, v in d["strat"]["sweep"].items()
    }

    dp = d["deep"]
    out["phase"] = [{a: r[a] for a in ("R", "n", "exp_pts", "t", "null_mean",
                                       "null_sd", "z", "rank")} for r in dp["phase"]]
    out["phase_nulls"] = {str(r["R"]): r["nulls"] for r in dp["phase"]}
    out["year"] = [{a: r[a] for a in ("R", "year", "n", "win_rate", "exp_pts",
                                      "t_stat", "total_pts")} for r in dp["year"]]
    out["cost"] = dp["cost"]
    out["random"] = dp["random"]
    out["vol"] = [{a: r[a] for a in ("f", "med_R", "n", "win_rate", "exp_pts",
                                     "t_stat", "per_year")} for r in dp["vol"]]

    fl = d["fill"]
    out["pen"] = [{a: r[a] for a in ("config", "pen", "n", "win_rate", "exp_pts",
                                     "t_stat", "total_pts")} for r in fl["pen"]]
    out["tod"] = [{a: r[a] for a in ("window", "n", "win_rate", "exp_pts", "t_stat")}
                  for r in fl["tod"]]
    out["rec"] = fl["recommended"]["stats"]
    out["rec_year"] = [{a: r[a] for a in ("year", "n", "win_rate", "exp_pts",
                                          "t_stat", "total_pts")} for r in fl["recommended_year"]]
    eq = fl["recommended"]["equity"]
    step = max(1, len(eq) // 400)
    out["rec_equity"] = [round(eq[i], 1) for i in range(0, len(eq), step)]
    return out


def main():
    d = json.load(open(os.path.join(HERE, "ALL.json")))
    payload = slim(d)
    tpl = open(os.path.join(HERE, "report_template.html")).read()
    html = tpl.replace("{{DATA}}", json.dumps(payload, separators=(",", ":")))
    if "{{" in html:
        raise SystemExit("unsubstituted token: {{%s" % html.split("{{")[1][:40])
    with open(OUT, "w") as fh:
        fh.write(html)
    print("wrote %s (%.0f KB)" % (OUT, os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
