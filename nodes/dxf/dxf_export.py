import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.dependencies import ezdxf
if ezdxf != None:
    import ezdxf
    from ezdxf.math import Vec3
    from ezdxf import colors
    from ezdxf import units
    from ezdxf.tools.standards import setup_dimstyle
from mathutils import Vector
from sverchok.data_structure import get_data_nesting_level, ensure_nesting_level
from sverchok.utils.dxf import LWdict, lineweights, linetypes



class SvDxfExportNode(SverchCustomTreeNode, bpy.types.Node):
    bl_idname = 'SvDxfExportNode'
    bl_label = 'DXF Export'
    bl_icon = 'EXPORT'
    bl_category = 'DXF'
    sv_dependencies = {'ezdxf'}

    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Path to save the DXF file",
        default="",
        subtype='FILE_PATH',
        update=updateNode
    )
    
    scale: bpy.props.FloatProperty(default=1.0,name='scale')

    text_scale: bpy.props.FloatProperty(default=1.0,name='text_scale')

    def sv_init(self, context):
        '''
        self.inputs.new('SvVerticesSocket', 'verts')
        self.inputs.new('SvStringsSocket', 'edges')
        self.inputs.new('SvStringsSocket', 'pols')
        self.inputs.new('SvVerticesSocket', 'Tvers')
        self.inputs.new('SvStringsSocket', 'Ttext')
        self.inputs.new('SvStringsSocket', 'FaceData')
        self.inputs.new('SvStringsSocket', 'FDDescr')
        self.inputs.new('SvStringsSocket', 'INFO')
        self.inputs.new('SvVerticesSocket', 'dim1')
        self.inputs.new('SvVerticesSocket', 'dim2')
        self.inputs.new('SvVerticesSocket', 'adim')
        self.inputs.new('SvStringsSocket', 'scal').prop_name = 'scale'
        self.inputs.new('SvStringsSocket', 'leader')
        self.inputs.new('SvVerticesSocket', 'vleader')
        self.inputs.new('SvStringsSocket', 't_scal').prop_name = 'text_scale'
        '''
        self.inputs.new('SvFilePathSocket', 'path').prop_name = 'file_path'
        self.inputs.new('SvSvgSocket', 'dxf')

    def draw_buttons(self, context, layout):
        layout.operator("node.dxf_export", text="Export DXF")
        layout.prop(self, "scale", expand=False)
        layout.prop(self, "text_scale", expand=False)

    def process(self):
        pass  # Данные будут обрабатываться в операторе

    def DXF_SAVER(self, context):
        ''' ЗАГОТОВКА ДЛЯ БУДУЩИХ ОТДЕЛЬНЫХ УЗЛОВ
            DXF ЭКСПОРТА. УСТРОЙСТВО ПО АНАЛОГИИ
            С SVG УЗЛАМИ '''

        def triangl(vertices,edges,faces):
            ''' WIP
                triangulation for mesh represantation
                with metadata vectorized for triangles '''
            from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
            import bmesh
            bm = bmesh_from_pydata(vertices, edges, faces, markup_face_data=True, normal_update=True)
            res = bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
            new_vertices, new_edges, new_faces = pydata_from_bmesh(res)
            bm.free()
            return  new_vertices, new_edges, new_faces

        def vertices_draw(v,scal,lvers,msp):
            ''' vertices as points draw '''
            #for x,y in [(0,10),(10,10),(10,0),(0,0)]:
            print('VERS!!')
            for ob in v:
                vers = []
                for ver in ob:
                    #vers.append(ver)
                    msp.add_point([i*scal for i in ver], dxfattribs={"layer": lvers})

        def hatches_draw(points, scal, lhatch, msp):
            for points_ in points:
                vers,col,patt,sc = points_.vers, points_.color,points_.pattern,points_.scale
                color_int = points_.color_int
                if color_int < 1:
                    col = tuple([int(i*255) for i in col[:3]])
                    col = ezdxf.colors.rgb2int(col)
                else:
                    col = color_int

                ht = msp.add_hatch(color=col, dxfattribs={"layer": lhatch})
                ht.set_pattern_fill(patt, scale=sc)
                ht.transparency = 0.5
                path = ht.paths.add_polyline_path(
                    vers,
                    is_closed=True,
                    flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL,
                )

        def polygons_draw(points, scal, lpols, msp):#(p,v,d1,d2,scal,lpols,msp):
            ''' draw simple polyline polygon '''
            print('POLS!!')
            for points_ in points:
                vers,col = points_.vers, points_.color
                lw,lt = points_.lineweight, points_.linetype
                color_int = points_.color_int
                if color_int < 1:
                    col = tuple([int(i*255) for i in col[:3]])
                    print('!!!',col)
                    col = ezdxf.colors.rgb2int(col)
                    pl = msp.add_polyline3d(points_.vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'true_color': col}, close=True)
                else:
                    pl = msp.add_polyline3d(points_.vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'color': color_int}, close=True)
                #pf = msp.add_polyface()
                #pf.append_face(points, dxfattribs={"layer": lpols})
                #pm = msp.add_polymesh()
                #pm.append_vertices(points, dxfattribs={"layer": lpols})
            '''
            (1070, data),  # 16bit
            (1040, 0.0), # float
            (1071, 1_048_576),  # 32bit
            # points and vectors
            (1010, (10, 20, 30)),
            (1011, (11, 21, 31)),
            (1012, (12, 22, 32)),
            (1013, (13, 23, 33)),
            # scaled distances and factors
            (1041, 10),
            (1042, 10),
            '''
        def polygondance_draw(p,v,d1,d2,scal,lpols,msp,APPID):
            ''' draw polygons if there is metadata d1 d2
                needed triangulation for mesh represantation
                with metadata vectorized for triangles '''

            from sverchok.data_structure import match_long_repeat as mlr
            from mathutils import Vector
            print('POLS!!')
            mlr([p,d1])
            for obp,obv,d in zip(p,v,d1):
                #obv,q,obp = triangl(obv,[],obp)
                mlr([obp,d])
                for po,data in zip(obp,d):
                    points = []
                    for ver in po:
                        if type(obv[ver]) == Vector: vr = (scal*obv[ver]).to_tuple()
                        else: vr = tuple([i*scal for i in obv[ver]])
                        points.append(vr)
                    pl = msp.add_polyline3d(points, dxfattribs={"layer": lpols},close=True)
                    pl.set_xdata(APPID, [(1000, str(d2[0][0])),(1000, str(data))])
                    #pf = msp.add_polyface()
                    #pf.append_vertices(points, dxfattribs={"layer": lpols})
                    #pf.append_face(points, dxfattribs={"layer": lpols})
                    #pf.set_xdata(APPID, [(1000, str(d2[0][0])),(1000, str(d[0]))])
                    #ent = ezdxf.entities.Mesh()
                    #for p in points:
                    #    ent.vertices.append(p)
                    #ppm = msp.add_entity(ent)
                    #ppm.append_vertices(points, dxfattribs={"layer": lpols})
                    #ppm.set_xdata(APPID, [(1000, str(d2[0][0])),(1000, str(data))])

        def edges_draw(points,scal,ledgs,msp):
            ''' edges as simple lines '''
            print('EDGES!!')

            for points_ in points:
                vers,col = points_.vers, points_.color
                lw,lt = points_.lineweight, points_.linetype
                v1,v2 = vers
                color_int = points_.color_int
                if color_int < 1:
                    col = tuple([int(i*255) for i in col[:3]])
                    col = ezdxf.colors.rgb2int(col)
                    ed = msp.add_line(v1,v2, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'true_color': col})
                else:
                    ed = msp.add_line(v1,v2, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'color': color_int})

        def text_draw(tv,tt,scal,ltext,msp,t_scal):
            ''' draw text '''
            from ezdxf.enums import TextEntityAlignment
            print('TEXT!!')
            for obtv, obtt in zip(tv,tt):
                for tver, ttext in zip(obtv,obtt):
                    tver = [i*scal for i in tver]
                    msp.add_text(
                    ttext, height=scal*t_scal,#0.05,
                    dxfattribs={
                        "layer": ltext,
                        "style": "OpenSans"
                    }).set_placement(tver, align=TextEntityAlignment.CENTER)

        def dimensions_draw(points,scal,ldims,msp):
            print('LINEAR DIMS!!')
            for points_ in points:
                vers,col = points_.vers, points_.color
                lw,lt = points_.lineweight, points_.linetype
                v1,v2 = vers
                t_scal = points_.text_scale
                print('LINEAR DIMS!!', t_scal)

                dim = msp.add_aligned_dim(p1=v1,p2=v2,  #p1=[i*scal for i in v1[:2]], p2=[i*scal for i in v2[:2]],\
                    distance=0.5, dimstyle='EZDXF1',dxfattribs={"layer": ldims},
                    override={"dimtxt": t_scal}
                )
                #dim.render()

        def angular_dimensions_draw(ang,scal,ldims,msp,t_scal):
            from mathutils import Vector
            print('ANGULAR DIMS!!')
            for a1,a2,a3 in zip(*ang):
                for ang1,ang2,ang3 in zip(a1,a2,a3):
                    if scal != 1.0:
                        bas = list(Vector(ang1)*scal+((Vector(ang3)*scal-Vector(ang1)*scal)/2))
                        ang1_ = [i*scal for i in ang1]
                        ang2_ = [i*scal for i in ang2]
                        ang3_ = [i*scal for i in ang3]
                        dim = msp.add_angular_dim_3p(base=bas, center=ang2_, p1=ang1_, p2=ang3_, \
                                    override={"dimtad": 1,"dimtxt": t_scal}, \
                                    dimstyle='EZDXF1',dxfattribs={"layer": ldims})
                    else:
                        bas = list(Vector(ang1)+((Vector(ang3)-Vector(ang1))/2))
                        dim = msp.add_angular_dim_3p(base=bas, center=ang2, p1=ang1, p2=ang3, \
                                    override={"dimtad": 1,"dimtxt": t_scal}, \
                                    dimstyle='EZDXF1',dxfattribs={"layer": ldims})
                    #dim.render()

        def get_values(diction):
            data = []
            for d in diction.values():
                for i in d.values():
                    data.append(i)
            return data

        def leader_draw(leader,vleader,scal,llidr,msp):
            from ezdxf.math import Vec2
            #from ezdxf.entities import mleader
            print('LEADERS!!')
            for lvo1,lvo2,leadobj in zip(vleader[0],vleader[1],leader):
                data = get_values(leadobj)
                for lt,lv1,lv2 in zip(data,lvo1,lvo2):
                    #msp.add_leader([lv1,lv2], dimstyle='EZDXF1', dxfattribs={"layer": llidr})
                    #print(lt,lv1,lv2)
                    ml_builder = msp.add_multileader_mtext("EZDXF2")
                    ml_builder.quick_leader(
                        lt,
                        target=Vec2(lv1)*scal,
                        segment1=Vec2(lv2)*scal-Vec2(lv1)*scal
                    #    connection_type=mleader.VerticalConnection.center_overline,
                    )#.render()
                    #ml_builder.text_attachment_point = 2
                    #Vec2.from_deg_angle(angle, 14),
                    #dxfattribs={"layer": llidr}

        '''
        def angl(d1,d2):
            from math import sqrt, acos, degrees
            ax, ay, bx, by = d1[0],d1[1],d2[0],d2[1]
            ma = sqrt(ax * ax + ay * ay)
            mb = sqrt(bx * bx + by * by)
            sc = ax * bx + ay * by
            res = acos(sc / ma / mb)
            return 90-degrees(res)
        '''

        # export main definition
        def export(fp,dxf,scal=1.0,t_scal=1.0):


            DIM_TEXT_STYLE = ezdxf.options.default_dimension_text_style
            # Create a new DXF document.
            doc = ezdxf.new(dxfversion="R2010",setup=True)
            doc.units = units.M
            # 25 строка
            doc.header['$INSUNITS'] = units.M
            #create a new dimstyle
            glo = scal  #scal*t_scal
            hai = t_scal   #scal/glo
            formt = f'EZ_M_{glo}_H{hai}_MM'
            '''
            Example: `fmt` = 'EZ_M_100_H25_CM'
            1. '<EZ>_M_100_H25_CM': arbitrary prefix
            2. 'EZ_<M>_100_H25_CM': defines the drawing unit, valid values are 'M', 'DM', 'CM', 'MM'
            3. 'EZ_M_<100>_H25_CM': defines the scale of the drawing, '100' is for 1:100
            4. 'EZ_M_100_<H25>_CM': defines the text height in mm in paper space times 10, 'H25' is 2.5mm
            5. 'EZ_M_100_H25_<CM>': defines the units for the measurement text, valid values are 'M', 'DM', 'CM', 'MM'
            '''
            setup_dimstyle(doc,
                           name='EZDXF1',
                           fmt=formt,
                           blk=ezdxf.ARROWS.architectural_tick,#closed_filled,
                           style=DIM_TEXT_STYLE,
                           )

            dimstyle = doc.dimstyles.get('EZDXF1')
            #keep dim line with text        
            #dimstyle.dxf.dimtmove=0
            # multyleader
            mleaderstyle = doc.mleader_styles.new("EZDXF2") #duplicate_entry("Standard","EZDXF2")
            mleaderstyle.set_mtext_style("OpenSans")
            mleaderstyle.dxf.char_height = t_scal*scal  # set the default char height of MTEXT
            # Create new table entries (layers, linetypes, text styles, ...).
            ltext = "SVERCHOK_TEXT"
            lvers = "SVERCHOK_VERS"
            ledgs = "SVERCHOK_EDGES"
            #ledg1 = "SVERCHOK_EDGES0.1"
            #ledg3 = "SVERCHOK_EDGES0.3"
            #ledg6 = "SVERCHOK_EDGES0.6"
            lpols = "SVERCHOK_POLYGONS"
            ldims = "SVERCHOK_DIMENTIONS"
            llidr = "SVERCHOK_LEADERS"
            lhatc = "SVERCHOK_HATCHES"

            doc.layers.add(ltext, color=colors.MAGENTA)
            doc.layers.add(lvers, color=colors.CYAN)
            doc.layers.add(ledgs, color=colors.YELLOW)
            #doc.layers.add(ledg1, color=colors.BLUE, lineweight=9)
            #doc.layers.add(ledg3, color=colors.GRAY, lineweight=30)
            #doc.layers.add(ledg6, color=colors.LIGHT_GRAY, lineweight=60)
            doc.layers.add(lpols, color=colors.WHITE)
            doc.layers.add(ldims, color=colors.GREEN)
            doc.layers.add(llidr, color=colors.CYAN)
            doc.layers.add(lhatc, color=colors.WHITE)
            '''
            doc.layers.add(ltext)
            doc.layers.add(lvers)
            doc.layers.add(ledgs)
            #doc.layers.add(ledg1)
            #doc.layers.add(ledg3)
            #doc.layers.add(ledg6)
            doc.layers.add(lpols)
            doc.layers.add(ldims)
            doc.layers.add(llidr)
            '''

            # DXF entities (LINE, TEXT, ...) reside in a layout (modelspace, 
            # paperspace layout or block definition).  
            msp = doc.modelspace()
            if info:
                print('INFO!!')
                for d in info[0].items():
                    doc.header.custom_vars.append(d[0], d[1]['Value'])

            APPID = "Sverchok"
            doc.appids.add(APPID)
            doc.header["$LWDISPLAY"] = 1
            # Add entities to a layout by factory methods: layout.add_...() 

            for data in dxf:
                #print(data)
                #print("Тип данных DXF",data[0].__repr__())
                if data[0].__repr__() == '<DXF Pols>':
                    polygons_draw(data,scal,lpols,msp) #(p,v,d1,d2,scal,lpols,msp)
                if data[0].__repr__() == '<DXF Lines>':
                    edges_draw(data,scal,ledgs,msp)
                if data[0].__repr__() == '<DXF Hatch>':
                    hatches_draw(data,scal,lhatc,msp)
                if data[0].__repr__() == '<DXF LinDims>':
                    dimensions_draw(data,scal,ldims,msp)

            '''
            if e:
                edges_draw(e,v,scal,ledgs,msp)#,ledg1,ledg3,ledg6)
            elif p and d1:
                polygondance_draw(p,v,d1,d2,scal,lpols,msp,APPID)
            elif p:
                polygons_draw(p,v,d1,d2,scal,lpols,msp)
            elif v:
                vertices_draw(v,scal,lvers,msp)
            if tv and tt:
                text_draw(tv,tt,scal,ltext,msp,t_scal)
            if dim1 and dim2:
                dimensions_draw(dim1,dim2,scal,ldims,msp,t_scal)
            if angular:
                angular_dimensions_draw(angular,scal,ldims,msp,t_scal)
            if vl and ll:
                leader_draw(ll,vl,scal,llidr,msp)
            '''
            # Save the DXF document.
            doc.saveas(fp[0][0])


        # MAKE DEFINITION BODY HERE #
        
        vers_, edges_, pols_, Tvers_, Ttext_, fpath_ = [],[],[],[],[],[]
        d1_, d2_, info, dim1_, dim2_,adim1_ = [],[],[],[],[],[]
        leader_, vleader_, dxf_ = [],[],[]

        '''
        if self.inputs['verts'].is_linked:
            vers_ = self.inputs['verts'].sv_get()
        #else: return {'FINISHED'}
        if self.inputs['edges'].is_linked:
            edges_ = self.inputs['edges'].sv_get()
        if self.inputs['pols'].is_linked:
            pols_ = self.inputs['pols'].sv_get()
        if self.inputs['Tvers'].is_linked:
            Tvers_ = self.inputs['Tvers'].sv_get()
        if self.inputs['Ttext'].is_linked:
            Ttext_ = self.inputs['Ttext'].sv_get()
        #else: return {'FINISHED'}
        if self.inputs['FaceData'].is_linked:
            d1_ = self.inputs['FaceData'].sv_get()
        if self.inputs['FDDescr'].is_linked:
            d2_ = self.inputs['FDDescr'].sv_get()
        if self.inputs['INFO'].is_linked:
            info = self.inputs['INFO'].sv_get()
        if self.inputs['dim1'].is_linked:
            dim1_ = self.inputs['dim1'].sv_get()
        if self.inputs['dim2'].is_linked:
            dim2_ = self.inputs['dim2'].sv_get()
        if self.inputs['adim'].is_linked:
            adim1_ = self.inputs['adim'].sv_get()
        if self.inputs['leader'].is_linked:
            leader_ = self.inputs['leader'].sv_get()
        if self.inputs['vleader'].is_linked:
            vleader_ = self.inputs['vleader'].sv_get()
            '''
        if self.inputs['path'].is_linked:
            fpath_ = self.inputs['path'].sv_get()
        if self.inputs['dxf'].is_linked:
            dxf_ = ensure_nesting_level(self.inputs['dxf'].sv_get(),2)

        #scal_ = self.inputs['scal'].sv_get()[0][0]
        #t_scal_ = self.inputs['t_scal'].sv_get()[0][0]
        #export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info,dim1_,dim2_,adim1_,scal_,vleader_,leader_,t_scal_,dxf_)
        export(fpath_,dxf_,scal=self.scale,t_scal=self.text_scale)




class DXFExportOperator(bpy.types.Operator):
    bl_idname = "node.dxf_export"
    bl_label = "Export DXF"

    def execute(self, context):
        node = context.node
        inputs = node.inputs

        file_path = inputs['path'].sv_get()[0][0]

        if not file_path:
            self.report({'ERROR'}, "File path not specified!")
            return {'CANCELLED'}

        try:
            node.DXF_SAVER(context)
            #node.create_dxf(**data)
            self.report({'INFO'}, f"DXF saved to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SvDxfExportNode)
    bpy.utils.register_class(DXFExportOperator)

def unregister():
    bpy.utils.unregister_class(SvDxfExportNode)
    bpy.utils.unregister_class(DXFExportOperator)

if __name__ == "__main__":
    register()