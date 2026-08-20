import pandas as pd, numpy as np, glob, pickle
from zoneinfo import ZoneInfo

fs=sorted(glob.glob('data/DAT_ASCII_NSXUSD_M1_*.csv'))
df=pd.concat([pd.read_csv(f,sep=';',header=None,names=['ts','o','h','l','c','v'],dtype={'ts':str}) for f in fs],ignore_index=True)
df['ny']=pd.to_datetime(df['ts'],format='%Y%m%d %H%M%S')
df=df.sort_values('ny').drop_duplicates('ny').reset_index(drop=True)

# NY local (DST-aware, per the empirical session-break test) -> Zurich
ny=df['ny'].dt.tz_localize(ZoneInfo("America/New_York"),ambiguous=True,nonexistent='shift_forward')
zh=ny.dt.tz_convert(ZoneInfo("Europe/Zurich"))
df['zh']=zh
df['H']=zh.dt.hour.astype(np.int16)
df['M']=zh.dt.minute.astype(np.int16)
df['mod']=(df['H']*60+df['M']).astype(np.int16)
df['date_zh']=zh.dt.date
df['dow']=zh.dt.dayofweek.astype(np.int8)
df['year']=zh.dt.year.astype(np.int16)

# contiguous session blocks: break wherever the gap exceeds 2 minutes
gap=df['ny'].diff().dt.total_seconds().fillna(0)
df['blk']=(gap>120).cumsum().astype(np.int32)

df=df[['zh','ny','H','M','mod','date_zh','dow','year','blk','o','h','l','c']].copy()
print("rows            : %d"%len(df))
print("Zurich range    : %s  ->  %s"%(df['zh'].iloc[0],df['zh'].iloc[-1]))
print("session blocks  : %d"%df['blk'].nunique())
print("trading days    : %d"%df['date_zh'].nunique())

# sanity: DST changeover weekends where US and EU differ
off=df['zh'].dt.strftime('%z').astype(str)
tmp=pd.DataFrame({'d':df['date_zh'],'ny':df['ny'].dt.hour,'zh':df['H']})
tmp['delta']=(tmp['zh']-tmp['ny'])%24
byday=tmp.groupby('d')['delta'].agg(lambda s:s.mode().iat[0])
print("\nNY->Zurich hour offset distribution (per day):")
print(byday.value_counts().to_string())
print("\nDays where offset = 5h (US switched, EU had not yet):")
odd=byday[byday==5]
print("  %d days, e.g. %s"%(len(odd),", ".join(str(x) for x in list(odd.index[:6]))))

with open('bars.pkl','wb') as f: pickle.dump(df,f)
print("\nsaved bars.pkl")
