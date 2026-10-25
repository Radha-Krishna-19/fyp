import numpy as np, sys
sys.path.insert(0,'.')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from attach import net
plt.rcParams.update({'font.size':10,'font.family':'serif','mathtext.fontset':'cm'})
fig=plt.figure(figsize=(12,6.6))
cases=[('pcu',(1,0,0)),('pcu',(1,1,0)),('pcu',(1,1,1)),('fcu',(1,1,1)),('fcu',(1,0,0)),('fcu',(1,1,0))]
for i,(kind,hkl) in enumerate(cases):
    P,nn=net(kind,4); n=np.array(hkl,float); n/=np.linalg.norm(n)
    P=P[np.linalg.norm(P,axis=1)<2.6*(1 if kind=='pcu' else .8)]
    h=np.round(P@n,6); h0=0.0
    crystal=P[h<=h0+1e-9]; nxt=P[(h>h0+1e-9)&(h<=h0+1.01)]
    nxt=nxt[np.argsort(np.linalg.norm(nxt-np.outer(nxt@n,n),axis=1))]
    best=max(nxt[:12],key=lambda s:np.sum(np.abs(np.linalg.norm(crystal-s,axis=1)-nn)<1e-6))
    nb=crystal[np.abs(np.linalg.norm(crystal-best,axis=1)-nn)<1e-6]
    ax=fig.add_subplot(2,3,i+1,projection='3d')
    top=crystal[(crystal@n)>h0-0.75]
    # crystal bonds among top layers
    for a in range(len(top)):
        d=np.linalg.norm(top-top[a],axis=1); 
        for b in np.where(np.abs(d-nn)<1e-6)[0]:
            if b>a: ax.plot(*np.c_[top[a],top[b]],color='#cccccc',lw=.6)
    surf=np.isclose(top@n,h0)
    ax.scatter(*top[~surf].T,s=14,c='#9aa7b8',depthshade=False)
    ax.scatter(*top[surf].T,s=26,c='#4C78A8',depthshade=False)
    for q in nb: ax.plot(*np.c_[best,q],color='#E45756',lw=3)
    ax.scatter(*best,s=110,c='#E45756',depthshade=False,edgecolor='k')
    # orient view along a direction tilted from the normal
    az=np.degrees(np.arctan2(n[1],n[0])); el=np.degrees(np.arcsin(n[2]))
    ax.view_init(el*0.6+20,az+35); ax.set_axis_off(); ax.set_box_aspect((1,1,1))
    name={'pcu':'pcu net (MOF-5)','fcu':'fcu net (UiO-66/67)'}[kind]
    ax.set_title(f"{name}, face ({''.join(map(str,hkl))})\nnew node makes {len(nb)} bond{'s' if len(nb)>1 else ''}",fontsize=10)
fig.text(.5,.02,"Blue = top layer of the crystal, red = a new node arriving on the face, red sticks = bonds it can form at once. "
         "More bonds = attaches easily = face grows fast.",ha='center',fontsize=9)
plt.savefig('fig/attach.png',dpi=200,bbox_inches='tight'); plt.close(); print('ok')
