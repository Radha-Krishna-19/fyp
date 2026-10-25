"""Graph 'attachment number': bonds a new node makes when it attaches to a flat face.
Chen et al. (Matter 2020) used this for UiO-67 (fcu): (110)=5, (100)=4, (111)=3."""
import numpy as np, itertools, json
def net(kind,N=6):
    if kind=='pcu':  # MOF-5 node net, node spacing 1
        P=np.array(list(itertools.product(range(-N,N+1),repeat=3)),float); nn=1.0
    if kind=='fcu':  # UiO-66/67 node net, conventional a=1
        B=np.array(list(itertools.product(range(-N,N+1),repeat=3)),float)
        P=np.vstack([B+o for o in ([0,0,0],[0,.5,.5],[.5,0,.5],[.5,.5,0])]); nn=1/np.sqrt(2)/1
        nn=np.sqrt(2)/2
    if kind=='sod':  # ZIF-8 Zn net, I-centred, conventional a=1: Zn at 12d (1/4,1/2,0)+perms
        B=np.array(list(itertools.product(range(-N,N+1),repeat=3)),float)
        base=set()
        for p in itertools.permutations([.25,.5,0]):
            for s in itertools.product([1,-1],repeat=3): base.add(tuple(np.mod(np.array(p)*s,1)))
        base=np.array(sorted(base)); P=np.vstack([B+b for b in base]); nn=np.sqrt(2)/4
    return P,nn
def attach(kind,hkl):
    P,nn=net(kind); n=np.array(hkl,float); n/=np.linalg.norm(n)
    P=P[np.linalg.norm(P,axis=1)<4.5]
    h=np.round(P@n,6); levels=np.unique(h)
    res=[]
    for h0 in levels[(levels>-0.5)&(levels<0.5)]:
        crystal=P[h<=h0]; nxt=P[(h>h0)&(h<=h0+1.01)]
        nxt=nxt[np.linalg.norm(nxt-np.outer(nxt@n,n),axis=1)<1.5]  # sites near the axis
        if len(nxt)==0: continue
        cnt=[int(np.sum(np.abs(np.linalg.norm(crystal-s,axis=1)-nn)<1e-6)) for s in nxt]
        res.append(max(cnt))
    return sorted(set(res))
out={}
for kind,fams in [('pcu',[(1,0,0),(1,1,0),(1,1,1)]),('fcu',[(1,0,0),(1,1,0),(1,1,1)]),('sod',[(1,0,0),(1,1,0),(1,1,1),(2,1,1)])]:
    out[kind]={str(f):attach(kind,f) for f in fams}
    print(kind,out[kind])
json.dump(out,open('fig/attach.json','w'))
