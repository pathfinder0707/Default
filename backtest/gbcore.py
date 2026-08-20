"""GB-time engine, ported from the tested JS engine in gb-time-trader.html."""
A={1:[{'l':'00','v':[0],'term':False},
      {'l':'11/14','v':[11,14],'term':False},
      {'l':'41/44','v':[41,44],'term':False},
      {'l':'03/7','v':[3,7],'term':False},
      {'l':'17/23','v':[17,23],'term':False},
      {'l':'71/77 · 29/35','v':[71,77,29,35],'term':True,
       'groups':[{'l':'71/77','v':[71,77]},{'l':'29/35','v':[29,35]}]}],
   2:[{'l':'03/7','v':[3,7],'term':True},
      {'l':'59/65','v':[59,65],'term':False},
      {'l':'17/23','v':[17,23],'term':False},
      {'l':'11/14','v':[11,14],'term':False},
      {'l':'47/53','v':[47,50,53,56],'term':False},
      {'l':'29/35','v':[29,35],'term':False}]}

def methods(hh,mm):
    return [('MM',mm,True),('HH+MM',hh+mm,False),('|HH-MM|',abs(hh-mm),False)]

def hit_values(hh,mm,vals,tol):
    best=None
    for name,val,pri in methods(hh,mm):
        for t in vals:
            d=abs(val-t)
            if d<=tol:
                if best is None or (pri and not best[2]) or (pri==best[2] and d<best[0]):
                    best=(d,name,pri,t)
    return best   # (dist, method, is_primary, target)

def label_for(node,val):
    if 'groups' in node and val is not None:
        for g in node['groups']:
            if val in g['v']: return g['l']
    return node['l']

def node_at(hh,mm,algo,tol=1,no_secondary=False):
    best=None
    for i,node in enumerate(A[algo]):
        h=hit_values(hh,mm,node['v'],tol)
        if h and no_secondary and not h[2]: h=None
        if h and (best is None or (h[2] and not best[1][2]) or (h[2]==best[1][2] and h[0]<best[1][0])):
            best=(i,h,node)
    if best is None: return None
    i,h,node=best
    return {'idx':i,'dist':h[0],'method':h[1],'pri':h[2],'label':label_for(node,h[3]),
            'term':node['term']}

def quality(hit):
    if hit is None: return 0
    return 3 if (hit['pri'] and hit['dist']==0) else (2 if hit['pri'] else 1)

def read_of(hh,mm,tol=1):
    """Best read across both algos. Returns dict or None."""
    a1=node_at(hh,mm,1,tol); a2=node_at(hh,mm,2,tol)
    if a1 is None and a2 is None: return None
    q=max(quality(a1),quality(a2))
    labs=sorted({x['label'] for x in (a1,a2) if x})
    return {'a1':a1,'a2':a2,'q':q,'labels':labs,
            'both':bool(a1 and a2),
            'shared':bool(a1 and a2 and a1['label']==a2['label'])}
