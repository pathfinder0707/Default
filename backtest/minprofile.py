import pandas as pd, numpy as np, pickle
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

cnt_sw=np.bincount(moh[sw],minlength=60).astype(float)
cnt_all=np.bincount(moh,minlength=60).astype(float)
rate=cnt_sw/cnt_all
base=sw.mean()
rel=(rate/base-1)*100

order=np.argsort(-rel)
print("SWING RATE BY MINUTE-OF-HOUR  (relative to the overall average)")
print("rank  min   is-GB   swing-rate   vs avg")
print("-------------------------------------------")
for r,m in enumerate(order[:14],1):
    print("  %2d   :%02d    %-5s   %.4f    %+6.2f%%"%(r,m,"GB" if m in GB else "-",rate[m],rel[m]))
print("   ...")
for r,m in enumerate(order[-5:],len(order)-4):
    print("  %2d   :%02d    %-5s   %.4f    %+6.2f%%"%(r,m,"GB" if m in GB else "-",rate[m],rel[m]))

gb=np.array([m in GB for m in range(60)])
print("\nMean relative swing rate:")
print("   GB minutes (16)    : %+6.3f%%"%rel[gb].mean())
print("   non-GB minutes (44): %+6.3f%%"%rel[~gb].mean())

print("\nTHE DECISIVE COMPARISON — round-clock minutes:")
for m in [0,30,15,45,5,10,20,25,40,50]:
    print("   :%02d   %-6s  %+6.2f%%"%(m,"GB" if m in GB else "NOT GB",rel[m]))

top5=set(order[:5].tolist())
print("\n   top-5 minutes: %s"%", ".join(":%02d%s"%(m,"(GB)" if m in GB else "(not GB)") for m in order[:5]))
