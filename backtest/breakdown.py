import pandas as pd, numpy as np, pickle, json
from gbcore import read_of

df=pickle.load(open('bars.pkl','rb')); N=len(df)
mod=df['mod'].to_numpy(); c=df['c'].to_numpy(); blk=df['blk'].to_numpy()
hi=df['h'].to_numpy(); lo=df['l'].to_numpy()

LUT=[read_of(m//60,m%60,1) for m in range(1440)]
q=np.array([0 if r is None else r['q'] for r in LUT],np.int8)
both=np.array([bool(r and r['both']) for r in LUT])
shared=np.array([bool(r and r['shared']) for r in LUT])
def labmask(lab):
    return np.array([bool(r and lab in r['labels']) for r in LUT])

def pivots(L,R):
    n=N; isH=np.zeros(n,bool); isL=np.zeros(n,bool)
    for i in range(L,n-R):
        if blk[i-L]!=blk[i+R]: continue
        wh=hi[i-L:i+R+1]; wl=lo[i-L:i+R+1]
        if hi[i]==wh.max() and (wh[:L]<hi[i]).all() and (wh[L+1:]<hi[i]).all(): isH[i]=True
        if lo[i]==wl.min() and (wl[:L]>lo[i]).all() and (wl[L+1:]>lo[i]).all(): isL[i]=True
    return isH,isL

isH,isL=pivots(3,3); sw=isH|isL
# significance filter: swing must stand out vs local ATR
tr=np.maximum(hi[1:]-lo[1:],np.abs(hi[1:]-c[:-1]))
tr=np.concatenate([[hi[0]-lo[0]],tr])
atr=pd.Series(tr).rolling(60,min_periods=20).mean().to_numpy()
swing_amp=np.full(N,np.nan)
for i in np.flatnonzero(sw):
    a=max(0,i-30); b=min(N,i+31)
    if blk[a]!=blk[b-1]: continue
    swing_amp[i]=(hi[i]-lo[a:b].min()) if isH[i] else (hi[a:b].max()-lo[i])
sig=sw&(swing_amp>2*atr)
print("swings 3/3        : %d"%sw.sum())
print("significant (>2ATR): %d  (%.1f%% of swings)"%(sig.sum(),sig.sum()/sw.sum()*100))

def rot_test(mask_clock, sel):
    """observed rate of sel-bars falling on mask_clock, vs 59 rotations"""
    smod=mod[sel]
    if len(smod)<200: return None
    obs=mask_clock[smod].mean()
    null=np.array([np.roll(mask_clock,k)[smod].mean() for k in range(1,60)])
    sd=null.std(ddof=1)
    return {'n':int(len(smod)),'obs':float(obs),'null':float(null.mean()),'sd':float(sd),
            'z':float((obs-null.mean())/sd) if sd>0 else 0.0,
            'lift':float(obs/null.mean()-1) if null.mean()>0 else 0.0}

out={}
MMX=(q==3)

print("\n=== A. swing quality tiers (buffer 3/3) ===")
for nm,sel in [("all swings",sw),("significant swings (>2ATR)",sig),
               ("highs only",isH),("lows only",isL)]:
    r=rot_test(MMX,sel)
    print("  %-28s n=%6d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%"%(nm,r['n'],r['obs'],r['null'],r['z'],r['lift']*100))
    out.setdefault('tiers',{})[nm]=r

print("\n=== B. by read quality of the clock minute ===")
for nm,mask in [("MM-exact (strong)",q==3),("MM +/-1 (medium)",q==2),("secondary only (weak)",q==1)]:
    r=rot_test(mask,sig)
    print("  %-24s clock-minutes %4d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%"%(nm,mask.sum(),r['obs'],r['null'],r['z'],r['lift']*100))
    out.setdefault('quality',{})[nm]=r

print("\n=== C. by node (MM-exact minutes only) ===")
nodes=['00','03/7','11/14','17/23','29/35','41/44','47/53','59/65','71/77']
for lab in nodes:
    mask=labmask(lab)&(q==3)
    if mask.sum()<12: 
        print("  %-8s clock-minutes %3d  (too few)"%(lab,mask.sum())); continue
    r=rot_test(mask,sig)
    flag=" <-- " if r and abs(r['z'])>2 else ""
    print("  %-8s clock-minutes %3d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%%s"%(lab,mask.sum(),r['obs'],r['null'],r['z'],r['lift']*100,flag))
    out.setdefault('nodes',{})[lab]=r

print("\n=== D. confluence ===")
for nm,mask in [("both algos fire",both&(q==3)),("shared node (same label)",shared&(q==3)),
                ("single algo only",(~both)&(q==3))]:
    r=rot_test(mask,sig)
    print("  %-26s clock-minutes %4d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%"%(nm,mask.sum(),r['obs'],r['null'],r['z'],r['lift']*100))
    out.setdefault('confluence',{})[nm]=r

print("\n=== E. by session / killzone (Zurich) ===")
KZ=[("Asia 01-05",60,300),("London KZ 08-11",480,660),("NY AM KZ 13-16",780,960),
    ("London Close 16-18",960,1080),("NY PM 18-20",1080,1200)]
for nm,a,b in KZ:
    inkz=(mod>=a)&(mod<b)
    sel=sig&inkz
    if sel.sum()<200: print("  %-22s too few swings"%nm); continue
    r=rot_test(MMX,sel)
    flag=" <-- " if abs(r['z'])>2 else ""
    print("  %-22s n=%6d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%%s"%(nm,r['n'],r['obs'],r['null'],r['z'],r['lift']*100,flag))
    out.setdefault('killzones',{})[nm]=r

print("\n=== F. by year (stability) ===")
yr=df['year'].to_numpy()
for y in [2023,2024,2025]:
    sel=sig&(yr==y)
    r=rot_test(MMX,sel)
    print("  %d  n=%6d  obs %.4f  null %.4f  z=%+.2f  lift %+.2f%%"%(y,r['n'],r['obs'],r['null'],r['z'],r['lift']*100))
    out.setdefault('years',{})[str(y)]=r

json.dump(out,open('results_breakdown.json','w'),indent=2)

zs=[v['z'] for grp in out.values() for v in grp.values() if v]
zs=np.array(zs)
print("\n=== MULTIPLE-COMPARISON CONTEXT ===")
print("  %d slices tested."%len(zs))
print("  |z|>2 : %d   (expected by chance at 5%%: %.1f)"%((np.abs(zs)>2).sum(),len(zs)*0.05))
print("  |z|>3 : %d   (expected by chance at 0.27%%: %.2f)"%((np.abs(zs)>3).sum(),len(zs)*0.0027))
print("  max |z| observed: %.2f"%np.abs(zs).max())
