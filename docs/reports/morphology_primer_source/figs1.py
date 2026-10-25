import numpy as np, math, json, sys
sys.path.insert(0,'.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from poly import *
plt.rcParams.update({'font.size':10,'font.family':'serif'})
COL={'100':'#4C78A8','111':'#E45756','110':'#54A24B','211':'#B279A2','oth':'#BAB0AC'}
def famkey(n):
    a=sorted(np.round(np.abs(n)/np.max(np.abs(n)),3))[::-1]
    if a[1]<1e-3: return '100'
    if a[2]<1e-3 and abs(a[1]-1)<1e-3: return '110'
    if abs(a[2]-1)<1e-3: return '111'
    if abs(a[1]-.5)<1e-3 and abs(a[2]-.5)<1e-3: return '211'
    return 'oth'
def draw(ax,polys,normals,title=None,view=(22,35)):
    for P,n in zip(polys,normals):
        pc=Poly3DCollection([P],facecolor=COL[famkey(n)],edgecolor='k',linewidth=.6,alpha=.92)
        ax.add_collection3d(pc)
    V=np.vstack(polys); r=np.abs(V).max()
    for f in (ax.set_xlim,ax.set_ylim,ax.set_zlim): f(-r,r)
    ax.set_box_aspect((1,1,1)); ax.view_init(*view); ax.set_axis_off()
    if title: ax.set_title(title,fontsize=10)

# ---- Fig: morph path cube -> octahedron
ts=[1e9,1.5,2/math.sqrt(3),0.85,1/math.sqrt(3)]
names=['Cube','Truncated cube','Cuboctahedron','Truncated octahedron','Octahedron']
fig=plt.figure(figsize=(12,3.0)); res=[]
for i,(t,nm) in enumerate(zip(ts,names)):
    V,ch,P,N=cubic_shape(min(t,10)); d=descriptors(V,ch)
    ax=fig.add_subplot(1,5,i+1,projection='3d'); draw(ax,P,N,nm+"\n$t="+(r"\infty" if t>100 else f"{t:.3f}")+"$")
    res.append(dict(name=nm,t=(None if t>100 else t),faces=len(P),verts=len(V),kappa2=d['kappa2'],psi=d['psi'],ar=d['ar']))
fig.text(.5,.02,"blue = {100} faces,  red = {111} faces;   $t$ = distance of {111} planes / distance of {100} planes",ha='center')
plt.savefig('fig/morph_path.png',dpi=200,bbox_inches='tight'); plt.close()

# ---- Fig: rod/plate by stretch
lams=[0.35,0.6,1.0,1.8,3.0]
fig=plt.figure(figsize=(12,3.2)); res2=[]
for i,l in enumerate(lams):
    V,ch,P,N=cubic_shape(0.85,lam=l); d=descriptors(V,ch)
    ax=fig.add_subplot(1,5,i+1,projection='3d'); draw(ax,P,N,f"$\\lambda={l}$\n$\\kappa^2={d['kappa2']:.3f}$",view=(12,35))
    res2.append(dict(lam=l,kappa2=d['kappa2'],psi=d['psi'],ar=d['ar']))
fig.text(.5,.02,"same faces, growth along $z$ slowed ($\\lambda<1$, plate) or sped up ($\\lambda>1$, rod)",ha='center')
plt.savefig('fig/rod_plate.png',dpi=200,bbox_inches='tight'); plt.close()

# ---- Fig: BFDH for F and I lattices
def bfdh(lattice):
    fams={'F':[((1,1,1),1/math.sqrt(3)),((1,0,0),1/2),((1,1,0),1/(2*math.sqrt(2))),((3,1,1),1/math.sqrt(11))],
          'I':[((1,1,0),1/math.sqrt(2)),((1,0,0),1/2),((2,1,1),1/math.sqrt(6)),((3,1,0),1/(2*math.sqrt(10))*2)]}[lattice]
    pl=[]
    for hkl,d in fams:
        for v in family(hkl): pl.append((np.array(v,float),1/d))
    return polytope(pl)
fig=plt.figure(figsize=(8,3.6)); res3={}
for i,(L,nm) in enumerate([('F','F-centred cubic (MOF-5, HKUST-1, UiO-66)'),('I','I-centred cubic (ZIF-8)')]):
    V,ch,P,N=bfdh(L); d=descriptors(V,ch)
    from collections import Counter
    cnt=Counter(famkey(n) for n in N)
    res3[L]=dict(faces=dict(cnt),verts=len(V),kappa2=d['kappa2'],psi=d['psi'])
    ax=fig.add_subplot(1,2,i+1,projection='3d'); draw(ax,P,N,nm)
fig.text(.5,.02,"blue {100}, red {111}, green {110}   (BFDH: face distance $\\propto 1/d_{\\rm eff}$)",ha='center')
plt.savefig('fig/bfdh_FI.png',dpi=200,bbox_inches='tight'); plt.close()
json.dump(dict(morph=res,stretch=res2,bfdh=res3),open('fig/numbers.json','w'),indent=1,default=float)
print(json.dumps(dict(morph=res,stretch=res2,bfdh=res3),indent=1,default=float))
