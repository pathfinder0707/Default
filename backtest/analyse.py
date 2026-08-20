import pandas as pd, numpy as np, pickle, json
from gbcore import read_of, node_at, quality, A

df=pickle.load(open('bars.pkl','rb'))
N=len(df)

# ---------- clock lookup tables: for each of 1440 minutes-of-day ----------
LUT={}
for mod in range(1440):
    h,m=divmod(mod,60)
    r=read_of(h,m,1)
    LUT[mod]={'q':0 if r is None else r['q'],
              'labels':[] if r is None else r['labels'],
              'both':bool(r and r['both']),'shared':bool(r and r['shared']),
              'a1':(r['a1']['idx'] if r and r['a1'] else -1) if r else -1,
              'a2':(r['a2']['idx'] if r and r['a2'] else -1) if r else -1,
              'a1lab':(r['a1']['label'] if r and r['a1'] else None) if r else None,
              'a2lab':(r['a2']['label'] if r and r['a2'] else None) if r else None}
qarr=np.array([LUT[m]['q'] for m in range(1440)],dtype=np.int8)
MMEXACT=(qarr==3)
print("MM-exact minutes in clock: %d / 1440  (%.1f%%)"%(MMEXACT.sum(),MMEXACT.sum()/1440*100))

# ---------- pivot detection within contiguous blocks ----------
def pivots(df,L,R):
    hi=df['h'].to_numpy(); lo=df['l'].to_numpy(); blk=df['blk'].to_numpy()
    n=len(hi); isH=np.zeros(n,bool); isL=np.zeros(n,bool)
    for i in range(L,n-R):
        if blk[i-L]!=blk[i+R]: continue
        w_hi=hi[i-L:i+R+1]; w_lo=lo[i-L:i+R+1]
        if hi[i]==w_hi.max() and (w_hi[:L]<hi[i]).all() and (w_hi[L+1:]<hi[i]).all(): isH[i]=True
        if lo[i]==w_lo.min() and (w_lo[:L]>lo[i]).all() and (w_lo[L+1:]>lo[i]).all(): isL[i]=True
    return isH,isL

mod=df['mod'].to_numpy()
results={}
print("\nDetecting pivots...")
PIV={}
for L,R in [(2,2),(3,3),(5,5)]:
    isH,isL=pivots(df,L,R)
    PIV[(L,R)]=(isH,isL)
    print("  buffer %d/%d : %6d highs  %6d lows  (%.2f%% of bars)"%(L,R,isH.sum(),isL.sum(),(isH.sum()+isL.sum())/N*100))

# ---------- TEST 1: swing landing rate on MM-exact, with rotation null ----------
print("\n=== TEST 1: do confirmed swings land on MM-exact node minutes? ===")
base_rate=MMEXACT[mod].mean()
print("Empirical base rate (all bars, actual session distribution): %.4f  (%.2f%%)"%(base_rate,base_rate*100))
t1={}
for key in PIV:
    isH,isL=PIV[key]; sw=isH|isL
    swmod=mod[sw]
    obs=MMEXACT[swmod].mean()
    # rotation null: shift the clock by k minutes
    null=[]
    for k in range(1,60):
        rot=np.roll(MMEXACT,k)
        null.append(rot[swmod].mean())
    null=np.array(null)
    z=(obs-null.mean())/null.std(ddof=1)
    pct=(null<obs).mean()*100
    t1["%d/%d"%key]={'n':int(sw.sum()),'obs':float(obs),'base':float(base_rate),
                     'null_mean':float(null.mean()),'null_sd':float(null.std(ddof=1)),
                     'z':float(z),'pct_of_null_beaten':float(pct),
                     'lift':float(obs/null.mean()-1)}
    print("  buffer %-4s n=%6d  observed %.4f   rotation-null %.4f +/- %.4f   z=%+.2f   lift %+.2f%%"%(
        "%d/%d"%key,sw.sum(),obs,null.mean(),null.std(ddof=1),z,(obs/null.mean()-1)*100))
results['test1_swing_landing']=t1

# ---------- TEST 2: range expansion at node minutes ----------
print("\n=== TEST 2: is bar range elevated on MM-exact node minutes? ===")
rng=((df['h']-df['l'])/df['c']*10000).to_numpy()
obs_r=rng[MMEXACT[mod]].mean(); off_r=rng[~MMEXACT[mod]].mean()
null_r=[]
for k in range(1,60):
    rot=np.roll(MMEXACT,k); m=rot[mod]
    null_r.append(rng[m].mean()/rng[~m].mean())
null_r=np.array(null_r); obs_ratio=obs_r/off_r
z2=(obs_ratio-null_r.mean())/null_r.std(ddof=1)
print("  node minutes mean range   : %.3f bps"%obs_r)
print("  non-node minutes          : %.3f bps"%off_r)
print("  ratio                     : %.4f"%obs_ratio)
print("  rotation null ratio       : %.4f +/- %.4f   z=%+.2f"%(null_r.mean(),null_r.std(ddof=1),z2))
results['test2_range']={'node':float(obs_r),'nonnode':float(off_r),'ratio':float(obs_ratio),
   'null_mean':float(null_r.mean()),'null_sd':float(null_r.std(ddof=1)),'z':float(z2)}

# ---------- TEST 3: reversal rate at node minutes ----------
print("\n=== TEST 3: does price REVERSE at node minutes more than elsewhere? ===")
c=df['c'].to_numpy(); blk=df['blk'].to_numpy()
W=10
fwd=np.full(N,np.nan); bwd=np.full(N,np.nan)
valid=np.zeros(N,bool)
for i in range(W,N-W):
    if blk[i-W]==blk[i+W]:
        bwd[i]=c[i]-c[i-W]; fwd[i]=c[i+W]-c[i]; valid[i]=True
rev=valid&(np.sign(bwd)!=np.sign(fwd))&(bwd!=0)&(fwd!=0)
mnode=MMEXACT[mod]&valid
obs_rev=rev[mnode].mean(); off_rev=rev[valid&~MMEXACT[mod]].mean()
null_rev=[]
for k in range(1,60):
    rot=np.roll(MMEXACT,k); m=rot[mod]&valid
    null_rev.append(rev[m].mean())
null_rev=np.array(null_rev)
z3=(obs_rev-null_rev.mean())/null_rev.std(ddof=1)
print("  reversal rate at node     : %.4f"%obs_rev)
print("  at non-node               : %.4f"%off_rev)
print("  rotation null             : %.4f +/- %.4f   z=%+.2f"%(null_rev.mean(),null_rev.std(ddof=1),z3))
results['test3_reversal']={'node':float(obs_rev),'nonnode':float(off_rev),
   'null_mean':float(null_rev.mean()),'null_sd':float(null_rev.std(ddof=1)),'z':float(z3)}

json.dump(results,open('results_core.json','w'),indent=2)
print("\nsaved results_core.json")
