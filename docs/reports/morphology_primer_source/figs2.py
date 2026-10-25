import numpy as np, math, sys
sys.path.insert(0,'.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch, Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from scipy.spatial import HalfspaceIntersection, ConvexHull
plt.rcParams.update({'font.size':10,'font.family':'serif','mathtext.fontset':'cm'})
B,R,G,P,K='#4C78A8','#E45756','#54A24B','#B279A2','#444444'

# ---------- 1. three levels of "shape"
fig=plt.figure(figsize=(11,3.4))
ax=fig.add_subplot(131,projection='3d')
T=np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]])*1.0
ax.add_collection3d(Poly3DCollection([T[[0,1,2]],T[[0,1,3]],T[[0,2,3]],T[[1,2,3]]],facecolor=B,alpha=.5,edgecolor='k'))
ax.scatter(*T.T,s=120,c='#7f7f7f',depthshade=False); ax.scatter(0,0,0,s=60,c=R,depthshade=False)
ax.set_xlim(-1.3,1.3);ax.set_ylim(-1.3,1.3);ax.set_zlim(-1.3,1.3);ax.set_axis_off()
ax.set_title("(a) node shape\nZn$_4$O core = tetrahedron\n(size ~ 0.3 nm)")
ax=fig.add_subplot(132,projection='3d')
g=np.arange(3); X,Y,Z=np.meshgrid(g,g,g)
pts=np.c_[X.ravel(),Y.ravel(),Z.ravel()]
segs=[]
for p in pts:
    for d in np.eye(3):
        q=p+d
        if q.max()<=2: segs.append([p,q])
ax.add_collection3d(Line3DCollection(segs,colors=K,linewidths=1.2))
ax.scatter(*pts.T,s=40,c=B,depthshade=False); ax.set_axis_off()
ax.set_title("(b) net / framework\nnodes + linkers, pcu net\n(unit cell ~ 2.6 nm)")
ax=fig.add_subplot(133,projection='3d')
O=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],float)
ch=ConvexHull(O); ax.add_collection3d(Poly3DCollection([O[s] for s in ch.simplices],facecolor=R,alpha=.85,edgecolor='k'))
ax.set_xlim(-1,1);ax.set_ylim(-1,1);ax.set_zlim(-1,1);ax.set_axis_off()
ax.set_title("(c) particle morphology\nwhole crystal = octahedron\n(size ~ 100 nm to 1 mm)")
plt.tight_layout(); plt.savefig('fig/levels.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- 2. lattice, unit cell, primitive vs conventional (2D centred rectangular)
fig,ax=plt.subplots(figsize=(6.2,4.2))
a,b=2.0,1.4
pts=[(i*a,j*b) for i in range(-1,4) for j in range(-1,4)]+[(i*a+a/2,j*b+b/2) for i in range(-1,3) for j in range(-1,3)]
pts=[p for p in pts if -0.3<=p[0]<=6.3 and -0.3<=p[1]<=4.5]
ax.scatter(*zip(*pts),s=60,c=K,zorder=3)
ax.add_patch(Rectangle((0,0),a,b,fill=True,fc=B,alpha=.25,ec=B,lw=2,zorder=1))
pp=[(2*a,b),(2*a+a/2,b+b/2),(2*a+a,b),(2*a+a/2,b/2)]
ax.add_patch(Polygon(pp,closed=True,fc=R,alpha=.3,ec=R,lw=2))
ax.annotate("",xy=(a,0),xytext=(0,0),arrowprops=dict(arrowstyle='->',lw=2,color=B))
ax.annotate("",xy=(0,b),xytext=(0,0),arrowprops=dict(arrowstyle='->',lw=2,color=B))
ax.text(a/2,-0.35,r"$\mathbf{a}$",color=B,ha='center',fontsize=13);ax.text(-0.35,b/2,r"$\mathbf{b}$",color=B,fontsize=13)
ax.text(0.15,b+0.15,"conventional cell\n(2 lattice points, shows symmetry)",color=B,fontsize=9)
ax.text(2*a+a+0.1,b+0.2,"primitive cell\n(1 lattice point)",color=R,fontsize=9)
ax.set_aspect('equal'); ax.axis('off'); ax.set_xlim(-0.6,6.6); ax.set_ylim(-0.6,4.6)
ax.set_title("A 2D lattice with centring: two valid unit cells for the same crystal")
plt.savefig('fig/lattice2d.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- 3. Miller planes in a cube
fig=plt.figure(figsize=(10,3.4))
cube_edges=[]
C=np.array([[x,y,z] for x in (0,1) for y in (0,1) for z in (0,1)])
for i in range(8):
    for j in range(i+1,8):
        if np.sum(np.abs(C[i]-C[j]))==1: cube_edges.append([C[i],C[j]])
planes={'(100)':[[1,0,0],[1,1,0],[1,1,1],[1,0,1]],'(110)':[[1,0,0],[0,1,0],[0,1,1],[1,0,1]],'(111)':[[1,0,0],[0,1,0],[0,0,1]]}
for i,(nm,pl) in enumerate(planes.items()):
    ax=fig.add_subplot(1,3,i+1,projection='3d')
    ax.add_collection3d(Line3DCollection(cube_edges,colors='k',linewidths=1))
    ax.add_collection3d(Poly3DCollection([np.array(pl,float)],facecolor=[B,G,R][i],alpha=.6,edgecolor='k'))
    for v,l in zip(np.eye(3),'abc'):
        ax.quiver(0,0,0,*(v*1.25),color='gray',arrow_length_ratio=.1); ax.text(*(v*1.35),l)
    ax.set_axis_off(); ax.view_init(20,30); ax.set_title(nm,fontsize=13)
plt.savefig('fig/miller.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- 4. d-spacing in 2D
fig,axs=plt.subplots(1,3,figsize=(10,3.6))
for ax,(h,k) in zip(axs,[(1,0),(1,1),(2,1)]):
    xs=np.arange(0,5); X,Y=np.meshgrid(xs,xs)
    ax.scatter(X,Y,s=25,c=K,zorder=3)
    t=np.linspace(-1,6,10)
    for c in range(-6,12):
        # line h x + k y = c
        if k==0: ax.plot([c/h]*2,[-0.5,4.5],color=B,lw=1)
        else: ax.plot(t,(c-h*t)/k,color=B,lw=1)
    d=1/math.hypot(h,k)
    n=np.array([h,k])/math.hypot(h,k)
    p0=np.array([2,2]) if k==0 else np.array([2,2])
    ax.annotate("",xy=p0+n*d,xytext=p0,arrowprops=dict(arrowstyle='<->',color=R,lw=2))
    ax.set_xlim(-.5,4.5);ax.set_ylim(-.5,4.5);ax.set_aspect('equal');ax.axis('off')
    ax.set_title(f"({h}{k}) lines:  $d_{{{h}{k}}}=a/\\sqrt{{{h*h+k*k}}}={d:.3f}\\,a$")
plt.suptitle("Higher Miller indices = more closely spaced planes (smaller $d$)",y=0.98)
plt.savefig('fig/dspacing.png',dpi=200,bbox_inches='tight'); plt.close()

# ---------- 5. systematic absence picture + d_eff bars
fig,axs=plt.subplots(1,2,figsize=(10.5,3.9),gridspec_kw=dict(width_ratios=[1,1.3]))
ax=axs[0]
for x in range(0,3):
    for y in range(0,3): ax.scatter(x,y,s=70,c=K,zorder=3)
for x in range(0,2):
    for y in range(0,2): ax.scatter(x+.5,y+.5,s=70,c=R,zorder=3)
for x in [0,1,2]: ax.plot([x,x],[-.3,2.3],color=B,lw=2)
for x in [0.5,1.5]: ax.plot([x,x],[-.3,2.3],color=R,lw=2,ls='--')
ax.text(1,-1.25,"blue planes = (100) of the cell;  red dashed = identical\nplanes halfway between. Waves from them cancel:\n(100) is absent, the real spacing is $d_{200}=a/2$",ha='center',fontsize=8.5)
ax.set_aspect('equal');ax.axis('off');ax.set_ylim(-1.4,2.4);ax.set_title("Centring (face view of F or I cell)")
ax=axs[1]
fams=['100','110','111','200','210','211','220','310','311','222']
hk=[tuple(map(int,f)) for f in fams]
def allowed(lat,h):
    if lat=='P': return True
    if lat=='I': return sum(h)%2==0
    if lat=='F': return len({x%2 for x in h})==1
x=np.arange(len(fams)); w=.27
for j,(lat,c) in enumerate([('P','#999999'),('I',G),('F',R)]):
    d=[1/math.sqrt(sum(v*v for v in h)) if allowed(lat,h) else 0 for h in hk]
    ax.bar(x+(j-1)*w,d,w,color=c,label={'P':'P (primitive)','I':'I (ZIF-8)','F':'F (MOF-5, HKUST-1, UiO-66)'}[lat])
ax.set_xticks(x);ax.set_xticklabels(['('+f+')' for f in fams],rotation=45)
ax.set_ylabel("$d/a$ (0 = forbidden)");ax.legend(fontsize=8);ax.set_title("Which reflections survive in cubic lattices")
plt.tight_layout();plt.savefig('fig/absences.png',dpi=200,bbox_inches='tight');plt.close()

# ---------- 6. growth: fast faces grow themselves out
fig,axs=plt.subplots(1,4,figsize=(11,3.1))
th=np.arange(8)*np.pi/4
for ax,tm in zip(axs,[0,1,2,4]):
    dist=np.where(np.arange(8)%2==0,1+0.5*tm,1+1.2*tm)   # even = slow {10}, odd = fast {11}
    A=np.c_[np.cos(th),np.sin(th)]
    hs=HalfspaceIntersection(np.hstack([A,-dist[:,None]]),np.zeros(2)); V=hs.intersections
    h=ConvexHull(V); ax.add_patch(Polygon(V[h.vertices],fc='#cfe0f3',ec='k'))
    for i in range(8):
        n=A[i]; m=n*dist[i]; tv=np.array([-n[1],n[0]])
        ax.plot(*np.c_[m-tv*6,m+tv*6],color=(R if i%2 else B),lw=.8,ls=':')
    ax.set_xlim(-6,6);ax.set_ylim(-6,6);ax.set_aspect('equal');ax.axis('off');ax.set_title(f"time {tm}")
fig.text(.5,.0,"blue = slow faces (rate 0.5), red = fast faces (rate 1.2). Fast faces shrink and vanish: the crystal ends up bounded by its SLOWEST faces.",ha='center',fontsize=9)
plt.savefig('fig/growth.png',dpi=200,bbox_inches='tight');plt.close()

# ---------- 7. Wulff 2D
fig,axs=plt.subplots(1,2,figsize=(10,4.4))
th=np.linspace(0,2*np.pi,721)
gam=1+0.18*np.cos(4*th)
for ax,show in zip(axs,[0,1]):
    ax.plot(gam*np.cos(th),gam*np.sin(th),color=K,lw=1.5,label=r"polar plot of $\gamma(\theta)$")
    if show:
        for t,gm in zip(th[::12],gam[::12]):
            n=np.array([np.cos(t),np.sin(t)]); m=n*gm; tv=np.array([-n[1],n[0]])
            ax.plot(*np.c_[m-tv*2,m+tv*2],color='#bbbbbb',lw=.5)
        A=np.c_[np.cos(th),np.sin(th)]
        hs=HalfspaceIntersection(np.hstack([A,-gam[:,None]]),np.zeros(2));V=hs.intersections;h=ConvexHull(V)
        ax.add_patch(Polygon(V[h.vertices],fc=R,alpha=.35,ec=R,lw=2,label="Wulff shape"))
    ax.set_xlim(-1.5,1.5);ax.set_ylim(-1.5,1.5);ax.set_aspect('equal');ax.axis('off');ax.legend(loc='lower center',fontsize=8)
axs[0].set_title("step 1: surface energy $\\gamma$ in every direction")
axs[1].set_title("step 2: draw the plane $\\perp$ each direction at $\\gamma$;\nthe inner envelope is the Wulff shape")
plt.savefig('fig/wulff2d.png',dpi=200,bbox_inches='tight');plt.close()

# ---------- 8. Kossel crystal F/S/K
fig=plt.figure(figsize=(11,3.8))
spec=[("(100): F face",[[0,1,0],[0,0,1]],"two PBCs lie in the face\n$\\to$ flat, slow, layer growth",B),
      ("(110): S face",[[0,0,1]],"one PBC lies in the face\n$\\to$ stepped, faster",G),
      ("(111): K face",[],"no PBC lies in the face\n$\\to$ kinked, grows fastest",R)]
n_of={'(100)':np.array([1,0,0]),'(110)':np.array([1,1,0]),'(111)':np.array([1,1,1])}
g=np.arange(3); pts=np.array([[x,y,z] for x in g for y in g for z in g],float)
for i,(nm,chains,txt,c) in enumerate(spec):
    ax=fig.add_subplot(1,3,i+1,projection='3d')
    segs=[[p,p+d] for p in pts for d in np.eye(3) if (p+d).max()<=2]
    ax.add_collection3d(Line3DCollection(segs,colors='#bbbbbb',linewidths=.8))
    ax.scatter(*pts.T,s=14,c='#888888',depthshade=False)
    n=n_of[nm[:5]]; top=pts[np.isclose(pts@n,(pts@n).max())]
    ax.scatter(*top.T,s=40,c=c,depthshade=False)
    for d in chains:
        d=np.array(d,float)
        for p in top:
            q=p+d
            if q.max()<=2 and any(np.allclose(q,t) for t in top): ax.plot(*np.c_[p,q],color=c,lw=3.5)
    ax.set_axis_off(); ax.view_init(22,30); ax.set_title(nm+"\n"+txt,fontsize=9.5)
fig.text(.5,.02,"Simple cubic 'Kossel' crystal: every edge is one strong bond. A periodic bond chain (PBC) = an unbroken straight chain of strong bonds.",ha='center',fontsize=9)
plt.savefig('fig/fsk.png',dpi=200,bbox_inches='tight');plt.close()

# ---------- 9. quotient graph -> net, PBC as cycle with net translation
fig,axs=plt.subplots(1,2,figsize=(10.5,4.2),gridspec_kw=dict(width_ratios=[1,1.4]))
ax=axs[0]
ax.add_patch(Circle((0,0),.12,color=B,zorder=3)); ax.text(0,-.35,"$v$",ha='center',fontsize=13)
tt=np.linspace(0.15,2*np.pi-0.15,100)
ax.plot(0.55+0.45*np.cos(tt+np.pi),0.45*np.sin(tt+np.pi),color=R,lw=2)
ax.annotate("",xy=(0.12,-0.04),xytext=(0.2,-0.2),arrowprops=dict(arrowstyle='-|>',color=R,lw=2))
ax.plot(0.45*np.sin(tt),0.55-0.45*np.cos(tt),color=G,lw=2)
ax.annotate("",xy=(-0.04,0.12),xytext=(-0.2,0.2),arrowprops=dict(arrowstyle='-|>',color=G,lw=2))
ax.text(1.1,0,"$e_1$, voltage $(1,0)$",color=R,va='center'); ax.text(-.4,1.15,"$e_2$, voltage $(0,1)$",color=G)
ax.set_xlim(-1.2,2.2);ax.set_ylim(-1,1.5);ax.set_aspect('equal');ax.axis('off');ax.set_title("quotient graph: 1 vertex, 2 loops")
ax=axs[1]
for i in range(5):
    for j in range(4):
        ax.scatter(i,j,s=50,c=B,zorder=3)
        if i<4: ax.plot([i,i+1],[j,j],color=R,lw=1)
        if j<3: ax.plot([i,i],[j,j+1],color=G,lw=1)
ax.plot([0,4],[1,1],color=R,lw=4,alpha=.6); ax.text(4.15,1,"PBC along $(1,0)$:\nwalk $e_1e_1e_1\\dots$,\nnet translation $(1,0)$",fontsize=8.5,va='center')
ax.add_patch(Rectangle((-0.3,2.6),4.6,0.8,fill=False,ec=K,ls='--')); ax.text(-0.3,3.55,"slice for face (01): contains the red PBC",fontsize=8.5)
ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-.5,6.3);ax.set_ylim(-.5,4);ax.set_title("derived periodic net (square net)")
plt.savefig('fig/quotient.png',dpi=200,bbox_inches='tight');plt.close()
print('done')
