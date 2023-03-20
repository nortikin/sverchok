'''
in vers    v d=[[]] n=0
in edges   s d=[[]] n=0
in pols    s d=[[]] n=0
in areas   s d=[[]] n=0
in border  s d=[[]] n=0
in cutarea s d=0.1  n=2
'''

'''
The principle of operation -
    outside:
        define areas
        define boundaries
    inside:
        define the bordering polygons
        define the adjacent edges
    next:
        output of edge indexes
Принцип работы - 
    снаружи:
        определить площади
        определить границы
    снутри:
        определить граничащие полигоны
        определить граничащие рёбра
    далее:
        вывод индексов рёбер
'''


import bpy

self.make_operator('make')

    
def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='B A K E').cb_name='make'

def make(self, context):
    from mathutils import Vector as V
    def do_text(out_string):
        if not self.name in bpy.data.texts:
            bpy.data.texts.new(self.name)
        datablock = bpy.data.texts[self.name]
        datablock.clear()
        datablock.from_string(out_string)

    def main_border(vers,edges,pols,areas,border,cutarea):
        j = 0 # номер полигона короткого
        found = []
        used = []
        for pol,bor,ar in zip(pols,border,areas):
            if ar < cutarea and bor:
                fou = [i for i,po in enumerate(pols) if any([e in po for e in pol]) and po != pol]
                # i номер полигона большого
                for i in fou:
                #i = fou[0]
                    if i not in used:
                        used.append(i)
                        # v это искомые индексы вершин, нужны индексы рёбер
                        v = list(set(pols[i]) & set(pol))
                        if len(v) < 2: continue
                        # записать индексы рёбер, в которых совпало два индекса вершин
                        eds_ = [i for i,e in enumerate(edges) if len(set(v) & set(e))==2]
                        a = lambda x: (V(vers[edges[x][0]])-V(vers[edges[x][1]])).length
                        eds = sorted(eds_,key=a)
                        #print(v,eds_)
                        found.extend(eds)
            j += 1
        foundout = sorted(list(set(found)))
        #print(foundout[:5],len(foundout))
        #edges_out = []
        #for i,e in enumerate(edges):
        #    if i in foundout: edges_out.extend([True])
        #    else: edges_out.extend([False])
        #print([edges_out])
        return [foundout]

    if self.inputs['vers'].is_linked:
        vers = self.inputs['vers'].sv_get()
    else: return {'FINISHED'}
    if self.inputs['pols'].is_linked:
        pols = self.inputs['pols'].sv_get()
    else: return {'FINISHED'}
    if self.inputs['edges'].is_linked:
        edges = self.inputs['edges'].sv_get()
    else: return {'FINISHED'}
    if self.inputs['areas'].is_linked:
        areas = self.inputs['areas'].sv_get()
    else: return {'FINISHED'}
    if self.inputs['border'].is_linked:
        border = self.inputs['border'].sv_get()
    else: return {'FINISHED'}
    cutarea = self.inputs['cutarea'].sv_get()
    if type(cutarea[0][0]) == int:
        cutarea = cutarea[0]
    #print('\n'.join([str(i) for i in (vers[0][:5],edges[0][:5],pols[0][:5],areas[0][:5],border[0][:5],cutarea[0][0])]))
    edges_out = main_border(vers[0],edges[0],pols[0],areas[0],border[0],cutarea[0][0])
    do_text(str(edges_out))
    
    return {'FINISHED'}


