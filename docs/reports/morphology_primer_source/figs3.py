import numpy as np, sys, warnings; warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from matplotlib.patches import FancyBboxPatch
from scipy.spatial import ConvexHull
from ase.io import read
from ase.neighborlist import neighbor_list
import spglib
from ase import Atoms
plt.rcParams.update({'font.size':10,'font.family':'serif','mathtext.fontset':'cm'})
import os
CIF=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","..","code","spectrum_pipeline","%s.cif")   # the four demonstration CIFs
col={'Zn':'#7d80b0','Cu':'#c88033','Zr':'#3fa59b','O':'#e0402f','C':'#555555','H':'#dddddd','N':'#3050f8'}
fig=plt.figure(figsize=(12,3.6))
for i,(n,lab) in enumerate([("MOF5","MOF-5  (Zn$_4$O + BDC)\nFm$\\bar3$m, $a$=25.87 Å"),("HKUST-1","HKUST-1 (Cu paddlewheel + BTC)\nFm$\\bar3$m, $a$=26.30 Å"),("UiO-66","UiO-66 (Zr$_6$ + BDC)\nF$\\bar4$3m in this CIF*, $a$=20.52 Å"),("ZIF-8","ZIF-8 (Zn + 2-methylimidazolate)\nI$\\bar4$3m, $a$=16.99 Å")]):
    at=read(CIF%n)
    if n in("HKUST-1","UiO-66"):
        L,p,num=spglib.standardize_cell((at.cell[:],at.get_scaled_positions(),at.numbers),to_primitive=False,symprec=1e-2)
        at=Atoms(numbers=num,scaled_positions=p,cell=L,pbc=True)
    at=at[[s!='H' for s in at.get_chemical_symbols()]]; at.wrap()
    I,J=neighbor_list('ij',at,{('C','C'):1.7,('C','O'):1.6,('C','N'):1.6,('N','N'):1.6,('Zn','O'):2.3,('Cu','O'):2.3,('Zr','O'):2.5,('Zn','N'):2.3})
    X=at.positions; segs=[[X[a],X[b]] for a,b in zip(I,J) if a<b and np.linalg.norm(X[a]-X[b])<2.6]
    ax=fig.add_subplot(1,4,i+1,projection='3d')
    ax.add_collection3d(Line3DCollection(segs,colors='#888888',linewidths=.5))
    S=at.get_chemical_symbols()
    for el in set(S):
        m=np.array([s==el for s in S]); big=el in('Zn','Cu','Zr')
        ax.scatter(*X[m].T,s=(26 if big else 4),c=col[el],depthshade=False)
    ax.set_proj_type('ortho'); ax.set_box_aspect((1,1,1)); ax.set_axis_off(); ax.view_init(0,0); ax.set_title(lab,fontsize=9)
fig.text(.5,.01,"Conventional unit cells viewed down the $a$ axis (H atoms hidden; large dots = metal atoms; pores are the empty regions). *see text on UiO-66 and ZIF-8 symmetry.",ha='center',fontsize=8.5)
plt.savefig('fig/mofs.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- geometric prototypes (own drawing, after Wu & Jiang's scheme)
def poly(ax,V,c):
    ch=ConvexHull(V); ax.add_collection3d(Poly3DCollection([V[s] for s in ch.simplices],facecolor=c,alpha=.8,edgecolor=c,linewidth=.2))
    ax.scatter(*V.T,s=12,c='k',depthshade=False)
fig=plt.figure(figsize=(12,2.8))
shapes=[("L2  linear",np.array([[-1,0,0],[1,0,0]]),None),
        ("T3  triangle",np.array([[np.cos(t),np.sin(t),0] for t in np.arange(3)*2*np.pi/3]),'#4C78A8'),
        ("S4  square",np.array([[1,0,0],[0,1,0],[-1,0,0],[0,-1,0]]),'#E45756'),
        ("T4  tetrahedron",np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]])/1.7,'#4C78A8'),
        ("O6  octahedron",np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]]),'#999999'),
        ("C8  cube",np.array([[x,y,z] for x in(-1,1) for y in(-1,1) for z in(-1,1)])/1.5,'#E45756')]
for i,(nm,V,c) in enumerate(shapes):
    ax=fig.add_subplot(1,6,i+1,projection='3d'); V=V.astype(float)
    if c is None: ax.plot(*V.T,color='k',lw=3); ax.scatter(*V.T,s=12,c='k')
    elif nm.startswith(("T3","S4")):
        ax.add_collection3d(Poly3DCollection([V],facecolor=c,alpha=.8)); ax.scatter(*V.T,s=12,c='k')
    else: poly(ax,V,c)
    for f in(ax.set_xlim,ax.set_ylim,ax.set_zlim): f(-1.1,1.1)
    ax.set_box_aspect((1,1,1)); ax.set_axis_off(); ax.view_init(20,30); ax.set_title(nm,fontsize=10)
fig.text(.5,.02,"Geometric signatures: black dots = connection points of a building unit. (6 of the 13 prototypes used by Wu & Jiang, redrawn.)",ha='center',fontsize=8.5)
plt.savefig('fig/prototypes.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- pipeline
fig,ax=plt.subplots(figsize=(12,4.6)); ax.axis('off'); ax.set_xlim(0,12); ax.set_ylim(0,4.6)
boxes=[(0.1,3.0,"CIF file\n(unit cell +\natom positions)",'#eeeeee'),
       (2.1,3.0,"Symmetry\n(spglib):\nspace group $G$",'#dbe7f3'),
       (4.1,3.0,"Allowed faces\n$(hkl)$ and\n$d_{\\rm eff}$",'#dbe7f3'),
       (6.1,3.0,"BFDH polytope\n$n\\cdot x\\leq 1/d_{\\rm eff}$",'#dbe7f3'),
       (8.1,3.0,"Morph family\n(vary face rates,\nstretch)",'#dbe7f3'),
       (10.1,3.0,"Shape numbers\n$\\kappa^2$, $\\Psi$, AR,\nfaces/vertices",'#dbe7f3'),
       (4.1,0.6,"Periodic graph\n(quotient graph\n+ voltages)",'#e3f1de'),
       (6.1,0.6,"PBCs and F/S/K\nclass per face;\nbroken linkers",'#e3f1de'),
       (8.1,0.6,"UFF slab energies\n$\\gamma_{hkl}$ $\\to$ Wulff",'#f8dede'),
       (10.1,0.6,"Validate: CCDC /\nWulffman / lab\nshapes (Chen)",'#f3e6c4')]
for x,y,t,c in boxes:
    ax.add_patch(FancyBboxPatch((x,y),1.7,1.25,boxstyle="round,pad=0.05",fc=c,ec='k'))
    ax.text(x+.85,y+.62,t,ha='center',va='center',fontsize=8.6)
def arr(x1,y1,x2,y2): ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',lw=1.3))
for i in range(5): arr(1.85+2*i,3.62,2.1+2*i,3.62)
arr(0.95,3.0,4.1,1.5); arr(5.85,1.22,6.1,1.22); arr(7.85,1.22,8.1,1.22); arr(9.85,1.22,10.1,1.22)
arr(6.95,3.0,6.95,1.9); arr(9.0,1.9,9.0,3.0)
ax.text(0.1,4.45,"Stage 1: pure geometry (unit cell + symmetry only)",color='#2b5d8a',fontsize=10,weight='bold')
ax.text(4.1,0.2,"Stage 2: graph layer",color='#2f7a2a',fontsize=10,weight='bold')
ax.text(8.1,0.2,"Stage 3: chemistry",color='#b03434',fontsize=9,weight='bold')
ax.text(10.4,0.2,"Stage 4: checks",color='#8a6d1d',fontsize=9,weight='bold')
plt.savefig('fig/pipeline.png',dpi=200,bbox_inches='tight'); plt.close()
print('ok')
