import numpy as np, itertools, math
from scipy.spatial import HalfspaceIntersection, ConvexHull

def family(hkl, cubic_point_group="m-3m"):
    """All symmetry-equivalent directions for cubic m-3m: permutations and sign changes."""
    out=set()
    for p in itertools.permutations(hkl):
        for s in itertools.product([1,-1],repeat=3):
            v=tuple(a*b for a,b in zip(p,s))
            if any(v): out.add(v)
    return sorted(out)

def polytope(planes):
    """planes: list of (normal(3,), distance). Returns vertices, face polygons (ordered), face normals."""
    A=np.array([n/np.linalg.norm(n) for n,_ in planes]); b=np.array([d for _,d in planes])
    hs=HalfspaceIntersection(np.hstack([A,-b[:,None]]),np.zeros(3))
    V=hs.intersections; ch=ConvexHull(V)
    # merge coplanar triangles into faces
    faces={}
    for eq,simp in zip(ch.equations,ch.simplices):
        key=tuple(np.round(eq,6))
        faces.setdefault(key,set()).update(simp)
    polys=[];normals=[]
    for key,idx in faces.items():
        n=np.array(key[:3]); P=V[list(idx)]; c=P.mean(0)
        u=P[0]-c; u/=np.linalg.norm(u); w=np.cross(n,u)
        ang=np.arctan2((P-c)@w,(P-c)@u); P=P[np.argsort(ang)]
        polys.append(P); normals.append(n)
    return V,ch,polys,normals

def descriptors(V,ch,M=400000,seed=0):
    rng=np.random.default_rng(seed); lo,hi=V.min(0),V.max(0)
    P=rng.uniform(lo,hi,(M,3))
    P=P[np.all(P@ch.equations[:,:3].T+ch.equations[:,3]<=1e-12,axis=1)]; P-=P.mean(0)
    lam=np.sort(np.linalg.eigvalsh(P.T@P/len(P)))[::-1]
    k2=1.5*np.sum(lam**2)/np.sum(lam)**2-0.5
    psi=math.pi**(1/3)*(6*ch.volume)**(2/3)/ch.area
    return dict(kappa2=float(k2),psi=float(psi),ar=float(math.sqrt(lam[0]/lam[2])),lam=lam)

def cubic_shape(t, lam=1.0):
    """{100} at distance 1, {111} at distance t; optional affine stretch along z by lam (applied to vertices)."""
    pl=[(np.array(v,float),1.0) for v in family((1,0,0))]+[(np.array(v,float),t) for v in family((1,1,1))]
    V,ch,P,N=polytope(pl)
    if lam==1.0: return V,ch,P,N
    S=np.diag([1,1,lam]); V2=V@S
    ch2=ConvexHull(V2); P2=[p@S for p in P]
    N2=[(np.linalg.inv(S).T@n)/np.linalg.norm(np.linalg.inv(S).T@n) for n in N]
    return V2,ch2,P2,N
