import re
import random

import bpy
from bpy.props import IntProperty
import mathutils
from mathutils import Vector, Matrix


bpy.types.Scene.SvGreekAlphabet_index = IntProperty(default=0, min=0, max=24)
greek_alphabet = [
    'Alpha', 'Beta', 'Gamma', 'Delta',
    'Epsilon', 'Zeta', 'Eta', 'Theta',
    'Iota', 'Kappa', 'Lamda', 'Mu',
    'Nu', 'Xi', 'Omicron', 'Pi',
    'Rho', 'Sigma', 'Tau', 'Upsilon',
    'Phi', 'Chi', 'Psi', 'Omega']


def matrix_sanitizer(matrix):
    #  reduces all values below threshold (+ or -) to 0.0, to avoid meaningless
    #  wandering floats.
    # print(matrix)
    coord_strip = lambda c: 0.0 if (-1.6e-5 <= c <= 1.6e-5) else c
    san = lambda v: Vector((coord_strip(c) for c in v[:]))
    return Matrix([san(v) for v in matrix])




def natural_plus_one(object_names):

    ''' sorts ['Alpha', 'Alpha1', 'Alpha11', 'Alpha2', 'Alpha23']
        into ['Alpha', 'Alpha1', 'Alpha2', 'Alpha11', 'Alpha23']
        and returns (23+1)
    '''

    def extended_sort(a):
        ''' finds the digit trailing, or 0 if no digits '''
        k = re.split('(\d*)', a)
        return 0 if len(k) == 1 else int(k[1])

    natural_sort = sorted(object_names, key=extended_sort)
    last = natural_sort[-1]
    num = extended_sort(last)
    return num+1


def get_children(node, kind='MESH'):
    # critera, basename must be in object.keys and the value must be self.basemesh_name
    objects = bpy.data.objects
    objs = [obj for obj in objects if obj.type == kind]
    return [o for o in objs if o.get('basename') == node.basemesh_name]


def remove_non_updated_objects(node, obj_index, kind='MESH'):
    objs = get_children(node, kind)
    objs = [obj.name for obj in objs if obj['idx'] > obj_index]
    if not objs:
        return

    if kind == 'MESH':
        kinds = bpy.data.meshes
    elif kind == 'CURVE':
        kinds = bpy.data.curves

    objects = bpy.data.objects
    collection = bpy.context.scene.collection

    # remove excess objects
    for object_name in objs:
        obj = objects[object_name]
        obj.hide_select = False
        collection.objects.unlink(obj)
        objects.remove(obj, do_unlink=True)

    # delete associated meshes
    for object_name in objs:
        kinds.remove(kinds[object_name])        
