import bpy
import sys
from bpy.props import EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_cycle as mlr
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode

def boolean_internal(VA, PA, VB, PB, operation):
    """
    Create two temporary mesh objects from the given vertices and faces,
    apply a Boolean modifier on object A using object B as the target,
    then extract the resulting geometry.
    """
    # --- Create temporary object A ---
    mesh_a = bpy.data.meshes.new("temp_mesh_a")
    mesh_a.from_pydata(VA, [], PA)
    mesh_a.update()
    obj_a = bpy.data.objects.new("temp_obj_a", mesh_a)
    bpy.context.collection.objects.link(obj_a)
    
    # --- Create temporary object B ---
    mesh_b = bpy.data.meshes.new("temp_mesh_b")
    mesh_b.from_pydata(VB, [], PB)
    mesh_b.update()
    obj_b = bpy.data.objects.new("temp_obj_b", mesh_b)
    bpy.context.collection.objects.link(obj_b)
    
    # --- Add and configure the Boolean modifier ---
    mod = obj_a.modifiers.new(name="Boolean", type='BOOLEAN')
    mod.object = obj_b
    if operation == 'ITX':
        mod.operation = 'INTERSECT'
    elif operation == 'JOIN':
        mod.operation = 'UNION'
    elif operation == 'DIFF':
        mod.operation = 'DIFFERENCE'
    
    # --- Evaluate the modifier and extract the result ---
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj_a.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(obj_eval)
    
    verts = [list(v.co) for v in new_mesh.vertices]
    faces = [list(p.vertices) for p in new_mesh.polygons]
    
    # --- Cleanup: remove temporary data ---
    bpy.data.meshes.remove(new_mesh)
    bpy.data.objects.remove(obj_a, do_unlink=True)
    bpy.data.objects.remove(obj_b, do_unlink=True)
    bpy.data.meshes.remove(mesh_a)
    bpy.data.meshes.remove(mesh_b)
    
    return verts, faces

class SvInternalBooleanNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    '''Internal Boolean Node using Blender’s Boolean Modifier'''
    bl_idname = 'SvInternalBooleanNode'
    bl_label = 'Internal Boolean'
    bl_icon = 'MOD_BOOLEAN'

    mode_options = [
        ("ITX", "Intersect", "", 0),
        ("JOIN", "Union", "", 1),
        ("DIFF", "Difference", "", 2)
    ]

    selected_mode: EnumProperty(
        items=mode_options,
        description="Select the Boolean operation (using Blender's modifier)",
        default="ITX",
        update=updateNode)

    def update_mode(self, context):
        self.inputs['Verts A'].hide_safe = self.nest_objs
        self.inputs['Polys A'].hide_safe = self.nest_objs
        self.inputs['Verts B'].hide_safe = self.nest_objs
        self.inputs['Polys B'].hide_safe = self.nest_objs
        self.inputs['Verts Nested'].hide_safe = not self.nest_objs
        self.inputs['Polys Nested'].hide_safe = not self.nest_objs
        updateNode(self, context)

    nest_objs: BoolProperty(
        name="Accumulate Nested",
        description="Boolean the first two objects, then apply subsequent booleans to the result one by one",
        default=False,
        update=update_mode)

    out_last: BoolProperty(
        name="Only Final Result",
        description="Output only the final iteration result",
        default=True,
        update=update_mode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts A')
        self.inputs.new('SvStringsSocket',  'Polys A')
        self.inputs.new('SvVerticesSocket', 'Verts B')
        self.inputs.new('SvStringsSocket',  'Polys B')
        self.inputs.new('SvVerticesSocket', 'Verts Nested').hide_safe = True
        self.inputs.new('SvStringsSocket',  'Polys Nested').hide_safe = True
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Polygons')

    @property
    def sv_internal_links(self):
        if self.nest_objs:
            return [
                (self.inputs['Verts Nested'], self.outputs[0]),
                (self.inputs['Polys Nested'], self.outputs[1]),
            ]
        else:
            return super().sv_internal_links

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)
        col = layout.column(align=True)
        col.prop(self, "nest_objs", toggle=True)
        if self.nest_objs:
            col.prop(self, "out_last", toggle=True)

    def process(self):
        OutV, OutP = self.outputs
        if not OutV.is_linked:
            return

        VertA, PolA, VertB, PolB, VertN, PolN = self.inputs
        op_mode = self.selected_mode
        results = []
        
        # Increase recursion limit if needed (as in your original node)
        recursionlimit = sys.getrecursionlimit()
        sys.setrecursionlimit(10000)
        
        if not self.nest_objs:
            for v1, p1, v2, p2 in zip(*mlr([VertA.sv_get(), PolA.sv_get(), VertB.sv_get(), PolB.sv_get()])):
                result = boolean_internal(v1, p1, v2, p2, op_mode)
                results.append(result)
        else:
            vnest, pnest = VertN.sv_get(), PolN.sv_get()
            result = boolean_internal(vnest[0], pnest[0], vnest[1], pnest[1], op_mode)
            if not self.out_last:
                results.append(result)
                for i in range(2, len(vnest)):
                    result = boolean_internal(result[0], result[1], vnest[i], pnest[i], op_mode)
                    results.append(result)
            else:
                for i in range(2, len(vnest)):
                    result = boolean_internal(result[0], result[1], vnest[i], pnest[i], op_mode)
                results.append(result)
                
        sys.setrecursionlimit(recursionlimit)
        
        OutV.sv_set([r[0] for r in results])
        if OutP.is_linked:
            OutP.sv_set([r[1] for r in results])

def register():
    bpy.utils.register_class(SvInternalBooleanNode)

def unregister():
    bpy.utils.unregister_class(SvInternalBooleanNode)
