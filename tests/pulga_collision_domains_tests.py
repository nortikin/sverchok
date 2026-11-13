# This file is part of Sverchok.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Standalone numeric tests: python -m unittest tests/test_pulga_collision_domains.py"""
import unittest
import numpy as np

from sverchok.utils.pulga_collision_domains import (
    triangulate_faces, polygon_contact_forces, SvStaticPointEdgeObstacleForce,
    HAS_NUMBA, HAS_SCIPY)


class MockSystem:
    def __init__(self, verts, radii=None, velocities=None):
        self.verts=np.asarray(verts,dtype=np.float64).copy()
        self.v_len=len(self.verts)
        self.rads=np.asarray(radii if radii is not None else [0.5]*self.v_len,
                             dtype=np.float64)
        self.vel=np.asarray(velocities if velocities is not None else np.zeros_like(self.verts),
                            dtype=np.float64)
        self.force_resultant=np.zeros_like(self.verts)


class TestContacts(unittest.TestCase):
    def setUp(self):
        self.pts=np.array([[0.,0.,0.],[2.,0.,0.],[0.,2.,0.],[.4,.4,.2]], dtype=float)
        self.tris,self.exclude=triangulate_faces(self.pts,[[0,1,2]])

    def force(self, engine, z=.2):
        p=self.pts.copy();p[3,2]=z
        return polygon_contact_forces(p,np.zeros_like(p),np.full(4,.5),
                   self.tris,self.exclude,[1.],[0.],[0.],engine)

    def test_front_back(self):
        a=self.force('NUMPY', .2)
        b=self.force('NUMPY',-.2)
        self.assertGreater(a[3,2],0)
        self.assertLess(b[3,2],0)
        np.testing.assert_allclose(a.sum(axis=0),0.,atol=1e-12)
        np.testing.assert_allclose(b.sum(axis=0),0.,atol=1e-12)

    def test_incident_excluded(self):
        self.assertTrue(np.all(self.force('NUMPY')[:3,2] <= 0))
        # If all particles are face vertices, they must not collide with that face.
        tri, exc=triangulate_faces(self.pts[:3], [[0,1,2]])
        f=polygon_contact_forces(self.pts[:3],np.zeros((3,3)),[1.],tri,exc,[1.],[0.],[0.],'NUMPY')
        np.testing.assert_equal(f,0)

    def test_concave_face_triangulation(self):
        points=np.array([[0,0,0],[2,0,0],[2,2,0],[1,0.7,0],[0,2,0]],dtype=float)
        tri,block=triangulate_faces(points,[[0,1,2,3,4]])
        self.assertEqual(tri.shape,(3,3))
        self.assertEqual(block.shape,(3,5))
        self.assertEqual(set(block[0]),set(range(5)))

    def test_normal_zero_distance(self):
        self.assertTrue(np.all(np.isfinite(self.force('NUMPY',0.))))

    @unittest.skipUnless(HAS_NUMBA,'No Numba')
    def test_numba_matches_python(self):
        for z in [-0.2,0.,0.2]:
            np.testing.assert_allclose(self.force('NUMPY',z),self.force('NUMBA',z),atol=1e-12)

    def test_obstacle_points(self):
        ps=MockSystem([[.2,0,0]], [.5], velocities=[[-1,0,0]])
        f=SvStaticPointEdgeObstacleForce([[0,0,0]], [],[0.25],[0.], 'VERTS')
        f.setup(ps);f.add(ps)
        np.testing.assert_allclose(ps.verts,[[.5,0,0]])
        np.testing.assert_allclose(ps.vel,[[.75,0,0]])

    def test_obstacle_edge(self):
        ps=MockSystem([[1.,0.2,0.]], [.5], velocities=[[0.,-1.,0.]])
        f=SvStaticPointEdgeObstacleForce([[0,0,0],[2,0,0]], [[0,1]], [0.], [0.], 'EDGES')
        f.setup(ps);f.add(ps)
        np.testing.assert_allclose(ps.verts, [[1.,.5,0.]])
        np.testing.assert_allclose(ps.vel, [[0.,1.,0.]])

    def test_no_obstacles(self):
        ps=MockSystem([[.2,0,0]])
        f=SvStaticPointEdgeObstacleForce([],[],[0.1],[0.], 'VERTS')
        f.setup(ps);f.add(ps)
        np.testing.assert_allclose(ps.verts,[[.2,0,0]])

    @unittest.skipUnless(HAS_NUMBA,'No Numba')
    def test_edges_numba_python(self):
        target=[[0,0,0],[2,0,0],[1,1,0]]
        verts=[[1.,.2,0],[1.,2.,0]]
        a=SvStaticPointEdgeObstacleForce(target,[[0,1],[1,2]],[0.],[0.],'EDGES','NUMPY')
        b=SvStaticPointEdgeObstacleForce(target,[[0,1],[1,2]],[0.],[0.],'EDGES','NUMBA')
        qa,da=a.nearest(verts);qb,db=b.nearest(verts)
        np.testing.assert_allclose(qa,qb,atol=1e-12)
        np.testing.assert_allclose(da,db,atol=1e-12)

    @unittest.skipUnless(HAS_SCIPY,'No scipy')
    def test_scipy_point_index(self):
        f=SvStaticPointEdgeObstacleForce([[0,0,0],[1,1,0]],[],[0.],[0.],'VERTS')
        self.assertIsNotNone(f.tree)
        q,d2=f.nearest([[.1,0,0]])
        np.testing.assert_allclose(q,[[0,0,0]])
        np.testing.assert_allclose(d2,[.01])


class TestBilinearQuad(unittest.TestCase):
    def setUp(self):
        self.quad=np.array([[-1.,-1.,0.],[1.,-1.,0.],[1.,1.,0.],[-1.,1.,0.]],dtype=float)
        self.face=[[0,1,2,3]]

    def force(self, point, engine='NUMPY', velocity=None, quad=None, radius=.5):
        q=self.quad if quad is None else quad
        pos=np.vstack([q,point])
        vel=np.zeros_like(pos)
        if velocity is not None:
            vel[4]=velocity
        tris, excluded=triangulate_faces(pos,self.face)
        f=polygon_contact_forces(pos,vel,[0.,0.,0.,0.,radius],tris,excluded,
                                 [1.],[0.],[0.],engine)
        return pos,f

    def test_center_four_equal_reactions(self):
        _,f=self.force([0.,0.,.1])
        self.assertAlmostEqual(f[4,2],.4,places=11)
        np.testing.assert_allclose(f[:4,2],[-.1]*4,atol=1e-12)
        np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-12)

    def test_center_other_side(self):
        _,f=self.force([0.,0.,-.1])
        np.testing.assert_allclose(f[:4,2],[.1]*4,atol=1e-12)
        self.assertAlmostEqual(f[4,2],-.4,places=11)

    def test_boundary_midpoint_two_half(self):
        _,f=self.force([0.,-1.,.1])
        np.testing.assert_allclose(f[:4,2],[-.2,-.2,0.,0.],atol=1e-11)

    def test_offset_continuity_and_torque(self):
        for x in (-.001, 0., .001, .65):
            pos,f=self.force([x,0.,.15])
            np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-10)
            torque=np.sum(np.cross(pos,f),axis=0)
            np.testing.assert_allclose(torque,0.,atol=1e-9)
            expected=[(1-x)/4,(1+x)/4,(1+x)/4,(1-x)/4]
            np.testing.assert_allclose(f[:4,2],-f[4,2]*np.array(expected),atol=1e-10)

    def test_exact_zero_distance_uses_incoming_velocity(self):
        _,f=self.force([0,0,0],velocity=[0,0,-1.])
        self.assertGreater(f[4,2],0)
        np.testing.assert_allclose(f[:4,2],[-.125]*4,atol=1e-11)

    def test_face_incidence_excluded(self):
        pos=self.quad.copy()
        tri,exc=triangulate_faces(pos,self.face)
        f=polygon_contact_forces(pos,np.zeros_like(pos),[.5],tri,exc,[1.],[0.],[0.],'NUMPY')
        np.testing.assert_array_equal(f,0.)

    def test_ngon_single_contact_for_internal_edge(self):
        pent=np.array([[-1,-1,0],[1,-1,0],[2,0,0],[1,1,0],[-1,1,0],[0.,0.,.1]],float)
        tri,exc=triangulate_faces(pent,[[0,1,2,3,4]])
        f=polygon_contact_forces(pent,np.zeros_like(pent),[0,0,0,0,0,.5],
                 tri,exc,[1.],[0.],[0.],'NUMPY')
        self.assertAlmostEqual(float(f[5,2]),.4,places=11)
        np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-11)

    def test_warped_quad_bilinear_center(self):
        warped=self.quad.copy()
        warped[2,2]=.4
        p=np.array([0.,0.,.25])
        pos,f=self.force(p,quad=warped,radius=.5)
        np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-9)
        self.assertTrue(np.all(np.isfinite(f)))
        # Forces act continuously over all four control vertices.
        self.assertTrue(np.all(np.linalg.norm(f[:4],axis=1)>1e-6))

    def test_setup_add_integration(self):
        from sverchok.utils.pulga_collision_domains import SvSelfPolygonCollisionForce
        ps=MockSystem(np.vstack([self.quad,[0.,0.,.1]]),
                      radii=[0.,0.,0.,0.,.5])
        force=SvSelfPolygonCollisionForce(self.face,[1.],[0.],[0.],'NUMPY')
        force.setup(ps)
        force.add(ps)
        np.testing.assert_allclose(ps.force_resultant[:4,2],[-.1]*4,atol=1e-12)

    @unittest.skipUnless(HAS_NUMBA,'Numba not available')
    def test_numba_quad_and_ngon_match_numpy(self):
        for p in [[0,0,.1],[.8,.35,.2],[0,0,0.],[0,0,-.1]]:
            _,a=self.force(p,'NUMPY')
            _,b=self.force(p,'NUMBA')
            np.testing.assert_allclose(a,b,atol=1e-10)
        rng=np.random.default_rng(13)
        for _ in range(20):
            quad=self.quad.copy()
            quad[:,2]=rng.uniform(-.3,.3,4)
            p=list(rng.uniform(-.9,.9,2))+[rng.uniform(-.3,.3)]
            _,a=self.force(p,'NUMPY',quad=quad)
            _,b=self.force(p,'NUMBA',quad=quad)
            np.testing.assert_allclose(a,b,atol=1e-10)



class TestNgonMeanValueCollision(unittest.TestCase):
    def regular_ngon(self, n, x=0., y=0., z=.1, engine='NUMPY'):
        angles=np.linspace(0.,2*np.pi,n,endpoint=False)
        polygon=np.column_stack((np.cos(angles),np.sin(angles),np.zeros(n)))
        pos=np.vstack((polygon,[x,y,z]))
        tri,exc=triangulate_faces(pos,[list(range(n))])
        force=polygon_contact_forces(pos,np.zeros_like(pos),
                    [0.]*n+[.5],tri,exc,[1.],[0.],[0.],engine)
        return pos,force

    def test_center_regular_5_and_6_equal_reaction(self):
        for n in (5,6,7,8):
            for engine in (['NUMPY','NUMBA'] if HAS_NUMBA else ['NUMPY']):
                pos,f=self.regular_ngon(n,engine=engine)
                np.testing.assert_allclose(f[:n,2],[-.4/n]*n,atol=1e-10)
                np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-10)
                np.testing.assert_allclose(np.sum(np.cross(pos,f),axis=0),0.,atol=1e-9)

    def test_offset_regular_5_6_torque_and_continuity(self):
        for n in (5,6):
            results=[]
            for x in (-0.001,0,0.001,.3):
                pos,f=self.regular_ngon(n,x=x,y=.12,z=.2)
                self.assertTrue(np.all(f[:n,2]<0))
                np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-10)
                np.testing.assert_allclose(np.sum(np.cross(pos,f),axis=0),0.,atol=1e-8)
                results.append(f)
            self.assertLess(np.max(np.abs(results[0]-results[2])),0.01)

    def test_warped_offset_ngon_all_vertices_receive_contact(self):
        # Regression: v3 refused MVC after a single corner moved out of plane
        # and silently redistributed contact to just three triangle vertices.
        for n in (5, 6, 7):
            angles=np.linspace(0., 2*np.pi, n, endpoint=False)
            polygon=np.column_stack((np.cos(angles), np.sin(angles), np.zeros(n)))
            polygon[2,2]=.12
            pos=np.vstack((polygon,[.52,.11,.2]))
            tris, exc=triangulate_faces(pos,[list(range(n))])
            f=polygon_contact_forces(pos,np.zeros_like(pos),[0.]*n+[.5],
                     tris,exc,[1.],[0.],[0.],'NUMPY')
            self.assertTrue(np.all(np.linalg.norm(f[:n],axis=1)>1.e-5),
                f'Warped {n}-gon lost force on corners: {f[:n]}')
            np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-11)
            np.testing.assert_allclose(np.cross(pos,f).sum(axis=0),0.,atol=1e-10)

    def test_small_warp_continuity_offcenter(self):
        for n in (5,6):
            theta=np.linspace(0.,2*np.pi,n,endpoint=False)
            polygon=np.column_stack((np.cos(theta),np.sin(theta),np.zeros(n)))
            forces=[]
            for warp in (0.0,1.e-4,1.e-3):
                p=polygon.copy(); p[2,2]=warp
                pos=np.vstack((p,[.52,.11,.2]))
                tri,exc=triangulate_faces(pos,[list(range(n))])
                f=polygon_contact_forces(pos,np.zeros_like(pos),[0]*n+[.5],
                        tri,exc,[1.],[0.],[0.],'NUMPY')
                forces.append(f)
            self.assertLess(np.max(np.abs(forces[0]-forces[1])),2.e-4)
            self.assertLess(np.max(np.abs(forces[1]-forces[2])),2.e-3)

    @unittest.skipUnless(HAS_NUMBA,'No Numba')
    def test_warped_offset_numba_matches_numpy(self):
        rng=np.random.default_rng(20261109)
        for n in (5,6,7):
            theta=np.linspace(0,2*np.pi,n,endpoint=False)
            for case in range(16):
                xy=np.column_stack((np.cos(theta),np.sin(theta)))
                z=rng.uniform(-.15,.15,n)
                p=np.column_stack((xy,z))
                # Keep the query in the center-right interior of the polygon
                pos=np.vstack((p,[.43,.17,.2]))
                tri,exc=triangulate_faces(pos,[list(range(n))])
                args=(pos,np.zeros_like(pos),[0]*n+[.5],tri,exc,[1.],[0.],[0.])
                a=polygon_contact_forces(*args,engine='NUMPY')
                b=polygon_contact_forces(*args,engine='NUMBA')
                np.testing.assert_allclose(a,b,atol=1e-10)
                np.testing.assert_allclose(a.sum(axis=0),0.,atol=1e-10)
                np.testing.assert_allclose(np.cross(pos,a).sum(axis=0),0.,atol=1e-10)

    def test_boundary_edge_half_reaction(self):
        for n in (5,6):
            angle=2*np.pi/n
            x=(1+np.cos(angle))*.5
            y=np.sin(angle)*.5
            _,f=self.regular_ngon(n,x=x,y=y,z=.1)
            np.testing.assert_allclose(f[:2,2],[-.2,-.2],atol=1e-9)
            np.testing.assert_allclose(f[2:n,2],0.,atol=1e-9)

    def test_backface_invert(self):
        for n in (5,6):
            _,f=self.regular_ngon(n,z=-.1)
            np.testing.assert_allclose(f[:n,2],[.4/n]*n,atol=1e-9)

    def test_concave_and_warped_remain_finite(self):
        vertices=np.array([[0,0,0],[3,0,0],[3,2,0],[1.5,.6,0],[0,2,0]],float)
        for warp in (0,.15):
            vv=vertices.copy();vv[2,2]=warp
            pos=np.vstack((vv,[1.4,.3,.1]))
            tri,exc=triangulate_faces(pos,[[0,1,2,3,4]])
            f=polygon_contact_forces(pos,np.zeros_like(pos),[0]*5+[.5],
                 tri,exc,[1.],[0.],[0.],'NUMPY')
            self.assertTrue(np.isfinite(f).all())
            np.testing.assert_allclose(f.sum(axis=0),0.,atol=1e-10)

    @unittest.skipUnless(HAS_NUMBA,'No Numba')
    def test_numba_matches_numpy_ngon(self):
        for n in (5,6,7):
            for x,y,z in ((0.,0.,.1),(.21,-.13,.2),(-.23,.17,-.1),(0,0,0)):
                _,a=self.regular_ngon(n,x,y,z,'NUMPY')
                _,b=self.regular_ngon(n,x,y,z,'NUMBA')
                np.testing.assert_allclose(a,b,atol=1e-10)

if __name__ == '__main__':
    unittest.main()
