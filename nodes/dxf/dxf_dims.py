import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, dataCorrect_np
from mathutils import Vector
from sverchok.utils.dxf import LWdict, lineweights, linetypes


class DxfLinDims:
    def __repr__(self):
        return "<DXF LinDims>"

    def __init__(self, vers, color, lineweight, metadata, linetype, text_scale, node, color_int):
        self.vers = vers
        self.node = node
        self.color = color
        self.color_int = color_int
        self.lineweight = lineweight
        self.metadata = metadata
        self.linetype = linetype
        self.text_scale = text_scale

    def draw(self):
        return self.vers


class SvDxfLinDimsNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfLinDimsNode'
    bl_label = 'DXF Linear Dimensions'
    bl_icon = 'EXPORT'
    sv_icon = 'SV_DIMENSION_SVG'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    metadata: bpy.props.StringProperty(default='',name='metadata')

    color_int: bpy.props.IntProperty(default=-4, min=-4, max=255,name='color', description='-4 is ignore, -3')

    unit_color: bpy.props.FloatVectorProperty(
        update=updateNode, name='', default=(.3, .3, .2, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    linetype: bpy.props.EnumProperty(
        name="linetype", description="linetypes", default='CONTINUOUS', items=linetypes, update=updateNode)

    lineweight: bpy.props.EnumProperty(
        name="lineweight", description="lineweight", default='0.00', items=lineweights, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'vertsA')
        self.inputs.new('SvVerticesSocket', 'vertsB')
        #self.inputs.new('SvTextSocket', 'text')
        self.inputs.new('SvColorSocket', 'color').custom_draw = 'draw_color_socket'
        self.inputs.new('SvTextSocket', 'metadata').prop_name='metadata'
        self.outputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        layout.prop(self, "linetype", expand=False)
        layout.prop(self, "lineweight", expand=False)
        layout.prop(self, "text_scale", expand=False)
        layout.prop(self, "color_int", expand=False)

    def draw_color_socket(self, socket, context, layout):
        if not socket.is_linked:
            layout.prop(self, 'unit_color', text="")
        else:
            layout.label(text=socket.name+ '. ' + str(socket.objects_number))

    def process(self):
        if self.outputs['dxf'].is_linked and self.inputs['vertsA'].is_linked and self.inputs['vertsB'].is_linked:
            # All starts with dxf socket
            versa_ = self.inputs['vertsA'].sv_get()
            versb_ = self.inputs['vertsB'].sv_get()
            #if self.inputs['text'].is_linked:
            #    text_ = self.inputs['text'].sv_get()
            # color [[ (1,0,1) ]]
            if self.inputs['color'].is_linked:
                cols_ = self.inputs['color'].sv_get(deepcopy=False)
                cols_ = dataCorrect_np(cols_)[0][0]
            else:
                cols_ = self.unit_color[:]
            color_int = self.color_int
            # It is any text [['text']]
            meta_ = self.inputs['metadata'].sv_get()
            dxf = []
            # not match long repeate because we can use several nodes 
            # and multipliying mesh with colors absurdic, except meta
            lw = LWdict[self.lineweight]
            lt = self.linetype
            text_scale = self.text_scale
            for obva, obvb,met in zip_long_repeat(versa_,versb_,meta_):
                # объекты
                for va, vb, me in zip_long_repeat(obva,obvb,met):
                    # целый полигон [0,1,2,3]
                    vr = [va,vb]
                    # каждый полигон это отдельный экземпляр
                    dims = DxfLinDims(vr,cols_,lw,me,lt,text_scale,self,color_int)
                    dxf.append(dims)
            self.outputs['dxf'].sv_set([dxf])

    def sv_update(self):
        if not ("vertsA" in self.inputs):
            return

def register():
    bpy.utils.register_class(SvDxfLinDimsNode)

def unregister():
    bpy.utils.unregister_class(SvDxfLinDimsNode)

if __name__ == "__main__":
    register()