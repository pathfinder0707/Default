from gbcore import *
ok=fail=0
def chk(n,c,extra=None):
    global ok,fail
    if c: ok+=1; print("  ok   "+n)
    else: fail+=1; print("  FAIL "+n+("  -> "+repr(extra) if extra is not None else ""))

print("Cross-validating Python port against the tested JS engine\n")
# handoff worked example 11:03
m=methods(11,3)
chk("11:03 MM=3",m[0][1]==3); chk("11:03 HH+MM=14",m[1][1]==14); chk("11:03 |HH-MM|=8",m[2][1]==8)
a1=node_at(11,3,1); a2=node_at(11,3,2)
chk("11:03 A1 = 03/7 via MM exact", a1['label']=='03/7' and a1['method']=='MM' and a1['dist']==0, a1)
chk("11:03 A2 = 03/7 idx0 terminal", a2['label']=='03/7' and a2['idx']==0 and a2['term'], a2)
chk("12:02 prefers MM at d=1", node_at(12,2,1)['method']=='MM')
# group labels
t=A[1][5]
chk("29->29/35",label_for(t,29)=='29/35'); chk("71->71/77",label_for(t,71)=='71/77')
# quality
chk("MM exact=3",quality({'pri':True,'dist':0})==3)
chk("MM tol=2",quality({'pri':True,'dist':1})==2)
chk("secondary=1",quality({'pri':False,'dist':0})==1)

# density must match the JS numbers exactly
def density(tol,nosec):
    n=0
    for h in range(24):
        for mi in range(60):
            a1=node_at(h,mi,1,tol,nosec); a2=node_at(h,mi,2,tol,nosec)
            if a1 or a2: n+=1
    return n
print()
for name,tol,nosec,want in [("MM only tol0",0,True,384),("MM only tol1",1,True,1104),
                            ("all3 tol0",0,False,839),("all3 tol1",1,False,1406),
                            ("all3 tol2",2,False,1434)]:
    got=density(tol,nosec)
    chk("density %-14s = %d"%(name,want), got==want, got)

# MM-exact count
mmx=sum(1 for h in range(24) for mi in range(60)
        if (lambda r: r is not None and r['q']==3)(read_of(h,mi,1)))
chk("MM-exact minutes = 384", mmx==384, mmx)
print("\nPASS %d  FAIL %d"%(ok,fail))
raise SystemExit(1 if fail else 0)
