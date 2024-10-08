# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

import bpy, math, bmesh
from mathutils import Vector, Matrix
from collections import namedtuple

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import merge_mesh
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode
from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat, ensure_nesting_level, flatten_data

## internal.py #########################################
Plane = namedtuple('Plane', 'normal distance')

def normalOfPolygon(vertices):
    normal = Vector((0.0, 0.0, 0.0))
    for index, current in enumerate(vertices):
        prev = vertices[index-1]
        normal += (prev-vertices[0]).cross(current-vertices[0])
    return normal

def areaOfPolygon(vertices):
    return normalOfPolygon(vertices).length*0.5

def linePlaneIntersection(origin, dir, plane):
    # return mathutils.geometry.intersect_line_plane(origin, origin+dir, plane.normal*plane.distance, plane.normal)
    det = dir@plane.normal
    return float('nan') if det == 0 else (plane.distance-origin@plane.normal)/det

def planePlaneIntersection(planeA, planeB, tollerance=0.0001):
    # return mathutils.geometry.intersect_plane_plane(planeA.normal*planeA.distance, planeA.normal, planeB.normal*planeB.distance, planeB.normal)
    if 1.0-abs(planeA.normal@planeB.normal) < tollerance:
        return ('Parallel' if abs(planeA.distance-planeB.distance) > tollerance else 'Coplanar', None, None)
    dir = planeA.normal.cross(planeB.normal).normalized()
    ray_origin = planeA.normal*planeA.distance
    ray_dir = planeA.normal.cross(dir)
    origin = ray_origin+ray_dir*linePlaneIntersection(ray_origin, ray_dir, planeB)
    return ('Intersecting', origin, dir)

def linePointDistance(begin, dir, point):
    return (point-begin).cross(dir.normalized()).length

def nearestPointOfLines(originA, dirA, originB, dirB, param_tollerance=0.0, dist_tollerance=0.001):
    # https://en.wikipedia.org/wiki/Skew_lines#Nearest_Points
    normal = dirA.cross(dirB)
    normalA = dirA.cross(normal)
    normalB = dirB.cross(normal)
    divisorA = dirA@normalB
    divisorB = dirB@normalA
    originAB = originB-originA
    if abs(divisorA) <= param_tollerance or abs(divisorB) <= param_tollerance:
        if dirA@dirA == 0.0 or dirB@dirB == 0.0 or linePointDistance(originA, dirA, originB) >= dist_tollerance:
            return ('Parallel', float('nan'), float('nan'))
        paramA =  originAB@dirA/(dirA@dirA)
        paramB = -originAB@dirB/(dirB@dirB)
        return ('Coaxial', paramA, paramB)
    else:
        paramA =  originAB@normalB/divisorA
        paramB = -originAB@normalA/divisorB
        nearestPointA = originA+dirA*paramA
        nearestPointB = originB+dirB*paramB
        return ('Crossing' if (nearestPointA-nearestPointB).length <= dist_tollerance else 'Skew', paramA, paramB)

def lineSegmentLineSegmentIntersection(lineAVertexA, lineAVertexB, lineBVertexA, lineBVertexB):
    dirA = lineAVertexB-lineAVertexA
    dirB = lineBVertexB-lineBVertexA
    type, paramA, paramB = nearestPointOfLines(lineAVertexA, dirA, lineBVertexA, dirB)
    if type == 'Parallel' or type == 'Skew':
        return (float('nan'), float('nan'))
    if type == 'Coaxial':
        if paramA < 0.0 and paramB < 0.0: # Facing away from one another
            return (float('nan'), float('nan'))
        if paramA > 0.0 and paramB > 0.0: # Facing towards each other
            if paramA > 1.0 and (lineBVertexB-lineAVertexA)@dirA > 1.0: # End of B is not in A
                return (float('nan'), float('nan'))
        elif paramA > 1.0 or paramB > 1.0: # One is chasing the other but out of reach
            return (float('nan'), float('nan'))
        paramA = max(0.0, (lineBVertexB-lineAVertexA)@dirA/(dirA@dirA))
        paramB = max(0.0, (lineAVertexB-lineBVertexA)@dirB/(dirB@dirB))
        return (paramA, paramB)
    if paramA < 0.0 or paramA > 1.0 or paramB < 0.0 or paramB > 1.0: # Intersection is outside the line segments
        return (float('nan'), float('nan'))
    return (paramA, paramB)

def rayLineSegmentIntersection(originA, dirA, lineVertexA, lineVertexB):
    dirB = lineVertexB-lineVertexA
    type, paramA, paramB = nearestPointOfLines(originA, dirA, lineVertexA, dirB)
    if type == 'Parallel' or type == 'Skew':
        return float('nan')
    if type == 'Coaxial':
        if paramA > 0.0:
            return paramA if (paramB < 0.0) else max(0.0, (lineVertexB-originA)@dirA/(dirA@dirA))
        else:
            return float('nan') if (paramB < 0.0 or paramB > 1.0) else 0.0
    if paramA < 0.0 or paramB < 0.0 or paramB > 1.0: # Intersection is behind the rays origin or outside of the line segment
        return float('nan')
    return paramA

def rayRayIntersection(originA, dirA, originB, dirB):
    type, paramA, paramB = nearestPointOfLines(originA, dirA, originB, dirB)
    if type == 'Parallel' or type == 'Skew':
        return (float('nan'), float('nan'))
    if type == 'Coaxial':
        if paramA < 0.0 and paramB < 0.0: # Facing away from one another
            return (float('nan'), float('nan'))
        if paramA > 0.0 and paramB > 0.0: # Facing towards each other
            paramSum = paramA+paramB
            paramA = paramA*paramA/paramSum
            paramB = paramB*paramB/paramSum
            return (paramA, paramB)
        return (paramA, 0.0) if paramA > 0.0 else (0.0, paramB) # One is chasing the other
    if paramA < 0.0 or paramB < 0.0: # Intersection is behind the rays origins
        return (float('nan'), float('nan'))
    return (paramA, paramB)

def insort_right(sorted_list, keyfunc, entry, lo=0, hi=None):
    if hi == None:
        hi = len(sorted_list)
    while lo < hi:
        mid = (lo+hi)//2
        if keyfunc(entry) < keyfunc(sorted_list[mid]):
            hi = mid
        else:
            lo = mid+1
    sorted_list.insert(lo, entry)



def selectedPolygons(src_obj):
    polygons = []
    in_edit_mode = (src_obj.mode == 'EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if src_obj.type == 'CURVE':
        if in_edit_mode:
            splines = []
            for spline in bpy.context.object.data.splines:
                selected = True
                if spline.type == 'POLY':
                    for index, point in enumerate(spline.points):
                        if point.select == False:
                            selected = False
                            break
                    if selected:
                        splines.append(spline)
        else:
            splines = src_obj.data.splines
        for spline in splines:
            polygons.append(list(point.co.xyz for point in spline.points))
    else:
        loops = []
        for face in src_obj.data.polygons:
            if in_edit_mode and not face.select:
                continue
            polygons.append(list(src_obj.data.vertices[vertex_index].co for vertex_index in face.vertices))
    return polygons

def addObject(type, name):
    if type == 'CURVE':
        data = bpy.data.curves.new(name=name, type='CURVE')
        data.dimensions = '3D'
    elif type == 'MESH':
        data = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name, data)
    obj.location = bpy.context.scene.cursor.location
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj

def addPolygonSpline(obj, cyclic, vertices, weights=None, select=False):
    spline = obj.data.splines.new(type='POLY')
    spline.use_cyclic_u = cyclic
    spline.points.add(len(vertices)-1)
    for index, point in enumerate(spline.points):
        point.co.xyz = vertices[index]
        point.select = select
        if weights:
            point.weight_softbody = weights[index]
    return spline



class SlabIntersection:
    __slots__ = ['prev_slab', 'next_slab', 'origin', 'dir', 'begin_param', 'end_param']
    def __init__(self, prev_slab, next_slab, origin, dir, begin_param, end_param):
        self.prev_slab = prev_slab
        self.next_slab = next_slab
        self.origin = origin
        self.dir = dir
        self.begin_param = begin_param
        self.end_param = end_param

    def reverse(self):
        self.dir *= -1.0
        [self.begin_param, self.end_param] = [-self.end_param, -self.begin_param]

    def otherSlab(self, slab):
        return self.prev_slab if slab == self.next_slab else self.next_slab

class Slab:
    __slots__ = ['edge', 'slope', 'plane', 'prev_slab', 'next_slab', 'prev_polygon_vertex', 'next_polygon_vertex', 'prev_lightcycles', 'next_lightcycles', 'vertices', 'slab_intersections']
    def __init__(self, polygon_normal, prev_polygon_vertex, next_polygon_vertex):
        self.edge = (next_polygon_vertex-prev_polygon_vertex).normalized()
        edge_orthogonal = self.edge.cross(polygon_normal).normalized()
        normal = (polygon_normal+edge_orthogonal).normalized()
        self.slope = (polygon_normal-edge_orthogonal).normalized()
        self.plane = Plane(normal=normal, distance=next_polygon_vertex@normal)
        self.prev_lightcycles = []
        self.next_lightcycles = []
        self.prev_polygon_vertex = prev_polygon_vertex
        self.next_polygon_vertex = next_polygon_vertex
        self.vertices = [self.prev_polygon_vertex, self.next_polygon_vertex]
        self.slab_intersections = []

    def isOuterOfCollision(self, in_dir, out_dir, polygon_normal):
        normal = in_dir.cross(polygon_normal)
        return (normal@self.plane.normal > 0.0) == (normal@out_dir > 0.0)

    def calculateVerticesFromLightcycles(self):
        def handleSide(lightcycles, prepend):
            for lightcycle in lightcycles:
                if lightcycle.slab_intersection.origin is None or lightcycle.slab_intersection.dir is None or lightcycle.slab_intersection.end_param is None:
                    pass
                else:
                    vertex = lightcycle.slab_intersection.origin+lightcycle.slab_intersection.dir*lightcycle.slab_intersection.end_param
                    if prepend:
                        self.vertices.insert(0, vertex)
                    else:
                        self.vertices.append(vertex)
        handleSide(self.prev_lightcycles, True)
        handleSide(self.next_lightcycles, False)

    def rayBoundaryIntersection(self, origin, dir, tollerance=0.0001):
        intersections = []
        for i in range(0, len(self.vertices)+1):
            is_last = (i == 0 or i == len(self.vertices))
            type, paramA, paramB = nearestPointOfLines(origin, dir, self.vertices[0 if i == 0 else i-1], self.slope if is_last else self.vertices[i]-self.vertices[i-1])
            if type == 'Crossing':
                if paramB > -tollerance and (is_last or paramB < 1.0+tollerance):
                    intersections.append((i, paramA))
            elif type == 'Coaxial':
                assert(not is_last)
                intersections.append((i-1, paramA))
                intersections.append((i, (self.vertices[i]-origin)@dir/(dir@dir)))
        intersections.sort(key=lambda entry: entry[1])
        i = 1
        while i < len(intersections):
            if intersections[i][1]-intersections[i-1][1] < tollerance:
                del intersections[i]
            else:
                i += 1
        return intersections

    def calculateSlabIntersection(self, other_slab, is_first, tollerance=0.0001):
        lightcycles = self.next_lightcycles if is_first else self.prev_lightcycles
        if len(lightcycles) > 0 and (lightcycles[0].slab_intersection.prev_slab == other_slab or lightcycles[0].slab_intersection.next_slab == other_slab):
            return
        type, origin, dir = planePlaneIntersection(self.plane, other_slab.plane)
        if type != 'Intersecting':
            if self.prev_slab == other_slab or self.next_slab == other_slab:
                slab_intersection = SlabIntersection(self, other_slab, self.prev_polygon_vertex if self.prev_slab == other_slab else self.next_polygon_vertex, self.slope, 0.0, float('inf'))
                self.slab_intersections.append(slab_intersection)
                other_slab.slab_intersections.append(slab_intersection)
            return
        intersectionsA = self.rayBoundaryIntersection(origin, dir)
        intersectionsB = other_slab.rayBoundaryIntersection(origin, dir)
        if len(intersectionsA) == 2 and len(intersectionsB) == 2:
            begin_param = max(intersectionsA[0][1], intersectionsB[0][1])
            end_param = min(intersectionsA[1][1], intersectionsB[1][1])
            if begin_param < end_param and end_param-begin_param >= tollerance:
                slab_intersection = SlabIntersection(self, other_slab, origin+begin_param*dir, dir, 0.0, end_param-begin_param)
                self.slab_intersections.append(slab_intersection)
                other_slab.slab_intersections.append(slab_intersection)

    def calculateVerticesFromIntersections(self, tollerance=0.001):
        pivot = self.prev_polygon_vertex
        current_line = None
        for candidate in self.slab_intersections:
            if candidate.prev_slab == self.prev_slab or candidate.next_slab == self.prev_slab:
                current_line = candidate
                break
        if current_line == None:
            print('ERROR: calculateVerticesFromIntersections() could not find the first current_line')
            return
        if abs((current_line.origin+current_line.dir*current_line.begin_param-pivot)@current_line.dir) > abs((current_line.origin+current_line.dir*current_line.end_param-pivot)@current_line.dir):
            current_line.reverse()
        self.vertices = [self.prev_polygon_vertex, self.next_polygon_vertex]
        while current_line.prev_slab != self.next_slab and current_line.next_slab != self.next_slab:
            self.slab_intersections.remove(current_line)
            pivot_param = (pivot-current_line.origin)@current_line.dir
            best_candidate = None
            best_param = float('nan')
            current_other_slab = current_line.otherSlab(self)
            lightcycles = []
            if len(current_other_slab.prev_lightcycles) > 0:
                lightcycles.append(current_other_slab.prev_lightcycles[-1])
            if len(current_other_slab.next_lightcycles) > 0:
                lightcycles.append(current_other_slab.next_lightcycles[-1])
            for lightcycle in lightcycles:
                if lightcycle.slab_intersection.origin is None or lightcycle.slab_intersection.dir is None:
                    pass
                else:
                    param = linePlaneIntersection(lightcycle.slab_intersection.origin, lightcycle.slab_intersection.dir, self.plane)
                    if lightcycle.slab_intersection.begin_param-tollerance <= param and param <= lightcycle.slab_intersection.end_param+tollerance:
                        candidate_other_slab = lightcycle.slab_intersection.otherSlab(current_other_slab)
                        position = lightcycle.slab_intersection.origin+lightcycle.slab_intersection.dir*param
                        param = (position-pivot)@current_line.dir
                        if candidate_other_slab != self and param > 0.0:
                            for candidate in self.slab_intersections:
                                if candidate.otherSlab(self) == candidate_other_slab:
                                    best_candidate = candidate
                                    best_param = current_line.end_param
                                    if abs((best_candidate.origin+best_candidate.dir*best_candidate.begin_param-pivot)@best_candidate.dir) > abs((best_candidate.origin+best_candidate.dir*best_candidate.end_param-pivot)@best_candidate.dir):
                                        best_candidate.reverse()
                                    break
            for candidate in self.slab_intersections:
                if candidate == best_candidate:
                    continue
                type, paramA, paramB = nearestPointOfLines(current_line.origin, current_line.dir, candidate.origin, candidate.dir)
                if (type == 'Crossing' or type == 'Coaxial') and pivot_param-tollerance <= paramA and \
                   current_line.begin_param-tollerance <= paramA and paramA <= current_line.end_param+tollerance and \
                   candidate.begin_param-tollerance <= paramB and paramB <= candidate.end_param+tollerance and \
                   (best_candidate == None or best_param > paramA):
                    best_candidate = candidate
                    best_param = paramA
                    normal = self.plane.normal.cross(current_line.dir)
                    if (best_candidate.origin+best_candidate.dir*best_candidate.begin_param-pivot)@normal < (best_candidate.origin+best_candidate.dir*best_candidate.end_param-pivot)@normal:
                        best_candidate.reverse()
            if best_candidate == None:
                print('ERROR: calculateVerticesFromIntersections() could not find the next current_line')
                return
            pivot = current_line.origin+current_line.dir*best_param
            current_line = best_candidate
            self.vertices.insert(0, pivot)
        self.slab_intersections = None

class Collision:
    __slots__ = ['winner_time', 'looser_time', 'winner', 'loosers', 'children']
    def __init__(self, winner_time, looser_time, winner, loosers):
        self.winner_time = winner_time
        self.looser_time = looser_time
        self.winner = winner
        self.loosers = loosers
        self.children = []

    def checkCandidate(self):
        if self.winner != None and self.winner.collision != None and self.winner.collision.looser_time < self.winner_time:
            return False
        for looser in self.loosers:
            if looser.collision != None:
                return False
        return True

    def collide(self, lightcycles, collision_candidates, polygon_vertices, polygon_normal, tollerance=0.0001):
        for looser in self.loosers:
            looser.collision = self
        if len(self.loosers) == 2:
            assert(self.loosers[0].ground_normal@self.loosers[1].ground_normal > 0.0)
            position = self.loosers[0].ground_origin+self.loosers[0].ground_velocity*self.looser_time
            dirA = self.loosers[0].ground_velocity.normalized()
            dirB = self.loosers[1].ground_velocity.normalized()
            ground_dir = dirA+dirB
            if ground_dir.length > tollerance:
                index = 1 if self.loosers[0].slab_intersection.prev_slab.isOuterOfCollision(dirA, ground_dir, polygon_normal) else 0
                if dirA.cross(dirB)@polygon_normal > 0.0:
                    index = 1-index
                self.children = [Lightcycle(
                    lightcycles, collision_candidates, polygon_vertices, polygon_normal, False,
                    self.looser_time, self.loosers[index].slab_intersection.prev_slab, self.loosers[1-index].slab_intersection.next_slab,
                    position, ground_dir.normalized(), self.loosers[0].ground_normal
                )]
            else:
                ground_dir = dirA.cross(self.loosers[0].ground_normal)
                index = 1 if self.loosers[0].slab_intersection.prev_slab.isOuterOfCollision(dirA, ground_dir, polygon_normal) else 0
                self.children = [Lightcycle(
                    lightcycles, collision_candidates, polygon_vertices, polygon_normal, False,
                    self.looser_time, self.loosers[index].slab_intersection.prev_slab, self.loosers[1-index].slab_intersection.next_slab,
                    position, ground_dir, self.loosers[0].ground_normal
                ), Lightcycle(
                    lightcycles, collision_candidates, polygon_vertices, polygon_normal, True,
                    self.looser_time, self.loosers[1-index].slab_intersection.prev_slab, self.loosers[index].slab_intersection.next_slab,
                    position, -ground_dir, self.loosers[0].ground_normal
                )]

class Lightcycle:
    __slots__ = ['start_time', 'ground_origin', 'ground_velocity', 'ground_normal', 'inwards', 'collision', 'slab_intersection']
    def __init__(self, lightcycles, collision_candidates, polygon_vertices, polygon_normal, immunity, start_time, prev_slab, next_slab, position, ground_dir, ground_normal):
        exterior_angle = math.pi-math.acos(max(-1.0, min(prev_slab.edge@-next_slab.edge, 1.0)))
        # pitch_angle = math.atan(math.cos(exterior_angle*0.5))
        ground_speed = 1.0/math.cos(exterior_angle*0.5)
        self.start_time = start_time
        self.ground_origin = position
        self.ground_velocity = ground_dir*ground_speed
        self.ground_normal = ground_normal
        self.inwards = (self.ground_normal@polygon_normal > 0.0)
        self.collision = None
        self.slab_intersection = SlabIntersection(prev_slab, next_slab, None, None, 0.0, 0.0)
        if self.inwards:
            prev_slab.next_lightcycles.append(self)
            next_slab.prev_lightcycles.append(self)
        self.collideWithLightcycles(lightcycles, collision_candidates, immunity)
        self.collideWithPolygon(collision_candidates, polygon_vertices, immunity)
        lightcycles.append(self)

    def collideWithLightcycles(self, lightcycles, collision_candidates, immunity, arrival_tollerance=0.001):
        for i in range(0, len(lightcycles)-1 if immunity == True else len(lightcycles)):
            timeA, timeB = rayRayIntersection(self.ground_origin, self.ground_velocity, lightcycles[i].ground_origin, lightcycles[i].ground_velocity)
            if math.isnan(timeA) or math.isnan(timeB):
                continue
            timeA += self.start_time
            timeB += lightcycles[i].start_time
            winner = None if abs(timeA-timeB) < arrival_tollerance else self if timeA < timeB else lightcycles[i]
            # TODO: Insert in manyfold collision
            insort_right(collision_candidates, lambda collision: collision.looser_time, Collision(
                winner_time=min(timeA, timeB),
                looser_time=max(timeA, timeB),
                winner=winner,
                loosers=([self, lightcycles[i]] if winner == None else [self if timeA > timeB else lightcycles[i]])
            ))

    def collideWithPolygon(self, collision_candidates, polygon_vertices, immunity):
        min_time = float('inf')
        for index in range(0, len(polygon_vertices)):
            if type(immunity) is int and (index == immunity or index == (immunity+1)%len(polygon_vertices)):
                continue
            time = rayLineSegmentIntersection(self.ground_origin, self.ground_velocity, polygon_vertices[index-1], polygon_vertices[index])
            if not math.isnan(time):
                min_time = min(time+self.start_time, min_time)
        if min_time < float('inf'):
            insort_right(collision_candidates, lambda collision: collision.looser_time, Collision(
                winner_time=0.0,
                looser_time=min_time,
                winner=None,
                loosers=[self]
            ))

    def calculateSlabIntersection(self, tollerance=0.0001):
        if self.collision == None:
            return
        self.slab_intersection.origin = self.ground_origin+self.ground_normal*self.start_time
        dir = self.ground_velocity+self.ground_normal
        self.slab_intersection.dir = dir.normalized()
        self.slab_intersection.end_param = dir@self.slab_intersection.dir*(self.collision.looser_time-self.start_time)
        if self.inwards:
            self.slab_intersection.prev_slab.slab_intersections.append(self.slab_intersection)
            self.slab_intersection.next_slab.slab_intersections.append(self.slab_intersection)

def straightSkeletonOfPolygon(polygon_vertices, mesh_data, height=1.5, tollerance=0.0001):
    polygon_normal = normalOfPolygon(polygon_vertices).normalized()
    polygon_plane = Plane(normal=polygon_normal, distance=polygon_vertices[0]@polygon_normal)
    for polygon_vertex in polygon_vertices:
        if abs(polygon_vertex@polygon_plane.normal-polygon_plane.distance) > tollerance:
            return 'Polygon is not planar / level'

    polygon_tangent = (polygon_vertices[1]-polygon_vertices[0]).normalized()
    plane_matrix = Matrix.Identity(4)
    plane_matrix.col[0] = polygon_tangent.to_4d()
    plane_matrix.col[1] = polygon_normal.cross(polygon_tangent).normalized().to_4d()
    plane_matrix.col[2] = polygon_normal.to_4d()
    plane_matrix.col[3] = (polygon_plane.normal*polygon_plane.distance).to_4d()
    plane_matrix.col[0].w = plane_matrix.col[1].w = plane_matrix.col[2].w = 0.0
    plane_matrix_inverse = plane_matrix.inverted()
    plane_matrix_inverse.row[2].zero()
    polygon_vertices = [plane_matrix_inverse@vertex for vertex in polygon_vertices]
    polygon_normal = Vector((0.0, 0.0, 1.0))

    slabs = []
    lightcycles = []
    collision_candidates = []

    for index, next_polygon_vertex in enumerate(polygon_vertices):
        prev_polygon_vertex = polygon_vertices[index-1]
        slabs.append(Slab(polygon_normal, prev_polygon_vertex, next_polygon_vertex))

    for index, prev_slab in enumerate(slabs):
        next_slab = slabs[(index+1)%len(polygon_vertices)]
        next_slab.prev_slab = prev_slab
        prev_slab.next_slab = next_slab
        Lightcycle(
            lightcycles, collision_candidates, polygon_vertices, polygon_normal, index,
            0.0, prev_slab, next_slab, polygon_vertices[index],
            (prev_slab.edge-next_slab.edge).normalized(), prev_slab.edge.cross(-next_slab.edge).normalized()
        )

    i = 0
    while i < len(collision_candidates):
        collision = collision_candidates[i]
        if collision.checkCandidate():
            collision.collide(lightcycles, collision_candidates, polygon_vertices, polygon_normal)
            if len(collision.loosers) > 2:
                return 'Manyfold collision' # TODO
        i += 1

    verts = []
    edges = []
    faces = []

    for lightcycle in lightcycles:
        lightcycle.calculateSlabIntersection()
        # if lightcycle.collision != None:
        #     verts += [lightcycle.slab_intersection.origin, lightcycle.slab_intersection.origin+lightcycle.slab_intersection.dir*lightcycle.slab_intersection.end_param]
        #     edges.append((len(verts)-2, len(verts)-1))

    for j, slabA in enumerate(slabs):
        slabA.calculateVerticesFromLightcycles()
        for i, slabB in enumerate(slabs):
            if i >= j:
                continue
            slabA.calculateSlabIntersection(slabB, i == 0)
        # for slab_intersection in slabA.slab_intersections:
        #     verts += [slab_intersection.origin+slab_intersection.dir*slab_intersection.begin_param, slab_intersection.origin+slab_intersection.dir*slab_intersection.end_param]
        #     edges.append((len(verts)-2, len(verts)-1))

    for index, slab in enumerate(slabs):
        slab.calculateVerticesFromIntersections()
        vert_index = len(verts)
        verts += slab.vertices
        faces.append(range(vert_index, len(verts)))

    #mesh_data.from_pydata(verts, edges, faces)
    return plane_matrix, verts, edges, faces



def sliceMesh(src_mesh, dst_obj, distances, axis):
    if dst_obj.type == 'MESH':
        dst_obj.data.clear_geometry()
    else:
        dst_obj.data.splines.clear()
    out_vertices = []
    out_edges = []
    for distance in distances:
        aux_mesh = src_mesh.copy()
        cut_geometry = bmesh.ops.bisect_plane(aux_mesh, geom=aux_mesh.edges[:]+aux_mesh.faces[:], dist=0, plane_co=axis*distance, plane_no=axis, clear_outer=False, clear_inner=False)['geom_cut']
        edge_pool = set((e for e in cut_geometry if isinstance(e, bmesh.types.BMEdge)))
        while len(edge_pool) > 0:
            current_edge = edge_pool.pop()
            first_vertex = current_vertex = current_edge.verts[0]
            vertices = [current_vertex.co]
            while True:
                current_vertex = current_edge.other_vert(current_vertex)
                if current_vertex == first_vertex:
                    break
                vertices.append(current_vertex.co)
                follow_edge_loop = False
                for edge in current_vertex.link_edges:
                    if edge in edge_pool:
                        current_edge = edge
                        edge_pool.remove(current_edge)
                        follow_edge_loop = True
                        break
                if not follow_edge_loop:
                    break
            if dst_obj.type == 'MESH':
                for i in range(len(out_vertices), len(out_vertices)+len(vertices)-1):
                    out_edges.append((i, i+1))
                if current_vertex == first_vertex:
                    out_edges.append((len(out_vertices), len(out_vertices)+len(vertices)-1))
                out_vertices += [Vector(vertex) for vertex in vertices]
            else:
                addPolygonSpline(dst_obj, current_vertex == first_vertex, vertices)
        aux_mesh.free()
    if dst_obj.type == 'MESH':
        dst_obj.data.from_pydata(out_vertices, out_edges, [])

## /internal.py #########################################

class SvStraightSkeleton2DTest001(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Merge two 2d meshes

    Each mesh can have disjoint parts
    Only X and Y coordinate takes in account
    """
    bl_idname = 'SvStraightSkeleton2DTest001'
    bl_label = 'Straight Skeleton 2D Test001'
    bl_icon = 'AUTOMERGE_ON'

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        pass

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertices')
        self.inputs.new('SvStringsSocket' , 'edges')
        self.inputs.new('SvStringsSocket' , 'polygons')
        #self.inputs.new('SvMatrixSocket'  , "matrixes")

        self.inputs['vertices'].label = 'Vertices'
        self.inputs['edges'].label = 'Edges'
        self.inputs['polygons'].label = 'Polygons'
        #self.inputs['matrixes'].label = 'Matrixes'

        self.outputs.new('SvVerticesSocket', 'vertices')
        self.outputs.new('SvStringsSocket' , 'edges')
        self.outputs.new('SvStringsSocket' , 'polygons')

        self.outputs['vertices'].label = 'Vertices'
        self.outputs['edges'].label = 'Edges'
        self.outputs['polygons'].label = 'Polygons'

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        if not any([sock.is_linked for sock in self.outputs]):
            return
        
        inputs = self.inputs
        _Vertices = inputs['vertices'].sv_get(default=[[]], deepcopy=False)
        Vertices  = ensure_nesting_level(_Vertices, 3)
        _Edges    = inputs['edges'].sv_get(default=[[]], deepcopy=False)
        Edges     = ensure_nesting_level(_Edges, 3)
        _Faces    = inputs['polygons'].sv_get(default=[[]], deepcopy=False)
        Faces     = ensure_nesting_level(_Faces, 3)

        res_verts = []
        res_edges = []
        res_faces = []

        for verts_i, edges_i, faces_i in zip_long_repeat(Vertices, Edges, Faces):

            #src_obj = bpy.context.object
            vverts_i = [Vector(v) for v in verts_i]
            polygons = [vverts_i] #selectedPolygons(src_obj)
            if len(faces_i) != 1:
                self.report({'WARNING'}, 'Invalid selection')
                return {'CANCELLED'}
            #dst_obj = addObject('MESH', 'Straight Skeleton')
            plane_matrix, verts, edges, faces = straightSkeletonOfPolygon(polygons[0], None)
            if isinstance(plane_matrix, str):
                self.report({'WARNING'}, result)
                return {'CANCELLED'}
            #dst_obj.matrix_world = src_obj.matrix_world@plane_matrix
            res_verts.append(verts)
            res_edges.append(edges)
            res_faces.append(faces)
            pass

        self.outputs['vertices'].sv_set(res_verts)
        self.outputs['edges'].sv_set(res_edges)
        self.outputs['polygons'].sv_set(res_faces)

        pass

classes = [SvStraightSkeleton2DTest001,]
register, unregister = bpy.utils.register_classes_factory(classes)