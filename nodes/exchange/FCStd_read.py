from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvReadFCStdNode', 'SvReadFCStdNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy
    from bpy.props import StringProperty, BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.utils.logging import info

    class SvReadFCStdNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Read FreeCAD file
        Tooltip: import parts from a .FCStd file 
        """
        bl_idname = 'SvReadFCStdNode'
        bl_label = 'Read FCStd'
        bl_icon = 'IMPORT'
        solid_catergory = "Inputs"
        
        read_update : BoolProperty(name="read_update", default=True, update = updateNode )
        inv_filter : BoolProperty(name="inv_filter", default=False)

        def draw_buttons(self, context, layout):
            col = layout.column(align=True)
            col.prop(self, 'read_update') 
            col.prop(self, 'inv_filter')
         
        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Part Filter")   
            self.inputs.new('SvFilePathSocket', "File Path")       
            self.outputs.new('SvSolidSocket', "Solid")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return
            if not self.inputs['File Path'].is_linked:
                return            

            if self.read_update:       
                files = self.inputs['File Path'].sv_get()[0]
                                               
                part_filter = []
                if self.inputs['Part Filter'].is_linked:
                    part_filter = self.inputs['Part Filter'].sv_get()             
             
                solids = []

                for f in files:
                    S = LoadSolid(f, self.part_filter, self.inv_filter)
                    for s in S:
                        solids.append(s)
                
                self.outputs['Solid'].sv_set(solids)
            
            else:
                return


def LoadSolid(fc_file, part_filter, inv_filter):
    solids = []

    try:

        F.open(fc_file) 
        Fname = bpy.path.display_name_from_filepath(fc_file)
        F.setActiveDocument(Fname)

        for obj in F.ActiveDocument.Objects:

            if obj.Module in ('Part', 'PartDesign'):
                
                if not inv_filter:

                    if obj.Label in part_filter or len(part_filter)==0:
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
