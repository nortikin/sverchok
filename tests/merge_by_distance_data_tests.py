# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable Merge by Distance data-provenance regressions for Sverchok CI.

Discovered by run_tests.sh as ``tests/*_tests.py``. Needs NumPy only;
Blender is not imported. Additional SciPy/Numba engines are optional.
"""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'utils' / 'mesh'
if not CORE.exists():
    CORE = ROOT / 'files' / 'utils' / 'mesh'  # standalone package layout
if not CORE.exists():
    raise RuntimeError('sv_mesh_core not found')
sys.path.insert(0, str(CORE))

from sv_mesh_core.merge import merge_by_distance
from sv_mesh_core.data_nesting import map_mesh_tree_data


V = np.array([[0,0,0],[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,0]],np.float32)
F = [[0,2,3,4],[1,2,3,4]]
E = [[0,2],[1,2],[2,3],[0,0]]


def weld(poly=F, edges=E, vdata=tuple('abcdef'), edata=('a','b','c','d'),
         distance=.001, **kwargs):
    return merge_by_distance(V,poly,distance,edges=edges,
                             vert_data=vdata,edge_data=edata,
                             output_mesh_data=True,backend='GRID_PY',
                             **kwargs)


class MeshDataTests(unittest.TestCase):
    def test_vertex_groups_are_complete_and_sorted(self):
        out=weld()
        self.assertEqual(out[8],[[0,1,5],[2],[3],[4]])
        self.assertEqual(out[6],['a','c','d','e'])

    def test_edge_groups_and_attribute_from_first_source(self):
        out=weld()
        self.assertEqual(out[9],[[0,1],[2],[],[]])
        self.assertEqual(out[7],['a','c',None,None])
        self.assertEqual(len(out[1]),len(out[9]))

    def test_face_groups_and_first_face_attribute(self):
        out=weld(face_data=['red','blue'])
        self.assertEqual(out[2],[[0,1,2,3]])
        self.assertEqual(out[3],['red'])
        self.assertEqual(out[10],[[0,1]])

    def test_generated_perimeter_has_no_fake_edge_origin(self):
        out=weld(edges=[])
        self.assertEqual(out[9],[[],[],[],[]])
        self.assertEqual(out[7],[None,None,None,None])

    def test_legacy_polyedge_edge_mode_has_origin_indices(self):
        out=weld(poly=E,edges=[],edata=('a','b','c','d'),edge_data_from_poly=True)
        self.assertEqual(out[9],[[0,1],[2]])
        self.assertEqual(out[7],['a','c'])
        self.assertEqual(out[10],[])

    def test_multiple_explicit_edges_with_single_face(self):
        out=weld(poly=[[0,2,3,4]],edges=E)
        self.assertEqual(out[9][0],[0,1])
        self.assertEqual(out[10],[[0]])

    def test_output_numpy_does_not_change_origins(self):
        a=weld(output_numpy=False)
        b=weld(output_numpy=True)
        np.testing.assert_array_equal(a[0],b[0])
        self.assertEqual(a[8:11],b[8:11])
        self.assertIsInstance(b[0],np.ndarray)
        self.assertEqual(len(b[1]),len(b[9]))

    def test_mask_excludes_vertex_from_merge_group(self):
        out=weld(mask=[1,0,1,1,1,1])
        self.assertEqual(out[8][0],[0,5])
        self.assertEqual(out[8][1],[1])

    def test_origin_data_handles_missing_values(self):
        out=weld(vdata=['only-first'],edata=['only-first'])
        self.assertEqual(out[6][0],'only-first')
        self.assertEqual(out[6][1:],[None,None,None])
        self.assertEqual(out[7][0],'only-first')
        self.assertEqual(out[7][1:], [None,None,None])

    def test_pinched_and_collapsed_faces(self):
        # Merges vertex 1 onto 0; polygon becomes pinched or collapsed.
        result = merge_by_distance(V,[[0,2,3,0,4],[1,2,3,4]],.001,
            output_mesh_data=True,backend='GRID_PY')
        self.assertEqual(len(result[2]),len(result[10]))
        self.assertEqual(len(result[1]),len(result[9]))
        self.assertTrue(all(all(0<=i<len(F) for i in group) for group in result[10]))

    def test_no_sources_return_empty_origin_groups(self):
        out=weld(poly=[],edges=[])
        self.assertEqual(out[1],[])
        self.assertEqual(out[2],[])
        self.assertEqual(out[9],[])
        self.assertEqual(out[10],[])
        self.assertEqual(len(out[8]),len(out[0]))

    def test_old_fast_path_unmodified_without_data(self):
        plain=merge_by_distance(V,F,.001,backend='GRID_PY')
        kw=merge_by_distance(V,F,.001,backend='GRID_PY',edges=[],output_mesh_data=False)
        self.assertEqual(len(plain),6)
        self.assertEqual(len(kw),6)
        for a,b in zip(plain,kw):
            self.assertEqual(a,b)

    def test_all_origin_indices_resolve_into_input_domain(self):
        out=weld()
        self.assertEqual(sorted(x for g in out[8] for x in g),list(range(len(V))))
        self.assertTrue(all(0<=x<len(E) for g in out[9] for x in g))
        self.assertTrue(all(0<=x<len(F) for g in out[10] for x in g))

    def test_grid_implementations_agree_when_available(self):
        base=weld()
        for backend in ('AUTO','GRID_SCIPY','GRID_PY'):
            with self.subTest(backend=backend):
                other=merge_by_distance(V,F,.001,edges=E,
                    vert_data=list('abcdef'),edge_data=('a','b','c','d'),
                    output_mesh_data=True,backend=backend)
                self.assertEqual(other,base)

    def test_reject_out_of_range_explicit_edges(self):
        with self.assertRaises(IndexError):
            weld(edges=[[9,10]])
        with self.assertRaises(IndexError):
            weld(edges=[[-8,3]])

    def test_reject_non_pair_explicit_edges(self):
        with self.assertRaises(ValueError):
            weld(edges=[[0,1,2]])


class MeshDataNestingTests(unittest.TestCase):
    @staticmethod
    def operation(v,p,f,m,d,e,vd,ed):
        result=merge_by_distance(v,p,d,face_data=f,mask=m,
            edges=e,vert_data=vd,edge_data=ed,
            output_mesh_data=True,backend='GRID_PY')
        return result

    def test_two_mesh_groups_and_metadata(self):
        out=map_mesh_tree_data([[V,V],[V]],F,['red','blue'],[],.001,
             E,list('abcdef'),list('abcd'),self.operation)
        self.assertEqual([len(g) for g in out[0]],[2,1])
        self.assertEqual(out[8][0][0],[[0,1,5],[2],[3],[4]])

    def test_short_broadcasts_unlinked_default_attributes(self):
        out=map_mesh_tree_data([V,V],[],[],[],.001,[],[],[],
            self.operation,matching='SHORT')
        self.assertEqual(len(out[0]),2)
        self.assertEqual(len(out[8]),2)

    def test_edge_lists_match_per_mesh(self):
        out=map_mesh_tree_data([V,V],[],[],[],.001,
            [E,[[0,2]]],['a','b','c','d','e','f'],
            [['a','b','c','d'],['x']],self.operation)
        self.assertEqual(len(out[0]),2)
        self.assertEqual(out[9][0],[[0,1],[2]])
        self.assertEqual(out[9][1],[[0]])
        self.assertEqual(out[7][1],['x'])

    def test_face_data_payload_vectors(self):
        colors=[[1.,0.,0.],[0.,1.,0.]]
        out=map_mesh_tree_data(V,F,colors,[],.001,E,[],[],self.operation)
        self.assertEqual(out[3],[[1.,0.,0.]])
        self.assertEqual(out[10],[[0,1]])


if __name__=='__main__':
    unittest.main(verbosity=2)
