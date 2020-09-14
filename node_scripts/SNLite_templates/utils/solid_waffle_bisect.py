"""
in solid_in So
in matrix_a_in m
in matrix_b_in m
in zs_a_in s
in zs_b_in s
in split_in S
out solid_a_out So
out solid_b_out So
out matrices_a_out m
out matrices_b_out m
"""

from collections import defaultdict
import numpy as np

from mathutils import Vector

from sverchok.data_structure import zip_long_repeat, ensure_nesting_level
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.freecad import SvFreeCadCurve, SvFreeCadNurbsCurve, curve_to_freecad_nurbs
from sverchok.utils.surface.core import SvSurface
from sverchok.utils.surface.freecad import SvSolidFaceSurface, is_solid_face_surface, surface_to_freecad

from sverchok.dependencies import FreeCAD

if FreeCAD is None:
    raise Exception("FreeCAD libraries are not available")

import Part
from FreeCAD import Base

from sverchok.utils.solid import SvSolidTopology

class SvGeneralFuse(object):
    def __init__(self, solids):
        self.solids = solids
        self.result, self.map = solids[0].generalFuse(solids[1:])
        self._per_source = defaultdict(set)
        self._per_source_idx = defaultdict(set)
        for i, (source, items) in enumerate(zip(solids, self.map)):
            items = set(SvSolidTopology.Item(i) for i in items)
            key = SvSolidTopology.Item(source)
            print(f":: [{key}] := {items}")
            self._per_source[key] = items
            self._per_source_idx[i] = items
    
    def get_by_source(self, solid):
        return self._per_source[SvSolidTopology.Item(solid)]
    
    def get_by_source_idx(self, idx):
        return self._per_source_idx[idx]
    
    def get_intersection(self, solid_a, solid_b):
        result_a = self._per_source[SvSolidTopology.Item(solid_a)]
        result_b = self._per_source[SvSolidTopology.Item(solid_b)]
        print(f"A: {solid_a.hashCode()} => {result_a}")
        print(f"B: {solid_b.hashCode()} => {result_b}")
        return result_a.intersection(result_b)
    
    def get_intersection_by_idx(self, idx_a, idx_b):
        result_a = self._per_source_idx[idx_a]
        result_b = self._per_source_idx[idx_b]
        print(f"A: {idx_a} => {result_a}")
        print(f"B: {idx_b} => {result_b}")
        return result_a.intersection(result_b)
    
    def get_difference(self, solid_a, solid_b):
        result_a = self._per_source[SvSolidTopology.Item(solid_a)]
        result_b = self._per_source[SvSolidTopology.Item(solid_b)]
        return result_a.difference(result_b)
    
    def get_clean_part(self, solid):
        item = SvSolidTopology.Item(solid)
        result = self._per_source[item].copy()
        for source, results in self._per_source.items():
            if source != item:
                result.difference_update(results)
        return result
    
    def get_clean_part_by_idx(self, idx):
        result = self._per_source_idx[idx].copy()
        print(f"get_clean[{idx}] = {result}")
        for source_idx, results in self._per_source_idx.items():
            if source_idx != idx:
                print(f"get_clean[{idx}] -= {results}")
                result.difference_update(results)
        return result
    
def matrix_z(matrix):
    location = matrix.translation
    z = matrix @ Vector((0,0,1)) - location
    return z

def matrix_offset(matrix, offset):
    z = matrix_z(matrix).normalized()
    m = matrix.copy()
    m.translation = matrix.translation + offset * z
    return m

def bisect_wire(solid, matrix):
    location = matrix.translation
    norm = (matrix @ Vector((0,0,1))) - location
    dist = norm.dot(location)
    wires = solid.slice(Base.Vector(norm), dist)
    #solid.slices(Base.Vector(norm), [dist])
    return wires

def bisect_face(solid, matrix):
    wires = bisect_wire(solid, matrix)
    return Part.Face(wires)

def bisect_thick(solid, matrix, offset):
    z = matrix_z(matrix)
    face1 = bisect_face(solid, matrix)
    matrix2 = matrix_offset(matrix, offset)
    face2 = bisect_face(solid, matrix2)
    res, map = solid.generalFuse([face1, face2])
    solids = res.Solids
    if len(solids) < 3:
        print("Thick:", solids)
        return None
    
    key = lambda s: s.CenterOfMass.dot(Base.Vector(z))
    solids = list(sorted(solids, key=key))
    return solids[1]

def do_intersect(solid, matrix1, matrix2, offset):
    layer1 = bisect_thick(solid, matrix1, offset)
    layer2 = bisect_thick(solid, matrix2, offset)
    return layer1.common(layer2)

class IntersectResult(object):
    def __init__(self):
        self.by_pair = dict()
        self.by_a = defaultdict(list)
        self.by_b = defaultdict(list)
        self.clean_a = self.clean_b = None

def do_intersect_pairs(solid, matrix_a, matrix_b, zs_a, zs_b, thickness):
    matrices_a = [matrix_offset(matrix_a, z) for z in zs_a]
    matrices_b = [matrix_offset(matrix_b, z) for z in zs_b]
    solids_a = [bisect_thick(solid, matrix, thickness) for matrix in matrices_a]
    solids_b = [bisect_thick(solid, matrix, thickness) for matrix in matrices_b]
    solids_a = list(filter(lambda s: s is not None, solids_a))
    solids_b = list(filter(lambda s: s is not None, solids_b))
    all_solids = solids_a + solids_b
    n_a = len(solids_a)
    fused = SvGeneralFuse(all_solids)
    
    result_a = []
    for i, solid in enumerate(solids_a):
        parts = fused.get_clean_part_by_idx(i)
        print(f"A: i#{i} => {parts}")
        #for part in parts:
        #    part.item.fix(0.01, 0.01, 0.01)
        result_a.append(parts)
    
    result_b = []
    for j, solid in enumerate(solids_b):
        dj = j + n_a
        parts = fused.get_clean_part_by_idx(dj)
        print(f"B: Dj#{dj} => {parts}")
        #for part in parts:
        #    part.item.fix(0.01, 0.01, 0.01)
        result_b.append(parts)
    
    #print(f"Clean A: {result_a}")
    #print(f"Clean B: {result_b}")
    
    intersections = IntersectResult()
    for i, solid_a in enumerate(solids_a):
        for j, solid_b in enumerate(solids_b):
            dj = j + n_a
            intersection = fused.get_intersection_by_idx(i, dj)
            if not intersection:
                print(f"I {i} x {j}: {solid_a} x {solid_b}: no intersection")
                continue
            if len(intersection) > 1:
                raise Exception("Intersection gives more than one part")
            body = list(intersection)[0].item
            #body.fix(0.01, 0.01, 0.01)
            intersections.by_pair[(i,j)] = body
            intersections.by_a[i].append(body)
            intersections.by_b[j].append(body)
    #print(f"By_a: {intersections.by_a}")
    intersections.n_a = n_a
    intersections.solids_a = solids_a
    intersections.solids_b = solids_b
    intersections.clean_a = result_a
    intersections.clean_b = result_b
    intersections.matrices_a = matrices_a
    intersections.matrices_b = matrices_b
    return intersections

def do_split(body, split, select):
    res, map = body.generalFuse([split.face])
    mid_parts = map[0]
    #print("M", mid_parts[0].Shells)
    if len(mid_parts) != 2:
        raise Exception(f"The surface does not cut the intersection of solids in 2 parts; result is {mid_parts}")
    mid_1, mid_2 = mid_parts
    c1, c2 = mid_1.CenterOfMass, mid_2.CenterOfMass
    select = Base.Vector(*select)
    d1, d2 = select.dot(c1), select.dot(c2)
    if d1 > d2:
        mid_2, mid_1 = mid_1, mid_2
    return mid_1, mid_2

def do_waffel(solid, matrix_a, matrix_b, zs_a, zs_b, thickness, split, select):
    intersections = do_intersect_pairs(solid, matrix_a, matrix_b, zs_a, zs_b, thickness)
    split_parts_a = defaultdict(list)
    split_parts_b = defaultdict(list)
    other_parts_a = defaultdict(list)
    other_parts_b = defaultdict(list)
    n_a = intersections.n_a
    
    for i in range(len(zs_a)):
        for j in range(len(zs_b)):
            intersection = intersections.by_pair.get((i,j), None)
            if intersection is None:
                continue
            intersection.fix(0.01, 0.01, 0.01)
            mid_a, mid_b = do_split(intersection, split, select)
            split_parts_a[i].append(mid_a)
            split_parts_b[j].append(mid_b)
            other_parts_a[i].append(mid_b)
            other_parts_b[j].append(mid_a)
    
    result_a = []
    for i, solid_a in enumerate(intersections.solids_a):
        cut_parts = other_parts_a[i]
        print(f"A[{i}]/parts: {solid_a} - {cut_parts}")
        if not cut_parts:
            print(f"A[{i}]: no parts")
        else:
            for part in cut_parts:
                part.fix(0.01, 0.01, 0.01)
            body = solid_a.cut(cut_parts)
            result_a.append(body)
            
    result_b = []
    for j, solid_b in enumerate(intersections.solids_b):
        cut_parts = other_parts_b[j]
        print(f"B[{j}]/parts: {solid_b} - {cut_parts}")
        if not cut_parts:
            print(f"B[{j}]: no parts")
        else:
            for part in cut_parts:
                part.fix(0.01, 0.01, 0.01)
            body = solid_b.cut(cut_parts)
            result_b.append(body)
    
    return result_a, result_b, intersections.matrices_a, intersections.matrices_b


solid_in = ensure_nesting_level(solid_in, 1, data_types=(Part.Shape,))
split_in = ensure_nesting_level(split_in, 1, data_types=(SvSurface,))
zs_a_in = ensure_nesting_level(zs_a_in, 2)
zs_b_in = ensure_nesting_level(zs_b_in, 2)

solid_a_out = []
solid_b_out = []
matrices_a_out = []
matrices_b_out = []

for solid, matrix_a, matrix_b, zs_a, zs_b, split in zip_long_repeat(solid_in, matrix_a_in, matrix_b_in, zs_a_in, zs_b_in, split_in):
    if not is_solid_face_surface(split):
        split = surface_to_freecad(split, make_face=True)
    select = matrix_z(matrix_a).cross(matrix_z(matrix_b))
    select = tuple(select)
    thickness = 0.1
    result_a, result_b, matrices_a, matrices_b = do_waffel(solid, matrix_a, matrix_b, zs_a, zs_b, thickness, split, select)    
    solid_a_out.append(result_a)
    solid_b_out.append(result_b)
    matrices_a_out.extend(matrices_a)
    matrices_b_out.extend(matrices_b)
