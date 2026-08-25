"""The fixed-clock explorer: choose a level, an arrival side and a trade side,
and read the stats at every hold.

The static table in the report showed one slice of a cube with 336 cells in it.
This exposes the whole thing. FADE and FOLLOW are exact mirrors trade by trade,
so only the fade side is stored and the follow side is derived in the browser --
mean and median negate, best and worst swap, the two excursions swap, and the
hit rate becomes the stored loss rate rather than one minus the win rate, since
a trade finishing exactly flat is neither.

The bar chart is anchored at zero and uses a single hue: position already
encodes the sign of a P&L, so colour would be redundant, and the reserved
status palette stays reserved.
"""
import json

CSS = """
.clockgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:.9rem;margin:1.2rem 0}
.zerobar{fill:var(--s1)}
.zeroline{stroke:var(--ink);stroke-width:1.5}
.nulltick{stroke:var(--ink-3);stroke-width:2;stroke-dasharray:2 2}
.barlab{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;
  fill:var(--ink);stroke:var(--chart-bg);stroke-width:3px;paint-order:stroke;
  stroke-linejoin:round}
.clockwarn{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
  color:var(--ink-3);margin:.6rem 0}
"""

JS = r"""
(function(){
  var C = window.CLOCKDATA;
  if(!C) return;
  var host = document.getElementById("clock-app");
  if(!host) return;
  var COST = 0.45;

  var LEVELS = [["any","All 20"],["boundary","0 / 100 boundary"],["eq","50 EQ"],
                ["ext","97 & 3"],["fv","29 & 71 FV"],["gip","17 & 83 GIP"],
                ["llod","7 & 93 LLOD"]];
  var RS = ["81","243","729"];
  var HOLDS = ["15","30","45","60"];
  var sel = {R:"243", lv:"boundary", side:"below", trade:"fade"};

  function el(t,c,x){var e=document.createElement(t);
    if(c)e.className=c; if(x!=null)e.textContent=x; return e;}

  /* fade is stored; follow is its exact mirror, trade by trade */
  function view(s){
    if(sel.trade==="fade") return {
      n:s.n, win:s.win, mean:s.mean, med:s.med, best:s.best, worst:s.worst,
      mfe:s.mfe, mae:s.mae, pf:s.pf, lo:s.lo, hi:s.hi, null_:s.null, days:s.days};
    return {
      n:s.n, win:s.loss, mean:-s.mean, med:-s.med, best:-s.worst, worst:-s.best,
      mfe:s.mae, mae:s.mfe, pf:s.pf_follow, lo:-s.hi, hi:-s.lo,
      null_:(s.null==null?null:-s.null), days:s.days};
  }

  function seg(label, items, key){
    var g = el("div","ctl-group");
    g.appendChild(el("span","ctl-lab",label));
    var s = el("div","seg");
    items.forEach(function(it){
      var b = el("button",null,it[1]);
      b.setAttribute("aria-pressed", sel[key]===it[0]);
      b.onclick = function(){
        sel[key]=it[0];
        s.querySelectorAll("button").forEach(function(x,i){
          x.setAttribute("aria-pressed", items[i][0]===it[0]);});
        draw();
      };
      s.appendChild(b);
    });
    g.appendChild(s);
    return g;
  }

  var bar = el("div","ctl");
  bar.appendChild(seg("Block", RS.map(function(r){return [r,"R="+r];}), "R"));
  bar.appendChild(seg("Level", LEVELS, "lv"));
  host.appendChild(bar);
  var bar2 = el("div","ctl");
  bar2.appendChild(seg("Reached", [["below","from below"],["above","from above"]], "side"));
  bar2.appendChild(seg("Trade", [["fade","fade it"],["follow","follow it"]], "trade"));
  host.appendChild(bar2);
  var body = el("div");
  host.appendChild(body);

  function chart(rows){
    var W=680,H=200,ml=46,mr=14,mt=14,mb=30;
    var vals = rows.map(function(r){return r.net;});
    var nulls = rows.map(function(r){return r.null_==null?null:r.null_-COST;});
    var all = vals.concat(nulls.filter(function(x){return x!=null;}));
    var mx = Math.max(0.6, Math.max.apply(null, all.map(Math.abs))*1.35);
    var y = function(v){return mt+(H-mt-mb)*(1-(v+mx)/(2*mx));};
    var bw = (W-ml-mr)/rows.length;
    var s = '<svg class="chartsvg" viewBox="0 0 '+W+' '+H+'" role="img"'
          + ' aria-label="net points by holding time">';
    [-mx/2,0,mx/2].forEach(function(v){
      s += '<line class="gridline" x1="'+ml+'" y1="'+y(v).toFixed(1)+'" x2="'
         + (W-mr)+'" y2="'+y(v).toFixed(1)+'"/>'
         + '<text class="tick" x="'+(ml-7)+'" y="'+(y(v)+3.2).toFixed(1)
         + '" text-anchor="end">'+v.toFixed(1)+'</text>';
    });
    rows.forEach(function(r,i){
      var cx = ml+bw*i+bw/2, w = Math.min(48,bw*0.5);
      var y0 = y(0), y1 = y(r.net);
      s += '<rect class="zerobar" x="'+(cx-w/2).toFixed(1)+'" y="'
         + Math.min(y0,y1).toFixed(1)+'" width="'+w.toFixed(1)+'" height="'
         + Math.max(1,Math.abs(y1-y0)).toFixed(1)+'" rx="2"/>';
      if(nulls[i]!=null)
        s += '<line class="nulltick" x1="'+(cx-w/2-4).toFixed(1)+'" y1="'
           + y(nulls[i]).toFixed(1)+'" x2="'+(cx+w/2+4).toFixed(1)+'" y2="'
           + y(nulls[i]).toFixed(1)+'"/>';
      // label last, with a background-coloured halo, so it stays readable
      // where a small bar and its null tick land on top of each other
      s += '<text class="barlab" x="'+cx.toFixed(1)+'" y="'
         + (y1 + (r.net>=0?-8:16)).toFixed(1)+'" text-anchor="middle">'
         + (r.net>=0?"+":"")+r.net.toFixed(2)+'</text>';
      s += '<text class="tick" x="'+cx.toFixed(1)+'" y="'+(H-mb+16)
         + '" text-anchor="middle">'+HOLDS[i]+' min</text>';
    });
    s += '<line class="zeroline" x1="'+ml+'" y1="'+y(0).toFixed(1)+'" x2="'
       + (W-mr)+'" y2="'+y(0).toFixed(1)+'"/></svg>';
    return s;
  }

  function draw(){
    body.innerHTML="";
    var node = ((C[sel.R]||{})[sel.lv]||{})[sel.side];
    if(!node){
      body.appendChild(el("p","clockwarn",
        "Fewer than 200 arrivals in this combination — nothing worth reporting."));
      return;
    }
    var rows = HOLDS.map(function(hd){
      var v = view(node[hd]); v.net = v.mean - COST; v.hold = hd; return v;});

    var fig = el("figure","chart");
    fig.appendChild(el("figcaption",null,
      "Net points per trade after costs — dashed tick is the same cell on shifted lattices"));
    var cv = el("div"); cv.innerHTML = chart(rows); fig.appendChild(cv);
    body.appendChild(fig);

    var r0 = rows[0];
    body.appendChild(el("div","clockwarn",
      r0.n.toLocaleString()+" arrivals across "+r0.days.toLocaleString()
      +" days · entry filled at the level · exit at the close, no stop, no target"));

    var head = ["Hold","n","Win","Mean","Net","Median","Best","Worst",
                "MFE avg","MAE avg","PF","95% CI on net"];
    var t = '<div class="scroll"><table><thead><tr>'
      + head.map(function(x){return '<th class="num">'+x+'</th>';}).join("")
      + '</tr></thead><tbody>';
    rows.forEach(function(r){
      t += '<tr><td class="num">'+r.hold+'m</td>'
        + '<td class="num dim">'+r.n.toLocaleString()+'</td>'
        + '<td class="num">'+(r.win*100).toFixed(1)+'%</td>'
        + '<td class="num '+(r.mean>=0?"pos":"neg")+'">'+(r.mean>=0?"+":"")+r.mean.toFixed(2)+'</td>'
        + '<td class="num big '+(r.net>=0?"pos":"neg")+'">'+(r.net>=0?"+":"")+r.net.toFixed(2)+'</td>'
        + '<td class="num '+(r.med>=0?"pos":"neg")+'">'+(r.med>=0?"+":"")+r.med.toFixed(2)+'</td>'
        + '<td class="num dim">'+r.best.toFixed(0)+'</td>'
        + '<td class="num dim">'+r.worst.toFixed(0)+'</td>'
        + '<td class="num dim">'+r.mfe.toFixed(1)+'</td>'
        + '<td class="num dim">'+r.mae.toFixed(1)+'</td>'
        + '<td class="num">'+(r.pf==null?"—":r.pf.toFixed(2))+'</td>'
        + '<td class="num dim">['+(r.lo>=0?"+":"")+r.lo.toFixed(2)+', '
        + (r.hi>=0?"+":"")+r.hi.toFixed(2)+']</td></tr>';
    });
    t += '</tbody></table></div>';
    var d = el("div"); d.innerHTML = t; body.appendChild(d);

    var sig = rows.filter(function(r){return r.lo>0;}).length;
    var note = el("div","clockwarn");
    note.textContent = sig
      ? sig+" of 4 holds have a day-clustered interval above zero."
      : "No hold has a day-clustered interval above zero in this combination.";
    body.appendChild(note);
  }
  draw();
})();
"""


def html(D):
    data = json.dumps(D["clock"], separators=(",", ":"))
    cells = sum(len(s) for R in D["clock"] for g in D["clock"][R]
                for s in [D["clock"][R][g]]) * 4
    return """
<div class="col">
<section id="clock-explore">
  <div class="sec-head"><h2>Pick a level and a clock</h2>
    <span class="eyebrow">Explorer</span></div>
  <p>The table above is one slice of a much larger cube. This is the whole
  thing: choose a block size, which Goldbach level, whether price arrived at it
  from below or from above, and whether you fade or follow &mdash; and read
  what happened at every holding time.</p>
  <p>Entry is filled at the level. Exit is the close 15, 30, 45 or 60 minutes
  later, whatever has happened in between. No stop, no target, nothing to tune.
  The dashed tick on each bar is the identical cell computed on shifted
  lattices; where the bar and the tick agree, whatever you are looking at is not
  a property of these levels.</p>
</section>
</div>

<div id="clock-app"></div>

<div class="col">
  <div class="note key">
    <p><strong>Worth doing before you read the conclusions.</strong> Try the
    boundary at R=243 from below, then switch to follow. Then try EQ. Then any
    level. The bars move around, and some combinations look excellent &mdash;
    but almost none has an interval that clears zero, and the shifted-lattice
    tick sits on top of the bar nearly everywhere.</p>
    <p>That is the whole study in one control panel: plenty of cells that look
    like something, almost none that survive being asked whether the lattice
    had anything to do with it.</p>
  </div>
</div>

<script id="clockdata" type="application/json">%(data)s</script>
<script>window.CLOCKDATA = JSON.parse(document.getElementById("clockdata").textContent);</script>
<script>%(js)s</script>
""" % {"data": data, "js": JS}
