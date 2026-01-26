import bpy
from bpy.props import StringProperty, BoolProperty,EnumProperty

from sverchok.node_tree import SverchCustomTreeNode # OLD throttled
from sverchok.data_structure import updateNode, match_long_repeat # NEW throttle_and_update_node
from sverchok.utils.sv_logging import sv_logger
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator

if FreeCAD is not None:
    F = FreeCAD


class SvWriteFCStdOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_write_fcstd_operator"
    bl_label = "write freecad file"
    bl_options = {'INTERNAL', 'REGISTER'}

    def execute(self, context):
        node = self.get_node(context)

        if not node: return {'CANCELLED'}

        node.write_FCStd(node)
        updateNode(node,context)

        return {'FINISHED'}


class SvWriteFCStdNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: write FreeCAD file
    Tooltip: write parts in a .FCStd file
    """

    bl_idname = 'SvWriteFCStdNode'
    bl_label = 'Write FCStd'
    bl_icon = 'IMPORT'
    sv_category = "Solid Inputs"
    sv_dependencies = {'FreeCAD'}

    write_update : BoolProperty(
        name="write_update",
        default=False)

    part_name : StringProperty(
        name="part_name",
        default="part_name")

    #@throttled
    def changeMode(self, context):

        if self.obj_format == 'mesh':
            if 'Verts' not in self.inputs:
                self.inputs.remove(self.inputs['Solid'])
                self.inputs.new('SvVerticesSocket', 'Verts')
                self.inputs.new('SvVerticesSocket', 'Faces')
                return
        else:
            if 'Solid' not in self.inputs:
                self.inputs.remove(self.inputs['Verts'])
                self.inputs.remove(self.inputs['Faces'])
                self.inputs.new('SvSolidSocket', 'Solid')
                return

    obj_format : EnumProperty(
                name='format',
                description='choose format',
                items={
                ('solid', 'solid', 'solid'),
                ('mesh', 'mesh', 'mesh')},
                default='solid',
                update=changeMode)

    def draw_buttons(self, context, layout):

        layout.label(text="write name:")
        col = layout.column(align=True)
        col.prop(self, 'part_name',text="")
        col.prop(self, 'obj_format',text="")
        col.prop(self, 'write_update')
        if self.obj_format == 'mesh':
            col.label(text="need triangle meshes")
        self.wrapper_tracked_ui_draw_op(layout, SvWriteFCStdOperator.bl_idname, icon='FILE_REFRESH', text="UPDATE")


    def sv_init(self, context):
        self.inputs.new('SvFilePathSocket', "File Path")

        if self.obj_format == 'mesh':
            self.inputs.new('SvVerticesSocket', "Verts")
            self.inputs.new('SvStringsSocket', "Faces")

        else:
            self.inputs.new('SvSolidSocket', 'Solid')

    def write_FCStd(self,node):

        if not node.inputs['File Path'].is_linked:
            return

        files = node.inputs['File Path'].sv_get()

        if  not len(files[0]) == 1:
            print ('FCStd write node support just 1 file at once')
            return

        fc_file=files[0][0]

        if node.obj_format == 'mesh':

            if any((node.inputs['Verts'].is_linked,node.inputs['Faces'].is_linked)):

                verts_in = node.inputs['Verts'].sv_get(deepcopy=False)
                pols_in = node.inputs['Faces'].sv_get(deepcopy=False)
                verts, pols = match_long_repeat([verts_in, pols_in])
                fc_write_parts(fc_file, verts, pols, node.part_name, None, node.obj_format)

        elif node.obj_format == 'solid':

            if node.inputs['Solid'].is_linked:
                solid=node.inputs['Solid'].sv_get()
                fc_write_parts(fc_file, None, None, node.part_name, solid, node.obj_format)

        else:
            return

    def process(self):

        if self.write_update:
            self.write_FCStd(self)
        else:
            return


def fc_write_parts(fc_file, verts, faces, part_name, solid, mod):

    try:
        from os.path import exists

        Fname = bpy.path.display_name_from_filepath(fc_file)

        if not exists(fc_file):
            doc = F.newDocument(Fname)
            doc.recompute()
            doc.saveAs(fc_file) # using full filepath, saveAs also sets doc.FileName internally

        F.open(fc_file)

    except Exception as err:
        sv_logger.info(f'FCStd open error, {err}')
        return

    F.setActiveDocument(Fname)
    fc_root = F.getDocument(Fname)

    obj_names = set( [ i.Name for i in fc_root.Objects] )

    part_name += '_sv_' #->suffix added to avoid deleting freecad objects erroneously

    # SEARCH the freecad project for previous written parts from this node

    if part_name in obj_names: #if the part name is numberless is detected as single
        fc_root.removeObject(part_name)

    else:
        for name in obj_names: #if not, check the fc project if there are parts with same root name
            if part_name in name:
                fc_root.removeObject(name)

    ############### if there, previous writted parts are removed ####################
    ############### so then write them again...

    if mod == 'solid': #EXPORT SOLID 

        for i, s in enumerate(solid):      
            new_part = F.ActiveDocument.addObject( "Part::Feature",part_name+str(i) ) #multiple: give numbered name
            new_part.Shape = s

    else: #EXPORT MESH
        
        import Mesh
        
        for i in range(len(verts)):

            temp_faces = faces[i]
            temp_verts = verts[i]
            meshdata = []

            for f in temp_faces:
                v1,v2,v3 = f[0],f[1],f[2]
                meshdata.append( temp_verts[v1] )
                meshdata.append( temp_verts[v2] )
                meshdata.append( temp_verts[v3] )

            mesh = Mesh.Mesh( meshdata )
            obj = F.ActiveDocument.addObject( "Mesh::Feature", part_name+str(i) )
            obj.Mesh = mesh


    F.ActiveDocument.recompute()
    F.getDocument(Fname).save()
    F.closeDocument(Fname)


def register():
    bpy.utils.register_class(SvWriteFCStdNode)
    bpy.utils.register_class(SvWriteFCStdOperator)


def unregister():
    bpy.utils.unregister_class(SvWriteFCStdNode)
    bpy.utils.unregister_class(SvWriteFCStdOperator)
