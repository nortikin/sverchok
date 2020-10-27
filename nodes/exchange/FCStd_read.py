from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvReadFCStdNode', 'SvReadFCStdNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy,sys
    from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.utils.logging import info, exception
    from numpy import ndarray

    class SvReadFCStdNode(bpy.types.Node, SverchCustomTreeNode):
        ''' SvReadFCStdNode '''
        bl_idname = 'SvReadFCStdNode'
        bl_label = 'Read FCStd'
        bl_icon = 'IMPORT'
        solid_catergory = "Inputs"
        
        read_update : BoolProperty(name="read_update", default=True)
        part_filter : StringProperty(name="part_filter", default="", description="use ',' to separate name with no space: part1,part2,... ")
        inv_filter : BoolProperty(name="inv_filter", default=False)

        def draw_buttons(self, context, layout):

            layout.label(text="filter by name:")

            col = layout.column(align=True)
            col.prop(self, 'part_filter',text="")
            col.prop(self, 'inv_filter')
            col.prop(self, 'read_update')          

        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")       
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return
            if not self.inputs['File Path'].is_linked:
                return            

            if self.read_update:
                
                files = self.inputs['File Path'].sv_get()[0]
                solids = []

                for f in files:
                    S = LoadSolid(f,self.part_filter,self.inv_filter)
                    for s in S:
                        solids.append(s)
                
                self.outputs['Solid'].sv_set(solids)
            
            else:
                return


def LoadSolid(fc_file,part_filter,inv_filter):
    solids = []

    if ',' in part_filter:
        part_filter = part_filter.split(',')

    elif not part_filter:
        part_filter = ['all']

    else:
        part_filter = [part_filter]

    try:

        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)

        for obj in F.ActiveDocument.Objects:

            if obj.Module in ('Part','PartDesign'):
                
                if not inv_filter:
                    if obj.Label in part_filter or 'all' in part_filter:
                        solids.append(obj.Shape)

                else:
                    if not obj.Label in part_filter:
                        solids.append(obj.Shape)

    except:
        info('FCStd read error')
    finally:
        F.closeDocument(Fname)
    return solids
    

def register():
    bpy.utils.register_class(SvReadFCStdNode)

def unregister():
    bpy.utils.unregister_class(SvReadFCStdNode)
