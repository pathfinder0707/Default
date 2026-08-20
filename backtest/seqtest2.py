import numpy as np, pickle
from gbcore import node_at
rng=np.random.default_rng(7)
df=pickle.load(open('bars.pkl','rb')); N=len(df)
mod=df['mod'].to_numpy(); blk=df['blk'].to_numpy(); hi=df['h'].to_numpy(); lo=df['l'].to_numpy()
L=R=3
isH=np.zeros(N,bool); isL=np.zeros(N,bool)
for i in range(L,N-R):
    if blk[i-L]!=blk[i+R]: continue
    wh=hi[i-L:i+R+1]; wl=lo[i-L:i+R+1]
    if hi[i]==wh.max() and (wh[:L]<hi[i]).all() and (wh[L+1:]<hi[i]).all(): isH[i]=True
    if lo[i]==wl.min() and (wl[:L]>lo[i]).all() and (wl[L+1:]>lo[i]).all(): isL[i]=True
swi=np.flatnonzero(isH|isL)

A1I=np.full(1440,-1,np.int8); A2I=np.full(1440,-1,np.int8)
for m in range(1440):
    h,mi=divmod(m,60)
    a1=node_at(h,mi,1,1); a2=node_at(h,mi,2,1)
    if a1 and a1['pri'] and a1['dist']==0: A1I[m]=a1['idx']
    if a2 and a2['pri'] and a2['dist']==0: A2I[m]=a2['idx']

def rates(idxs):
    m=mod[idxs]; b=blk[idxs]
    a1=A1I[m]; a2=A2I[m]; same=b[1:]==b[:-1]
    p1,c1=a1[:-1],a1[1:]; p2,c2=a2[:-1],a2[1:]
    ok1=same&(p1>=0)&(c1>=0); ok2=same&(p2>=0)&(c2>=0)
    return ((ok1&((c1-p1)==1)).sum()/max(ok1.sum(),1),
            (ok2&((p2-c2)==1)).sum()/max(ok2.sum(),1))

o1,o2=rates(swi)
print("REAL SWINGS            A1 forward %.4f   A2 reverse %.4f   (n=%d)"%(o1,o2,len(swi)))

# null: random bars, same count, kept in chronological order
n1=[];n2=[]
for it in range(200):
    pick=np.sort(rng.choice(N,size=len(swi),replace=False))
    r1,r2=rates(pick); n1.append(r1); n2.append(r2)
n1=np.array(n1);n2=np.array(n2)
print("RANDOM CHRONOLOGICAL   A1 forward %.4f +/- %.4f   A2 reverse %.4f +/- %.4f"%(n1.mean(),n1.std(ddof=1),n2.mean(),n2.std(ddof=1)))
print()
print("  A1  z = %+.2f   lift %+.2f%%"%((o1-n1.mean())/n1.std(ddof=1),(o1/n1.mean()-1)*100))
print("  A2  z = %+.2f   lift %+.2f%%"%((o2-n2.mean())/n2.std(ddof=1),(o2/n2.mean()-1)*100))
print()
print("=> If swings were special, they would beat random chronological points.")

# show the artifact directly: A2 index vs clock order within an hour
print("\nWHY A2 'wins' against a shuffled null - the index map is partly monotonic with the clock:")
row=[]
for mi in range(60):
    a2=node_at(12,mi,2,1)
    if a2 and a2['pri'] and a2['dist']==0: row.append((mi,a2['idx']))
print("   minute:idx  ", "  ".join(":%02d=%d"%(m,i) for m,i in row))
seq=[i for _,i in row]
dec=sum(1 for a,b in zip(seq,seq[1:]) if b==a-1)
print("   walking the clock FORWARD through one hour yields %d A2-valid (-1) steps out of %d transitions"%(dec,len(seq)-1))
print("   so simply moving forward in time manufactures A2 steps - no market behaviour required.")
