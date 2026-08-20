import pandas as pd, numpy as np, glob
fs=sorted(glob.glob('data/DAT_ASCII_NSXUSD_M1_*.csv'))
df=pd.concat([pd.read_csv(f,sep=';',header=None,
    names=['ts','o','h','l','c','v'],dtype={'ts':str}) for f in fs],ignore_index=True)
df['dt']=pd.to_datetime(df['ts'],format='%Y%m%d %H%M%S')
df=df.sort_values('dt').reset_index(drop=True)
df['rng']=(df['h']-df['l'])/df['c']*10000   # bps, comparable across price levels
df['mod']=df['dt'].dt.hour*60+df['dt'].dt.minute
df['mon']=df['dt'].dt.month

print("rows: %d   %s -> %s"%(len(df),df['dt'].iloc[0],df['dt'].iloc[-1]))
print()
def peak(months,label):
    sub=df[df['mon'].isin(months)]
    g=sub.groupby('mod')['rng'].mean()
    top=g.nlargest(4)
    print(label)
    for mod,val in top.items():
        print("     %02d:%02d   mean range %6.2f bps"%(mod//60,mod%60,val))
    m=top.index[0]
    return m

w=peak([1,2,12],"WINTER (Jan/Feb/Dec — US on EST):")
print()
s=peak([6,7,8],"SUMMER (Jun/Jul/Aug — US on EDT):")
print()
print("winter peak %02d:%02d   summer peak %02d:%02d   shift = %+d min"%(w//60,w%60,s//60,s%60,s-w))
print()
if w==570 and s==510:
    print("=> CONFIRMED: timestamps are FIXED EST (UTC-5, no DST).")
    print("   NY cash open 09:30 local shows at 09:30 in winter and 08:30 in summer.")
elif w==s:
    print("=> Timestamps FOLLOW US DST (they are America/New_York local).")
    print("   Cash open pinned to the same clock minute year-round.")
else:
    print("=> Unexpected pattern - needs manual inspection before proceeding.")
