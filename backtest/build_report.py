import json, html
D=json.load(open('ALL.json'))
M=D['meta']; C=D['core']; B=D['breakdown']; T=D['trade']
import numpy as np
nn=np.array(M['rot_null'])

def f(x,n=2): return ("%."+str(n)+"f")%x
def sgn(x,n=2): return ("%+."+str(n)+"f")%x

# ---------- sigma strip: where the observation sits in the null band ----------
def strip(z,lo=-4,hi=4):
    z=max(lo,min(hi,z)); pos=(z-lo)/(hi-lo)*100
    band1=( (-1-lo)/(hi-lo)*100, 2/(hi-lo)*100 )
    band2=( (-2-lo)/(hi-lo)*100, 4/(hi-lo)*100 )
    return f"""<div class="sig" role="img" aria-label="observed z-score {f(z)} sigma against the null distribution">
<div class="sig-track">
  <div class="sig-b2" style="left:{band2[0]:.2f}%;width:{band2[1]:.2f}%"></div>
  <div class="sig-b1" style="left:{band1[0]:.2f}%;width:{band1[1]:.2f}%"></div>
  <div class="sig-zero"></div>
  <div class="sig-mark" style="left:{pos:.2f}%"><span class="sig-val">{sgn(z)}&#963;</span></div>
</div>
<div class="sig-ax"><span>&minus;4&#963;</span><span>&minus;2&#963;</span><span>0</span><span>+2&#963;</span><span>+4&#963;</span></div>
</div>"""

def verdict(z,thresh=2.0):
    a=abs(z)
    if a<1: return ('null','No effect')
    if a<thresh: return ('null','Within noise')
    return ('hit','Outside noise')

# ---------- minute-of-hour chart ----------
prof=M['minute_profile']
vals=[p['rel'] for p in prof]
vmax=max(max(vals),abs(min(vals)))
W,H=980,240; PADL=44; PADB=30; PADT=14
bw=(W-PADL-10)/60
bars=[]
for p in prof:
    x=PADL+p['m']*bw
    h=abs(p['rel'])/vmax*((H-PADT-PADB)/2)
    y=(H-PADB)/2 if p['rel']>=0 else (H-PADB)/2
    y0=(H-PADB)/2
    yy=y0-h if p['rel']>=0 else y0
    cls="gb" if p['gb'] else "no"
    bars.append(f'<rect class="mb {cls}" x="{x:.1f}" y="{yy:.1f}" width="{bw-1.6:.1f}" height="{max(h,0.6):.1f}"><title>:{p["m"]:02d} {"GB node" if p["gb"] else "not a GB node"} — {sgn(p["rel"])}%</title></rect>')
labels=[]
for m in [0,15,30,45,59]:
    x=PADL+m*bw+bw/2
    labels.append(f'<text class="mx" x="{x:.1f}" y="{H-PADB+16:.0f}" text-anchor="middle">:{m:02d}</text>')
y0=(H-PADB)/2
gl=[]
for v in [-40,-20,0,20,40]:
    yy=y0-v/vmax*((H-PADT-PADB)/2)
    gl.append(f'<line class="mg" x1="{PADL}" y1="{yy:.1f}" x2="{W-10}" y2="{yy:.1f}"/>')
    gl.append(f'<text class="my" x="{PADL-8}" y="{yy+3.5:.1f}" text-anchor="end">{v:+d}%</text>')
chart=f'''<svg viewBox="0 0 {W} {H}" class="mchart" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Swing rate by minute of hour. The tallest bars are :00 and :30; :30 is not a GB node.">
{''.join(gl)}{''.join(bars)}{''.join(labels)}
</svg>'''

# ---------- breakdown rows ----------
def rows(section,keyname):
    out=[]
    for k,v in B[section].items():
        if not v: continue
        vc,vt=verdict(v['z'])
        out.append(f'''<tr><td class="lbl">{html.escape(k)}</td>
<td class="num">{v['n']:,}</td><td class="num">{f(v['obs'],4)}</td><td class="num">{f(v['null'],4)}</td>
<td class="num {'neg' if v['lift']<0 else ''}">{sgn(v['lift']*100)}%</td>
<td class="num strong">{sgn(v['z'])}</td>
<td><span class="pill {vc}">{vt}</span></td></tr>''')
    return "\n".join(out)

t1=C['test1_swing_landing']['3/3']; t2=C['test2_range']; t3=C['test3_reversal']

buf_rows=[]
for k,v in C['test1_swing_landing'].items():
    neg='neg' if v['lift']<0 else ''
    buf_rows.append('<tr><td class="lbl">'+k+' bars</td><td class="num">'+format(v['n'],',')+'</td>'
      '<td class="num">'+f(v['obs'],4)+'</td><td class="num">'+f(v['null_mean'],4)+'</td>'
      '<td class="num '+neg+'">'+sgn(v['lift']*100)+'%</td>'
      '<td class="num strong">'+sgn(v['z'])+'</td>'
      '<td><span class="pill null">'+verdict(v['z'])[1]+'</span></td></tr>')
BUF_ROWS="".join(buf_rows)

rule_rows=[]
for k,v in T['rules'].items():
    rule_rows.append('<tr><td class="lbl">'+html.escape(k)+'</td><td class="num">'+format(v['n'],',')+'</td>'
      '<td class="num">'+f(v['win']*100)+'%</td>'
      '<td class="num strong neg">'+f(v['mean_bps'],3)+'</td></tr>')
RULE_ROWS="".join(rule_rows)

SIG_SW=B['tiers']['significant swings (>2ATR)']
NODE_ROWS=rows('nodes','node'); KZ_ROWS=rows('killzones','kz')
CONF_ROWS=rows('confluence','c'); YEAR_ROWS=rows('years','y')
CONF_BOTH=sgn(B['confluence']['both algos fire']['z'])
CONF_SHARED=sgn(B['confluence']['shared node (same label)']['z'])
zs=[v['z'] for grp in B.values() for v in grp.values() if v]
n_slices=len(zs); n2=sum(1 for z in zs if abs(z)>2)

TPL=f'''<title>Does GB-Time Survive Contact With Data</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;450;500;600&display=swap">
<style>
:root{{
  --paper:#F4F6F8; --card:#FFFFFF; --ink:#101519; --ink2:#2B333C; --muted:#5B6773; --faint:#8B95A1;
  --rule:#DFE4E9; --rule2:#C9D0D8;
  --null:#B4ADA3; --null-soft:#DCD6CD; --null-softer:#EDE9E3;
  --mark:#1746C4; --mark-soft:#E4EAFA;
  --neg:#A32B1C; --pos:#1D6B45;
  --shadow:0 1px 2px rgba(16,21,25,.05),0 8px 24px -12px rgba(16,21,25,.14);
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --paper:#0E1216; --card:#151B21; --ink:#E9EDF1; --ink2:#C6CDD5; --muted:#93A0AD; --faint:#69747F;
  --rule:#242C34; --rule2:#333D47;
  --null:#7C756B; --null-soft:#3A3730; --null-softer:#292722;
  --mark:#7AA0FF; --mark-soft:#18233D;
  --neg:#E0796A; --pos:#5FB78C;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}}}}
:root[data-theme="dark"]{{
  --paper:#0E1216; --card:#151B21; --ink:#E9EDF1; --ink2:#C6CDD5; --muted:#93A0AD; --faint:#69747F;
  --rule:#242C34; --rule2:#333D47;
  --null:#7C756B; --null-soft:#3A3730; --null-softer:#292722;
  --mark:#7AA0FF; --mark-soft:#18233D;
  --neg:#E0796A; --pos:#5FB78C;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"IBM Plex Sans",ui-sans-serif,system-ui,sans-serif;font-size:16.5px;line-height:1.62;
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}}
.shell{{display:grid;grid-template-columns:232px minmax(0,1fr);gap:52px;max-width:1240px;margin:0 auto;padding:0 32px}}
@media(max-width:1000px){{.shell{{grid-template-columns:1fr;gap:0}}}}

/* nav */
nav{{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;padding:40px 0 40px;border-right:1px solid var(--rule)}}
@media(max-width:1000px){{nav{{position:static;height:auto;border-right:none;border-bottom:1px solid var(--rule);padding:16px 0}}}}
.nav-t{{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);margin-bottom:14px}}
nav ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}}
@media(max-width:1000px){{nav ol{{flex-direction:row;flex-wrap:wrap;gap:6px}}}}
nav a{{display:flex;gap:9px;text-decoration:none;color:var(--muted);font-size:13.5px;padding:5px 9px;border-radius:5px;border-left:2px solid transparent}}
nav a:hover{{color:var(--ink);background:var(--card)}}
nav a .n{{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);padding-top:2px}}
nav a:focus-visible{{outline:2px solid var(--mark);outline-offset:2px}}

main{{padding:52px 0 120px;min-width:0}}
h1{{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:clamp(34px,4.6vw,52px);line-height:1.08;
  letter-spacing:-.018em;margin:0 0 18px;text-wrap:balance;max-width:19ch}}
h2{{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:28px;line-height:1.2;letter-spacing:-.012em;
  margin:0 0 6px;text-wrap:balance}}
h3{{font-size:14px;font-weight:600;margin:30px 0 10px;letter-spacing:-.005em}}
p{{margin:0 0 15px;max-width:68ch;color:var(--ink2)}}
strong{{font-weight:600;color:var(--ink)}}
a{{color:var(--mark)}}
.eyebrow{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.17em;text-transform:uppercase;color:var(--faint)}}
.lede{{font-size:19px;line-height:1.55;color:var(--muted);max-width:62ch;margin-bottom:30px}}
.rule{{height:1px;background:var(--rule);margin:0 0 34px}}

section{{scroll-margin-top:22px;margin-bottom:62px}}
.sec-h{{display:flex;gap:14px;align-items:baseline;margin-bottom:14px;border-top:2px solid var(--ink);padding-top:14px}}
.sec-n{{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--mark);font-weight:600;padding-top:6px}}

/* verdict */
.verdict{{background:var(--card);border:1px solid var(--rule2);border-radius:3px;padding:26px 28px;margin-bottom:34px;box-shadow:var(--shadow)}}
.verdict .eyebrow{{margin-bottom:9px}}
.verdict-h{{font-family:Newsreader,Georgia,serif;font-size:27px;line-height:1.22;font-weight:500;margin:0 0 12px;text-wrap:balance}}
.verdict p{{margin-bottom:0;font-size:15.5px}}

.facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:1px;background:var(--rule);
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin:26px 0 34px}}
.fact{{background:var(--card);padding:15px 16px}}
.fact-v{{font-family:"IBM Plex Mono",monospace;font-size:23px;font-weight:500;letter-spacing:-.02em;line-height:1.15}}
.fact-l{{font-size:11px;color:var(--muted);margin-top:3px;line-height:1.4}}

/* sigma strip */
.test{{background:var(--card);border:1px solid var(--rule);border-radius:3px;padding:20px 22px;margin:18px 0 22px}}
.test-top{{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:4px}}
.test-q{{font-size:15px;font-weight:600;color:var(--ink)}}
.test-n{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint)}}
.sig{{margin:20px 0 4px}}
.sig-track{{position:relative;height:38px;background:var(--null-softer);border-radius:2px}}
.sig-b2{{position:absolute;top:0;height:100%;background:var(--null-soft)}}
.sig-b1{{position:absolute;top:0;height:100%;background:var(--null);opacity:.45}}
.sig-zero{{position:absolute;left:50%;top:-4px;bottom:-4px;width:1px;background:var(--rule2)}}
.sig-mark{{position:absolute;top:-7px;bottom:-7px;width:2.5px;background:var(--mark);border-radius:2px}}
.sig-val{{position:absolute;left:50%;transform:translateX(-50%);top:-21px;font-family:"IBM Plex Mono",monospace;
  font-size:11.5px;font-weight:600;color:var(--mark);white-space:nowrap}}
.sig-ax{{display:flex;justify-content:space-between;font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);margin-top:7px}}
.sig-cap{{font-size:12.5px;color:var(--muted);margin-top:12px;max-width:none}}

.pill{{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em;
  text-transform:uppercase;padding:3px 8px;border-radius:2px;white-space:nowrap;font-weight:500}}
.pill.null{{background:var(--null-softer);color:var(--muted);border:1px solid var(--null-soft)}}
.pill.hit{{background:var(--mark-soft);color:var(--mark);border:1px solid var(--mark)}}

table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:16px 0}}
.tw{{overflow-x:auto;border:1px solid var(--rule);border-radius:3px;background:var(--card)}}
.tw table{{margin:0}}
th{{text-align:left;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--faint);font-weight:500;padding:11px 14px;border-bottom:1px solid var(--rule2);white-space:nowrap}}
td{{padding:10px 14px;border-bottom:1px solid var(--rule);color:var(--ink2);white-space:nowrap}}
tr:last-child td{{border-bottom:none}}
.num{{font-family:"IBM Plex Mono",monospace;text-align:right}}
.num.strong{{color:var(--ink);font-weight:600}}
.lbl{{font-weight:500;color:var(--ink)}}
.neg{{color:var(--neg)}}
.pos{{color:var(--pos)}}

.mchart{{width:100%;height:auto;display:block;margin:8px 0 4px}}
.mb.gb{{fill:var(--mark)}}
.mb.no{{fill:var(--null)}}
.mg{{stroke:var(--rule);stroke-width:1}}
.my,.mx{{font-family:"IBM Plex Mono",monospace;font-size:10px;fill:var(--faint)}}
.legend{{display:flex;gap:18px;font-size:12px;color:var(--muted);margin-top:6px;flex-wrap:wrap}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:1px;margin-right:6px;vertical-align:middle}}

.callout{{border-left:2px solid var(--mark);padding:2px 0 2px 18px;margin:22px 0;max-width:68ch}}
.callout p:last-child{{margin-bottom:0}}
.note{{font-size:13px;color:var(--muted);max-width:68ch}}
ul{{max-width:68ch;color:var(--ink2);padding-left:20px}}
li{{margin-bottom:7px}}
code{{font-family:"IBM Plex Mono",monospace;font-size:.9em;background:var(--null-softer);padding:1px 5px;border-radius:2px;color:var(--ink)}}
footer{{border-top:1px solid var(--rule);padding-top:22px;margin-top:14px;font-size:12.5px;color:var(--faint);max-width:68ch}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>

<div class="shell">
<nav>
  <div class="nav-t">Contents</div>
  <ol>
    <li><a href="#verdict"><span class="n">—</span><span>Verdict</span></a></li>
    <li><a href="#data"><span class="n">—</span><span>Data &amp; method</span></a></li>
    <li><a href="#t0"><span class="n">01</span><span>Can it be tested?</span></a></li>
    <li><a href="#t1"><span class="n">02</span><span>Do swings land on nodes?</span></a></li>
    <li><a href="#t2"><span class="n">03</span><span>Does range expand?</span></a></li>
    <li><a href="#t3"><span class="n">04</span><span>Does price reverse?</span></a></li>
    <li><a href="#t4"><span class="n">05</span><span>The :00 anomaly</span></a></li>
    <li><a href="#t5"><span class="n">06</span><span>Do paths sequence?</span></a></li>
    <li><a href="#t6"><span class="n">07</span><span>Can it be traded?</span></a></li>
    <li><a href="#best"><span class="n">08</span><span>What worked best</span></a></li>
    <li><a href="#mc"><span class="n">09</span><span>Multiple comparisons</span></a></li>
    <li><a href="#means"><span class="n">10</span><span>What this means</span></a></li>
  </ol>
</nav>

<main>
<div class="eyebrow">Backtest &#183; NASDAQ 100 &#183; 1-minute &#183; 2023&ndash;2025</div>
<h1>Does GB&#8209;Time survive contact with data?</h1>
<p class="lede">Every claim the GB&#8209;time framework makes, tested against {M['bars']:,} bars with a matched null model for each one. This is the result, including the two findings that looked real and were not.</p>

<div class="facts">
  <div class="fact"><div class="fact-v">{M['bars']:,}</div><div class="fact-l">1-minute bars</div></div>
  <div class="fact"><div class="fact-v">{M['days']}</div><div class="fact-l">trading days</div></div>
  <div class="fact"><div class="fact-v">{M['swings']:,}</div><div class="fact-l">confirmed swings</div></div>
  <div class="fact"><div class="fact-v">6</div><div class="fact-l">claims tested</div></div>
  <div class="fact"><div class="fact-v">0</div><div class="fact-l">survived</div></div>
</div>

<section id="verdict">
<div class="verdict">
  <div class="eyebrow">Verdict</div>
  <div class="verdict-h">GB&#8209;time nodes show no measurable edge on NASDAQ 1&#8209;minute data.</div>
  <p>Swings do not land on nodes more than chance. Range does not expand at nodes. Price does not reverse at nodes. Swings do not walk the Algo&nbsp;1 or Algo&nbsp;2 sequences &mdash; they do so <em>less</em> than random points. Every directional rule loses precisely the spread. Two results looked significant on first pass; both dissolved under the correct control, and section&nbsp;05 and section&nbsp;06 show exactly how.</p>
</div>
</section>

<section id="data">
<div class="sec-h"><div><div class="eyebrow">Provenance</div><h2>Data &amp; method</h2></div></div>
<p>HistData NSXUSD 1-minute bars, {M['start']} to {M['end']} &mdash; {M['bars']:,} bars over {M['days']} trading days, spanning a bull run, a correction and two Fed cycles.</p>

<div class="callout">
<p><strong>The timezone nearly broke this before it started.</strong> HistData documents these timestamps as fixed EST with no DST. They are not. The daily session break sits at <code>16:15&ndash;17:59</code> in both winter and summer &mdash; identical clock time. Under fixed EST it would shift by an hour seasonally. The timestamps track <code>America/New_York</code> <em>with</em> DST.</p>
<p>This matters more here than in most backtests: the framework reads the <em>minute value</em> of the Zurich clock, so a 60-minute error changes <code>HH+MM</code> and <code>|HH&minus;MM|</code> on every single bar. Converting properly &mdash; per-date, via IANA rules &mdash; produced 720 days at a 6-hour offset and <strong>65 days at 5 hours</strong>, the windows where the US has switched and the EU has not. A fixed offset silently corrupts those 65 days.</p>
</div>

<h3>The control that does the work</h3>
<p>Whether a minute is a GB node is a <em>deterministic function of the clock</em>. So node-minutes are perfectly confounded with time-of-day, and any raw comparison of "node vs non-node" measures intraday seasonality, not GB.</p>
<p>Every test below therefore uses a <strong>rotation null</strong>: the identical measurement repeated under 59 clocks shifted by 1&ndash;59 minutes. Rotation is a bijection on minutes, so the node set keeps <em>exactly</em> its size &mdash; 384 MM-exact minutes in all 60 variants. If GB times carry information, the true clock must stand out against its own rotations. That is what &#963; measures throughout.</p>
</section>

<section id="t0">
<div class="sec-h"><span class="sec-n">01</span><div><div class="eyebrow">Precondition</div><h2>Can the framework be tested at all?</h2></div></div>
<p>Before measuring anything: at the tool's default settings &mdash; three reads, &plusmn;1 tolerance &mdash; how much of the day qualifies as a node?</p>
<div class="tw"><table>
<thead><tr><th>Configuration</th><th class="num">Node minutes</th><th class="num">Share of day</th></tr></thead>
<tbody>
<tr><td class="lbl">MM only, tolerance 0</td><td class="num">{M['density']['mm0']}</td><td class="num strong">26.7%</td></tr>
<tr><td class="lbl">All three methods, tolerance 0</td><td class="num">{M['density']['all0']}</td><td class="num">58.3%</td></tr>
<tr><td class="lbl">MM only, tolerance 1</td><td class="num">{M['density']['mm1']}</td><td class="num">76.7%</td></tr>
<tr><td class="lbl">All three methods, tolerance 1 &mdash; <em>the default</em></td><td class="num">{M['density']['all1']}</td><td class="num strong neg">97.6%</td></tr>
<tr><td class="lbl">All three methods, tolerance 2</td><td class="num">{M['density']['all2']}</td><td class="num">99.6%</td></tr>
</tbody></table></div>
<p>At default settings <strong>97.6% of the day is a node</strong>. The longest stretch with no node anywhere is three minutes; the median gap is one minute.</p>
<div class="callout"><p>This is not a bug &mdash; it falls out of the arithmetic. Three reads per minute, each &plusmn;1, against eleven node buckets covering most values from 0 to 97. But it means the default configuration is <strong>unfalsifiable</strong>: "price reacted at a GB node" is true of almost every minute, so it cannot be wrong, so it cannot be tested. Everything below therefore uses <strong>MM-exact</strong> reads &mdash; 384 minutes, 26.7% &mdash; the only setting with discriminating power.</p></div>
</section>

<section id="t1">
<div class="sec-h"><span class="sec-n">02</span><div><div class="eyebrow">Claim</div><h2>Swings land on GB nodes</h2></div></div>
<p>The foundational claim. Confirmed pivots were extracted at three buffer settings, mapped to Zurich time, and tested against the rotation null.</p>
<div class="test">
  <div class="test-top"><span class="test-q">Do confirmed swings land on MM-exact node minutes more than chance?</span>
  <span class="test-n">n = {t1['n']:,} swings &#183; buffer 3/3</span></div>
  {strip(t1['z'])}
  <div class="sig-cap">Observed <strong>{f(t1['obs'],4)}</strong> &#183; rotation null <strong>{f(t1['null_mean'],4)} &plusmn; {f(t1['null_sd'],4)}</strong> &#183; lift <strong>{sgn(t1['lift']*100)}%</strong>. The observation sits essentially on top of the null mean.</div>
</div>
<div class="tw"><table>
<thead><tr><th>Pivot buffer</th><th class="num">Swings</th><th class="num">Observed</th><th class="num">Null</th><th class="num">Lift</th><th class="num">&#963;</th><th>Verdict</th></tr></thead>
<tbody>
{BUF_ROWS}
</tbody></table></div>
<p>Three independent buffer settings, all null. Filtering to <strong>significant</strong> swings only &mdash; amplitude greater than twice the local ATR, {SIG_SW['n']:,} of them &mdash; moves the needle to {sgn(SIG_SW['z'])}&#963;. Still nothing.</p>
</section>

<section id="t2">
<div class="sec-h"><span class="sec-n">03</span><div><div class="eyebrow">Claim</div><h2>Volatility expands at nodes</h2></div></div>
<div class="test">
  <div class="test-top"><span class="test-q">Is bar range elevated on node minutes?</span><span class="test-n">n = {M['bars']:,} bars</span></div>
  {strip(t2['z'])}
  <div class="sig-cap">Node minutes <strong>{f(t2['node'],3)} bps</strong> &#183; non-node <strong>{f(t2['nonnode'],3)} bps</strong> &#183; ratio <strong>{f(t2['ratio'],4)}</strong> against a null of {f(t2['null_mean'],4)}. Node minutes are fractionally <em>calmer</em>, well inside noise.</div>
</div>
</section>

<section id="t3">
<div class="sec-h"><span class="sec-n">04</span><div><div class="eyebrow">Claim</div><h2>Price reverses at nodes</h2></div></div>
<p>The framework's central idea: a node is a decision level where price holds or breaks. If so, direction should flip at nodes more often than elsewhere.</p>
<div class="test">
  <div class="test-top"><span class="test-q">Does the 10-minute trend flip at node minutes more than elsewhere?</span><span class="test-n">&plusmn;10 minute window</span></div>
  {strip(t3['z'])}
  <div class="sig-cap">Reversal rate at nodes <strong>{f(t3['node'],4)}</strong> &#183; elsewhere <strong>{f(t3['nonnode'],4)}</strong> &#183; null {f(t3['null_mean'],4)} &plusmn; {f(t3['null_sd'],4)}. The largest &#963; in the core tests &mdash; and the effect is <strong>0.0006</strong> on a coin flip. Untradeable even if it were real.</div>
</div>
</section>

<section id="t4">
<div class="sec-h"><span class="sec-n">05</span><div><div class="eyebrow">The first false positive</div><h2>The :00 anomaly</h2></div></div>
<p>Across 27 slices, exactly one crossed 2&#963;: the <code>00</code> node, at <strong>+4.86&#963;</strong> with a <strong>+55%</strong> lift. Worth taking seriously &mdash; so here is every minute of the hour, GB nodes marked.</p>
{chart}
<div class="legend"><span><i style="background:var(--mark)"></i>GB node minute</span><span><i style="background:var(--null)"></i>not a GB node</span><span>swing rate vs the hourly average</span></div>
<div class="tw"><table>
<thead><tr><th>Minute</th><th>GB node?</th><th class="num">Swing rate vs average</th></tr></thead>
<tbody>
<tr><td class="lbl">:00</td><td><span class="pill hit">GB node</span></td><td class="num strong">+46.7%</td></tr>
<tr><td class="lbl">:30</td><td><span class="pill null">not a node</span></td><td class="num strong">+41.6%</td></tr>
<tr><td class="lbl">:50</td><td><span class="pill hit">GB node</span></td><td class="num">+15.2%</td></tr>
<tr><td class="lbl">:15</td><td><span class="pill null">not a node</span></td><td class="num">+14.4%</td></tr>
<tr><td class="lbl">:45</td><td><span class="pill null">not a node</span></td><td class="num">+13.5%</td></tr>
<tr><td class="lbl">:29</td><td><span class="pill hit">GB node</span></td><td class="num neg">&minus;16.6%</td></tr>
<tr><td class="lbl">:59</td><td><span class="pill hit">GB node</span></td><td class="num neg">&minus;21.1%</td></tr>
</tbody></table></div>
<div class="callout">
<p><strong>The <code>:00</code> effect is real, and it is not GB.</strong> It is the round-clock effect &mdash; quarter- and half-hour clustering from hourly bar closes, scheduled flow and news on the hour. <code>:30</code>, <code>:15</code> and <code>:45</code> are <em>not</em> GB nodes and show the same pattern. GB captures <code>:00</code> only incidentally, because the handoff happens to list <code>00</code> as a valid node.</p>
<p>Averaged across the whole hour, GB minutes run at <strong>&minus;0.095%</strong> versus <strong>+0.041%</strong> for non-GB minutes. Two of the three worst minutes in the hour &mdash; <code>:59</code> and <code>:29</code> &mdash; are GB nodes.</p>
</div>
</section>

<section id="t5">
<div class="sec-h"><span class="sec-n">06</span><div><div class="eyebrow">The second false positive</div><h2>Do swings walk the Algo paths?</h2></div></div>
<p>A fair objection to everything above: individual nodes may not matter while the <em>sequence</em> does. Algo&nbsp;1 should walk indices forward, Algo&nbsp;2 in reverse. Tested against two different nulls &mdash; and the choice of null decides the answer.</p>
<div class="tw"><table>
<thead><tr><th>Null model</th><th class="num">A1 forward &#963;</th><th class="num">A2 reverse &#963;</th><th>What it actually tests</th></tr></thead>
<tbody>
<tr><td class="lbl">Rotate the clock</td><td class="num strong">&minus;1.26</td><td class="num strong">&minus;1.52</td><td>Keeps swing times, moves the node map</td></tr>
<tr><td class="lbl">Shuffle swing order</td><td class="num strong neg">&minus;11.38</td><td class="num strong pos">+10.84</td><td>Destroys chronology &mdash; <strong>wrong null</strong></td></tr>
<tr><td class="lbl">Random points, in time order</td><td class="num strong neg">&minus;7.97</td><td class="num strong neg">&minus;4.34</td><td>Are <em>swings</em> special? &mdash; <strong>right null</strong></td></tr>
</tbody></table></div>
<p>The shuffle null hands Algo&nbsp;2 a spectacular <strong>+10.84&#963;</strong>. It is an artifact. Shuffling destroys the arrow of time, which was never the hypothesis &mdash; and Algo&nbsp;2's index map is <em>partly monotonic with the clock</em>, so simply moving forward through an hour manufactures valid A2 steps with no market behaviour required:</p>
<p class="note" style="font-family:'IBM Plex Mono',monospace;font-size:12px;overflow-x:auto;white-space:nowrap">:03=0 &#183; :07=0 &#183; :11=3 &#183; :14=3 &#183; :17=2 &#183; :23=2 &#183; :29=5 &#183; :35=5 &#183; :47=4 &#183; :50=4 &#183; :53=4 &#183; :56=4 &#183; :59=1</p>
<div class="callout"><p>Against the correct control &mdash; random bars taken in the same chronological order &mdash; real swings are <strong>worse</strong> at forming both paths than random points: A1 at &minus;7.97&#963;, A2 at &minus;4.34&#963;. The sequence logic does not describe how this market moves.</p></div>
</section>

<section id="t6">
<div class="sec-h"><span class="sec-n">07</span><div><div class="eyebrow">Bottom line</div><h2>Can any of it be traded?</h2></div></div>
<p>Four directional rules at MM-exact nodes, 15-minute hold, net of a conservative 1&nbsp;bp round-trip spread.</p>
<div class="tw"><table>
<thead><tr><th>Rule</th><th class="num">Trades</th><th class="num">Win rate</th><th class="num">Mean bps</th></tr></thead>
<tbody>
{RULE_ROWS}
</tbody></table></div>
<p>Every rule loses almost exactly the spread &mdash; the signature of no signal whatsoever. And the deeper number: mean absolute move in the 15 minutes after a node is <strong>{f(T['hold15']['node_absmove'],3)} bps</strong>, versus <strong>{f(T['hold15']['nonnode_absmove'],3)} bps</strong> after a non-node minute. Identical to three decimal places. Nothing distinguishes the minutes the framework says are decisive.</p>
</section>

<section id="best">
<div class="sec-h"><span class="sec-n">08</span><div><div class="eyebrow">The original question</div><h2>What worked best, when, and with what confluence</h2></div></div>
<p>You asked what works best and under which conditions. Here is every slice, ranked as asked &mdash; with the honest caveat that ranking noise produces a ranking, not a finding.</p>
<h3>By node</h3>
<div class="tw"><table><thead><tr><th>Node</th><th class="num">Swings</th><th class="num">Observed</th><th class="num">Null</th><th class="num">Lift</th><th class="num">&#963;</th><th>Verdict</th></tr></thead><tbody>
{NODE_ROWS}
</tbody></table></div>
<h3>By session</h3>
<div class="tw"><table><thead><tr><th>Killzone (Zurich)</th><th class="num">Swings</th><th class="num">Observed</th><th class="num">Null</th><th class="num">Lift</th><th class="num">&#963;</th><th>Verdict</th></tr></thead><tbody>
{KZ_ROWS}
</tbody></table></div>
<h3>By confluence</h3>
<div class="tw"><table><thead><tr><th>Confluence condition</th><th class="num">Swings</th><th class="num">Observed</th><th class="num">Null</th><th class="num">Lift</th><th class="num">&#963;</th><th>Verdict</th></tr></thead><tbody>
{CONF_ROWS}
</tbody></table></div>
<p class="note">Both algos firing &mdash; the tool's strongest confluence grade &mdash; comes in at {CONF_BOTH}&#963;. A shared node on both paths is <em>negative</em> at {CONF_SHARED}&#963;.</p>
<h3>By year</h3>
<div class="tw"><table><thead><tr><th>Year</th><th class="num">Swings</th><th class="num">Observed</th><th class="num">Null</th><th class="num">Lift</th><th class="num">&#963;</th><th>Verdict</th></tr></thead><tbody>
{YEAR_ROWS}
</tbody></table></div>
</section>

<section id="mc">
<div class="sec-h"><span class="sec-n">09</span><div><div class="eyebrow">Discipline</div><h2>Multiple comparisons</h2></div></div>
<p>{n_slices} slices were tested. At a 5% threshold, chance alone produces about <strong>{n_slices*0.05:.1f}</strong> results past 2&#963;. Observed: <strong>{n2}</strong>.</p>
<p>The framework scores exactly as a coin would. And the single slice that did clear the bar &mdash; the <code>00</code> node &mdash; was traced in section 05 to a mechanism that has nothing to do with GB. Had it not been chased down, it would have become the finding this whole report was built around.</p>
</section>

<section id="means">
<div class="sec-h"><span class="sec-n">10</span><div><div class="eyebrow">Reading it straight</div><h2>What this does and does not establish</h2></div></div>
<h3>What it establishes</h3>
<ul>
<li>On NASDAQ 1-minute data across three years, GB&#8209;time nodes carry <strong>no information</strong> about where swings form, where volatility expands, where price reverses, or where it can be traded.</li>
<li>At default settings the framework is <strong>unfalsifiable</strong> &mdash; 97.6% of minutes qualify, so no observation could contradict it.</li>
<li>Both apparent positives were artifacts: one a well-known clock effect, one a broken null.</li>
</ul>
<h3>What it does not establish</h3>
<ul>
<li>Nothing about <strong>XAUUSD or GBPUSD</strong>. Send either and it runs in minutes &mdash; the pipeline is built.</li>
<li>Nothing about GB&#8209;time <em>combined with</em> the Quarterly Theory layer. This tested the time framework alone, which is what the tool automates.</li>
<li>Nothing about your discretionary reading. A trader can be profitable using a framework as a <em>process scaffold</em> &mdash; forcing patience and a defined level &mdash; while the framework's specific claims carry no edge. Those are different propositions, and only the second was tested here.</li>
</ul>
<div class="callout">
<p><strong>The one thing worth keeping.</strong> The trade gate in the tool &mdash; requiring a seen reaction, HTF bias agreement and tCISD before it will grade a setup &mdash; enforces patience and structure. None of its power came from the node arithmetic. The gate is worth keeping. The node timing that triggers it is decoration.</p>
</div>
<footer>
Method: HistData NSXUSD M1, {M['start']}&ndash;{M['end']}. Timestamps America/New_York, DST-aware, converted per-date to Europe/Zurich via IANA. Pivots {M['swings']:,} at buffer 3/3 within contiguous session blocks. Node engine cross-validated against the tool's tested JavaScript implementation (17/17 assertions, including all five density figures). Every test carries a rotation null across 59 shifted clocks; sequence tests additionally carry shuffle and chronological-random nulls. Costs 1&nbsp;bp round trip. &#963; is the observation's distance from its own null mean in null standard deviations.
</footer>
</section>
</main>
</div>'''
open('gb-backtest-report.html','w').write(TPL)
print("written: gb-backtest-report.html  (%d bytes)"%len(TPL))
