import numpy as np
import mcs
from index import Index3D

DEPOSITION_IDENT = -2

def grow_ice(agg, ice_vol, outer_rad_norm=2., move_norm=1.):
    elem_index = Index3D(elem_size=agg.grid_res)
    elem_index.insert(agg.X)

    p_vol = agg.grid_res**3
    n_needed = int(round(abs(ice_vol)/p_vol))
    if n_needed == 0:
        return        
    sig = move_norm*agg.grid_res

    def covering_sphere():
        if agg.X.shape[0] > 1:
            return mcs.minimum_covering_sphere(agg.X)
        else:
            return (agg.X[0,:], agg.grid_res/2.)

    (c,rad) = covering_sphere()

    def attach(p0, p1, n_iters=8):
        for i in xrange(n_iters):
            p = 0.5*(p0+p1)
            near = list(elem_index.items_near(p,search_rad=agg.grid_res))
            if near:
                near = np.array(near)
                dist_sqr_nearest = ((near-p)**2).sum(1).min()
                dist_sqr_nearest /= agg.grid_res**2
            else:
                dist_sqr_nearest = 999.

            if dist_sqr_nearest-1 < 0.01:
                break

            if dist_sqr_nearest > 1:
                p0 = p
            else:
                p1 = p
        agg.add_elements(p[None,:], ident=DEPOSITION_IDENT, update=False)
        return p
    
    n_added = 0
    while n_added < n_needed:
        # randomize starting point on a sphere outside particle
        phi = 2*np.pi*np.random.rand()
        theta = np.arccos(1-2*np.random.rand())
        r = rad*outer_rad_norm
        p = c + np.array([
            r*np.sin(theta)*np.cos(phi),
            r*np.sin(theta)*np.sin(phi),
            r*np.cos(theta)
        ])
        
        while True:
            p_old = p.copy()
            p += sig*np.random.randn(3)
            r_sqr = ((p-c)**2).sum()
            if r_sqr > (rad*outer_rad_norm)**2:
                break

            if r_sqr < rad**2:
                near = list(elem_index.items_near(p,search_rad=agg.grid_res))
                if near:
                    near = np.array(near)
                    dist_sqr = ((near-p)**2).sum(1)
                    if dist_sqr.min() < agg.grid_res**2:                        
                        if ice_vol < 0:
                            p = near[dist_sqr.argmin(),:]
                            agg.remove_elements(p[None,:], update=False)
                            elem_index.remove(p[None,:])
                        else:
                            p = attach(p_old, p)

                        if ((p-c)**2).sum() > rad**2:
                            (c,rad) = covering_sphere()
                        n_added += 1
                        break

    agg.update_coordinates()



