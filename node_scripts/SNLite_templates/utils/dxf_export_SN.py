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
    def export(v,e,p,tv,tt,fp,d1,d2,info):
        import ezdxf
        from ezdxf import colors
        from ezdxf.enums import TextEntityAlignment
        from sverchok.data_structure import match_long_repeat as mlr


        # Create a new DXF document.
        doc = ezdxf.new(dxfversion="R2010")

        # Create new table entries (layers, linetypes, text styles, ...).
        ltext = "SVERCHOK_TEXT"
        lvers = "SVERCHOK_VERS"
        ledgs = "SVERCHOK_EDGES"
        lpols = "SVERCHOK_POLYGONS"
        doc.layers.add(ltext, color=colors.RED)
        doc.layers.add(lvers, color=colors.WHITE)
        doc.layers.add(ledgs, color=colors.GREEN)
        doc.layers.add(lpols, color=colors.YELLOW)

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
                    msp.add_line(obv[ed[0]],obv[ed[1]], dxfattribs={"layer": ledgs}) 
                    #dxfattribs={"color": colors.YELLOW})
        elif p:
            mlr([p,d1])
            for obp,obv,d in zip(p,v,d1):
                for po,data in zip(obp,d):
                    points = []
                    for ver in po:
                        points.append(obv[ver])
                    pf = msp.add_polyface()
                    pf.append_face(points, dxfattribs={"layer": lpols})
                    pf.set_xdata(APPID, [(1000, str(d2[0][0])),
                                (1070, data),  # 16bit
                                ])
            '''
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
#msp.add_polyline3d(points, dxfattribs={"layer": "SVERCHOK_POLYGONS"},close=True)
        elif v:
        #for x,y in [(0,10),(10,10),(10,0),(0,0)]:
            for ob in v:
                vers = []
                for ver in ob:
                    vers.append(list(ver))
                msp.add_point(vers, dxfattribs={"layer": lvers})
        if tv and tt:
            for obtv, obtt in zip(tv,tt):
                for tver, ttext in zip(obtv,obtt):
                    msp.add_text(
                    ttext, height=0.05,
                    dxfattribs={
                        "layer": ltext
                    }).set_placement(tver, align=TextEntityAlignment.CENTER)
        
        # Save the DXF document.
        doc.saveas(fp[0][0])



    vers_,edges_,pols_,Tvers_,Ttext_,fpath_ = [],[],[],[],[],[]
    d1_, d2_, info = [],[],[]

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
    export(vers_,edges_,pols_,Tvers_,Ttext_,fpath_,d1_,d2_,info)
    
    return {'FINISHED'}
