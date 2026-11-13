# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Contact geometry for deforming polygons and stationary point/edge obstacles.

Standalone mathematical kernels, no bpy dependency. All contacts are discrete
(no continuous collision detection). The Numba version uses the same serial
accumulation as Python, avoiding races on shared face vertices.
"""
import math
import numpy as np

try:
    from sverchok.dependencies import numba, scipy
except ImportError:  # Numeric tests outside Blender
    try:
        import numba
    except ImportError:
        numba = None
    try:
        import scipy
    except ImportError:
        scipy = None

from sverchok.utils.pulga_self_edge_collision import _fit_parameter

HAS_NUMBA = numba is not None
HAS_SCIPY = scipy is not None
EPS = 1.e-24


def _validate_engine(engine):
    if engine not in ('AUTO', 'NUMPY', 'NUMBA'):
        raise ValueError(f'Unknown collision engine {engine}')
    if engine == 'NUMBA' and not HAS_NUMBA:
        raise RuntimeError('Numba requested but not installed')
    return engine == 'NUMBA' or engine == 'AUTO' and HAS_NUMBA


def _points(data):
    arr = np.asarray(data, dtype=np.float64)
    if arr.size == 0:
        return np.zeros((0, 3), dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3 or not np.all(np.isfinite(arr)):
        raise ValueError('Expected finite XYZ points')
    return np.ascontiguousarray(arr)


def _edges(data, count):
    arr = np.asarray(data)
    if arr.size == 0:
        return np.zeros((0, 2), dtype=np.int64)
    if arr.ndim != 2 or arr.shape[1] != 2 or not np.issubdtype(arr.dtype, np.integer):
        raise ValueError('Edges must be pairs of integer vertex indices')
    result = np.ascontiguousarray(arr, dtype=np.int64)
    if np.any(result < 0) or np.any(result >= count):
        raise ValueError('Edge index out of range')
    return result


def _area_2d(points):
    return sum(points[i][0]*points[(i+1)%len(points)][1] -
               points[(i+1)%len(points)][0]*points[i][1]
               for i in range(len(points)))


def _orient2(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _point_in_triangle2(p, a, b, c, sign, eps):
    return (sign*_orient2(a,b,p) >= -eps and
            sign*_orient2(b,c,p) >= -eps and
            sign*_orient2(c,a,p) >= -eps)


def triangulate_faces(verts, faces):
    """Ear-clip planar polygons into triangles; preserve whole-face exclusion.

    Supports concave simple polygons. Nonplanar polygons use their best-area
    projection; triangulation is determined once at force setup.
    """
    v = _points(verts)
    tris, exclude = [], []
    for face in faces:
        ids = [int(i) for i in face]
        if len(ids) < 3:
            raise ValueError('Polygon must have at least three vertices')
        if len(set(ids)) != len(ids) or min(ids) < 0 or max(ids) >= len(v):
            raise ValueError('Invalid polygon indices')
        if len(ids) == 3:
            tris.append(ids)
            exclude.append(ids)
            continue
        coords = v[ids]
        # Newell normal: robust projection plane for a generally planar face.
        nx = ny = nz = 0.0
        for p, q in zip(coords, np.roll(coords, -1, axis=0)):
            nx += (p[1]-q[1])*(p[2]+q[2])
            ny += (p[2]-q[2])*(p[0]+q[0])
            nz += (p[0]-q[0])*(p[1]+q[1])
        if max(abs(nx),abs(ny),abs(nz)) < 1.e-12:
            raise ValueError('Degenerate polygon cannot be triangulated')
        drop = int(np.argmax(np.abs([nx, ny, nz])))
        axes = [k for k in range(3) if k != drop]
        flat = coords[:, axes]
        sign = 1.0 if _area_2d(flat) > 0 else -1.0
        remaining = list(range(len(ids)))
        epsilon = 1e-13 * max(1.0, np.max(np.abs(flat))**2)
        while len(remaining) > 3:
            found = False
            for k in range(len(remaining)):
                prev, mid, nxt = (remaining[k-1], remaining[k],
                                  remaining[(k+1) % len(remaining)])
                a, b, c = flat[prev], flat[mid], flat[nxt]
                if sign * _orient2(a, b, c) <= epsilon:
                    continue
                if any(_point_in_triangle2(flat[m], a, b, c, sign, epsilon)
                       for m in remaining if m not in (prev, mid, nxt)):
                    continue
                tris.append([ids[prev], ids[mid], ids[nxt]])
                exclude.append(ids)
                remaining.pop(k)
                found = True
                break
            if not found:
                raise ValueError('Polygon is degenerate or non-simple; cannot ear-clip')
        tris.append([ids[i] for i in remaining])
        exclude.append(ids)
    max_len = max(map(len, exclude), default=0)
    blocked = np.full((len(tris), max_len), -1, dtype=np.int64)
    for i, ids in enumerate(exclude):
        blocked[i, :len(ids)] = ids
    return np.asarray(tris, dtype=np.int64).reshape(-1, 3), blocked


def _segment_closest(px, py, pz, ax, ay, az, bx, by, bz):
    dx, dy, dz = bx-ax, by-ay, bz-az
    len2 = dx*dx + dy*dy + dz*dz
    t = 0.0
    if len2 > EPS:
        t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy+(pz-az)*dz)/len2))
    return ax+t*dx, ay+t*dy, az+t*dz, t


def _triangle_closest(px, py, pz, ax, ay, az, bx, by, bz, cx, cy, cz):
    """Closest point on triangle; return Q and barycentric coordinates.

    Ericson region tests with degenerate fallback to its three segments.
    """
    abx, aby, abz = bx-ax, by-ay, bz-az
    acx, acy, acz = cx-ax, cy-ay, cz-az
    apx, apy, apz = px-ax, py-ay, pz-az
    xx, xy, xz = aby*acz-abz*acy, abz*acx-abx*acz, abx*acy-aby*acx
    if xx*xx+xy*xy+xz*xz <= EPS:
        q0x,q0y,q0z,t0 = _segment_closest(px,py,pz, ax,ay,az,bx,by,bz)
        q1x,q1y,q1z,t1 = _segment_closest(px,py,pz, bx,by,bz,cx,cy,cz)
        q2x,q2y,q2z,t2 = _segment_closest(px,py,pz, cx,cy,cz,ax,ay,az)
        ds0=(px-q0x)**2+(py-q0y)**2+(pz-q0z)**2
        ds1=(px-q1x)**2+(py-q1y)**2+(pz-q1z)**2
        ds2=(px-q2x)**2+(py-q2y)**2+(pz-q2z)**2
        if ds0 <= ds1 and ds0 <= ds2: return q0x,q0y,q0z,1-t0,t0,0.0
        if ds1 <= ds2: return q1x,q1y,q1z,0.0,1-t1,t1
        return q2x,q2y,q2z,t2,0.0,1-t2
    d1 = abx*apx + aby*apy + abz*apz
    d2 = acx*apx + acy*apy + acz*apz
    if d1 <= 0.0 and d2 <= 0.0: return ax,ay,az,1.0,0.0,0.0
    bpx,bpy,bpz = px-bx, py-by, pz-bz
    d3 = abx*bpx + aby*bpy + abz*bpz
    d4 = acx*bpx + acy*bpy + acz*bpz
    if d3 >= 0.0 and d4 <= d3: return bx,by,bz,0.0,1.0,0.0
    vc=d1*d4-d3*d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v=d1/(d1-d3)
        return ax+v*abx,ay+v*aby,az+v*abz,1-v,v,0.0
    cpx,cpy,cpz=px-cx,py-cy,pz-cz
    d5=abx*cpx+aby*cpy+abz*cpz
    d6=acx*cpx+acy*cpy+acz*cpz
    if d6 >= 0.0 and d5 <= d6: return cx,cy,cz,0.0,0.0,1.0
    vb=d5*d2-d1*d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w=d2/(d2-d6)
        return ax+w*acx,ay+w*acy,az+w*acz,1-w,0.0,w
    va=d3*d6-d5*d4
    if va <= 0.0 and d4-d3 >= 0.0 and d5-d6 >= 0.0:
        w=(d4-d3)/((d4-d3)+(d5-d6))
        return bx+w*(cx-bx),by+w*(cy-by),bz+w*(cz-bz),0.0,1-w,w
    denom=1.0/(va+vb+vc)
    v=vb*denom; w=vc*denom
    return (ax+v*abx+w*acx, ay+v*aby+w*acy, az+v*abz+w*acz,
            1-v-w,v,w)


def _contact_normal(vx,vy,vz,rvx,rvy,rvz,ax,ay,az,bx,by,bz,cx,cy,cz):
    len2=vx*vx+vy*vy+vz*vz
    if len2 > EPS:
        d=math.sqrt(len2)
        return vx/d,vy/d,vz/d,d
    abx,aby,abz=bx-ax,by-ay,bz-az
    acx,acy,acz=cx-ax,cy-ay,cz-az
    nx,ny,nz=aby*acz-abz*acy,abz*acx-abx*acz,abx*acy-aby*acx
    nn=nx*nx+ny*ny+nz*nz
    if nn <= EPS:
        # Velocity-based fallback for a completely collapsed triangle.
        vn=rvx*rvx+rvy*rvy+rvz*rvz
        if vn > EPS:
            sc=-1/math.sqrt(vn)
            return rvx*sc,rvy*sc,rvz*sc,0.0
        return 0.0,0.0,1.0,0.0
    sc=1/math.sqrt(nn)
    nx*=sc;ny*=sc;nz*=sc
    if rvx*nx+rvy*ny+rvz*nz > 0.0:
        nx=-nx;ny=-ny;nz=-nz
    return nx,ny,nz,0.0


def group_polygon_faces(triangles, excluded):
    """Group triangles by their original face, retained in ``excluded``.

    Triangulation is used only for triangles and n-gons; each original face
    produces *one* collision response per particle. Quads use a bilinear patch.
    """
    triangles = np.asarray(triangles, dtype=np.int64).reshape(-1, 3)
    excluded = np.asarray(excluded, dtype=np.int64)
    if excluded.ndim != 2 or len(excluded) != len(triangles):
        raise ValueError('Excluded faces must match triangle count')
    if len(triangles) == 0:
        return (np.zeros((0, excluded.shape[1]), dtype=np.int64),
                np.zeros(0, dtype=np.int64), np.zeros(1, dtype=np.int64))
    faces, counts, offsets = [], [], [0]
    for t, row in enumerate(excluded):
        if t > 0 and np.array_equal(row, excluded[t - 1]):
            offsets[-1] = t + 1
        else:
            faces.append(row.copy())
            counts.append(int(np.count_nonzero(row >= 0)))
            offsets.append(t + 1)
    return (np.ascontiguousarray(faces, dtype=np.int64),
            np.asarray(counts, dtype=np.int64),
            np.asarray(offsets, dtype=np.int64))


def _quad_closest(px, py, pz, a, b, c, d):
    """Closest point on the *bilinear* quad Q(u,v), 0<=u,v<=1.

    Four boundary segments are checked analytically. Interior minima are
    refined with damped Gauss-Newton from three seeds (center and two triangle
    projections). Using multiple seeds reduces failures on warped quads;
    nonconvex and folded quads remain outside the guaranteed domain.
    """
    # A, B, C, D go around the quad perimeter.
    ex, ey, ez = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    fx, fy, fz = d[0]-a[0], d[1]-a[1], d[2]-a[2]
    gx = a[0]-b[0]+c[0]-d[0]
    gy = a[1]-b[1]+c[1]-d[1]
    gz = a[2]-b[2]+c[2]-d[2]

    # The boundary of a bilinear patch consists of four straight segments.
    best2=math.inf
    bu=bv=0.0
    bqx=bqy=bqz=0.0
    for k in range(4):
        if k == 0:
            qx,qy,qz,t=_segment_closest(px,py,pz,a[0],a[1],a[2],b[0],b[1],b[2])
            u,v=t,0.0
        elif k == 1:
            qx,qy,qz,t=_segment_closest(px,py,pz,b[0],b[1],b[2],c[0],c[1],c[2])
            u,v=1.0,t
        elif k == 2:
            qx,qy,qz,t=_segment_closest(px,py,pz,c[0],c[1],c[2],d[0],d[1],d[2])
            u,v=1.0-t,1.0
        else:
            qx,qy,qz,t=_segment_closest(px,py,pz,d[0],d[1],d[2],a[0],a[1],a[2])
            u,v=0.0,1.0-t
        ds=(qx-px)**2+(qy-py)**2+(qz-pz)**2
        if ds<best2:
            best2=ds
            bu,bv=u,v
            bqx,bqy,bqz=qx,qy,qz

    # Extra interior seeds from a piecewise-linear initial approximation.
    _,_,_,w0,w1,w2=_triangle_closest(px,py,pz,a[0],a[1],a[2],b[0],b[1],b[2],c[0],c[1],c[2])
    t1u,t1v=w1+w2,w2
    _,_,_,w0,w1,w2=_triangle_closest(px,py,pz,a[0],a[1],a[2],c[0],c[1],c[2],d[0],d[1],d[2])
    t2u,t2v=w1,w1+w2

    for seed in range(3):
        if seed == 0:
            u,v=.5,.5
        elif seed == 1:
            u,v=t1u,t1v
        else:
            u,v=t2u,t2v
        for iteration in range(25):
            qx=a[0]+u*ex+v*fx+u*v*gx
            qy=a[1]+u*ey+v*fy+u*v*gy
            qz=a[2]+u*ez+v*fz+u*v*gz
            rx,ry,rz=qx-px,qy-py,qz-pz
            old=rx*rx+ry*ry+rz*rz
            ux,uy,uz=ex+v*gx,ey+v*gy,ez+v*gz
            vx,vy,vz=fx+u*gx,fy+u*gy,fz+u*gz
            g0=rx*ux+ry*uy+rz*uz
            g1=rx*vx+ry*vy+rz*vz
            h00=ux*ux+uy*uy+uz*uz
            h01=ux*vx+uy*vy+uz*vz
            h11=vx*vx+vy*vy+vz*vz
            reg=1e-12*(1.0+h00+h11)
            h00+=reg
            h11+=reg
            determinant=h00*h11-h01*h01
            if determinant<=EPS:
                break
            du=(h11*g0-h01*g1)/determinant
            dv=(h00*g1-h01*g0)/determinant
            if du*du+dv*dv<1e-28:
                break
            scale=1.0
            accepted=False
            for step in range(12):
                nu=max(0.0,min(1.0,u-scale*du))
                nv=max(0.0,min(1.0,v-scale*dv))
                nx=a[0]+nu*ex+nv*fx+nu*nv*gx
                ny=a[1]+nu*ey+nv*fy+nu*nv*gy
                nz=a[2]+nu*ez+nv*fz+nu*nv*gz
                nd=(nx-px)**2+(ny-py)**2+(nz-pz)**2
                if nd<old-1e-15*max(old,1e-20):
                    u,v=nu,nv
                    accepted=True
                    break
                scale*=.5
            if not accepted:
                break
        qx=a[0]+u*ex+v*fx+u*v*gx
        qy=a[1]+u*ey+v*fy+u*v*gy
        qz=a[2]+u*ez+v*fz+u*v*gz
        ds=(qx-px)**2+(qy-py)**2+(qz-pz)**2
        if ds<best2:
            best2=ds
            bu,bv=u,v
            bqx,bqy,bqz=qx,qy,qz
    return bqx,bqy,bqz,bu,bv


def _ngon_mean_value_weights(pos, face, size, qx, qy, qz):
    """Planar polygon mean-value coordinates for a closest face point.

    Handles clockwise/counter-clockwise polygons, exact boundary contacts and
    warped faces. Weights are evaluated in a stable 2D projection; their lifted
    3D position defines the face contact (rather than switching to one triangle
    whenever a vertex leaves the original polygon plane). Invalid projections
    still use triangle weights as a safe fallback.
    """
    weights = np.zeros(size, dtype=np.float64)
    # Newell normal to choose a stable 2-D projection.
    nx = ny = nz = 0.0
    scale = 0.0
    for k in range(size):
        a = face[k]
        b = face[(k + 1) % size]
        ax, ay, az = pos[a, 0], pos[a, 1], pos[a, 2]
        bx, by, bz = pos[b, 0], pos[b, 1], pos[b, 2]
        nx += (ay-by)*(az+bz)
        ny += (az-bz)*(ax+bx)
        nz += (ax-bx)*(ay+by)
        dx,dy,dz=bx-ax,by-ay,bz-az
        scale = max(scale, math.sqrt(dx*dx+dy*dy+dz*dz))
    if scale <= 1.e-14 or max(abs(nx), abs(ny), abs(nz)) < 1.e-16*scale*scale:
        return weights, False
    drop = 0
    if abs(ny) > abs(nx) and abs(ny) >= abs(nz):
        drop = 1
    elif abs(nz) > abs(nx) and abs(nz) > abs(ny):
        drop = 2
    rx=np.empty(size,dtype=np.float64)
    ry=np.empty(size,dtype=np.float64)
    lengths=np.empty(size,dtype=np.float64)
    for k in range(size):
        idx=face[k]
        if drop == 0:
            rx[k]=pos[idx,1]-qy
            ry[k]=pos[idx,2]-qz
        elif drop == 1:
            rx[k]=pos[idx,0]-qx
            ry[k]=pos[idx,2]-qz
        else:
            rx[k]=pos[idx,0]-qx
            ry[k]=pos[idx,1]-qy
        lengths[k]=math.sqrt(rx[k]*rx[k]+ry[k]*ry[k])
        if lengths[k] <= scale*1.e-12:
            weights[k]=1.0
            return weights, True
    half=np.empty(size,dtype=np.float64)
    for k in range(size):
        k1=(k+1)%size
        cross=rx[k]*ry[k1]-ry[k]*rx[k1]
        dot=rx[k]*rx[k1]+ry[k]*ry[k1]
        edge_x,edge_y=rx[k1]-rx[k],ry[k1]-ry[k]
        edge_length=math.sqrt(edge_x*edge_x+edge_y*edge_y)
        # Projection falls on a boundary edge: linear edge weights.
        if (edge_length > 1.e-14*scale and
            abs(cross) <= 1.e-12*scale*edge_length and
            dot < 0.0):
            t=-(rx[k]*edge_x+ry[k]*edge_y)/(edge_length*edge_length)
            if -1.e-12 <= t <= 1.0+1.e-12:
                t=max(0.0,min(1.0,t))
                weights[k]=1.0-t
                weights[k1]=t
                return weights, True
        # Signed half-angle tangent, stable when angle is not near pi.
        den=lengths[k]*lengths[k1]+dot
        if abs(den) < 1.e-14*scale*scale:
            return weights, False
        half[k]=cross/den
    total=0.0
    for k in range(size):
        weights[k]=(half[k-1]+half[k])/lengths[k]
        total+=weights[k]
    if abs(total)<1.e-14/scale or not math.isfinite(total):
        return weights, False
    x=y=z=0.0
    for k in range(size):
        weights[k]/=total
        if weights[k]<-1.e-9 or not math.isfinite(weights[k]):
            return weights, False
        idx=face[k]
        x+=weights[k]*pos[idx,0]
        y+=weights[k]*pos[idx,1]
        z+=weights[k]*pos[idx,2]
    # MVC reproduces the 2D projection of Q, not its out-of-plane component.
    # Comparing the full 3D reconstruction to the triangulated contact would
    # wrongly reject virtually every deformed n-gon and fall back to a triangle.
    if drop == 0:
        planar_error=(y-qy)**2+(z-qz)**2
    elif drop == 1:
        planar_error=(x-qx)**2+(z-qz)**2
    else:
        planar_error=(x-qx)**2+(y-qy)**2
    if planar_error > (1.e-7*scale)**2:
        return weights, False
    return weights, True


def _polygon_forces_loop(pos, vel, rads, triangles, faces, sizes, offsets,
                         strength, thickness, damping):
    """Bilateral vertex/face forces: one contact per source point and face.

    Quad contact positions and four reaction weights are derived from the same
    bilinear patch, preserving force balance, and torque for a frictionless
    contact. N-gons use mean-value coordinates for smooth full-face force
    distribution. Warped n-gons use the lifted MVC patch, with local triangle
    fallback only for invalid or degenerate 2D projections.
    """
    n=len(pos)
    out=np.zeros((n,3),dtype=np.float64)
    for i in range(n):
        px,py,pz=pos[i,0],pos[i,1],pos[i,2]
        radius=rads[i]+thickness[i]
        if radius<=0.0 or (strength[i]<=0.0 and damping[i]<=0.0):
            continue
        for j in range(len(faces)):
            size=sizes[j]
            blocked=False
            lo_x=lo_y=lo_z=math.inf
            hi_x=hi_y=hi_z=-math.inf
            for k in range(size):
                id=faces[j,k]
                if id==i:
                    blocked=True
                    break
                x,y,z=pos[id,0],pos[id,1],pos[id,2]
                lo_x=min(lo_x,x);lo_y=min(lo_y,y);lo_z=min(lo_z,z)
                hi_x=max(hi_x,x);hi_y=max(hi_y,y);hi_z=max(hi_z,z)
            if blocked:
                continue
            # The entire bilinear patch and triangulation lie within the box.
            if (px<lo_x-radius or px>hi_x+radius or
                py<lo_y-radius or py>hi_y+radius or
                pz<lo_z-radius or pz>hi_z+radius):
                continue

            use_full=False
            if size==4:
                a,b,c,d=faces[j,0],faces[j,1],faces[j,2],faces[j,3]
                qx,qy,qz,u,v=_quad_closest(px,py,pz,pos[a],pos[b],pos[c],pos[d])
                ids=(a,b,c,d)
                weights=((1.0-u)*(1.0-v),u*(1.0-v),u*v,(1.0-u)*v)
                # Local bilinear derivatives supply a contact normal at d=0.
                dxu=(pos[b,0]-pos[a,0])+v*(pos[a,0]-pos[b,0]+pos[c,0]-pos[d,0])
                dyu=(pos[b,1]-pos[a,1])+v*(pos[a,1]-pos[b,1]+pos[c,1]-pos[d,1])
                dzu=(pos[b,2]-pos[a,2])+v*(pos[a,2]-pos[b,2]+pos[c,2]-pos[d,2])
                dxv=(pos[d,0]-pos[a,0])+u*(pos[a,0]-pos[b,0]+pos[c,0]-pos[d,0])
                dyv=(pos[d,1]-pos[a,1])+u*(pos[a,1]-pos[b,1]+pos[c,1]-pos[d,1])
                dzv=(pos[d,2]-pos[a,2])+u*(pos[a,2]-pos[b,2]+pos[c,2]-pos[d,2])
                ax,ay,az=qx,qy,qz
                bx,by,bz=qx+dxu,qy+dyu,qz+dzu
                cx,cy,cz=qx+dxv,qy+dyv,qz+dzv
            else:
                best2=math.inf
                best_a=best_b=best_c=-1
                best_wa=best_wb=best_wc=0.0
                qx=qy=qz=0.0
                # A polygon triangulated into multiple faces still gets only
                # one contact, avoiding duplicate forces at internal diagonals.
                for k in range(offsets[j],offsets[j+1]):
                    a,b,c=triangles[k,0],triangles[k,1],triangles[k,2]
                    tqx,tqy,tqz,wa,wb,wc=_triangle_closest(
                        px,py,pz,pos[a,0],pos[a,1],pos[a,2],pos[b,0],pos[b,1],pos[b,2],pos[c,0],pos[c,1],pos[c,2])
                    ds=(px-tqx)**2+(py-tqy)**2+(pz-tqz)**2
                    if ds<best2:
                        best2=ds
                        qx,qy,qz=tqx,tqy,tqz
                        best_a,best_b,best_c=a,b,c
                        best_wa,best_wb,best_wc=wa,wb,wc
                a,b,c=best_a,best_b,best_c
                ids=(a,b,c,-1)
                weights=(best_wa,best_wb,best_wc,0.0)
                use_full=False
                if size>4:
                    ngon_weights, use_full = _ngon_mean_value_weights(
                        pos,faces[j],size,qx,qy,qz)
                    if use_full:
                        # The contact point and force-transfer weights must
                        # describe the same 3D surface. The triangulated
                        # nearest point is only the starting location in the
                        # projected polygon, not the final MVC patch point.
                        qx=qy=qz=0.0
                        for kk in range(size):
                            index=faces[j,kk]
                            w=ngon_weights[kk]
                            qx+=w*pos[index,0]
                            qy+=w*pos[index,1]
                            qz+=w*pos[index,2]
                ax,ay,az=pos[a,0],pos[a,1],pos[a,2]
                bx,by,bz=pos[b,0],pos[b,1],pos[b,2]
                cx,cy,cz=pos[c,0],pos[c,1],pos[c,2]
            rx,ry,rz=px-qx,py-qy,pz-qz
            if rx*rx+ry*ry+rz*rz>=radius*radius:
                continue
            rvx,rvy,rvz=vel[i,0],vel[i,1],vel[i,2]
            if size>4 and use_full:
                for k in range(size):
                    idx=faces[j,k]
                    w=ngon_weights[k]
                    rvx-=w*vel[idx,0]
                    rvy-=w*vel[idx,1]
                    rvz-=w*vel[idx,2]
            else:
                for k in range(4):
                    idx=ids[k]
                    if idx>=0:
                        w=weights[k]
                        rvx-=w*vel[idx,0]
                        rvy-=w*vel[idx,1]
                        rvz-=w*vel[idx,2]
            nx,ny,nz,dist=_contact_normal(rx,ry,rz,rvx,rvy,rvz,
                                           ax,ay,az,bx,by,bz,cx,cy,cz)
            closing=max(0.0,-(rvx*nx+rvy*ny+rvz*nz))
            f=strength[i]*(radius-dist)+damping[i]*closing
            fx,fy,fz=f*nx,f*ny,f*nz
            out[i,0]+=fx;out[i,1]+=fy;out[i,2]+=fz
            if size>4 and use_full:
                for k in range(size):
                    idx=faces[j,k]
                    w=ngon_weights[k]
                    out[idx,0]-=w*fx
                    out[idx,1]-=w*fy
                    out[idx,2]-=w*fz
            else:
                for k in range(4):
                    idx=ids[k]
                    if idx>=0:
                        w=weights[k]
                        out[idx,0]-=w*fx
                        out[idx,1]-=w*fy
                        out[idx,2]-=w*fz
    return out


def _nearest_edges_loop(points, starts, ends):
    q=np.zeros((len(points),3),dtype=np.float64)
    dist2=np.full(len(points),np.inf,dtype=np.float64)
    for i in range(len(points)):
        px,py,pz=points[i,0],points[i,1],points[i,2]
        for k in range(len(starts)):
            ax,ay,az=starts[k,0],starts[k,1],starts[k,2]
            bx,by,bz=ends[k,0],ends[k,1],ends[k,2]
            x,y,z,_=_segment_closest(px,py,pz,ax,ay,az,bx,by,bz)
            ds=(px-x)**2+(py-y)**2+(pz-z)**2
            if ds < dist2[i]:
                dist2[i]=ds
                q[i,0]=x;q[i,1]=y;q[i,2]=z
    return q,dist2


def _nearest_points_loop(points, obstacles):
    q=np.zeros((len(points),3),dtype=np.float64)
    dist2=np.full(len(points),np.inf,dtype=np.float64)
    for i in range(len(points)):
        px,py,pz=points[i,0],points[i,1],points[i,2]
        for k in range(len(obstacles)):
            x,y,z=obstacles[k,0],obstacles[k,1],obstacles[k,2]
            ds=(px-x)**2+(py-y)**2+(pz-z)**2
            if ds < dist2[i]:
                dist2[i]=ds
                q[i,0]=x;q[i,1]=y;q[i,2]=z
    return q,dist2


if HAS_NUMBA:
    _segment_closest_jit=numba.njit(cache=True)(_segment_closest)
    import types
    _gt=_triangle_closest.__globals__.copy()
    _gt['_segment_closest']=_segment_closest_jit
    _triangle_closest_jit=numba.njit(cache=True)(
        types.FunctionType(_triangle_closest.__code__, _gt, '_triangle_closest'))
    _contact_normal_jit=numba.njit(cache=True)(_contact_normal)
    _ngon_weights_jit=numba.njit(cache=True)(_ngon_mean_value_weights)

    # Compile the same geometry helpers for Python and Numba.
    _g_quad=_quad_closest.__globals__.copy()
    _g_quad.update(_segment_closest=_segment_closest_jit,
                   _triangle_closest=_triangle_closest_jit)
    _quad_closest_jit=numba.njit(cache=True)(types.FunctionType(
        _quad_closest.__code__, _g_quad, '_quad_closest'))
    _g=_polygon_forces_loop.__globals__.copy()
    _g.update(_triangle_closest=_triangle_closest_jit,
              _quad_closest=_quad_closest_jit,
              _contact_normal=_contact_normal_jit,
              _ngon_mean_value_weights=_ngon_weights_jit)
    _compiled_polygon=types.FunctionType(_polygon_forces_loop.__code__, _g,
                                         '_polygon_forces_loop')
    _polygon_forces_jit=numba.njit(cache=True)(_compiled_polygon)
    _g2=_nearest_edges_loop.__globals__.copy()
    _g2['_segment_closest']=_segment_closest_jit
    _compiled_edges=types.FunctionType(_nearest_edges_loop.__code__, _g2,
                                        '_nearest_edges_loop')
    _nearest_edges_jit=numba.njit(cache=True)(_compiled_edges)
    _nearest_points_jit=numba.njit(cache=True)(_nearest_points_loop)


def polygon_contact_forces(positions, velocity, radii, triangles, excluded,
                           strength, thickness, damping, engine='AUTO',
                           grouping=None):
    accelerated=_validate_engine(engine)
    pos=_points(positions); vel=_points(velocity)
    if len(pos)!=len(vel): raise ValueError('Position/velocity mismatch')
    triangles=np.ascontiguousarray(np.asarray(triangles,dtype=np.int64).reshape(-1,3))
    excluded=np.ascontiguousarray(np.asarray(excluded,dtype=np.int64))
    if len(excluded)!=len(triangles): raise ValueError('Exclusion/triangle count mismatch')
    if len(triangles) and (np.min(triangles)<0 or np.max(triangles)>=len(pos)):
        raise ValueError('Triangle vertex index out of range')
    count=len(pos)
    r=_fit_parameter(radii,count,'Radius')
    s=_fit_parameter(strength,count,'Strength')
    t=_fit_parameter(thickness,count,'Thickness')
    d=_fit_parameter(damping,count,'Damping')
    if not count or not len(triangles): return np.zeros((count,3),dtype=np.float64)
    faces,sizes,offsets = (group_polygon_faces(triangles, excluded)
                           if grouping is None else grouping)
    if len(faces) and (np.min(faces[faces>=0])<0 or np.max(faces)>=len(pos)):
        raise ValueError('Polygon vertex index out of range')
    kernel=_polygon_forces_jit if accelerated else _polygon_forces_loop
    return kernel(pos,vel,r,triangles,faces,sizes,offsets,s,t,d)


class SvSelfPolygonCollisionForce:
    def __init__(self, polygons, strength, thickness, damping, engine='AUTO'):
        self.polygons=polygons
        self.strength=strength
        self.thickness=thickness
        self.damping=damping
        self.engine=engine

    def setup(self, ps):
        self.tris,self.exclude=triangulate_faces(ps.verts,self.polygons)
        self.groups=group_polygon_faces(self.tris,self.exclude)
        self._s=_fit_parameter(self.strength,ps.v_len,'Strength')
        self._t=_fit_parameter(self.thickness,ps.v_len,'Thickness')
        self._d=_fit_parameter(self.damping,ps.v_len,'Damping')

    def add(self, ps):
        ps.force_resultant += polygon_contact_forces(
            ps.verts,ps.vel,ps.rads,self.tris,self.exclude,
            self._s,self._t,self._d,self.engine,self.groups)


class SvStaticPointEdgeObstacleForce:
    """Stationary point or segment obstacles with one deepest contact per particle.

    Same positional response concept as SvObstaclesBVHForce, but no polygon
    normals are required. SciPy cKDTree is used for stationary point targets.
    """
    def __init__(self, verts, edges, absorption, thickness, domain, engine='AUTO'):
        self.verts=_points(verts)
        self.domain=domain
        self.edges=_edges(edges,len(self.verts)) if domain=='EDGES' else np.zeros((0,2),np.int64)
        self.absorption=1.0-max(0.0,min(1.0,float(np.asarray(absorption).reshape(-1)[0])))
        self.thickness=np.asarray(thickness,dtype=np.float64).reshape(-1)
        self.engine=engine
        self.tree=None
        if domain=='VERTS' and engine=='AUTO' and HAS_SCIPY and len(self.verts):
            self.tree=scipy.spatial.cKDTree(self.verts)
        if domain=='EDGES':
            self.starts=np.ascontiguousarray(self.verts[self.edges[:,0]])
            self.ends=np.ascontiguousarray(self.verts[self.edges[:,1]])

    def setup(self, ps):
        self._validate=_validate_engine(self.engine)
        self._thickness=_fit_parameter(self.thickness,ps.v_len,'Thickness')

    def nearest(self, points):
        p=_points(points)
        if self.domain=='VERTS':
            if not len(self.verts):
                return np.zeros_like(p),np.full(len(p),np.inf)
            if self.tree is not None:
                d,ids=self.tree.query(p)
                return np.ascontiguousarray(self.verts[ids]),np.asarray(d*d)
            fn=_nearest_points_jit if _validate_engine(self.engine) else _nearest_points_loop
            return fn(p,self.verts)
        if not len(self.edges):
            return np.zeros_like(p),np.full(len(p),np.inf)
        fn=_nearest_edges_jit if _validate_engine(self.engine) else _nearest_edges_loop
        return fn(p,self.starts,self.ends)

    def add(self, ps):
        closest,ds2=self.nearest(ps.verts)
        radii=ps.rads + self._thickness
        mask=np.where(ds2 < radii*radii)[0]
        for i in mask:
            d=math.sqrt(max(ds2[i],0.0))
            if d > 1.e-12:
                n=(ps.verts[i]-closest[i])/d
            else:
                v=ps.vel[i]
                norm=float(np.linalg.norm(v))
                if norm>1.e-12:
                    n=-v/norm
                elif self.domain=='EDGES' and len(self.edges):
                    # Find the segment responsible for the exact overlap.
                    best_j=0
                    best_d2=math.inf
                    for j in range(len(self.edges)):
                        qx,qy,qz,_=_segment_closest(
                            *ps.verts[i], *self.starts[j], *self.ends[j])
                        ds=(ps.verts[i,0]-qx)**2+(ps.verts[i,1]-qy)**2+(ps.verts[i,2]-qz)**2
                        if ds < best_d2:
                            best_j=j
                            best_d2=ds
                    e=self.ends[best_j]-self.starts[best_j]
                    p=np.cross(e,[0.,0.,1.])
                    if np.linalg.norm(p)<=1.e-12:p=np.cross(e,[0.,1.,0.])
                    norm=float(np.linalg.norm(p))
                    n=p/norm if norm>1.e-12 else np.array([1.,0.,0.])
                else:
                    n=np.array([1.,0.,0.])
            ps.verts[i]=closest[i]+n*radii[i]
            vn=np.dot(ps.vel[i],n)
            if vn < 0.0:
                ps.vel[i]-=2*vn*n
            ps.vel[i]*=self.absorption
            fn=np.dot(ps.force_resultant[i],n)
            if fn < 0.0:
                ps.force_resultant[i]-=2*fn*n
            ps.force_resultant[i]*=self.absorption
