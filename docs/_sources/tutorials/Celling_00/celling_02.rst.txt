***************************************
Celling 02. Preparing geometry for work
***************************************

Subject
~~~~~~~

Importing initial shape (railing lines) for celling, checking of consistency

Workflow
--------

|image1|

1. **Importing DXF**:

    First of all we import DXF. Last 15 years using Blender I did not checked correctness of geometry. Reason for that was usage of blender, mostly for vizualisation. But now checked for production we found that Blender' DXF importer works as shit in circles case. Deviation can achive 200 mm, that is not suits any needs of production ever in the world. So, only way to avoid such dissapointments was to write short importer by myself for only circles to replace original bezier. On vertical it have deviations because of different rails levels. It required  little triangulation, that not calculated, but manually esteblished and checked on viewer index node.

    |image2|

    
    .. code-block:: python
       :caption: Код узла DXF импорта кругов.
       
            '''
            in resol    s d=128 n=2
            in path    FP d=[[]] n=0
            out vers    v d=[[]] n=0
            out edges   s d=[[]] n=0
            '''

            '''
            Принцип работы - 
                брать данные и в dxf
            '''


            import bpy



            def make():
                ''' ЗАГОТОВКА ДЛЯ БУДУЩИХ ОТДЕЛЬНЫХ УЗЛОВ
                    DXF ИМПОРТА.'''

                def import_dxf(fp,resolution):
                    import ezdxf
                    from ezdxf import colors
                    from ezdxf import units
                    from ezdxf.tools.standards import setup_dimstyle
                    from mathutils import Vector

                    dxf = ezdxf.readfile(fp)
                    lifehack = 50
                    ran = [i/lifehack for i in range(0,lifehack*360,int((lifehack*360)/resolution))]
                    #print(ran)
                    vers = []
                    edges = []
                    for a in dxf.query('Arc'):
                    #a = dxf.query('Arc')[1]
                        #arc = sverchok.utils.curve.primitives.SvCircle
                        #arc.to_nurbs()
                        vers_ = []
                        for i in  a.vertices(ran): # line 43 is 35 in make 24 in import
                            cen = a.dxf.center.xyz
                            vers_.append([j/1000 for j,k in zip(i,cen)])
                        vers.append(vers_)
                        edges.append([[i,i+1] for i in range(len(vers_)-1)])
                        edges[-1].append([len(vers_)-1,0])
                    return [vers], [edges]



                # MAKE DEFINITION BODY HERE #



                if self.inputs['path'].is_linked:
                    fpath_ = self.inputs['path'].sv_get()[0][0]
                resol_ = self.inputs['resol'].sv_get()[0][0]

                verts_, edges_ = import_dxf(fpath_,resol_)

                if self.outputs['vers'].is_linked:
                    self.outputs['vers'].sv_set(verts_)
                if self.outputs['edges'].is_linked:
                    self.outputs['edges'].sv_set(edges_)

            make()

2. **Surface**:

    Surface created from two lines with ordered vertices. I naturally reparametrized them only for better view, that is eye-checked quality. Separately created flat part of surface, it is the same as curved.

    |image3|


3. **Raycasting on surface**:

    Raycasting pattern on surface. For cropping pattern i used other countour - offseted from shape-definition curves. dimensions are defined by farthere offset for plates. So, offset for plates is half of 14 mm, 7 mm. That means, i needed to offset other 7 mm here.

    |image4|

4. **Dissolve**:

    Dissolve accures with list of edges. Manually iterate all 2500 edges. So, i created edges generator, that choose edges by plate area threshold and boundary analising. Output is flat list in texts, that i need to edit manually. So, need to finish at some stage and not return back for autogenerate list. That means, shape boundary and pattern need to be fixed by design. In practic it was several times changed. After that, i get text with text in node and dissolve it. Than check border elevations (heights) to manually esteblish correct surface shape.

    |image5|
    
    |image6|
    
    |image7|

    
    .. code-block:: python
       :caption: Код узла нахождения лишних рёбер.
       
            '''
            in vers    v d=[[]] n=0
            in edges   s d=[[]] n=0
            in pols    s d=[[]] n=0
            in areas   s d=[[]] n=0
            in border  s d=[[]] n=0
            in cutarea s d=0.1  n=2
            '''

            '''
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

    
    .. code-block:: python
       :caption: Результат полуавтоматического списка индексов рёбер.
       
            [[3, 7, 14, 21, 24, 30, 33, 37, 41, 43, 45, 48, 54, 57, 60, 63, 66, 70, 78, 82, 88, 95, 104, 106,108, 112, 115, 119, 126, 130, 134, 145, 149, 152, 156, 160, 164, 168, 172, 176, 180, 184, 188, 192, 196, 200, 204, 208, 212, 216, 220, 224, 228, 232, 236, 240, 244, 248, 252, 256, 260, 264, 268, 272, 276, 280, 284, 288, 292, 296, 301, 306, 310, 315, 321, 330, 333, 337, 341, 347, 351, 391, 400, 405, 415, 417, 423, 427, 529, 591, 599, 661, 684, 708, 710, 728, 730, 732, 752, 762, 765, 767, 771, 777, 788, 793, 795, 797, 799, 802,805, 808, 810, 814, 816, 818, 822, 826, 830, 834, 838, 842, 846, 850, 854, 858, 862, 866, 870, 874, 878, 882, 886, 890, 894, 898, 902, 906, 910, 914, 918, 922, 926, 930, 934, 938, 942, 946, 950, 957, 965, 969, 975, 981, 987, 996, 999, 1003, 1007, 1013, 1017, 1278, 1298, 1300, 1313, 1315, 1317, 1325, 1337, 1340, 1965, 1966]]


5. **Separate corner plates**:

    To avoid jumping plates' corners, happening far from original surface, i created part of triangulated plates. Defined by lines, snapped to projected pattern corners, i filtered plates by lines location, later that lines helped me to define left and right side of plates' triangles, because, farthere offset happened only to two sides. Here I need to say, that all plates are completely flat. So, flattaning happens here in step forward. To flatten triangulated plate I separated triangles, flatted and joined pairs after.

    |image8|

    |image9|


.. |image1| image:: https://github.com/nortikin/sverchok/assets/5783432/10a4fcef-1eb9-421a-8863-f5057b5e4f84
.. |image2| image:: https://github.com/nortikin/sverchok/assets/5783432/696ec148-69b8-4436-b506-c6eff419e582
.. |image3| image:: https://github.com/nortikin/sverchok/assets/5783432/4ee4f3e7-9cef-4eaa-9aec-13f9d442b579
.. |image4| image:: https://github.com/nortikin/sverchok/assets/5783432/e625e033-cece-4166-8a1d-1789bf4b343f
.. |image5| image:: https://github.com/nortikin/sverchok/assets/5783432/4dfe924a-fca8-4dc8-be28-0f749257a06d
.. |image6| image:: https://github.com/nortikin/sverchok/assets/5783432/289bc089-ec0e-4f56-b0fe-8e9a9445c988
.. |image7| image:: https://github.com/nortikin/sverchok/assets/5783432/a7aeca59-f8dc-4308-98d1-da1a6068af29
.. |image8| image:: https://github.com/nortikin/sverchok/assets/5783432/5e7bea86-a6a6-48a9-9294-24df20655781
.. |image9| image:: https://github.com/nortikin/sverchok/assets/5783432/2b4fde10-8bcf-458f-9683-64959ed12083