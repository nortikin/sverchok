# -*- coding: cp1251 -*-
# Gorodetskiy Nikita - basic idea, first script versions
# Nedovzin Alexander - nodes integration, all corrections and script rebuilding

bl_info = {
    "name": "Sverchok_spread",
    "author": "Nedovizin Alexander, Gorodetskiy Nikita",
    "version": (0, 1, 1),
    "blender": (2, 6, 8), 
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "spreads donor on recipient object using nodes system",
    "warning": "requires nodes window",
    "wiki_url": "",          
    "tracker_url": "",  
    "category": "Node",
}

import bpy, copy
from mathutils.geometry import intersect_line_plane
import mathutils
import math
import parser
from bpy.props import IntProperty, FloatProperty, StringProperty
from bpy_types import NodeTree, Node, NodeSocket

# сам себе выдал задание:
# ближайшая точка к плоскости, а также построение объекта 
# относительно нормали полигона и его размещение. 
# Зависимость расстояние-размер вставляемого объекта.


per_cache = {}

# force a full recalculation next time
def cache_delete(cache):
    if cache in per_cache:
        
        if 'spreads' in per_cache[cache]:
            bpy.ops.object.select_all(action='DESELECT')
            for sh in per_cache[cache]['spreads']:
                obj = bpy.data.objects[sh[0]] 
                obj.select = True
            
            bpy.ops.object.delete()
            del per_cache[cache]['spreads']
        
        del per_cache[cache]
        
def cache_read(cache):
    # current tool not cached yet
    if not (cache in per_cache):
        return(False, False, False, False, False, False, False, False)
    
    object = per_cache[cache]["object"]
    donor = per_cache[cache]["donor"]
    centres = per_cache[cache]["centres"]
    idx_centre = per_cache[cache]["idx_centre"]
    formula = per_cache[cache]["formula"]
    diap_min = per_cache[cache]["diap_min"]
    diap_max = per_cache[cache]["diap_max"]
    
    return(True, object, donor, centres, idx_centre, formula, diap_min, diap_max)
    
    
# store information in the cache
def cache_write(cache, object, donor, centres, idx_centre, formula, diap_min, diap_max):
    # clear cache of current tool
    if cache in per_cache:
        #del per_cache[cache]
        if object != per_cache[cache]['object']: cache_delete(cache)
        elif donor != per_cache[cache]['donor']: cache_delete(cache)
        elif centres != per_cache[cache]['centres']: cache_delete(cache)
        elif formula != per_cache[cache]['formula']: cache_delete(cache)
        elif formula != per_cache[cache]['diap_min']: cache_delete(cache)
        elif formula != per_cache[cache]['diap_max']: cache_delete(cache)

    # update cache
    if not (cache in per_cache) and cache!='':
        per_cache[cache] = {"object": object, "donor": donor,
            "centres": centres, "idx_centre": idx_centre, "formula": formula, 
            "diap_min":diap_min, "diap_max":diap_max}
        
        
        



class RecepCustomTree(NodeTree):
    '''A custom node tree type that will show up in the node editor header'''
    bl_idname = 'RecepCustomTreeType'
    bl_label = 'Custom Node Tree'
    bl_icon = 'NODETREE'

    
class DonorSocket(NodeSocket):
        '''Donor Socket_type'''
        bl_idname = "DonorSocket"
        bl_label = "Donor Socket"
        
        DonorProperty = bpy.props.StringProperty(name="DonorProperty")

        def draw(self, context, layout, node, text):
            if self.is_linked:
                layout.label(text)
            else:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(self, 'DonorProperty', text=text)
                
        def draw_color(self, context, node):
            return(.8,.3,.75,1.0)
    


class RecepCustomTreeNode :
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'RecepCustomTreeType'


def object_select(self, context):
    '''Return tuples of objects in scene for enum props'''
    return [tuple(3 * [ob.name]) for ob in context.scene.objects \
            if (ob.type == 'MESH' or ob.type == 'EMPTY') and ob.name.split('.')[0]!='spread']


class DonorInput(Node, RecepCustomTreeNode):
    ''' DonorInput'''
    bl_idname = 'DonorInputNode'
    bl_label = 'Object input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    ObjectProperty = bpy.props.EnumProperty(items=object_select)
    
    def init(self, context):
        self.outputs.new('DonorSocket', "Object") 

    def draw_buttons(self, context, layout):
        layout.prop(self, "ObjectProperty", text="Object", icon='OBJECT_DATA')
    
    def update(self):
        if self.ObjectProperty and self.ObjectProperty in bpy.context.scene.objects \
            and len(self.outputs['Object'].links)>0:
            object = bpy.data.objects[self.ObjectProperty]
            self.outputs['Object'].DonorProperty = object.name
    
    def update_socket(self, context):
        self.update()


class SurfOutput(Node, RecepCustomTreeNode):
    ''' Surface output node for basics definition '''
    bl_idname = 'SurfOutputNode'
    bl_label = 'Surface object'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    cache = bpy.props.StringProperty(default='')
    
    ObjectProperty = bpy.props.EnumProperty(items=object_select)
    FormulaProperty = bpy.props.StringProperty(default='1/x', description = 'write your spread\'s scale formula, using X as distance variable')
    
    def init(self, context):
        self.inputs.new('DonorSocket', "Donor")      
        self.inputs.new('DonorSocket', "Centres")  
        self.inputs.new('NodeSocketFloat', "Min","MinScale") 
        self.inputs.new('NodeSocketFloat', "Max","MaxScale") 
        self.outputs.new('DonorSocket', "List Objects", "ListObjects")

    def draw_buttons(self, context, layout):
        layout.prop(self, "ObjectProperty", text="Object", icon='OBJECT_DATA')
        layout.prop(self, "FormulaProperty", text="Formula")
        
        
        if self.ObjectProperty and self.ObjectProperty in bpy.context.scene.objects \
            and len(self.inputs['Donor'].links)>0 \
            and len(self.inputs['Centres'].links)>0:
                
            layout.operator("node.sverchok_spread", text='Update').cache = self.name
        
        
    def update(self):
        if self.ObjectProperty and self.ObjectProperty in bpy.context.scene.objects \
            and len(self.inputs['Donor'].links)>0 \
            and len(self.inputs['Centres'].links)>0:

            object = bpy.data.objects[self.ObjectProperty]
            tmpDonor = self.inputs['Donor'].links[0].from_socket.DonorProperty.split()
            
            object = self.ObjectProperty
            donor = tmpDonor[0]
            centres = self.inputs['Centres'].links[0].from_socket.DonorProperty
            idx_centre = 0
            formula = self.FormulaProperty
            diap_min = self.inputs['MinScale'].default_value
            diap_max = self.inputs['MaxScale'].default_value

            cache_write(self.name, object, donor, centres, idx_centre, formula, diap_min, diap_max)

    def update_socket(self, context):
        #print('update soket surf')
        self.update()


class ListObjectsNode(Node, RecepCustomTreeNode):
    '''A custom node'''
    bl_idname = 'ListObjectsNode'
    bl_label = 'List Objects'
    bl_icon = 'SOUND'


    def init(self, context):
        self.inputs.new('DonorSocket', "Object 1", "Object1")
        self.inputs.new('DonorSocket', "Object 2", "Object2")
        self.inputs.new('DonorSocket', "Object 3", "Object3")
        self.inputs.new('DonorSocket', "Object 4", "Object4")

        self.outputs.new('DonorSocket', "List Objects", "ListObjects")

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        print("Copying from node ", node)
    
    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")

    def update(self):
        (s1,s2,s3,s4) = ('','','','')
        if len(self.inputs['Object1'].links)>0:
            s1 = self.inputs['Object1'].links[0].from_socket.DonorProperty + ' '
            
        if len(self.inputs['Object2'].links)>0:
            s2 = self.inputs['Object2'].links[0].from_socket.DonorProperty + ' '

        if len(self.inputs['Object3'].links)>0:
            s3 = self.inputs['Object3'].links[0].from_socket.DonorProperty + ' '

        if len(self.inputs['Object4'].links)>0:
            s4 = self.inputs['Object4'].links[0].from_socket.DonorProperty + ' '

        s = s1+s2+s3+s4
        s = s.rstrip()
            
        self.outputs["ListObjects"].DonorProperty = s
            

    def update_socket(self, context):
        #print('update soket surf')
        self.update()


### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type
class RecepNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'RecepCustomTreeType'

# all categories in a list
node_categories = [
    # identifier, label, items list
    RecepNodeCategory("SOMENODES", "Some Nodes", items=[
        # our basic node
        NodeItem("SurfOutputNode", label="Surface object"),
        NodeItem("DonorInputNode", label="Object input"),
        NodeItem("ListObjectsNode", label="List Objects"),
        ]),
    ]


def tree_update():
    for ng in bpy.context.blend_data.node_groups:
        ng.interface_update(bpy.context)
    return   



def vec_pols(pol2,ver2,mw2):
    vector_mediana = []
    for p in pol2:
        vs_idx = p.vertices

        v0 = ver2[vs_idx[0]].co
        v1 = ver2[vs_idx[1]].co
        v2 = ver2[vs_idx[2]].co
        v3 = ver2[vs_idx[3]].co
        
        point1 = (v0+v1)/2
        point2 = (v2+v3)/2
        vm = point2 - point1
        
        vector_mediana.append(vm)
    return vector_mediana


def cont_obj(ob):
    (l,r,f,b,t,d) = (0,0,0,0,0,0)
    for v in ob.data.vertices:
        if v.co[0]<l: l = v.co[0]
        if v.co[0]>r: r = v.co[0]
        if v.co[1]<b: b = v.co[1]
        if v.co[1]>f: f = v.co[1]
        if v.co[2]>t: t = v.co[2]
        if v.co[2]<d: d = v.co[2]
   
    length = abs(r-l)   
    weidth = abs(f-b)
    height = abs(t-d)
    
    return (length, weidth, height)


def cont_pol(pol,ver2):
        vs_idx = pol.vertices

        v0 = ver2[vs_idx[0]].co
        v1 = ver2[vs_idx[1]].co
        v2 = ver2[vs_idx[2]].co
        v3 = ver2[vs_idx[3]].co
        
        point1 = (v0+v1)/2
        point2 = (v2+v3)/2
        point3 = (v0+v3)/2
        point4 = (v1+v2)/2
        vmy = (point2 - point1).length
        vmx = (point3 - point4).length
   
        return (vmx,vmy) 


def scale_pols(pols, ver, ob):
    scale = []
    gab_ob = cont_obj(ob)
    for p in pols:
        gab_pol = cont_pol(p, ver)
        sc_length = gab_pol[0]/gab_ob[0]
        sc_weidth = gab_pol[1]/gab_ob[1]
        
        scale.append((sc_length,sc_weidth))
    return scale


def distance(x,y):
    vec = mathutils.Vector((x[0]-y[0], x[1]-y[1], x[2]-y[2]))
    return vec.length

def centres(pol2,ver2,mw2):
    centrs = []
    for p in pol2:
        (i,x,y,z) = (0,0,0,0)
        for v in p.vertices:
            x += ver2[v].co[0]
            y += ver2[v].co[1]
            z += ver2[v].co[2]
            i += 1
        (x,y,z) = (x/i, y/i, z/i)
        centrs.append(mw2 * mathutils.Vector((x, y, z)))
    return centrs


def dimension_obj(pols, ver, ob):
    dimen = []
    gab_ob = cont_obj(ob)
    for p in pols:
        gab_pol = cont_pol(p, ver)
        min_fig = True
        
        if (gab_pol[0]<gab_ob[0])or(gab_pol[1]<gab_ob[1]):
            min_fig = False
            
        if min_fig:
            dm_length = gab_pol[0]/2
            dm_weidth = gab_pol[1]/2
            dm_height = gab_ob[2]/2
        else:
            dm_length = gab_ob[0]/2
            dm_weidth = gab_ob[1]/2
            dm_height = gab_ob[2]/2
        
        dm = (dm_length, dm_weidth, dm_height)
        dimen.append(dm)
    return dimen
    

def normals(pol2,mw2):
    nor2 = []
    for p in pol2:
        nor2.append(p.normal)
    return nor2

def distancia(obj1,centrs):
    dist = []
    i = 0
    pt = obj1.matrix_world.translation
    for c in centrs:
        lent = distance(pt,c)
        dist.append((lent))
    return dist


#////////////////////////////////////////////////////////////////////
#/////////////////   main   ////////////////////////////////////////
#//////////////////////////////////////////////////////////////////

def main(cache):
    global per_cache
    rd_cache = cache_read(cache)
    if not rd_cache[0]:
        #print('rd_cache[0] is False')
        return False
    
    if not ('spreads' in per_cache[cache]):
        drawit(cache, redraw=False)
    else:
        if bpy.data.objects.find(per_cache[cache]['spreads'][0][0])==-1:
            del per_cache[cache]['spreads']
            drawit(cache, redraw=False)
        else:
            drawit(cache, redraw=True)


def drawit(cache, total_x=0,total_y=0,total_z=0, redraw=False):
    global per_cache
    
    rd_cache = cache_read(cache)
    #True, object, donor, centres, idx_centre, formula, diap_min, diap_max
    
    # достаём объекты
    formula = rd_cache[5]
    obj2_name = rd_cache[1]
    obj2 = bpy.data.objects[obj2_name] #bpy.data.objects['polygons']
    ObjectDonor = rd_cache[2] #per_cache[cache]['donor']
    obj3donor = bpy.data.objects[ObjectDonor] #bpy.data.objects['donor']
    #mw1 = obj1.matrix_world
    mw2 = obj2.matrix_world
    mw3 = obj3donor.matrix_world
    #mesh1 = obj1.data
    #mesh1.name = 'point'
    #mesh1.update()
    mesh2 = obj2.data
    mesh2.name = obj2_name
    mesh2.update()
    mesh3 = obj3donor.data
    mesh3.name = ObjectDonor
    #pol1 = mesh1.polygons
    pol2 = mesh2.polygons
    #edg1 = mesh1.edges
    edg2 = mesh2.edges
    #ver1 = mesh1.vertices
    ver2 = mesh2.vertices
    dist = []

    sc_pols = scale_pols(pol2, ver2, obj3donor)
    #dimens = dimension_obj(pol2, ver2, obj3donor)
    centrs = centres(pol2,ver2,mw2)
    nor2 = normals(pol2,mw2)    
    medians = vec_pols(pol2,ver2,mw2)
    
    #code_formula = parser.expr(formula).compile()
    minimum = rd_cache[7]
    maximum = rd_cache[6]
    
    code_formula = parser.expr("max(min("+formula+",minimum),maximum)").compile()

    centres_empty = per_cache[cache]['centres'].split()
    for i, obj1_name in enumerate(centres_empty):
        obj1 = bpy.data.objects[obj1_name]
        loc = obj1.location
        obj1.matrix_world.translation = mathutils.Vector((loc.x+total_x,loc.y+total_y,loc.z+total_z))
        tmpdist = distancia(obj1,centrs)
        if i == 0:
            dist = tmpdist
        else:
            dist = list(map(lambda x,y: min(x,y),tmpdist, dist))

    if redraw:
        spreads = per_cache[cache]['spreads']
        for i,sh in enumerate(spreads):
            tempob = bpy.data.objects.get(sh[0]) 
            x = dist[i]
            mul = eval(code_formula)
            mul = min(mul,sc_pols[i][0],sc_pols[i][1])
            tempob.dimensions = sh[1] * mul
    
    
    else:
      spreads = []
      for i,c in enumerate(centrs):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[ObjectDonor].select = True
        bpy.ops.object.duplicate(linked=True) 
        tempob = bpy.context.selected_objects[0]
        tempob.name = 'spread'
        tempob.matrix_world.translation = c
        
        aa = mathutils.Vector((0,1e-6,1)) 
        bb = mathutils.Vector((nor2[i].x,nor2[i].y,nor2[i].z))
        vec = aa
        q_rot = vec.rotation_difference(bb).to_matrix().to_4x4()

        vec2 = bb
        q_rot2 = vec2.rotation_difference(aa).to_matrix().to_4x4()

        a = mathutils.Vector((1e-6,1,0))* q_rot2
        b = medians[i] 
        vec1 = a
        q_rot1 = vec1.rotation_difference(b).to_matrix().to_4x4() 

        M = q_rot1*q_rot
        tempob.matrix_local *= M
        
        x = dist[i]
        mul = eval(code_formula)
        mul = min(mul,sc_pols[i][0],sc_pols[i][1])
        spreads.append((tempob.name, copy.copy(tempob.dimensions)))
        tempob.dimensions = tempob.dimensions * mul
      per_cache[cache]['spreads'] = spreads





class ObjectSverchokSpread(bpy.types.Operator):
    """Object Sverchok Spread"""
    bl_idname = "node.sverchok_spread"
    bl_label = "Sverchok Spread"
    bl_options = {'REGISTER', 'UNDO'}
    
    total_x = bpy.props.FloatProperty()
    total_y = bpy.props.FloatProperty()
    total_z = bpy.props.FloatProperty()
    
    first_mouse_x = IntProperty()
    first_mouse_y = IntProperty()

    first_value = FloatProperty()
    axis_mouse = IntProperty()
    
    cache = StringProperty()
    
    
    def execute(self, context):
        global per_cache
        
        if self.cache != '':
            tree_update()
            main(self.cache)
            if 'spreads' in per_cache[self.cache]:
                for ng in bpy.context.blend_data.node_groups:
                    if self.cache in ng.nodes:
                        ng.nodes[self.cache].outputs['ListObjects'].DonorProperty = \
                        str(per_cache[self.cache]['spreads'][0])
        return {'FINISHED'}
    
        
classes = [ObjectSverchokSpread, RecepCustomTree, DonorSocket, SurfOutput, 
    DonorInput, ListObjectsNode]

def register():
    for c in classes:
        bpy.utils.register_class(c)   
    nodeitems_utils.register_node_categories("CUSTOM_NODES", node_categories)
    
def unregister():
    for c in reversed(classes):  
        bpy.utils.unregister_class(c)  
    
    nodeitems_utils.unregister_node_categories("CUSTOM_NODES")
    
if __name__ == "__main__":
    #unregister()
    register()
 