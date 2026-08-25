"""The interactive path sections of the playbook: reach map, first-touch, sim.

Kept out of build_playbook.py because it is mostly a small client-side app --
two linked charts driven by a pair of segmented controls, and a Monte Carlo the
reader can re-run.

Series colours are the validated categorical slots 1 and 2 (blue, orange) from
the dataviz reference palette rather than the report's teal accent, which failed
the palette validator against a second hue: chroma floor and a normal-vision
delta E of 13.5. Chart series and brand chrome are different jobs, and the
series pair has to survive colour-vision deficiency, so it is chosen by the
validator rather than to match the furniture. Both modes pass all six checks.
"""
import json

CSS = """
/* ---- chart + control tokens ---- */
:root{
  --s1:#2a78d6; --s2:#eb6834;
  --s1-soft:#dbe8fa; --s2-soft:#fbe2d8;
  --grid:#E4E6EA; --axis:#B6BCC5; --chart-bg:#FFFFFF;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --s1:#3987e5; --s2:#d95926;
    --s1-soft:#152a44; --s2-soft:#3a1d10;
    --grid:#252A31; --axis:#3E464F; --chart-bg:#181C21;
  }
}
:root[data-theme="dark"]{
  --s1:#3987e5; --s2:#d95926;
  --s1-soft:#152a44; --s2-soft:#3a1d10;
  --grid:#252A31; --axis:#3E464F; --chart-bg:#181C21;
}

.ctl{display:flex;flex-wrap:wrap;gap:.5rem 1.4rem;align-items:center;
  margin:1.4rem 0 .4rem}
.ctl-group{display:flex;align-items:center;gap:.5rem}
.ctl-lab{font-family:"IBM Plex Mono",monospace;font-size:.62rem;
  letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3)}
.seg{display:inline-flex;border:1px solid var(--rule-2);border-radius:3px;
  overflow:hidden;background:var(--card)}
.seg button{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
  padding:.32rem .7rem;border:0;background:transparent;color:var(--ink-2);
  cursor:pointer;border-right:1px solid var(--rule)}
.seg button:last-child{border-right:0}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--ground)}
.seg button:hover:not([aria-pressed="true"]){background:var(--sunk)}

figure.chart{margin:1.1rem 0 0;background:var(--chart-bg);
  border:1px solid var(--rule);border-radius:3px;padding:16px 14px 8px}
figure.chart figcaption{font-family:"IBM Plex Mono",monospace;font-size:.68rem;
  letter-spacing:.06em;color:var(--ink-3);margin-bottom:.7rem;padding:0 4px}
.legend{display:flex;gap:1.2rem;flex-wrap:wrap;padding:0 4px .5rem;
  font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--ink-2)}
.legend span{display:inline-flex;align-items:center;gap:.4rem}
.swatch{width:14px;height:3px;border-radius:2px;display:inline-block}
.chartsvg{display:block;width:100%;height:auto;overflow:visible}
.gridline{stroke:var(--grid);stroke-width:1}
.axisline{stroke:var(--axis);stroke-width:1}
.tick{font-family:"IBM Plex Mono",monospace;font-size:9.5px;fill:var(--ink-3)}
.dlab{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600}
.refline{stroke:var(--ink-3);stroke-width:1;stroke-dasharray:3 3}
.reflab{font-family:"IBM Plex Mono",monospace;font-size:9px;fill:var(--ink-3)}
.hitzone{fill:transparent;cursor:crosshair}
.hover-v{stroke:var(--ink-3);stroke-width:1;opacity:0}
.tipbox{position:absolute;pointer-events:none;background:var(--card);
  border:1px solid var(--rule-2);border-radius:3px;padding:.45rem .6rem;
  font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--ink);
  box-shadow:var(--shadow);opacity:0;transition:opacity .1s;white-space:nowrap;
  z-index:5}
.chartwrap{position:relative}
details.tbl{margin:.8rem 0 0}
details.tbl summary{font-family:"IBM Plex Mono",monospace;font-size:.68rem;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);
  cursor:pointer;padding:.3rem 0}
details.tbl summary:hover{color:var(--ink-2)}

.simgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:1.1rem;margin:1.3rem 0}
.simstat{background:var(--card);border:1px solid var(--rule);border-radius:3px;
  padding:14px 16px}
.simstat .k{font-family:"IBM Plex Mono",monospace;font-size:.6rem;
  letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3)}
.simstat .v{font-family:"IBM Plex Mono",monospace;font-size:1.7rem;
  font-weight:600;line-height:1.1;margin-top:.4rem;
  font-variant-numeric:tabular-nums}
.runbtn{font-family:"IBM Plex Mono",monospace;font-size:.75rem;
  padding:.45rem 1.1rem;border:1px solid var(--ink);border-radius:3px;
  background:var(--ink);color:var(--ground);cursor:pointer}
.runbtn:hover{opacity:.85}
.streak{display:flex;flex-wrap:wrap;gap:2px;margin:.9rem 0 .2rem}
.streak i{width:9px;height:16px;border-radius:1px;display:block}
@media (prefers-reduced-motion:reduce){.tipbox{transition:none}}
"""

JS = r"""
(function(){
  var D = window.PATHDATA;
  if(!D) return;
  var STATES = [["break_up","Break up"],["break_dn","Break down"],
                ["reject_up","Reject above"],["reject_dn","Reject below"]];
  var RS = ["81","243","729"];
  var sel = {reach:{st:"break_up",R:"81"}, first:{st:"break_up",R:"81"}};

  function el(t,c,txt){var e=document.createElement(t);
    if(c)e.className=c; if(txt!=null)e.textContent=txt; return e;}
  function fmtPct(x){return (x*100).toFixed(1)+"%";}

  /* ---------- generic line chart ---------- */
  function lineChart(host, series, opts){
    var W=680, H=270, ml=44, mr=14, mt=10, mb=34;
    var xs = opts.xs, y0 = opts.y0, y1 = opts.y1;
    var px = function(i){return ml + (W-ml-mr)*(i/(xs.length-1));};
    var py = function(v){return mt + (H-mt-mb)*(1-(v-y0)/(y1-y0));};
    var s = '<svg class="chartsvg" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'
          + opts.aria + '">';
    var steps = opts.yticks;
    steps.forEach(function(v){
      s += '<line class="gridline" x1="'+ml+'" y1="'+py(v).toFixed(1)+'" x2="'
         + (W-mr)+'" y2="'+py(v).toFixed(1)+'"/>';
      s += '<text class="tick" x="'+(ml-7)+'" y="'+(py(v)+3.2).toFixed(1)
         + '" text-anchor="end">'+(v*100).toFixed(0)+'%</text>';
    });
    if(opts.ref!=null){
      s += '<line class="refline" x1="'+ml+'" y1="'+py(opts.ref).toFixed(1)
         + '" x2="'+(W-mr)+'" y2="'+py(opts.ref).toFixed(1)+'"/>';
      s += '<text class="reflab" x="'+(W-mr)+'" y="'+(py(opts.ref)-5).toFixed(1)
         + '" text-anchor="end">'+opts.reflab+'</text>';
    }
    s += '<line class="axisline" x1="'+ml+'" y1="'+(H-mb)+'" x2="'+(W-mr)
       + '" y2="'+(H-mb)+'"/>';
    xs.forEach(function(x,i){
      s += '<text class="tick" x="'+px(i).toFixed(1)+'" y="'+(H-mb+15)
         + '" text-anchor="middle">'+x+'</text>';
    });
    s += '<text class="tick" x="'+((ml+W-mr)/2)+'" y="'+(H-4)
       + '" text-anchor="middle">'+opts.xlab+'</text>';
    series.forEach(function(se,si){
      var d = se.v.map(function(v,i){
        return (i?"L":"M")+px(i).toFixed(1)+" "+py(v).toFixed(1);}).join(" ");
      s += '<path d="'+d+'" fill="none" stroke="'+se.color+'" stroke-width="2"'
         + (se.dash?' stroke-dasharray="4 3"':'')
         + ' stroke-linejoin="round" stroke-linecap="round"/>';
      se.v.forEach(function(v,i){
        s += '<circle cx="'+px(i).toFixed(1)+'" cy="'+py(v).toFixed(1)
           + '" r="3.2" fill="'+se.color+'" stroke="var(--chart-bg)"'
           + ' stroke-width="2"/>';
      });
      // Direct label on the first point, so identity is never colour-alone.
      // Staggered by series index: on the first-touch chart the two lines sit
      // almost exactly on top of each other -- which is the finding -- so
      // labels anchored to their own y overprint into an unreadable smudge.
      s += '<text class="dlab" x="'+(px(0)+7)+'" y="'
         + (py(se.v[0]) + (si === 0 ? -9 : 16)).toFixed(1)
         + '" fill="'+se.color+'">'+se.name+'</text>';
    });
    s += '<line class="hover-v" x1="0" y1="'+mt+'" x2="0" y2="'+(H-mb)+'"/>';
    xs.forEach(function(x,i){
      var w=(W-ml-mr)/(xs.length-1);
      s += '<rect class="hitzone" data-i="'+i+'" x="'+(px(i)-w/2).toFixed(1)
         + '" y="'+mt+'" width="'+w.toFixed(1)+'" height="'+(H-mb-mt)+'"/>';
    });
    s += '</svg>';
    host.innerHTML = s;

    var svg = host.querySelector("svg"), vline = host.querySelector(".hover-v");
    var tip = host.parentNode.querySelector(".tipbox");
    host.querySelectorAll(".hitzone").forEach(function(z){
      function show(ev){
        var i = +z.dataset.i;
        vline.setAttribute("x1", px(i)); vline.setAttribute("x2", px(i));
        vline.style.opacity = .55;
        var html = "<b>"+opts.xlab.split("(")[0].trim()+" "+xs[i]+"</b>";
        series.forEach(function(se){
          html += "<br>"+se.name+": "+fmtPct(se.v[i]);
        });
        if(opts.extra) html += opts.extra(i);
        tip.innerHTML = html;
        var r = host.getBoundingClientRect();
        var sx = px(i)/W*r.width;
        tip.style.left = Math.min(Math.max(sx-60,0), r.width-160)+"px";
        tip.style.top = "6px";
        tip.style.opacity = 1;
      }
      z.addEventListener("mousemove", show);
      z.addEventListener("mouseenter", show);
      z.addEventListener("mouseleave", function(){
        tip.style.opacity=0; vline.style.opacity=0;});
    });
  }

  /* ---------- segmented controls ---------- */
  function controls(host, which, redraw){
    var wrap = el("div","ctl");
    function group(label, items, key){
      var g = el("div","ctl-group");
      g.appendChild(el("span","ctl-lab",label));
      var seg = el("div","seg");
      items.forEach(function(it){
        var b = el("button",null,it[1]);
        b.setAttribute("aria-pressed", sel[which][key]===it[0]);
        b.onclick = function(){
          sel[which][key] = it[0];
          seg.querySelectorAll("button").forEach(function(x){
            x.setAttribute("aria-pressed", x.textContent===it[1]);});
          redraw();
        };
        seg.appendChild(b);
      });
      g.appendChild(seg); wrap.appendChild(g);
    }
    group("State", STATES, "st");
    group("Block", RS.map(function(r){return [r,"R="+r];}), "R");
    host.appendChild(wrap);
  }

  /* ---------- 1. reach map ---------- */
  var rHost = document.getElementById("reach-app");
  if(rHost){
    var rBody = el("div");
    controls(rHost, "reach", drawReach);
    rHost.appendChild(rBody);
    function drawReach(){
      var st = sel.reach.st, R = sel.reach.R;
      var d = (D.reach[R]||{})[st];
      rBody.innerHTML = "";
      if(!d){ rBody.appendChild(el("p","dim",
        "Not enough events at this block size to measure.")); return; }
      var ks=[], on=[], back=[];
      for(var k=1;k<=12;k++){
        if(d.rows[k]==null) continue;
        ks.push(k); on.push(d.rows[k].p);
        var b = d.rows[-k]; if(b!=null) back.push(b.p);
      }
      var series=[{name:"Toward",v:on,color:"var(--s1)"}];
      if(back.length===ks.length)
        series.push({name:"Against",v:back,color:"var(--s2)"});
      var wrap = el("div","chartwrap");
      var fig = el("figure","chart");
      fig.appendChild(el("figcaption",null,
        "Reach probability — "+d.n.toLocaleString()+" events, R="+R));
      var lg = el("div","legend");
      lg.innerHTML = '<span><i class="swatch" style="background:var(--s1)"></i>'
        + 'Toward — levels in the direction of travel</span>'
        + (back.length===ks.length
           ? '<span><i class="swatch" style="background:var(--s2)"></i>'
             + 'Against — the same number of levels the other way</span>' : '');
      fig.appendChild(lg);
      var cv = el("div"); fig.appendChild(cv);
      wrap.appendChild(fig);
      var tip = el("div","tipbox"); wrap.appendChild(tip);
      rBody.appendChild(wrap);
      lineChart(cv, series, {xs:ks, y0:0.3, y1:1.0,
        yticks:[0.4,0.6,0.8,1.0], xlab:"levels away (k)",
        aria:"reach probability by levels away"});
      var t = el("details","tbl");
      var rows = ks.map(function(k,i){
        return "<tr><td class='num'>"+k+"</td><td class='num big'>"
          + fmtPct(on[i])+"</td><td class='num dim'>"
          + (back.length===ks.length?fmtPct(back[i]):"—")
          + "</td><td class='num dim'>"+fmtPct(d.rows[k].null)+"</td></tr>";}).join("");
      t.innerHTML = "<summary>Show the numbers</summary><div class='scroll'>"
        + "<table><thead><tr><th class='num'>k</th><th class='num'>Toward</th>"
        + "<th class='num'>Against</th><th class='num'>Shifted lattices</th>"
        + "</tr></thead><tbody>"+rows+"</tbody></table></div>";
      rBody.appendChild(t);
    }
    drawReach();
  }

  /* ---------- 2. which comes first ---------- */
  var fHost = document.getElementById("first-app");
  if(fHost){
    var fBody = el("div");
    controls(fHost, "first", drawFirst);
    fHost.appendChild(fBody);
    function drawFirst(){
      var st = sel.first.st, R = sel.first.R;
      var d = (D.first[R]||{})[st], s = (D.stats[R]||{})[st];
      fBody.innerHTML = "";
      if(!d){ fBody.appendChild(el("p","dim",
        "Not enough events at this block size to measure.")); return; }
      var ks=[], tv=[], nv=[];
      for(var k=1;k<=6;k++){
        if(d[k]==null) continue;
        ks.push(k); tv.push(d[k].p); nv.push(d[k].null);
      }
      var wrap = el("div","chartwrap");
      var fig = el("figure","chart");
      fig.appendChild(el("figcaption",null,
        "P(reach k levels toward, before k levels against) — R="+R));
      var lg = el("div","legend");
      lg.innerHTML = '<span><i class="swatch" style="background:var(--s1)"></i>'
        + 'Goldbach lattice</span><span><i class="swatch" '
        + 'style="background:var(--s2)"></i>Shifted lattices (null)</span>';
      fig.appendChild(lg);
      var cv = el("div"); fig.appendChild(cv);
      wrap.appendChild(fig);
      var tip = el("div","tipbox"); wrap.appendChild(tip);
      fBody.appendChild(wrap);
      lineChart(cv, [
        {name:"Goldbach",v:tv,color:"var(--s1)"},
        {name:"Shifted",v:nv,color:"var(--s2)",dash:true}
      ], {xs:ks, y0:0.45, y1:0.68, yticks:[0.50,0.55,0.60,0.65],
          ref:0.5, reflab:"coin flip", xlab:"levels away (k)",
          aria:"first-touch probability by levels away",
          extra:function(i){
            var k=ks[i], ci=s&&s[k];
            return ci ? "<br>95% CI ["+fmtPct(ci.lo)+", "+fmtPct(ci.hi)+"]"
                      + "<br>"+ci.n.toLocaleString()+" events / "
                      + ci.days.toLocaleString()+" days" : "";}});
      var rows = ks.map(function(k,i){
        var ci = s&&s[k];
        return "<tr><td class='num'>"+k+"</td><td class='num dim'>"
          + (ci?ci.n.toLocaleString():"—")+"</td><td class='num big'>"
          + fmtPct(tv[i])+"</td><td class='num dim'>"
          + (ci?"["+fmtPct(ci.lo)+", "+fmtPct(ci.hi)+"]":"—")
          + "</td><td class='num dim'>"+fmtPct(nv[i])+"</td><td class='num'>"
          + (d[k].z>=0?"+":"")+d[k].z.toFixed(2)+"</td></tr>";}).join("");
      var t = el("details","tbl");
      t.innerHTML = "<summary>Show the numbers</summary><div class='scroll'>"
        + "<table><thead><tr><th class='num'>k</th><th class='num'>Events</th>"
        + "<th class='num'>Goldbach</th><th class='num'>95% CI by day</th>"
        + "<th class='num'>Shifted</th><th class='num'>z</th></tr></thead>"
        + "<tbody>"+rows+"</tbody></table></div>";
      fBody.appendChild(t);
    }
    drawFirst();
  }

  /* ---------- 3. what a 60% edge feels like ---------- */
  var sHost = document.getElementById("sim-app");
  if(sHost){
    var N = 120;
    function runOnce(p){
      var seq=[], best=0, cur=0;
      for(var i=0;i<N;i++){
        var w = Math.random() < p;
        seq.push(w);
        cur = w ? cur+1 : 0;
        if(cur>best) best=cur;
      }
      return {seq:seq, best:best, wins:seq.filter(Boolean).length};
    }
    function draw(){
      var p = 0.5958;
      var a = runOnce(p), b = runOnce(0.50);
      var bestsA=[], bestsB=[];
      for(var t=0;t<4000;t++){
        bestsA.push(runOnce(p).best); bestsB.push(runOnce(0.50).best);
      }
      var mean = function(x){return x.reduce(function(s,v){return s+v;},0)/x.length;};
      var ge = function(x,v){return x.filter(function(y){return y>=v;}).length/x.length;};
      sHost.innerHTML = "";
      var g = el("div","simgrid");
      [["Longest win streak, 60% process", mean(bestsA).toFixed(1), "var(--s1)"],
       ["Longest win streak, coin flip", mean(bestsB).toFixed(1), "var(--s2)"],
       ["Chance of a run of 8+, 60%", (ge(bestsA,8)*100).toFixed(0)+"%", "var(--s1)"],
       ["Chance of a run of 8+, coin flip", (ge(bestsB,8)*100).toFixed(0)+"%", "var(--s2)"]
      ].forEach(function(r){
        var c = el("div","simstat");
        c.appendChild(el("div","k",r[0]));
        var v = el("div","v",r[1]); v.style.color = r[2];
        c.appendChild(v); g.appendChild(c);
      });
      sHost.appendChild(g);
      [["This is 120 draws at the measured 59.6%", a, "var(--s1)"],
       ["This is 120 draws at a coin flip", b, "var(--s2)"]].forEach(function(r){
        var lab = el("div","ctl-lab", r[0] + "  —  " + r[1].wins
                     + " hits, longest run " + r[1].best);
        lab.style.marginTop = "1rem";
        sHost.appendChild(lab);
        var s = el("div","streak");
        r[1].seq.forEach(function(w){
          var i = el("i");
          i.style.background = w ? r[2] : "var(--sunk)";
          s.appendChild(i);
        });
        sHost.appendChild(s);
      });
      var btn = el("button","runbtn","Run it again");
      btn.onclick = draw;
      btn.style.marginTop = "1.1rem";
      sHost.appendChild(btn);
    }
    draw();
  }
})();
"""


def html(D):
    """The two interactive sections plus the simulation."""
    data = json.dumps({"reach": D["paths"], "first": D["firsttouch"],
                       "stats": D["pathstats"]}, separators=(",", ":"))
    ft = D["firsttouch"]["81"]
    bu = ft["break_up"]["1"]
    bd = ft["break_dn"]["1"]
    ru = ft["reject_up"]["1"]
    st = D["pathstats"]["81"]
    return """
<div class="col">
<section id="paths">
  <div class="sec-head"><h2>If this breaks, where does price go?</h2>
    <span class="chip chip-good">Usable</span></div>
  <p>No stop, no target, no expectancy &mdash; just destinations. Two states you
  can name the moment a bar closes, and then how often price reaches each level
  beyond. Distance is counted in <b>levels</b> rather than points, because the
  Goldbach gaps are uneven and "price travels to the next level" is the claim as
  stated.</p>
</section>
</div>

<div id="reach-app"></div>

<div class="col">
  <div class="note good">
    <p><strong>These are real base rates.</strong> Break a level at R=81 and
    price reaches the next one %(bu1)s of the time inside eight hours; three
    levels on, %(bu3)s. Reject a level and it reaches one level away %(ru1)s of
    the time. You can plan around numbers like these whatever their origin.</p>
  </div>
  <div class="note bad">
    <p><strong>But switch the chart to "Against" and the problem appears.</strong>
    After an upward break price reaches the next level up %(bu1)s of the time
    &mdash; and the next level <em>down</em> %(bk1)s of the time. After a
    rejection it goes one level away %(ru1)s of the time and back through the
    rejected level %(rk1)s of the time.</p>
    <p>It does both, nearly always. Over any horizon long enough to be useful,
    price touches everything nearby. A reach probability cannot tell a path from
    diffusion &mdash; so the destination question is really an <em>ordering</em>
    question.</p>
  </div>
</div>

<div class="col">
<section id="first">
  <div class="sec-head"><h2>Which one does it reach first?</h2>
    <span class="chip chip-acc">Real, not Goldbach</span></div>
  <p>The same events, asked properly: does price reach <b>k levels in the
  direction of travel</b> before <b>k levels against</b> it? Same number of steps
  each way on the lattice's own terms. Nothing is risked and nothing is exited
  &mdash; this is an ordering statistic, not a bracket.</p>
</section>
</div>

<div id="first-app"></div>

<div class="col">
  <div class="note good">
    <p><strong>Your read of the mechanism is right.</strong> All four states sit
    well clear of a coin flip at one level out: break up <b>%(bu)s</b>, break
    down <b>%(bd)s</b>, reject <b>%(ru)s</b>. Day-clustered across thousands of
    trading days, every interval clears 50%% comfortably.</p>
  </div>
  <p>Two things matter more than the headline. First, <b>the structure is almost
  entirely in the first step</b>: %(bu)s at one level out, %(bu6)s at six. Project
  further and it converges to a coin flip, so the data supports one leg, weakly
  supports two, and says nothing past that.</p>
  <p>Second, <b>downward breaks continue harder than upward ones</b> &mdash;
  %(bd)s against %(bu)s. That is a real asymmetry in the tape rather than drift,
  which would push the other way.</p>
  <div class="note bad">
    <p><strong>And it is not Goldbach.</strong> Switch the chart's second series
    on: shifted lattices give the same numbers to a tenth of a point. Across 48
    cells two pass |z|&nbsp;=&nbsp;3 and they have <em>opposite signs</em>, the
    larger being R=243 reject-above at six levels, where the true lattice
    <em>underperforms</em> its shifted twins at z&nbsp;&minus;4.03.</p>
    <p>The cause is geometry. A break leaves price just past the level and so
    nearer the next one; a rejection leaves it just short. Draw the lines at any
    offset and the head start is identical.</p>
  </div>
</div>

<div class="col">
<section id="sim">
  <div class="sec-head"><h2>What a 60%% edge looks like</h2>
    <span class="eyebrow">Simulation</span></div>
  <p>This is the part worth sitting with. Below are 120 draws from the measured
  59.6%% process and 120 from a coin flip, plus the streak statistics over 4,000
  simulated runs of each. Run it a few times.</p>
</section>
</div>

<div id="sim-app"></div>

<div class="col">
  <div class="note key">
    <p><strong>A 60%% process throws long winning streaks constantly.</strong>
    Runs of eight and nine are ordinary, not remarkable &mdash; and a coin flip
    produces them too, just less often. Neither strip looks random while you are
    living through it.</p>
    <p>This is the honest explanation for "these levels work, they're crazy
    accurate many times and sometimes not much". Both halves of that sentence are
    what a 60%% first-step rate feels like from the inside. The rate is real. What
    the eye cannot do &mdash; what nobody's eye can do &mdash; is tell it from the
    orange strip without counting several hundred of them.</p>
  </div>
</div>

<script id="pathdata" type="application/json">%(data)s</script>
<script>window.PATHDATA = JSON.parse(document.getElementById("pathdata").textContent);</script>
<script>%(js)s</script>
""" % {
        "data": data, "js": JS,
        "bu": "%.1f%%" % (bu["p"] * 100), "bd": "%.1f%%" % (bd["p"] * 100),
        "ru": "%.1f%%" % (ru["p"] * 100),
        "bu6": "%.1f%%" % (ft["break_up"]["6"]["p"] * 100),
        "bu1": "%.1f%%" % (D["paths"]["81"]["break_up"]["rows"]["1"]["p"] * 100),
        "bu3": "%.1f%%" % (D["paths"]["81"]["break_up"]["rows"]["3"]["p"] * 100),
        "bk1": "%.1f%%" % (D["paths"]["81"]["break_up"]["rows"]["-1"]["p"] * 100),
        "ru1": "%.1f%%" % (D["paths"]["81"]["reject_up"]["rows"]["1"]["p"] * 100),
        "rk1": "%.1f%%" % (D["paths"]["81"]["reject_up"]["rows"]["-1"]["p"] * 100),
    }
