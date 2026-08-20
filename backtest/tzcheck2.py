import pandas as pd, numpy as np, glob
fs=sorted(glob.glob('data/DAT_ASCII_NSXUSD_M1_*.csv'))
df=pd.concat([pd.read_csv(f,sep=';',header=None,names=['ts','o','h','l','c','v'],dtype={'ts':str}) for f in fs],ignore_index=True)
df['dt']=pd.to_datetime(df['ts'],format='%Y%m%d %H%M%S')
df['mod']=df['dt'].dt.hour*60+df['dt'].dt.minute
df['mon']=df['dt'].dt.month
df['dow']=df['dt'].dt.dayofweek

print("TEST 1 - daily session break (structural, cannot be confounded)")
print("  For weekdays, which minutes-of-day have essentially NO bars?\n")
wd=df[df['dow']<5]
for label,months in [("WINTER (Jan/Feb/Dec)",[1,2,12]),("SUMMER (Jun/Jul/Aug)",[6,7,8])]:
    sub=wd[wd['mon'].isin(months)]
    ndays=sub['dt'].dt.date.nunique()
    cnt=sub.groupby('mod').size().reindex(range(1440),fill_value=0)
    empty=cnt[cnt<ndays*0.05].index.tolist()
    # contiguous runs
    runs=[];start=None;prev=None
    for m in empty:
        if start is None: start=m
        elif m!=prev+1: runs.append((start,prev)); start=m
        prev=m
    if start is not None: runs.append((start,prev))
    runs=[r for r in runs if r[1]-r[0]>=20]
    print("  %s  (%d weekdays)"%(label,ndays))
    for a,b in runs:
        print("      no data %02d:%02d - %02d:%02d"%(a//60,a%60,b//60,b%60))
print()

print("TEST 2 - 08:30 vs 09:30 mean range, higher precision")
df['rng']=(df['h']-df['l'])/df['c']*10000
for label,months in [("WINTER",[1,2,12]),("SUMMER",[6,7,8])]:
    sub=df[df['mon'].isin(months)]
    g=sub.groupby('mod')['rng'].mean()
    print("  %-7s 08:30=%6.3f   09:30=%6.3f   ratio 09:30/08:30 = %.3f"%(label,g[510],g[570],g[570]/g[510]))
print()

print("TEST 3 - step change into the cash open (open minus the 5 min before)")
for label,months in [("WINTER",[1,2,12]),("SUMMER",[6,7,8])]:
    sub=df[df['mon'].isin(months)]
    g=sub.groupby('mod')['rng'].mean()
    for openmin,nm in [(510,"08:30"),(570,"09:30")]:
        base=g[openmin-5:openmin].mean()
        print("  %-7s %s  step = %+6.2f bps  (%.2f -> %.2f)"%(label,nm,g[openmin]-base,base,g[openmin]))
