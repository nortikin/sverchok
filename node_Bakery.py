import bpy
from node_s import *
from util import *

class BakeryNode(Node, SverchCustomTreeNode):
    ''' Bakery node to bake geometry every time '''
    bl_idname = 'BakeryNode'
    bl_label = 'Bakery'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    activate = bpy.props.BoolProperty(name='Show', description='Activate node?', default=True,update=updateNode)
    
    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Show")
        pass
        
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        
    def update(self):
        if self.inputs['vertices'].links and self.inputs['edg_pol'].links and self.activate:
            if 'vertices' in self.inputs and self.inputs['vertices'].links and \
                    type(self.inputs['vertices'].links[0].from_socket) == VerticesSocket:
                propv = SvGetSocketAnyType(self, self.inputs['vertices'])
                vertices = dataCorrect(propv, nominal_dept=2)
            else:
                vertices = []
                            
            if 'edg_pol' in self.inputs and self.inputs['edg_pol'].links and \
                    type(self.inputs['edg_pol'].links[0].from_socket) == StringsSocket:
                prope = SvGetSocketAnyType(self, self.inputs['edg_pol'])
                edges = dataCorrect(prope)
            else:
                edges = []
                    
            if 'matrix' in self.inputs and self.inputs['matrix'].links and \
                    type(self.inputs['matrix'].links[0].from_socket) == MatrixSocket:
                propm = SvGetSocketAnyType(self, self.inputs['matrix'])
                matrices = dataCorrect(propm)
            else:
                matrices = []
                if vertices and edges:
                    for i in vertices:
                        matrices.append(Matrix())
            
            if vertices and edges:
                self.makeobjects(vertices, edges, matrices)
            else:
                self.makeobjects([[[0,0,0],[1,0,0],[0.5,1,0]]], [[[1,2,0]]], matrixes)
        else:
            for obj in bpy.context.scene.objects:
                nam = 'Sv_' + self.name
                if nam in obj.name:
                    bpy.context.scene.objects[obj.name].select = True
                    bpy.ops.object.delete(use_global=False)
    
    def makeobjects(self, vers, edg_pol, mats):
        # fht = предохранитель от перебора рёбер и полигонов.
        fht = []
        if len(edg_pol[0][0]) == 2:
            pols = []
            for edgs in edg_pol:
                maxi = max(max(a) for a in edgs)
                fht.append(maxi)
        elif len(edg_pol[0][0]) > 2:
            edgs = []
            for pols in edg_pol:
                maxi = max(max(a) for a in pols)
                fht.append(maxi)
        vertices = Vector_generate(vers)
        matrixes = Matrix_generate(mats)
        objects = {}
        fhtagn = []
        for u, f in enumerate(fht):
            fhtagn.append(min(len(vertices[u]), fht[u]))
        #lenmesh = len(vertices) - 1
        
        # delete previous objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            nam = 'Sv_' + self.name
            if nam in obj.name:
                bpy.context.scene.objects[obj.name].select = True
                bpy.ops.object.delete(use_global=False)

        for i, m in enumerate(matrixes):
            k = i
            lenver = len(vertices) - 1
            if i > lenver:
                v = vertices[-1]
                k = lenver
            else:
                v = vertices[k]
            if (len(v)-1) < fhtagn[k]:
                continue
            # возможно такая сложность не нужна, но пусть лежит тут. Удалять лишние точки не обязательно.
            elif fhtagn[k] < (len(v)-1):
                nonneed = (len(v)-1) - fhtagn[k]
                for q in range(nonneed):
                    v.pop((fhtagn[k]+1))

            e = edg_pol[k] if edgs else []
            p = edg_pol[k] if pols else []
            
            objects[str(i)] = self.makemesh(i,v,e,p,m)
            
        for ite in objects.values():
            me = ite[1]
            ob = ite[0]
            calcedg = True
            if edgs: calcedg = False
            me.update(calc_edges=calcedg)
            bpy.context.scene.objects.link(ob)
            
    def makemesh(self,i,v,e,p,m):
        name = 'Sv_' + self.name + str(i)
        me = bpy.data.meshes.new(name)
        me.from_pydata(v, e, p)
        ob = bpy.data.objects.new(name, me)
        ob.matrix_world = m
        ob.show_name = False
        ob.hide_select = False
        return [ob,me]
                
def register():
    bpy.utils.register_class(BakeryNode)
    
def unregister():
    bpy.utils.unregister_class(BakeryNode)


if __name__ == "__main__":
    register()
