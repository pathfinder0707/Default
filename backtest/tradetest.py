import numpy as np, pickle, json
from gbcore import read_of
df=pickle.load(open('bars.pkl','rb')); N=len(df)
mod=df['mod'].to_numpy(); blk=df['blk'].to_numpy(); c=df['c'].to_numpy()
hi=df['h'].to_numpy(); lo=df['l'].to_numpy()
q=np.array([0 if (r:=read_of(m//60,m%60,1)) is None else r['q'] for m in range(1440)],np.int8)
MMX=(q==3)
node=MMX[mod]

SPREAD_BPS=1.0   # NAS100 CFD typical ~1 point on ~20000 = 0.5bp; 1bp is conservative-but-fair
res={}
print("Mean forward return after a node minute vs a non-node minute (bps, before costs)")
print("hold   node-long   nonnode-long    diff      node |move|  nonnode |move|")
print("-------------------------------------------------------------------------")
for H in [5,10,15,30,60]:
    fwd=np.full(N,np.nan)
    ok=np.zeros(N,bool)
    idx=np.arange(N-H)
    good=blk[idx]==blk[idx+H]
    fwd[idx[good]]=(c[idx[good]+H]-c[idx[good]])/c[idx[good]]*10000
    ok[idx[good]]=True
    a=fwd[ok&node]; b=fwd[ok&~node]
    print("%4dm  %+8.3f    %+8.3f     %+7.3f     %8.3f      %8.3f"%(
        H,a.mean(),b.mean(),a.mean()-b.mean(),np.abs(a).mean(),np.abs(b).mean()))
    res["hold%d"%H]={'node_mean':float(a.mean()),'nonnode_mean':float(b.mean()),
                     'node_absmove':float(np.abs(a).mean()),'nonnode_absmove':float(np.abs(b).mean()),
                     'n_node':int(len(a))}

print("\nDirectional rules at MM-exact nodes, 15-min hold, net of %.1fbp round-trip spread"%SPREAD_BPS)
print("rule                              trades    win%%     mean bps    total bps")
print("---------------------------------------------------------------------------")
H=15
fwd=np.full(N,np.nan); ok=np.zeros(N,bool)
idx=np.arange(N-H); good=blk[idx]==blk[idx+H]
fwd[idx[good]]=(c[idx[good]+H]-c[idx[good]])/c[idx[good]]*10000; ok[idx[good]]=True
prior=np.full(N,np.nan)
idx2=np.arange(10,N); good2=blk[idx2]==blk[idx2-10]
prior[idx2[good2]]=c[idx2[good2]]-c[idx2[good2]-10]
sel=ok&node&~np.isnan(prior)
rules={
 "always long":            np.ones(sel.sum()),
 "always short":          -np.ones(sel.sum()),
 "momentum (follow prior)":np.sign(prior[sel]),
 "reversal (fade prior)":  -np.sign(prior[sel]),
}
r=fwd[sel]
for nm,sgn in rules.items():
    pnl=sgn*r-SPREAD_BPS
    print("%-32s %7d  %6.2f%%   %+8.3f   %+10.0f"%(nm,len(pnl),(pnl>0).mean()*100,pnl.mean(),pnl.sum()))
    res.setdefault('rules',{})[nm]={'n':int(len(pnl)),'win':float((pnl>0).mean()),
                                    'mean_bps':float(pnl.mean()),'total_bps':float(pnl.sum())}
# same rules on NON-node minutes for comparison
sel2=ok&~node&~np.isnan(prior); r2=fwd[sel2]
print("\nSame rules on NON-node minutes (the control):")
for nm,f in [("momentum (follow prior)",lambda s:np.sign(prior[s])),("reversal (fade prior)",lambda s:-np.sign(prior[s]))]:
    pnl=f(sel2)*r2-SPREAD_BPS
    print("%-32s %7d  %6.2f%%   %+8.3f   %+10.0f"%(nm,len(pnl),(pnl>0).mean()*100,pnl.mean(),pnl.sum()))
json.dump(res,open('results_trade.json','w'),indent=2)
print("\nsaved results_trade.json")
