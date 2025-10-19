import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, dataCorrect_np
from mathutils import Vector
from sverchok.utils.dxf import LWdict, lineweights, linetypes, patterns


class DxfHatch:
    def __repr__(self):
        return "<DXF Hatch>"

    def __init__(self, vers, color, metadata, pattern, scale, node, color_int):
        self.vers = vers
        self.node = node
        self.color = color
        self.color_int = color_int
        self.pattern = pattern
        self.scale = scale
        self.metadata = metadata

    def draw(self):
        return self.vers


class SvDxfHatchNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfHatchNode'
    bl_label = 'DXF Hatches'
    bl_icon = 'EXPORT'
    sv_icon = 'SV_PATTERN_SVG'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    hatch_scale: bpy.props.FloatProperty(default=0.5,name='hatch_scale', description='Hatch can be too dense or too rear, carefully')

    metadata: bpy.props.StringProperty(default='',name='metadata')

    color_int: bpy.props.IntProperty(default=-4, min=-4, max=255,name='color', description='-4 is ignore, -3')

    unit_color: bpy.props.FloatVectorProperty(
        update=updateNode, name='', default=(.3, .3, .2, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    pattern: bpy.props.EnumProperty(
        name="pattern", description="pattern", default='ANSI31', items=patterns, update=updateNode)

    linetype: bpy.props.EnumProperty(
        name="linetype", description="linetypes", default='CONTINUOUS', items=linetypes, update=updateNode)

    lineweight: bpy.props.EnumProperty(
        name="lineweight", description="lineweight", default='0.00', items=lineweights, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'pols')
        self.inputs.new('SvColorSocket', 'color').custom_draw = 'draw_color_socket'
        self.inputs.new('SvTextSocket', 'metadata').prop_name='metadata'
        self.outputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        #layout.prop(self, "linetype", expand=False)
        #layout.prop(self, "lineweight", expand=False)
        layout.prop(self, "pattern", expand=False)
        layout.prop(self, "hatch_scale")
        layout.prop(self, "color_int", expand=False)

    def draw_color_socket(self, socket, context, layout):
        if not socket.is_linked:
            layout.prop(self, 'unit_color', text="")
        else:
            layout.label(text=socket.name+ '. ' + str(socket.objects_number))

    def process(self):
        if self.outputs['dxf'].is_linked and self.inputs['verts'].is_linked and self.inputs['pols'].is_linked:
            # All starts with dxf socket
            vers_ = self.inputs['verts'].sv_get()
            pols_ = self.inputs['pols'].sv_get()
            #if self.inputs['color'].is_linked:
            # color [[ (1,0,1) ]]
            if self.inputs['color'].is_linked:
                cols_ = self.inputs['color'].sv_get(deepcopy=False)
                cols_ = dataCorrect_np(cols_)[0][0]
            else:
                cols_ = self.unit_color[:]
            color_int = self.color_int
            #if self.inputs['metadata'].is_linked:
            # It is any text [['text']]
            meta_ = self.inputs['metadata'].sv_get()
            dxf = []
            # not match long repeate because we can use several nodes 
            # and multipliying mesh with colors absurdic, except meta
            # lw,lt - lineweight, linetype
            lw = LWdict[self.lineweight]
            lt = self.linetype
            pt = self.pattern
            sc = self.hatch_scale
            #print('$%#@$%#%#%#',sc)
            for obv,obp,met in zip_long_repeat(vers_,pols_,meta_):
                # объекты
                for po, me in zip_long_repeat(obp,met):
                    # целый полигон [0,1,2,3]
                    points = []
                    for ver in po:
                        # индексы вершин полигона вытаскивают точки
                        vr = obv[ver]
                        if type(vr) == Vector: vr = vr.to_tuple()
                        points.append(vr)
                    # каждый полигон это отдельный экземпляр
                    pols = DxfHatch(points,cols_,me,pt,sc,self,color_int)
                    dxf.append(pols)
            self.outputs['dxf'].sv_set([dxf])

    def sv_update(self):
        if not ("verts" in self.inputs):
            return

def register():
    bpy.utils.register_class(SvDxfHatchNode)

def unregister():
    bpy.utils.unregister_class(SvDxfHatchNode)

if __name__ == "__main__":
    register()