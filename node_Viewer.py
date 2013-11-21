import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
import Viewer_draw
from Viewer_draw import *
from util import *

cache_viewer_baker = {}

class SvObjBake(bpy.types.Operator):
    """Sverchok mesh baker"""
    bl_idname = "node.sverchok_mesh_baker"
    bl_label = "Sverchok mesh baker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global cache_viewer_baker
        if cache_viewer_baker['m'] and not cache_viewer_baker['v']:
            return {'CANCELLED'}
        vers = dataCorrect(cache_viewer_baker['v'])
        edg_pol = dataCorrect(cache_viewer_baker['ep'])
        if cache_viewer_baker['m']:
            matrixes = dataCorrect(cache_viewer_baker['m'])
        else:
            matrixes = []
            for i in range((len(vers))):
                matrixes.append(Matrix())
        
        self.makeobjects(vers, edg_pol, matrixes)
        cache_viewer_baker = {}
        return {'FINISHED'}
    
    def makeobjects(self, vers, edg_pol, mats):
        # inception
        # fht = предохранитель от перебора рёбер и полигонов.
        fht = []
        if len(edg_pol[0][0]) == 2:
            pols = []
            for edgs in edg_pol:
                maxi = max(max(a) for a in edgs)
                fht.append(maxi)
                print (maxi)
        elif len(edg_pol[0][0]) > 2:
            edgs = []
            for pols in edg_pol:
                maxi = max(max(a) for a in pols)
                fht.append(maxi)
                print (maxi)
        #print (fht)
        vertices = Vector_generate(vers)
        matrixes = Matrix_generate(mats)
        #print('mats' + str(matrixes))
        objects = {}
        fhtagn = []
        for u, f in enumerate(fht):
            fhtagn.append(min(len(vertices[u]), fht[u]))
        #lenmesh = len(vertices) - 1
        #print ('запекание вершин ', vertices, " матрицы запекашка ", matrixes, " полиглоты ", edg_pol)
        #print (matrixes)
        for i, m in enumerate(matrixes):
            k = i
            if i > len(matrixes) - 1:
                v = vertices[-1]
            else:
                v = vertices[k]
            #print (fhtagn, len(v)-1)
            if (len(v)-1) < fhtagn[k]:
                continue
            # возможно такая сложность не нужна, но пусть лежит тут. Удалять лишние точки не обязательно.
            elif fhtagn[k] < (len(v)-1):
                nonneed = (len(v)-1) - fhtagn[k]
                for q in range(nonneed):
                    v.pop((fhtagn[k]+1))
                #print (fhtagn[k], (len(v)-1))
            if edgs:
                e = edg_pol[k]
            else:
                e = []
            if pols:
                p = edg_pol[k]
            else:
                p = []
            objects[str(i)] = self.makemesh(i,v,e,p,m)
        for ite in objects.values():
            me = ite[1]
            ob = ite[0]
            calcedg = True
            if edgs: calcedg = False
            me.update(calc_edges=calcedg)
            bpy.context.scene.objects.link(ob)
            
    def makemesh(self,i,v,e,p,m):
        name = 'Sv_' + str(i)
        me = bpy.data.meshes.new(name)
        me.from_pydata(v, e, p)
        ob = bpy.data.objects.new(name, me)
        ob.matrix_world = m
        ob.show_name = False
        ob.hide_select = False
        #print ([ob,me])
        #print (ob.name + ' baked')
        return [ob,me]

class ViewerNode(Node, SverchCustomTreeNode):
    ''' ViewerNode '''
    bl_idname = 'ViewerNode'
    bl_label = 'Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Vertex_show = bpy.props.BoolProperty(name='Vertex_show', description='Show or not vertices', default=True)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        layout.operator('node.sverchok_mesh_baker', text='bake')
        layout.prop(self, "Vertex_show", text="Vertex show")
        
    def update(self):
        global cache_viewer_baker
        cache_viewer_baker['v'] = []
        cache_viewer_baker['ep'] = []
        cache_viewer_baker['m'] = []
        if self.inputs['vertices'].links or self.inputs['matrix'].links:
            callback_disable(self.name)
            if len(self.inputs['vertices'].links)>0:
                if not self.inputs['vertices'].node.socket_value_update:
                    self.inputs['vertices'].node.update()
                if self.inputs['vertices'].links[0].from_socket.VerticesProperty:
                    propv = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
                    cache_viewer_baker['v'] = dataCorrect(propv)
            else:
                cache_viewer_baker['v'] = []
                            
            if 'edg_pol' in self.inputs and self.inputs['edg_pol'].links and len(self.inputs['edg_pol'].links)>0:
                if not self.inputs['edg_pol'].node.socket_value_update:
                    self.inputs['edg_pol'].node.update()
                if self.inputs['edg_pol'].links[0].from_socket.StringsProperty:
                    prope = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
                    cache_viewer_baker['ep'] = dataCorrect(prope)
                    #print (prope)
            else:
                cache_viewer_baker['ep'] = []
                    
            if 'matrix' in self.inputs and self.inputs['matrix'].links and len(self.inputs['matrix'].links)>0:
                if not self.inputs['matrix'].node.socket_value_update:
                    self.inputs['matrix'].node.update()
                if self.inputs['matrix'].links[0].from_socket.MatrixProperty:
                    propm = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
                    cache_viewer_baker['m'] = dataCorrect(propm)
            else:
                cache_viewer_baker['m'] = []
        if cache_viewer_baker['v'] or cache_viewer_baker['m']:
            callback_enable(self.name, cache_viewer_baker['v'], cache_viewer_baker['ep'], cache_viewer_baker['m'], self.Vertex_show)
            #print ('отражения вершин ',len(cache_viewer_baker['v']), " рёбёры ", len(cache_viewer_baker['ep']), "матрицы",len(cache_viewer_baker['m']))
        if not self.inputs['vertices'].links and not self.inputs['matrix'].links:
            callback_disable(self.name)
            cache_viewer_baker = {}
    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ViewerNode)
    bpy.utils.register_class(SvObjBake)
    
def unregister():
    bpy.utils.unregister_class(SvObjBake)
    bpy.utils.unregister_class(ViewerNode)
    

if __name__ == "__main__":
    register()