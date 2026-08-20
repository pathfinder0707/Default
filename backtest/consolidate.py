import numpy as np, pickle, json
from gbcore import read_of
df=pickle.load(open('bars.pkl','rb')); N=len(df)
mod=df['mod'].to_numpy(); blk=df['blk'].to_numpy(); hi=df['h'].to_numpy(); lo=df['l'].to_numpy()
L=R=3
isH=np.zeros(N,bool); isL=np.zeros(N,bool)
for i in range(L,N-R):
    if blk[i-L]!=blk[i+R]: continue
    wh=hi[i-L:i+R+1]; wl=lo[i-L:i+R+1]
    if hi[i]==wh.max() and (wh[:L]<hi[i]).all() and (wh[L+1:]<hi[i]).all(): isH[i]=True
    if lo[i]==wl.min() and (wl[:L]>lo[i]).all() and (wl[L+1:]>lo[i]).all(): isL[i]=True
sw=isH|isL
moh=mod%60
GB={0,3,7,11,14,17,23,29,35,41,44,47,50,53,56,59}
rate=np.bincount(moh[sw],minlength=60)/np.bincount(moh,minlength=60)
rel=(rate/sw.mean()-1)*100
prof=[{'m':int(m),'gb':bool(m in GB),'rel':float(rel[m])} for m in range(60)]

q=np.array([0 if (r:=read_of(m//60,m%60,1)) is None else r['q'] for m in range(1440)],np.int8)
MMX=(q==3); swmod=mod[sw]
obs=MMX[swmod].mean()
null=np.array([np.roll(MMX,k)[swmod].mean() for k in range(1,60)])

meta={'bars':int(N),'days':int(df['date_zh'].nunique()),
      'start':str(df['zh'].iloc[0])[:10],'end':str(df['zh'].iloc[-1])[:10],
      'swings':int(sw.sum()),
      'density':{'mm0':384,'mm1':1104,'all0':839,'all1':1406,'all2':1434},
      'minute_profile':prof,
      'rot_obs':float(obs),'rot_null':[float(x) for x in null]}
core=json.load(open('results_core.json')); brk=json.load(open('results_breakdown.json'))
seq=json.load(open('results_seq.json')); trd=json.load(open('results_trade.json'))
json.dump({'meta':meta,'core':core,'breakdown':brk,'seq':seq,'trade':trd},
          open('ALL.json','w'),indent=2)
print("consolidated -> ALL.json")
print("bars %d  days %d  swings %d  %s..%s"%(N,meta['days'],meta['swings'],meta['start'],meta['end']))
