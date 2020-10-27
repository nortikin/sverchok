
from sverchok.dependencies import FreeCAD
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None:
    add_dummy('SvWriteFCStdNode', 'SvWriteFCStdNode', 'FreeCAD')

else:
    F = FreeCAD
    import bpy,sys
    from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty,EnumProperty
    from sverchok.node_tree import SverchCustomTreeNode, throttled
    from sverchok.data_structure import updateNode
    from numpy import ndarray

    class SvWriteFCStdNode(bpy.types.Node, SverchCustomTreeNode):
        ''' SvWriteFCStdNode '''
        bl_idname = 'SvWriteFCStdNode'
        bl_label = 'Write FCStd'
        bl_icon = 'IMPORT'
        solid_catergory = "Inputs"
        
        write_update : BoolProperty(
            name="write_update", 
            default=True)

        part_name : StringProperty(
            name="part_name", 
            default="part_name")

        @throttled
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


        def sv_init(self, context):
            self.inputs.new('SvFilePathSocket', "File Path")

            if self.obj_format == 'mesh':
                self.inputs.new('SvVerticesSocket', "Verts")
                self.inputs.new('SvStringsSocket', "Faces")

            else:
                self.inputs.new('SvSolidSocket', 'Solid')
           

        def process(self):

            if not self.inputs['File Path'].is_linked:
                return
            
            files = self.inputs['File Path'].sv_get()

            if  not len(files[0]) == 1:
                print ('FCStd write node support just 1 file at once')
                return

            fc_file=files[0][0]

            if self.obj_format == 'mesh':

                if any((self.inputs['Verts'].is_linked,self.inputs['Faces'].is_linked,self.write_update)):

                    verts=self.inputs['Verts'].sv_get()
                    pols=self.inputs['Faces'].sv_get()
                    fc_write_parts(fc_file,verts,pols,self.part_name,None,self.obj_format)

            elif self.obj_format == 'solid':

                if self.inputs['Solid'].is_linked and self.write_update:
                    solid=self.inputs['Solid'].sv_get()
                    fc_write_parts(fc_file,None,None,self.part_name,solid,self.obj_format)

            else:
                return             
            

def fc_write_parts(fc_file, verts, faces, part_name, solid, mod):

    try:
        F.open(fc_file)
        Fname = bpy.path.display_name_from_filepath(fc_file)
    except:
        print ('FCStd open error')
        return


    F.setActiveDocument(Fname)
    fc_root = F.getDocument(Fname)

    obj_names = set( [ i.Name for i in fc_root.Objects] )

    part_name += '_sv_' #->suffix added to avoid deleting erroneusly freecad objects

    # SEARCH the freecad project for previous writed parts from this node

    if part_name in obj_names: #if the part name is numberless is detected as single
        fc_root.removeObject(part_name)

    else:
        for name in obj_names: #if not, check the fc project if there are parts with same root name
            if part_name in name:
                fc_root.removeObject(name)

    ############### if there, previous writed parts are removed ####################
    ############### so then write them again...

    if mod == 'solid': #EXPORT SOLID 

        #if len(solid)==1:
            #new_part = F.ActiveDocument.addObject("Part::Feature",part_name) #single: give numberless name
            #new_part.Shape = solid[0]

        #else:
        for i,s in enumerate(solid):      
            new_part = F.ActiveDocument.addObject("Part::Feature",part_name+str(i)) #multiple: give numbered name
            new_part.Shape = s

    else: #EXPORT MESH
        
        import Mesh
        
        for i in range(len(verts)):

            temp_faces=faces[i]
            temp_verts=verts[i]

            meshdata=[]

            for f in temp_faces:
                v1,v2,v3 = f[0],f[1],f[2]
                meshdata.append( temp_verts[v1] )
                meshdata.append( temp_verts[v2] )
                meshdata.append( temp_verts[v3] )

            mesh = Mesh.Mesh(meshdata)
            obj = F.ActiveDocument.addObject("Mesh::Feature", part_name+str(i))
            obj.Mesh = mesh


    F.ActiveDocument.recompute()
    F.getDocument(Fname).save()
    F.closeDocument(Fname)


def register():
    bpy.utils.register_class(SvWriteFCStdNode)

def unregister():
    bpy.utils.unregister_class(SvWriteFCStdNode)
