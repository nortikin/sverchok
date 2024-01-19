'''
in vers    v d=[[]] n=0
in edges   s d=[[]] n=0
in pols    s d=[[]] n=0
in Tvers   v d=[[]] n=0
in Ttext   s d=[[]] n=0
in FaceData   s d=[[]] n=0
in FDDescr   s d=[[]] n=0
in path    FP d=[[]] n=0
in INFO    s d=[[]] n=0
in dim1    v d=[[]] n=0
in dim2    v d=[[]] n=0
in adim  v d=[[]] n=0
in scal    s d=1 n=2
in leader  s d=[[]] n=0
in vleader v d=[[]] n=0
in t_scal    s d=0.25 n=2
'''

'''
Принцип работы - 
    брать данные и в dxf
'''


import bpy


self.make_operator('make')

    
def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='B A K E').cb_name='make'



def make(self, context):
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

    def polygons_draw(p,v,d1,d2,scal,lpols,msp):
        ''' draw simple polyline polygon '''
        from mathutils import Vector
        print('POLS!!')
        for obp,obv in zip(p,v):
            for po in obp:
                points = []
                for ver in po:
                    if type(obv[ver]) == Vector: vr = (scal*obv[ver]).to_tuple()
                    else: vr = [i*scal for i in obv[ver]]
                    points.append(vr)
                pl = msp.add_polyline3d(points, dxfattribs={"layer": lpols},close=True)
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

    def edges_draw(e,v,scal,ledgs,msp):
        ''' edges as simple lines '''
        print('EDGES!!')
        if get_data_nesting_level(e) > 3:
            lays = [ledg1,ledg3,ledg6]
            for ik in range(len(e)):
                for obe,obv in zip(e[ik],v):
                    edgs = []
                    for ed in obe:
                        msp.add_line([i*scal for i in obv[ed[0]]],[i*scal for i in obv[ed[1]]], dxfattribs={"layer": lays[ik], "lineweight": -1})
        else:
            for obe,obv in zip(e,v):
                edgs = []
                for ed in obe:
                    msp.add_line([i*scal for i in obv[ed[0]]],[i*scal for i in obv[ed[1]]], dxfattribs={"layer": ledgs})

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

    def dimensions_draw(dim1,dim2,scal,ldims,msp,t_scal):
        print('LINEAR DIMS!!')
        for obd1,obd2 in zip(dim1,dim2):
            for d1,d2 in zip(obd1,obd2):
                dim = msp.add_aligned_dim(p1=[i*scal for i in d1[:2]], p2=[i*scal for i in d2[:2]],\
                                distance=0.5*scal, dimstyle='EZDXF1',dxfattribs={"layer": ldims},\
                                override={"dimtxt": t_scal})
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
    def export(v,e,p,tv,tt,fp,d1,d2,info,dim1,dim2,angular,scal,vl,ll,t_scal):
        import ezdxf
        from ezdxf import colors
        from ezdxf import units
        from ezdxf.tools.standards import setup_dimstyle
        from mathutils import Vector
        from sverchok.data_structure import get_data_nesting_level

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
        ledg1 = "SVERCHOK_EDGES0.1"
        ledg3 = "SVERCHOK_EDGES0.3"
        ledg6 = "SVERCHOK_EDGES0.6"
        lpols = "SVERCHOK_POLYGONS"
        ldims = "SVERCHOK_DIMENTIONS"
        llidr = "SVERCHOK_LEADERS"
        doc.layers.add(ltext, color=colors.MAGENTA)
        doc.layers.add(lvers, color=colors.CYAN)
        doc.layers.add(ledgs, color=colors.YELLOW)
        doc.layers.add(ledg1, color=colors.BLUE, lineweight=9)
        doc.layers.add(ledg3, color=colors.GRAY, lineweight=30)
        doc.layers.add(ledg6, color=colors.LIGHT_GRAY, lineweight=60)
        doc.layers.add(lpols, color=colors.WHITE)
        doc.layers.add(ldims, color=colors.GREEN)
        doc.layers.add(llidr, color=colors.CYAN)

        # DXF entities (LINE, TEXT, ...) reside in a layout (modelspace, 
        # paperspace layout or block definition).  
        msp = doc.modelspace()
        if info:
            print('INFO!!')
            for d in info[0].items():
                doc.header.custom_vars.append(d[0], d[1]['Value'])

        APPID = "Sverchok"
        doc.appids.add(APPID)
        # Add entities to a layout by factory methods: layout.add_...() 

        if e:
            edges_draw(e,v,scal,ledgs,msp,ledg1,ledg3,ledg6)
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
        # Save the DXF document.
        doc.saveas(fp[0][0])


    # MAKE DEFINITION BODY HERE #
    
    vers_, edges_, pols_, Tvers_, Ttext_, fpath_ = [],[],[],[],[],[]
    d1_, d2_, info, dim1_, dim2_,adim1_ = [],[],[],[],[],[]
    leader_, vleader_ = [],[]

    if self.inputs['vers'].is_linked:
        vers_ = self.inputs['vers'].sv_get()
    #else: return {'FINISHED'}
    if self.inputs['edges'].is_linked:
        edges_ = self.inputs['edges'].sv_get()
    if self.inputs['pols'].is_linked:
        pols_ = self.inputs['pols'].sv_get()
    if self.inputs['Tvers'].is_linked:
        Tvers_ = self.inputs['Tvers'].sv_get()
    if self.inputs['Ttext'].is_linked:
        Ttext_ = self.inputs['Ttext'].sv_get()
    if self.inputs['path'].is_linked:
        fpath_ = self.inputs['path'].sv_get()
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

    scal_ = self.inputs['scal'].sv_get()[0][0]
    t_scal_ = self.inputs['t_scal'].sv_get()[0][0]
    export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info,dim1_,dim2_,adim1_,scal_,vleader_,leader_,t_scal_)
    
    return {'FINISHED'}