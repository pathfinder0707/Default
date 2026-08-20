import numpy as np, pickle, json
from gbcore import node_at
rng=np.random.default_rng(42)
df=pickle.load(open('bars.pkl','rb')); N=len(df)
mod=df['mod'].to_numpy(); blk=df['blk'].to_numpy(); hi=df['h'].to_numpy(); lo=df['l'].to_numpy()
L=R=3
isH=np.zeros(N,bool); isL=np.zeros(N,bool)
for i in range(L,N-R):
    if blk[i-L]!=blk[i+R]: continue
    wh=hi[i-L:i+R+1]; wl=lo[i-L:i+R+1]
    if hi[i]==wh.max() and (wh[:L]<hi[i]).all() and (wh[L+1:]<hi[i]).all(): isH[i]=True
    if lo[i]==wl.min() and (wl[:L]>lo[i]).all() and (wl[L+1:]>lo[i]).all(): isL[i]=True
sw=np.flatnonzero(isH|isL)

# clock -> algo indices (MM-exact only, the strongest read)
A1I=np.full(1440,-1,np.int8); A2I=np.full(1440,-1,np.int8)
for m in range(1440):
    h,mi=divmod(m,60)
    a1=node_at(h,mi,1,1); a2=node_at(h,mi,2,1)
    if a1 and a1['pri'] and a1['dist']==0: A1I[m]=a1['idx']
    if a2 and a2['pri'] and a2['dist']==0: A2I[m]=a2['idx']

swmod=mod[sw]; swblk=blk[sw]
def count_steps(mods):
    a1=A1I[mods]; a2=A2I[mods]
    same=swblk[1:]==swblk[:-1]
    p1,c1=a1[:-1],a1[1:]; p2,c2=a2[:-1],a2[1:]
    ok1=same&(p1>=0)&(c1>=0); ok2=same&(p2>=0)&(c2>=0)
    d1=(c1-p1); d2=(p2-c2)
    fwd1=(ok1&(d1==1)).sum(); any1=ok1.sum()
    rev2=(ok2&(d2==1)).sum(); any2=ok2.sum()
    skip1=(ok1&(d1>1)&(d1<=3)).sum(); skip2=(ok2&(d2>1)&(d2<=3)).sum()
    return dict(a1_consec=int(fwd1),a1_pairs=int(any1),a1_skip=int(skip1),
                a2_consec=int(rev2),a2_pairs=int(any2),a2_skip=int(skip2))

obs=count_steps(swmod)
print("OBSERVED (buffer 3/3, MM-exact node reads only)")
print("  A1 consecutive forward steps : %6d / %6d pairs = %.4f"%(obs['a1_consec'],obs['a1_pairs'],obs['a1_consec']/obs['a1_pairs']))
print("  A1 valid skips (2-3)         : %6d           = %.4f"%(obs['a1_skip'],obs['a1_skip']/obs['a1_pairs']))
print("  A2 consecutive reverse steps : %6d / %6d pairs = %.4f"%(obs['a2_consec'],obs['a2_pairs'],obs['a2_consec']/obs['a2_pairs']))
print("  A2 valid skips (2-3)         : %6d           = %.4f"%(obs['a2_skip'],obs['a2_skip']/obs['a2_pairs']))

print("\nNULL 1 - rotate the clock (keeps swing times, moves the node map)")
r1={'a1':[],'a2':[]}
for k in range(1,60):
    A1r=np.roll(A1I,k); A2r=np.roll(A2I,k)
    a1=A1r[swmod]; a2=A2r[swmod]
    same=swblk[1:]==swblk[:-1]
    p1,c1=a1[:-1],a1[1:]; p2,c2=a2[:-1],a2[1:]
    ok1=same&(p1>=0)&(c1>=0); ok2=same&(p2>=0)&(c2>=0)
    r1['a1'].append(((ok1&((c1-p1)==1)).sum())/max(ok1.sum(),1))
    r1['a2'].append(((ok2&((p2-c2)==1)).sum())/max(ok2.sum(),1))
for nm,key,o,d in [("A1 forward",'a1',obs['a1_consec']/obs['a1_pairs'],'a1'),
                   ("A2 reverse",'a2',obs['a2_consec']/obs['a2_pairs'],'a2')]:
    arr=np.array(r1[key]); z=(o-arr.mean())/arr.std(ddof=1)
    print("  %-12s obs %.4f   null %.4f +/- %.4f   z=%+.2f   lift %+.2f%%"%(nm,o,arr.mean(),arr.std(ddof=1),z,(o/arr.mean()-1)*100))

print("\nNULL 2 - shuffle swing ORDER within each session block (destroys sequence, keeps times)")
r2={'a1':[],'a2':[]}
for it in range(200):
    sm=swmod.copy()
    for b in np.unique(swblk):
        m=swblk==b
        if m.sum()>1: sm[m]=rng.permutation(sm[m])
    s=count_steps(sm)
    r2['a1'].append(s['a1_consec']/max(s['a1_pairs'],1))
    r2['a2'].append(s['a2_consec']/max(s['a2_pairs'],1))
for nm,key,o in [("A1 forward",'a1',obs['a1_consec']/obs['a1_pairs']),
                 ("A2 reverse",'a2',obs['a2_consec']/obs['a2_pairs'])]:
    arr=np.array(r2[key]); z=(o-arr.mean())/arr.std(ddof=1)
    print("  %-12s obs %.4f   null %.4f +/- %.4f   z=%+.2f   lift %+.2f%%"%(nm,o,arr.mean(),arr.std(ddof=1),z,(o/arr.mean()-1)*100))

json.dump({'observed':obs,
  'rot_null':{k:[float(x) for x in v] for k,v in r1.items()},
  'shuf_null':{k:[float(x) for x in v] for k,v in r2.items()}},open('results_seq.json','w'),indent=2)
print("\nsaved results_seq.json")
