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
in scal    s d=1.0 n=2
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
    # export main definition
    def export(v,e,p,tv,tt,fp,d1,d2,info,dim1,dim2,scal):
        import ezdxf
        from ezdxf import colors
        from ezdxf.enums import TextEntityAlignment
        from sverchok.data_structure import match_long_repeat as mlr
        from mathutils import Vector
        from ezdxf.tools.standards import setup_dimstyle

        
        DIM_TEXT_STYLE = ezdxf.options.default_dimension_text_style
        # Create a new DXF document.
        doc = ezdxf.new(dxfversion="R2010",setup=True)
        #create a new dimstyle
        glo = scal*0.025
        hai = scal/glo
        formt = f'EZ_MM_{glo}_H{hai}_MM'
        setup_dimstyle(doc,
                       name='EZDXF1',
                       fmt=formt,
                       blk=ezdxf.ARROWS.architectural_tick,#closed_filled,
                       style=DIM_TEXT_STYLE,
                       )

        dimstyle = doc.dimstyles.get('EZDXF1')
        #keep dim line with text        
        dimstyle.dxf.dimtmove=0
        # Create new table entries (layers, linetypes, text styles, ...).
        ltext = "SVERCHOK_TEXT"
        lvers = "SVERCHOK_VERS"
        ledgs = "SVERCHOK_EDGES"
        lpols = "SVERCHOK_POLYGONS"
        ldims = "SVERCHOK_DIMENTIONS"
        doc.layers.add(ltext, color=colors.MAGENTA)
        doc.layers.add(lvers, color=colors.CYAN)
        doc.layers.add(ledgs, color=colors.YELLOW)
        doc.layers.add(lpols, color=colors.WHITE)
        doc.layers.add(ldims, color=colors.GREEN)#CYAN)

        # DXF entities (LINE, TEXT, ...) reside in a layout (modelspace, 
        # paperspace layout or block definition).  
        msp = doc.modelspace()
        if info[0]:
            for d in info[0].items():
                doc.header.custom_vars.append(d[0], d[1]['Value'])

        APPID = "Sverchok"
        doc.appids.add(APPID)
        # Add entities to a layout by factory methods: layout.add_...() 

        if e:
            for obe,obv in zip(e,v):
                edgs = []
                for ed in obe:
                    msp.add_line([i*scal for i in obv[ed[0]]],[i*scal for i in obv[ed[1]]], dxfattribs={"layer": ledgs}) 
                    #dxfattribs={"color": colors.YELLOW})
        elif p and d1:
            mlr([p,d1])
            for obp,obv,d in zip(p,v,d1):
                for po,data in zip(obp,d):
                    points = []
                    for ver in po:
                        if type(obv[ver]) == Vector: vr = (scal*obv[ver]).to_tuple()
                        else: vr = [i*scal for i in obv[ver]]
                        points.append(vr)
                    pl = msp.add_polyline3d(points, dxfattribs={"layer": lpols},close=True)
                    pl.set_xdata(APPID, [(1000, str(d2[0][0])),(1000, str(data))])
        elif p:
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

        elif v:
        #for x,y in [(0,10),(10,10),(10,0),(0,0)]:
            for ob in v:
                vers = []
                for ver in ob:
                    #vers.append(ver)
                    msp.add_point([i*scal for i in ver], dxfattribs={"layer": lvers})
        if tv and tt:
            for obtv, obtt in zip(tv,tt):
                for tver, ttext in zip(obtv,obtt):
                    tver = [i*scal for i in tver]
                    msp.add_text(
                    ttext, height=scal*0.12,#0.05,
                    dxfattribs={
                        "layer": ltext
                    }).set_placement(tver, align=TextEntityAlignment.CENTER)
        
        if dim1 and dim2:
            for obd1,obd2 in zip(dim1,dim2):
                for d1,d2 in zip(obd1,obd2):
                    dim = msp.add_aligned_dim(p1=[i*scal for i in d1[:2]], p2=[i*scal for i in d2[:2]],distance=-0.2*scal, dimstyle='EZDXF1',dxfattribs={"layer": ldims})
                    #dim.render()
        
        # Save the DXF document.
        doc.saveas(fp[0][0])
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

    vers_,edges_,pols_,Tvers_,Ttext_,fpath_ = [],[],[],[],[],[]
    d1_, d2_, info,dim1_,dim2_ = [],[],[],[],[]

    if self.inputs['vers'].is_linked:
        vers_ = self.inputs['vers'].sv_get()
    else: return {'FINISHED'}
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
    else: return {'FINISHED'}
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
    scal_ = self.inputs['scal'].sv_get()[0][0]
    export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info,dim1_,dim2_,scal_)
    
    return {'FINISHED'}
