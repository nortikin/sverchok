# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import math
from sverchok.dependencies import ezdxf
if ezdxf != None:
    import ezdxf
    from ezdxf.math import Vec3
    from ezdxf import colors
    from ezdxf import units
    from ezdxf.tools.standards import setup_dimstyle
#from sverchok.utils.nurbs_common import SvNurbsMaths
from sverchok.utils.curve import SvCircle, SvLine, SvEllipse
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve import knotvector as sv_knotvector
from mathutils import Vector as V
from mathutils import Matrix as M
import numpy as np

######################
######################
#####   IMPORT   #####
######################
######################

def dxf_read(node, fp, resolution, scale, curve_degree, layers=None, curves_import=False):
    curves_out = []
    knots_out = []
    VE, EE = [], []
    VP, PP = [], []
    VA, EA = [], []
    VT, TT = [], []

    dxf = ezdxf.readfile(fp)
    lifehack = 500 # for increase range int values to reduce than to floats. Seems like optimal maybe 50-100
    # all_types = {e.dxftype() for e in doc.modelspace()} # все типы в файле, чтобы не тыкаться
    # во имя отделения размеров и выносок!
    ANNOTATION_TYPES = [
        "DIMENSION", "LEADER", "MLEADER",
        "TEXT", "MTEXT", "ARC_DIMENSION", "DIAMETER_DIMENSION",
        "RADIAL_DIMENSION",
    ]
    SERVICE_TYPES = [
        "ATTRIB", "ATTDEF", "HATCH", "DIMENSION_STYLE",
        "VIEWPORT", "IMAGE", "XLINE", "RAY", "TABLE", "TOLERANCE"
    ]
    GEOMETRY_TYPES = [
        "LINE", "CIRCLE", "ARC", "POLYLINE", "LWPOLYLINE", "SPLINE",
        "ELLIPSE", "POINT", "VERTEX", "3DFACE", "SOLID",
        "POLYMESH", "POLYFACE"
    ]
    #pure_geometry = []
    #annotation_geometry = []
    #servise_geometry = []
    #dimension_handles = {dim.dxf.handle for dim in dxf.query("DIMENSION")}

    for entity in dxf.modelspace():
        if layers != None:
            if not entity.dxf.layer in layers:
                continue
        if entity.dxftype() in ANNOTATION_TYPES:
            vers, edges, pols, curves, knots, VT_, TT_ = dxf_geometry_loader(node, entity, curve_degree, resolution, lifehack, scale, curves_import)
            if vers:
                VA.extend(vers)
                EA.extend(edges)
            if VT_:
                VT.extend(VT_)
                TT.extend(TT_)
        elif entity.dxftype() in GEOMETRY_TYPES:
            vers, edges, pols, curves, knots, VT_, TT_ = dxf_geometry_loader(node, entity, curve_degree, resolution, lifehack, scale, curves_import)
            if edges:
                VE.extend(vers)
                EE.extend(edges)
            elif pols:
                VP.extend(vers)
                PP.extend(pols)
            if curves:
                curves_out.extend(curves)
                knots_out.extend(knots)
        elif entity.dxftype() in SERVICE_TYPES:
            continue
    return curves_out, knots_out, VE, EE, VP, PP, VA, EA, VT, TT


def dxf_geometry_loader(self, entity, curve_degree, resolution, lifehack, scale, curves_import=False):
    ''' dxf_geometry_loader(entity) ВОЗВРАЩАЕТ вершины, рёбра, полигоны и кривые всей геометрии, что находит у сущности'''
    typ = entity.dxftype().lower()
    #print('!!! type element:',typ)
    vers, edges, pols, VT, TT, curves_out, knots_out = [], [], [], [], [], [], []
    pointered = ['arc','circle','ellipse']
    if typ in pointered:
        vers_ = []
        center = entity.dxf.center*scale
        #radius = a.dxf.radius
        if typ == 'arc':
            start  = int(entity.dxf.start_angle)
            #print('start angle:', start)
            end    = int(entity.dxf.end_angle)
            #print('end angle:', end)
            if start > end:
                start1 = (360-start)
                overall = start1+end
                resolution_arc = max(3,int(resolution*(overall/360))) # redefine resolution for partially angles
                step = max(1,int((start1+end)/resolution_arc))
                ran = [i/lifehack for i in range(lifehack*start,lifehack*360,lifehack*step)]
                ran.extend([i/lifehack for i in range(0,lifehack*end,lifehack*step)])
            else:
                start1 = start
                overall = end-start1
                resolution_arc = max(3,int(resolution*(overall/360))) # redefine resolution for partially angles
                ran = [i/lifehack for i in range(lifehack*start,lifehack*end,max(1,int(lifehack*(end-start)/resolution_arc)))]
        elif typ == 'circle':
            ran = [i/lifehack for i in range(0,lifehack*360,max(1,int((lifehack*360)/resolution)))]
            #print('Circle consists of: ',dir(entity),dir(entity.dxf))
            #print('DXF Circle consists of: ',center,entity.dxf.center.xyz,entity.dxf.radius)
            if curves_import:
                cur = SvCircle(center=np.array(center), normal=np.array((0.,0.,1.)), vectorx=np.array((1.,0.,0.)), radius=np.float64(entity.dxf.radius*scale)).to_nurbs()
                cur.u_bounds = (0., math.pi*2)
                curves_out.append(cur)
                knots_out.append([])
        elif typ == 'ellipse':
            start  = entity.dxf.start_param
            end    = entity.dxf.end_param
            ran = [start + ((end-start)*i)/(lifehack*360) for i in range(0,lifehack*360,max(1,int(lifehack*360/resolution)))]
            if curves_import:
                major_radius = entity.dxf.major_axis[0]*scale
                minor_radius = major_radius*entity.dxf.ratio
                matrix = M()
                matrix.translation = V(center)
                curves_out.append(SvEllipse(matrix, major_radius, minor_radius, center_type = SvEllipse.CENTER))
        for i in entity.vertices(ran): # line 43 is 35 in make 24 in import
            cen = entity.dxf.center.xyz #*scale
            vers_.append([j*scale for j in i])

        vers.append(vers_)
        edges.append([[i,i+1] for i in range(len(vers_)-1)])
        if typ == 'circle':
            edges[-1].append([len(vers_)-1,0])
        if typ == 'ellipse' and (start <= 0.001 or end >= math.pi*4-0.001):
            edges[-1].append([len(vers_)-1,0])

    if typ == 'point':
        mu = 0.2
        ver = entity.dxf.location.xyz #[i for i in entity.dxf.location.xyz]
        ver_ = [ ver,
                [-mu+ver[0],-mu+ver[1],ver[2]],
                [-mu+ver[0],mu+ver[1],ver[2]],
                [mu+ver[0],mu+ver[1],ver[2]],
                [mu+ver[0],-mu+ver[1],ver[2]],
                ]
        vers.append((np.array(ver_)*scale).tolist())
        edges.append([[1,3],[2,4]])

    if typ == 'line':
        edges.append([[0,1]])
        vers.append([[i*scale for i in entity.dxf.start.xyz],[i*scale for i in entity.dxf.end.xyz]])
        # Сегменты кривыми
        if curves_import:
            curves_out.append(SvLine.from_two_points(vers[-1][0],vers[-1][1]))


    #print(typ)

    if typ in ["polyline"]:
        #print('Полилиния попалась ========', entity.dxftype)
        #print(dir(entity.dxf))
        #print(entity.is_closed)
        #print('==Polyline points type',type(entity.points())) # тип генератор
        vers.append([[i*scale for i in vert.xyz] for vert in entity.points()])
        # Сегменты кривыми
        if curves_import:
            for i in range(len(vers[-1])-1):
                curves_out.append(SvLine.from_two_points(vers[-1][i],vers[-1][i+1]))
            if entity.is_closed != 0:
                curves_out.append(SvLine.from_two_points(vers[-1][i+1],vers[-1][0]))
        if entity.is_closed != 0:
            pols.append([[i for i in range(len(vers[-1]))]])
            #print(pols)
        else:
            edges.append([[i,i+1] for i in range(len(vers[-1])-1)])
            #print(edges)

    if typ in ["3dface"]:
        #print('3D лицо попалось ========', entity.dxftype)
        #print(entity.dxf.vtx0)
        #print(entity.dxf.vtx3)
        vs = entity.dxf.vtx0,entity.dxf.vtx1,entity.dxf.vtx2,entity.dxf.vtx3 if entity.dxf.vtx3 \
            else entity.dxf.vtx0,entity.dxf.vtx1,entity.dxf.vtx2
        vers.append((np.array(vs)*scale).tolist())
        pols.append([[i,i+1,i+2] for i in range(0,len(vers[-1]),3)])
        #print(pols)

    if typ in ["solid", "polymesh", "polyface"]:
        print('3Д попалась, пока не обрабатывается ========', entity.dxftype)

    if typ in ['dimension',"arc-dimension", "diameter_dimension","radial_dimension"]:
        #print(entity.dxftype,entity.dxf.dimtype, dir(entity.dxf))
        edges.append([[0,1]])
        if entity.dxf.dimtype == 32:
            mes = round(entity.dxf.defpoint2.distance(entity.dxf.defpoint3),2)
            vers.append([[i*scale for i in entity.dxf.defpoint2.xyz],[i*scale for i in entity.dxf.defpoint3.xyz]])
        else:
            mes = round(entity.dxf.defpoint.distance(entity.dxf.defpoint4),2)
            vers.append([[i*scale for i in entity.dxf.defpoint.xyz],[i*scale for i in entity.dxf.defpoint4.xyz]])
        try:
            mp = [i for i in entity.dxf.text_midpoint.xyz]
        except:
            mp = list((V(vers[-1][1]) + (V(vers[-1][0])-V(vers[-1][1]))/2).to_tuple())
        VT.append((np.array(mp)*scale).tolist())
        TT.append([mes])

    if typ == 'lwpolyline':
        # Это 2D линия, у которой нет Z координат
        #print('lwpolyline попалась ========', entity.dxftype)
        edges_ = []
        vers_ = []
        points = list(entity.get_points())
        vertices = list(entity.vertices())

        for i, (x, y, start_width, end_width, bulge) in enumerate(points):
            current_point = (x, y, 0) # was scale

            # Добавляем текущую точку
            if i == 0:
                vers_.append(current_point)

            # Обрабатываем сегмент между текущей и следующей точкой
            if i < len(points) - 1:
                next_point_data = points[i+1]
                next_point = (next_point_data[0], next_point_data[1], 0) # was scale
                next_bulge = next_point_data[4]

                if bulge != 0:
                    # Дуга с bulge-фактором
                    segment_points = arc_points(current_point, next_point, bulge, resolution=resolution)
                    # Пропускаем первую точку (она уже добавлена)
                    vers_.extend(segment_points[1:])
                    # Создаем рёбра для сегментов дуги
                    start_idx = len(vers_) - len(segment_points) + 1
                    edges_.extend([[j-1, j] for j in range(start_idx, len(vers_))])
                else:
                    # Линейный сегмент
                    vers_.append(next_point)
                    edges_.append([len(vers_)-2, len(vers_)-1])

        # Замыкаем полилинию если нужно
        if entity.closed:
            edges_.append([len(vers_)-1, 0])
            # Для замкнутой полилинии обрабатываем последний сегмент
            if points and points[-1][4] != 0:  # Если последний сегмент - дуга
                first_point = vers_[0]
                last_point = vers_[-1]
                last_bulge = points[-1][4]

                segment_points = arc_points(last_point, first_point, last_bulge, resolution=resolution)
                # Обновляем рёбра для последней дуги
                if len(segment_points) > 2:
                    start_idx = len(vers_) - 1
                    vers_.extend(segment_points[1:-1])  # Пропускаем первую и последнюю точки
                    edges_.extend([[j-1, j] for j in range(start_idx + 1, len(vers_))])
                    edges_.append([len(vers_)-1, 0])
        # Сегменты кривыми
        if curves_import:
            for i in range(len(vers_)-1):
                curves_out.append(SvLine.from_two_points(vers_[i],vers_[i+1]))
            if entity.closed:
                curves_out.append(SvLine.from_two_points(vers_[i+1],vers_[0]))

        vers.append((np.array(vers_)*scale).tolist())
        edges.append(edges_)
    # Splines as NURBS curves
    vers_ = []
    if typ == 'spline':
        #print('Блок', a.source_block_reference)
        control_points = entity.control_points
        control_points.values *= scale
        #print('== Curve control_points',type(control_points),control_points)
        n_total = len(control_points)
        # Set knot vector
        if entity.closed:
            self.debug("N: %s, degree: %s", n_total, curve_degree)
            knots = list(range(n_total + curve_degree + 1))
        else:
            knots = sv_knotvector.generate(curve_degree, n_total)

        #print('== Curve knots', type(knots), knots)
        curve_weights = [1 for i in control_points]
        self.debug('Auto knots: %s', knots)
        curve_knotvector = knots*scale

        # Nurbs curve
        new_curve = SvNurbsCurve.build(self.implementation, curve_degree, curve_knotvector, control_points, curve_weights, normalize_knots = True)

        curve_knotvector = new_curve.get_knotvector().tolist()
        if entity.closed:
            u_min = curve_knotvector[curve_degree]
            u_max = curve_knotvector[-curve_degree-1]
            new_curve.u_bounds = u_min, u_max
        else:
            u_min = min(curve_knotvector)
            u_max = max(curve_knotvector)
            new_curve.u_bounds = (u_min, u_max)
        if curves_import:
            curves_out.append(new_curve)
            knots_out.append(curve_knotvector)
        ver_curv = []
        #print('==Curve min max ',u_min, u_max, [i* (u_min+((u_max-u_min) / (30))) for i in range(31)])
        for i in range(resolution+1):
            ver_curv.append(list(new_curve.evaluate(  i* (u_min+((u_max-u_min) / resolution))  )))
        vers.append(ver_curv)
        edges.append([[i,i+1] for i in range(len(ver_curv)-1)])
    #print('^$#^%^#$%',typ)
    if typ == 'mtext':
        #print([(k.dxf.insert, k.text) for k in i.entitydb.query('Mtext')])
        VT.append([[i*scale for i in entity.dxf.insert.xyz]])
        TT.append([[entity.text]])
        #print(VT,TT)
    if typ == 'text':
        #print( dir(entity.dxf) )
        VT.append([[i*scale for i in entity.dxf.insert.xyz]])
        TT.append([[entity.dxf.text]])
    return vers, edges, pols, curves_out, knots_out, VT, TT

def arc_points(start, end, bulge, num_points=3, resolution=50):
    """Генерирует точки на дуге между start и end с заданным bulge."""
    if bulge == 0:
        return [start, end]  # Линейный сегмент

    # Преобразуем точки в Vec3 для удобства вычислений
    start_point = Vec3(start)
    end_point = Vec3(end)

    # Вычисляем параметры дуги по формуле bulge
    chord_vector = end_point - start_point
    chord_length = chord_vector.magnitude

    # Вычисляем высоту стрелки (sagitta)
    sagitta = abs(bulge) * chord_length / 2

    # Радиус дуги
    radius = (chord_length**2) / (8 * sagitta) + sagitta / 2

    # Вычисляем центр дуги
    chord_mid = (start_point + end_point) / 2
    perpendicular = chord_vector.orthogonal().normalize()

    # Направление зависит от знака bulge
    if bulge > 0:
        center = chord_mid + perpendicular * (radius - sagitta)
    else:
        center = chord_mid - perpendicular * (radius - sagitta)

    # Вычисляем начальный и конечный углы
    start_angle = (start_point - center).angle
    end_angle = (end_point - center).angle

    # Корректируем углы для правильного направления
    if bulge > 0:
        # Положительный bulge - против часовой стрелки
        if end_angle <= start_angle:
            end_angle += 2 * math.pi
    else:
        # Отрицательный bulge - по часовой стрелке
        if start_angle <= end_angle:
            start_angle += 2 * math.pi

    # Генерируем точки дуги
    total_angle = abs(end_angle - start_angle)
    num_segments = max(2, int(total_angle * resolution / (2 * math.pi)))

    points = []
    for i in range(num_segments + 1):
        t = i / num_segments
        angle = start_angle + t * (end_angle - start_angle)
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        z = start_point.z  # Сохраняем Z-координату
        points.append((x, y, z))

    return points

######################################
######################################
#####        DXF STANDARDS       #####
######################################
######################################

patterns = [
    ('ANSI31',        'Simple cut ANSI31','ANSI31',         1),
    ('ANSI32',        'Brick cut ANSI32','ANSI32',          2),
    ('ANSI33',        'R/f concrete cut ANSI33','ANSI33',   3),
    ('ANSI34',        'ground cut ANSI34','ANSI34',         4),
    ('ANSI35',        'R/f concrete cut ANSI35','ANSI35',   5),
    ('ANSI36',        'Concrete cut ANSI36','ANSI36',       6),
    ('ANSI37',        'Insulation cut ANSI37','ANSI37',     7),
    ('ANSI38',        'Wood cut ANSI38','ANSI38',           8),
    ('ACAD_ISO02W100','dash 02 W100','ACAD_ISO',            9),
    ('ACAD_ISO03W100','dash 03 W100','ACAD_ISO',            10),
    ('ACAD_ISO04W100','dash 04 W100','ACAD_ISO',            11),
    ('ACAD_ISO05W100','dashdot 05 W100','ACAD_ISO',         12),
    ('ACAD_ISO06W100','dashdotdot 06 W100','ACAD_ISO',      13),
    ('ACAD_ISO07W100','dots 07 W100','ACAD_ISO',            14),
    ('ACAD_ISO08W100','solid 08 W100','ACAD_ISO',           15),
    ('ACAD_ISO09W100','dash 09 W100','ACAD_ISO',            16),
    ('ACAD_ISO10W100','dashdot 10 W100','ACAD_ISO',         17),
    ('ACAD_ISO11W100','dashdot 11 W100','ACAD_ISO',         18),
    ('ACAD_ISO12W100','dashdotdot 12 W100','ACAD_ISO',      19),
    ('ACAD_ISO13W100','dashdotdot 13 W100','ACAD_ISO',      20),
    ('ACAD_ISO14W100','dashdotdot 14 W100','ACAD_ISO',      21),
    ('ACAD_ISO15W100','dashdotdot 15 W100','ACAD_ISO',      22),
    ('ANGLE',         'ANGLE','Angle',                      23),
    ('AR-B816',       'Brick 816','Simple Brick',           24),
    ('AR-B816C',      'Brick 816C','Simple Brick',          25),
    ('AR-B88',        'Brick 88','Simple Brick',            26),
    ('AR-BRELM',      'Brick ELM','Simple Brick',           27),
    ('AR-BRSTD',      'Brick STD','Simple Brick',           28),
    ('AR-CONC',       'Concrete','Concrete',                29),
    ('AR-HBONE',      'Pavement Hbone','Pavement',          30),
    ('AR-PARQ1',      'Parquete square','Parquete',         31),
    ('AR-RROOF',      'Water like roof','Roof',             32),
    ('AR-RSHKE',      'Slices roof','Roof',                 33),
    ('AR-SAND',       'Sand','Sand',                        34),
    ('BOX',           'Box pattern','Crosses and dots',     35),
    ('BRASS',         'Brass','solids and dashed lines',    36),
    ('BRICK',         'Brick','Brick',                      37),
    ('BRSTONE',       'Brick Stone','Long mansory bricks',  38),
    ('CLAY',          'CLAY cut','Glina/Clay cut',          39),
    ('CORK',          'CORK cut','Cork cut',                40),
    ('CROSS',         'CROSS','Cross',                      41),
    ('DASH',          'DASH','Dash',                        42),
    ('DOLMIT',        'DOLMIT','DOLMIT',                    43),
    ('DOTS',          'DOTS','Dots',                        44),
    ('EARTH',         'EARTH cut','English symbol for earth cut',45),
    ('ESCHER',        'ESCHER','ESCHER pattern',            46),
    ('FLEX',          'FLEX','Flex',                        47),
    ('GOST_GLASS',    'GOST_GLASS','GLASS symbol by ГОСТ',  48),
    ('GOST_WOOD',     'GOST_WOOD','WOOD symbol by ГОСТ',    49),
    ('GOST_GROUND',   'GOST_GROUND','GROUND symbol by ГОСТ',50),
    ('GRASS',         'GRASS','GRASS',                      51),
    ('GRATE',         'GRATE','GRATE',                      52),
    ('GRAVEL',        'GRAVEL','GRAVEL',                    53),
    ('HEX',           'HEX','HEX',                          54),
    ('HONEY',         'HONEY','HONEY',                      55),
    ('HOUND',         'HOUND','HOUND',                      56),
    ('INSUL',         'INSUL','INSUL',                      57),
    ('LINE',          'LINE','LINE horisontal',             58),
    ('MUDST',         'MUDST','MUDST',                      59),
    ('NET',           'NET','NET',                          60),
    ('NET3',          'NET3','NET3',                        61),
    ('PLAST',         'PLAST','PLAST',                      62),
    ('PLASTI',        'PLASTI','PLASTI',                    63),
    ('SACNCR',        'SACNCR','SACNCR',                    64),
    ('SQUARE',        'SQUARE','SQUARE',                    65),
    ('STARS',         'STARS','STARS',                      66),
    ('STEEL',         'STEEL','STEEL',                      67),
    ('SWAMP',         'SWAMP','SWAMP',                      68),
    ('TRANS',         'TRANS','TRANS',                      69),
    ('TRIANG',        'TRIANG','TRIANG',                    70),
    ('ZIGZAG',        'ZIGZAG','ZIGZAG',                    71),

]


ACI_RGB = {1: [1.0, 0.0, 0.0], 2: [1.0, 1.0, 0.0], 3: [0.0, 1.0, 0.0], 4: [0.0, 1.0, 1.0], 5: [0.0, 0.0, 1.0], 6: [1.0, 0.0, 1.0], 7: [1.0, 1.0, 1.0], 8: [0.5019607843137255, 0.5019607843137255, 0.5019607843137255], 9: [0.7529411764705882, 0.7529411764705882, 0.7529411764705882], 10: [1.0, 0.0, 0.0], 11: [1.0, 0.4980392156862745, 0.4980392156862745], 12: [0.8, 0.0, 0.0], 13: [0.8, 0.4, 0.4], 14: [0.6, 0.0, 0.0], 15: [0.6, 0.2980392156862745, 0.2980392156862745], 16: [0.4980392156862745, 0.0, 0.0], 17: [0.4980392156862745, 0.24705882352941178, 0.24705882352941178], 18: [0.2980392156862745, 0.0, 0.0], 19: [0.2980392156862745, 0.14901960784313725, 0.14901960784313725], 20: [1.0, 0.24705882352941178, 0.0], 21: [1.0, 0.6235294117647059, 0.4980392156862745], 22: [0.8, 0.2, 0.0], 23: [0.8, 0.4980392156862745, 0.4], 24: [0.6, 0.14901960784313725, 0.0], 25: [0.6, 0.37254901960784315, 0.2980392156862745], 26: [0.4980392156862745, 0.12156862745098039, 0.0], 27: [0.4980392156862745, 0.30980392156862746, 0.24705882352941178], 28: [0.2980392156862745, 0.07450980392156863, 0.0], 29: [0.2980392156862745, 0.1843137254901961, 0.14901960784313725], 30: [1.0, 0.4980392156862745, 0.0], 31: [1.0, 0.7490196078431373, 0.4980392156862745], 32: [0.8, 0.4, 0.0], 33: [0.8, 0.6, 0.4], 34: [0.6, 0.2980392156862745, 0.0], 35: [0.6, 0.4470588235294118, 0.2980392156862745], 36: [0.4980392156862745, 0.24705882352941178, 0.0], 37: [0.4980392156862745, 0.37254901960784315, 0.24705882352941178], 38: [0.2980392156862745, 0.14901960784313725, 0.0], 39: [0.2980392156862745, 0.2235294117647059, 0.14901960784313725], 40: [1.0, 0.7490196078431373, 0.0], 41: [1.0, 0.8745098039215686, 0.4980392156862745], 42: [0.8, 0.6, 0.0], 43: [0.8, 0.6980392156862745, 0.4], 44: [0.6, 0.4470588235294118, 0.0], 45: [0.6, 0.5215686274509804, 0.2980392156862745], 46: [0.4980392156862745, 0.37254901960784315, 0.0], 47: [0.4980392156862745, 0.43529411764705883, 0.24705882352941178], 48: [0.2980392156862745, 0.2235294117647059, 0.0], 49: [0.2980392156862745, 0.25882352941176473, 0.14901960784313725], 50: [1.0, 1.0, 0.0], 51: [1.0, 1.0, 0.4980392156862745], 52: [0.8, 0.8, 0.0], 53: [0.8, 0.8, 0.4], 54: [0.6, 0.6, 0.0], 55: [0.6, 0.6, 0.2980392156862745], 56: [0.4980392156862745, 0.4980392156862745, 0.0], 57: [0.4980392156862745, 0.4980392156862745, 0.24705882352941178], 58: [0.2980392156862745, 0.2980392156862745, 0.0], 59: [0.2980392156862745, 0.2980392156862745, 0.14901960784313725], 60: [0.7490196078431373, 1.0, 0.0], 61: [0.8745098039215686, 1.0, 0.4980392156862745], 62: [0.6, 0.8, 0.0], 63: [0.6980392156862745, 0.8, 0.4], 64: [0.4470588235294118, 0.6, 0.0], 65: [0.5215686274509804, 0.6, 0.2980392156862745], 66: [0.37254901960784315, 0.4980392156862745, 0.0], 67: [0.43529411764705883, 0.4980392156862745, 0.24705882352941178], 68: [0.2235294117647059, 0.2980392156862745, 0.0], 69: [0.25882352941176473, 0.2980392156862745, 0.14901960784313725], 70: [0.4980392156862745, 1.0, 0.0], 71: [0.7490196078431373, 1.0, 0.4980392156862745], 72: [0.4, 0.8, 0.0], 73: [0.6, 0.8, 0.4], 74: [0.2980392156862745, 0.6, 0.0], 75: [0.4470588235294118, 0.6, 0.2980392156862745], 76: [0.24705882352941178, 0.4980392156862745, 0.0], 77: [0.37254901960784315, 0.4980392156862745, 0.24705882352941178], 78: [0.14901960784313725, 0.2980392156862745, 0.0], 79: [0.2235294117647059, 0.2980392156862745, 0.14901960784313725], 80: [0.24705882352941178, 1.0, 0.0], 81: [0.6235294117647059, 1.0, 0.4980392156862745], 82: [0.2, 0.8, 0.0], 83: [0.4980392156862745, 0.8, 0.4], 84: [0.14901960784313725, 0.6, 0.0], 85: [0.37254901960784315, 0.6, 0.2980392156862745], 86: [0.12156862745098039, 0.4980392156862745, 0.0], 87: [0.30980392156862746, 0.4980392156862745, 0.24705882352941178], 88: [0.07450980392156863, 0.2980392156862745, 0.0], 89: [0.1843137254901961, 0.2980392156862745, 0.14901960784313725], 90: [0.0, 1.0, 0.0], 91: [0.4980392156862745, 1.0, 0.4980392156862745], 92: [0.0, 0.8, 0.0], 93: [0.4, 0.8, 0.4], 94: [0.0, 0.6, 0.0], 95: [0.2980392156862745, 0.6, 0.2980392156862745], 96: [0.0, 0.4980392156862745, 0.0], 97: [0.24705882352941178, 0.4980392156862745, 0.24705882352941178], 98: [0.0, 0.2980392156862745, 0.0], 99: [0.14901960784313725, 0.2980392156862745, 0.14901960784313725], 100: [0.0, 1.0, 0.24705882352941178], 101: [0.4980392156862745, 1.0, 0.6235294117647059], 102: [0.0, 0.8, 0.2], 103: [0.4, 0.8, 0.4980392156862745], 104: [0.0, 0.6, 0.14901960784313725], 105: [0.2980392156862745, 0.6, 0.37254901960784315], 106: [0.0, 0.4980392156862745, 0.12156862745098039], 107: [0.24705882352941178, 0.4980392156862745, 0.30980392156862746], 108: [0.0, 0.2980392156862745, 0.07450980392156863], 109: [0.14901960784313725, 0.2980392156862745, 0.1843137254901961], 110: [0.0, 1.0, 0.4980392156862745], 111: [0.4980392156862745, 1.0, 0.7490196078431373], 112: [0.0, 0.8, 0.4], 113: [0.4, 0.8, 0.6], 114: [0.0, 0.6, 0.2980392156862745], 115: [0.2980392156862745, 0.6, 0.4470588235294118], 116: [0.0, 0.4980392156862745, 0.24705882352941178], 117: [0.24705882352941178, 0.4980392156862745, 0.37254901960784315], 118: [0.0, 0.2980392156862745, 0.14901960784313725], 119: [0.14901960784313725, 0.2980392156862745, 0.2235294117647059], 120: [0.0, 1.0, 0.7490196078431373], 121: [0.4980392156862745, 1.0, 0.8745098039215686], 122: [0.0, 0.8, 0.6], 123: [0.4, 0.8, 0.6980392156862745], 124: [0.0, 0.6, 0.4470588235294118], 125: [0.2980392156862745, 0.6, 0.5215686274509804], 126: [0.0, 0.4980392156862745, 0.37254901960784315], 127: [0.24705882352941178, 0.4980392156862745, 0.43529411764705883], 128: [0.0, 0.2980392156862745, 0.2235294117647059], 129: [0.14901960784313725, 0.2980392156862745, 0.25882352941176473], 130: [0.0, 1.0, 1.0], 131: [0.4980392156862745, 1.0, 1.0], 132: [0.0, 0.8, 0.8], 133: [0.4, 0.8, 0.8], 134: [0.0, 0.6, 0.6], 135: [0.2980392156862745, 0.6, 0.6], 136: [0.0, 0.4980392156862745, 0.4980392156862745], 137: [0.24705882352941178, 0.4980392156862745, 0.4980392156862745], 138: [0.0, 0.2980392156862745, 0.2980392156862745], 139: [0.14901960784313725, 0.2980392156862745, 0.2980392156862745], 140: [0.0, 0.7490196078431373, 1.0], 141: [0.4980392156862745, 0.8745098039215686, 1.0], 142: [0.0, 0.6, 0.8], 143: [0.4, 0.6980392156862745, 0.8], 144: [0.0, 0.4470588235294118, 0.6], 145: [0.2980392156862745, 0.5215686274509804, 0.6], 146: [0.0, 0.37254901960784315, 0.4980392156862745], 147: [0.24705882352941178, 0.43529411764705883, 0.4980392156862745], 148: [0.0, 0.2235294117647059, 0.2980392156862745], 149: [0.14901960784313725, 0.25882352941176473, 0.2980392156862745], 150: [0.0, 0.4980392156862745, 1.0], 151: [0.4980392156862745, 0.7490196078431373, 1.0], 152: [0.0, 0.4, 0.8], 153: [0.4, 0.6, 0.8], 154: [0.0, 0.2980392156862745, 0.6], 155: [0.2980392156862745, 0.4470588235294118, 0.6], 156: [0.0, 0.24705882352941178, 0.4980392156862745], 157: [0.24705882352941178, 0.37254901960784315, 0.4980392156862745], 158: [0.0, 0.14901960784313725, 0.2980392156862745], 159: [0.14901960784313725, 0.2235294117647059, 0.2980392156862745], 160: [0.0, 0.24705882352941178, 1.0], 161: [0.4980392156862745, 0.6235294117647059, 1.0], 162: [0.0, 0.2, 0.8], 163: [0.4, 0.4980392156862745, 0.8], 164: [0.0, 0.14901960784313725, 0.6], 165: [0.2980392156862745, 0.37254901960784315, 0.6], 166: [0.0, 0.12156862745098039, 0.4980392156862745], 167: [0.24705882352941178, 0.30980392156862746, 0.4980392156862745], 168: [0.0, 0.07450980392156863, 0.2980392156862745], 169: [0.14901960784313725, 0.1843137254901961, 0.2980392156862745], 170: [0.0, 0.0, 1.0], 171: [0.4980392156862745, 0.4980392156862745, 1.0], 172: [0.0, 0.0, 0.8], 173: [0.4, 0.4, 0.8], 174: [0.0, 0.0, 0.6], 175: [0.2980392156862745, 0.2980392156862745, 0.6], 176: [0.0, 0.0, 0.4980392156862745], 177: [0.24705882352941178, 0.24705882352941178, 0.4980392156862745], 178: [0.0, 0.0, 0.2980392156862745], 179: [0.14901960784313725, 0.14901960784313725, 0.2980392156862745], 180: [0.24705882352941178, 0.0, 1.0], 181: [0.6235294117647059, 0.4980392156862745, 1.0], 182: [0.2, 0.0, 0.8], 183: [0.4980392156862745, 0.4, 0.8], 184: [0.14901960784313725, 0.0, 0.6], 185: [0.37254901960784315, 0.2980392156862745, 0.6], 186: [0.12156862745098039, 0.0, 0.4980392156862745], 187: [0.30980392156862746, 0.24705882352941178, 0.4980392156862745], 188: [0.07450980392156863, 0.0, 0.2980392156862745], 189: [0.1843137254901961, 0.14901960784313725, 0.2980392156862745], 190: [0.4980392156862745, 0.0, 1.0], 191: [0.7490196078431373, 0.4980392156862745, 1.0], 192: [0.4, 0.0, 0.8], 193: [0.6, 0.4, 0.8], 194: [0.2980392156862745, 0.0, 0.6], 195: [0.4470588235294118, 0.2980392156862745, 0.6], 196: [0.24705882352941178, 0.0, 0.4980392156862745], 197: [0.37254901960784315, 0.24705882352941178, 0.4980392156862745], 198: [0.14901960784313725, 0.0, 0.2980392156862745], 199: [0.2235294117647059, 0.14901960784313725, 0.2980392156862745], 200: [0.7490196078431373, 0.0, 1.0], 201: [0.8745098039215686, 0.4980392156862745, 1.0], 202: [0.6, 0.0, 0.8], 203: [0.6980392156862745, 0.4, 0.8], 204: [0.4470588235294118, 0.0, 0.6], 205: [0.5215686274509804, 0.2980392156862745, 0.6], 206: [0.37254901960784315, 0.0, 0.4980392156862745], 207: [0.43529411764705883, 0.24705882352941178, 0.4980392156862745], 208: [0.2235294117647059, 0.0, 0.2980392156862745], 209: [0.25882352941176473, 0.14901960784313725, 0.2980392156862745], 210: [1.0, 0.0, 1.0], 211: [1.0, 0.4980392156862745, 1.0], 212: [0.8, 0.0, 0.8], 213: [0.8, 0.4, 0.8], 214: [0.6, 0.0, 0.6], 215: [0.6, 0.2980392156862745, 0.6], 216: [0.4980392156862745, 0.0, 0.4980392156862745], 217: [0.4980392156862745, 0.24705882352941178, 0.4980392156862745], 218: [0.2980392156862745, 0.0, 0.2980392156862745], 219: [0.2980392156862745, 0.14901960784313725, 0.2980392156862745], 220: [1.0, 0.0, 0.7490196078431373], 221: [1.0, 0.4980392156862745, 0.8745098039215686], 222: [0.8, 0.0, 0.6], 223: [0.8, 0.4, 0.6980392156862745], 224: [0.6, 0.0, 0.4470588235294118], 225: [0.6, 0.2980392156862745, 0.5215686274509804], 226: [0.4980392156862745, 0.0, 0.37254901960784315], 227: [0.4980392156862745, 0.24705882352941178, 0.43529411764705883], 228: [0.2980392156862745, 0.0, 0.2235294117647059], 229: [0.2980392156862745, 0.14901960784313725, 0.25882352941176473], 230: [1.0, 0.0, 0.4980392156862745], 231: [1.0, 0.4980392156862745, 0.7490196078431373], 232: [0.8, 0.0, 0.4], 233: [0.8, 0.4, 0.6], 234: [0.6, 0.0, 0.2980392156862745], 235: [0.6, 0.2980392156862745, 0.4470588235294118], 236: [0.4980392156862745, 0.0, 0.24705882352941178], 237: [0.4980392156862745, 0.24705882352941178, 0.37254901960784315], 238: [0.2980392156862745, 0.0, 0.14901960784313725], 239: [0.2980392156862745, 0.14901960784313725, 0.2235294117647059], 240: [1.0, 0.0, 0.24705882352941178], 241: [1.0, 0.4980392156862745, 0.6235294117647059], 242: [0.8, 0.0, 0.2], 243: [0.8, 0.4, 0.4980392156862745], 244: [0.6, 0.0, 0.14901960784313725], 245: [0.6, 0.2980392156862745, 0.37254901960784315], 246: [0.4980392156862745, 0.0, 0.12156862745098039], 247: [0.4980392156862745, 0.24705882352941178, 0.30980392156862746], 248: [0.2980392156862745, 0.0, 0.07450980392156863], 249: [0.2980392156862745, 0.14901960784313725, 0.1843137254901961], 250: [0.2, 0.2, 0.2], 251: [0.3568627450980392, 0.3568627450980392, 0.3568627450980392], 252: [0.5176470588235295, 0.5176470588235295, 0.5176470588235295], 253: [0.6784313725490196, 0.6784313725490196, 0.6784313725490196], 254: [0.8392156862745098, 0.8392156862745098, 0.8392156862745098]}

LWdict = {
    '0.00':0,
    '0.05':5,
    '0.09':9,
    '0.13':13,
    '0.15':15,
    '0.18':18,
    '0.20':20,
    '0.25':25,
    '0.30':30,
    '0.35':35,
    '0.40':40,
    '0.50':50,
    '0.53':53,
    '0.60':60,
    '0.70':70,
    '0.80':80,
    '0.90':90,
    '1.00':100,
    '1.06':106,
    '1.20':120,
    '1.40':140,
    '1.58':158,
    '2.00':200,
    '2.11':211,
}
lineweights = [
    ('0.00', '0.00','Thin mm',1),
    ('0.05', '0.05','0.05 mm',2),
    ('0.09', '0.09','0.09 mm',3),
    ('0.13', '0.13','0.13 mm',4),
    ('0.15', '0.15','0.15 mm',5),
    ('0.18', '0.18','0.18 mm',6),
    ('0.20', '0.20','0.20 mm',7),
    ('0.25', '0.25','0.25 mm',8),
    ('0.30', '0.30','0.30 mm',9),
    ('0.35', '0.35','0.35 mm',10),
    ('0.40', '0.40','0.40 mm',11),
    ('0.50', '0.50','0.50 mm',12),
    ('0.53', '0.53','0.53 mm',13),
    ('0.60', '0.60','0.60 mm',14),
    ('0.70', '0.70','0.70 mm',15),
    ('0.80', '0.80','0.80 mm',16),
    ('0.90', '0.90','0.90 mm',17),
    ('1.00', '1.00','1.00 mm',18),
    ('1.06', '1.06','1.06 mm',19),
    ('1.20', '1.20','1.20 mm',20),
    ('1.40', '1.40','1.40 mm',21),
    ('1.58', '1.58','1.58 mm',22),
    ('2.00', '2.00','2.00 mm',23),
    ('2.11', '2.11','2.11 mm',24),
]

linetypes = [
    ("CONTINUOUS", "CONTINUOUS", "So called Solid linetype", 1),
    ("CENTER", "CENTER", "CENTER linetype", 2),
    ("DASHED", "DASHED", "DASHED linetype", 3),
    ("PHANTOM", "PHANTOM", "PHANTOM linetype", 4),
    ("DASHDOT", "DASHDOT", "DASHDOT linetype", 5),
    ("DOT", "DOT", "DOT linetype", 6),
    ("DIVIDE", "DIVIDE", "DIVIDE linetype", 7),
    ("CENTERX2", "CENTERX2", "CENTERX2 linetype", 8),
    ("DASHEDX2", "DASHEDX2", "DASHEDX2 linetype", 9),
    ("PHANTOMX2", "PHANTOMX2", "PHANTOMX2 linetype", 10),
    ("DASHDOTX2", "DASHDOTX2", "DASHDOTX2 linetype", 11),
    ("DOTX2", "DOTX2", "DOTX2 linetype", 12),
    ("DIVIDEX2", "DIVIDEX2", "DIVIDEX2 linetype", 13),
    ("CENTER2", "CENTER2", "CENTER2 linetype", 14),
    ("DASHED2", "DASHED2", "DASHED2 linetype", 15),
    ("PHANTOM2", "PHANTOM2", "PHANTOM2 linetype", 16),
    ("DASHDOT2", "DASHDOT2", "DASHDOT2 linetype", 17),
    ("DOT2", "DOT2", "DOT2 linetype", 18),
    ("DIVIDE2", "DIVIDE2", "DIVIDE2 linetype", 19)
]

objecttypes3d = [
    ("FACE", "FACE", "3D polyface", 1),
    ("LINE", "LINE", "3D polyline", 2),
    ("FACE3D", "FACE3D", "3D face", 3),
]

######################
######################
#####   EXPORT   #####
######################
######################



def vertices_draw(v,scal,lvers,msp):
    ''' vertices as points draw '''
    #for x,y in [(0,10),(10,10),(10,0),(0,0)]:
    #print('VERS!!')
    for ob in v:
        vers = []
        for ver in ob:
            #vers.append(ver)
            msp.add_point([i*scal for i in ver], dxfattribs={"layer": lvers})

def hatches_draw(points, scal, lhatch, msp):
    ''' Hatch with amountt of default hatch types
        Seems like bug, hatches sometimes 
        opened in zcad and librecad 
        and others with unwanted arcs '''
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
            [[i*scal for i in ver] for ver in vers],
            is_closed=True,
            flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL,
        )

def polygons_draw(points, scal, lpols, msp):#(p,v,d1,d2,scal,lpols,msp):
    ''' draw simple polyline polygon or polyface
        todo 2026 polymesh '''
    #print('POLS!!')
    for points_ in points:
        vers,col = points_.vers, points_.color
        lw,lt = points_.lineweight, points_.linetype
        color_int = points_.color_int
        objecttype = points_.objecttype
        vers = [[i*scal for i in ver] for ver in points_.vers]
        if color_int < 1:
            col = tuple([int(i*255) for i in col[:3]])
            #print('!!!',col)
            col = ezdxf.colors.rgb2int(col)
            if objecttype == 'FACE':
                #print('face start')
                pf = msp.add_polyface()
                pf.append_face(vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'true_color': col})
                #print('face finnish')
            elif objecttype == 'LINE':
                pl = msp.add_polyline3d(vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'true_color': col}, close=True)
            elif objecttype == 'FACE3D':
                for i in range(1, len(vers)-1):
                    pf3 = msp.add_3dface([vers[0],vers[i],vers[i+1]], dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'true_color': col})
                #ezdxf.entities.Face3d
        else:
            if objecttype == 'FACE':
                #print('face start')
                pf = msp.add_polyface()
                pf.append_face(vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'color': color_int})
                #print('face finnish')
            elif objecttype == 'LINE':
                pl = msp.add_polyline3d(vers, dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'color': color_int}, close=True)
            elif objecttype == 'FACE3D':
                for i in range(1, len(vers)-1):
                    pf3 = msp.add_3dface([vers[0],vers[i],vers[i+1]], dxfattribs={"layer": lpols,'linetype': lt,'lineweight': lw, 'color': color_int})
                #ezdxf.entities.Face3d

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
        with metadata vectorized for triangles 
        2026 not in use, want not to use '''

    from sverchok.data_structure import match_long_repeat as mlr
    from mathutils import Vector
    #print('POLS!!')
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
    #print('EDGES!!')

    for points_ in points:
        vers = [[i*scal for i in ver] for ver in points_.vers]
        col = points_.color
        lw,lt = points_.lineweight, points_.linetype
        v1,v2 = vers
        color_int = points_.color_int
        if color_int < 1:
            col = tuple([int(i*255) for i in col[:3]])
            col = ezdxf.colors.rgb2int(col)
            ed = msp.add_line(v1,v2, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'true_color': col})
        else:
            ed = msp.add_line(v1,v2, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'color': color_int})

def circles_draw(points,scal,ledgs,msp):
    ''' circles as simple circles '''
    #print('CIRCLES!!')
    for points_ in points:
        curve =  points_.vers
        #print('== Curve_type','\n   ',type(curve),'\n   ',curve.__repr__(),'\n   ',curve)
        col = points_.color
        lw,lt = points_.lineweight, points_.linetype
        color_int = points_.color_int
        if curve.__repr__()[:7] == '<Circle':
            matrix = (curve.center*scal).tolist()
            radius = curve.radius*scal
            #print('==Circles export',matrix, radius)
            if color_int < 1:
                col = tuple([int(i*255) for i in col[:3]])
                col = ezdxf.colors.rgb2int(col)
                circle = msp.add_circle(center=matrix, radius=radius, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'true_color': col})
            else:
                circle = msp.add_circle(center=matrix, radius=radius, dxfattribs={"layer": ledgs,'linetype': lt,'lineweight': lw, 'color': color_int})
        elif curve.__repr__()[:7] == '<BezierCurve': # SvCurve SvEllipse SvCubicBezierCurve SvLine SvNurbsCurve SvSplineCurve Sv
            pass

def text_draw(tv,tt,scal,ltext,msp,t_scal):
    ''' draw text todo in 2026 '''
    from ezdxf.enums import TextEntityAlignment
    #print('TEXT!!')
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
    #print('LINEAR DIMS!!')
    for points_ in points:
        vers = [[i*scal for i in ver] for ver in points_.vers]
        col = points_.color
        lw,lt = points_.lineweight, points_.linetype
        v1,v2 = vers
        t_scal = points_.text_scale
        #print('LINEAR DIMS!!', t_scal)

        dim = msp.add_aligned_dim(p1=v1,p2=v2,  #p1=[i*scal for i in v1[:2]], p2=[i*scal for i in v2[:2]],\
            distance=0.5, dimstyle='Sverchok_dimstyle',dxfattribs={"layer": ldims},
            override={"dimtxt": t_scal} #,"dimfac":1}
        )
        #dim.render()

def angular_dimensions_draw(ang,scal,ldims,msp,t_scal):
    ''' 2026 todo '''
    from mathutils import Vector
    #print('ANGULAR DIMS!!')
    for a1,a2,a3 in zip(*ang):
        for ang1,ang2,ang3 in zip(a1,a2,a3):
            if scal != 1.0:
                bas = list(Vector(ang1)*scal+((Vector(ang3)*scal-Vector(ang1)*scal)/2))
                ang1_ = [i*scal for i in ang1]
                ang2_ = [i*scal for i in ang2]
                ang3_ = [i*scal for i in ang3]
                dim = msp.add_angular_dim_3p(base=bas, center=ang2_, p1=ang1_, p2=ang3_, \
                            override={"dimtad": 1,"dimtxt": t_scal}, \
                            dimstyle='Sverchok_dimstyle',dxfattribs={"layer": ldims})
            else:
                bas = list(Vector(ang1)+((Vector(ang3)-Vector(ang1))/2))
                dim = msp.add_angular_dim_3p(base=bas, center=ang2, p1=ang1, p2=ang3, \
                            override={"dimtad": 1,"dimtxt": t_scal}, \
                            dimstyle='Sverchok_dimstyle',dxfattribs={"layer": ldims})
            #dim.render()

def get_values(diction):
    data = []
    for d in diction.values():
        for i in d.values():
            data.append(i)
    return data

def leader_draw(leader,vleader,scal,llidr,msp):
    ''' 2026 todo '''
    from ezdxf.math import Vec2
    #from ezdxf.entities import mleader
    #print('LEADERS!!')
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

def clean_dimstyles_except_mine(doc, my_style_name):
    """
    Удаляет все размерные стили, кроме указанного.
    """
    all_styles = list(doc.dimstyles)
    for style in all_styles:
        if style.dxf.name != my_style_name:
            doc.dimstyles.remove(style.dxf.name)
    #doc.dimstyles.set_active_style_name(my_style_name)

# export main definition
def export(fp,dxf,scal=1000.0,t_scal=1.0,info='',do_block=False):

    DIM_TEXT_STYLE = ezdxf.options.default_dimension_text_style
    # Create a new DXF document.
    doc = ezdxf.new(dxfversion="R2010",setup=True)
    doc.units = units.MM
    # 25 строка
    doc.header['$INSUNITS'] = units.MM
    #create a new dimstyle
    glo = scal  #scal*t_scal
    hai = t_scal   #scal/glo
    if 0.0 < scal < 5.0:
        scl = 'M'
    elif 5.0 < scal < 50.0:
        scl = 'DM'
    elif 50.0 < scal < 500.0:
        scl = 'CM'
    elif 500.0 < scal:
        scl = 'MM'
    formt = f'EZ_{scl}_{int(100)}_H{int(hai*2.5*10)}_MM'
    dimstylename = 'Sverchok_dimstyle'
    #print('Format_dimentions',formt)
    '''HELP
    Example: `fmt` = 'EZ_M_100_H25_CM'
    1. '<EZ>_M_100_H25_CM': arbitrary prefix
    2. 'EZ_<M>_100_H25_CM': defines the drawing unit, valid values are 'M', 'DM', 'CM', 'MM'
    3. 'EZ_M_<100>_H25_CM': defines the scale of the drawing, '100' is for 1:100
    4. 'EZ_M_100_<H25>_CM': defines the text height in mm in paper space times 10, 'H25' is 2.5mm
    5. 'EZ_M_100_H25_<CM>': defines the units for the measurement text, valid values are 'M', 'DM', 'CM', 'MM'
    '''
    setup_dimstyle(doc,
                   name=dimstylename,
                   fmt=formt,
                   blk=ezdxf.ARROWS.architectural_tick, #closed_filled,
                   style=DIM_TEXT_STYLE,
                   )
    #my_style = doc.dimstyles[dimstylename]
    #my_style.dxf.dimtxt = 3.0      # Высота текста
    #my_style.dxf.dimasz = 2.5      # Размер стрелки
    #my_style.dxf.dimexe = 1.0      # Вынос за размерную линию
    #my_style.dxf.dimexo = 1.75     # Отступ от объекта
    #my_style.dxf.dimgap = 0.625    # Зазор вокруг текста
    #my_style.dxf.dimtad = 1        # Текст над размерной линией
    #my_style.dxf.dimunit = 2       # Метрические единицы
    #my_style.dxf.dimdec = 0        # 0 десятичных знака
    #my_style.dxf.dimclrd = 3       # Зеленый цвет размерной линии
    #my_style.dxf.dimclre = 3       # Зеленый цвет выносных линий
    #my_style.dxf.dimclrt = 1       # Красный цвет текста
    clean_dimstyles_except_mine(doc, dimstylename)
    '''HELP
    doc: DXF drawing
    fmt: format string
    style: text style for measurement
    blk: block name of arrow head, ``None`` for oblique stroke
    name: dimension style name, if name is '', `fmt` string is used as name
    {3: 'dimpost', 4: 'dimapost', 5: 'dimblk', 6: 'dimblk1', 7: 'dimblk2', 40: 'dimscale', 41: 'dimasz', 
    42: 'dimexo', 43: 'dimdli', 44: 'dimexe', 45: 'dimrnd', 46: 'dimdle', 47: 'dimtp', 48: 'dimtm', 
    49: 'dimfxl', 50: 'dimjogang', 140: 'dimtxt', 141: 'dimcen', 142: 'dimtsz', 143: 'dimaltf', 144: 'dimlfac', 
    145: 'dimtvp', 146: 'dimtfac', 147: 'dimgap', 148: 'dimaltrnd', 69: 'dimtfill', 70: 'dimtfillclr', 
    71: 'dimtol', 72: 'dimlim', 73: 'dimtih', 74: 'dimtoh', 75: 'dimse1', 76: 'dimse2', 77: 'dimtad', 
    78: 'dimzin', 79: 'dimazin', 90: 'dimarcsym', 170: 'dimalt', 171: 'dimaltd', 172: 'dimtofl', 173: 'dimsah', 
    174: 'dimtix', 175: 'dimsoxd', 176: 'dimclrd', 177: 'dimclre', 178: 'dimclrt', 179: 'dimadec', 270: 'dimunit', 
    271: 'dimdec', 272: 'dimtdec', 273: 'dimaltu', 274: 'dimalttd', 275: 'dimaunit', 276: 'dimfrac', 
    277: 'dimlunit', 278: 'dimdsep', 279: 'dimtmove', 280: 'dimjust', 281: 'dimsd1', 282: 'dimsd2', 
    283: 'dimtolj', 284: 'dimtzin', 285: 'dimaltz', 286: 'dimalttz', 287: 'dimfit', 288: 'dimupt', 
    289: 'dimatfit', 290: 'dimfxlon', 340: 'dimtxsty_handle', 342: 'dimblk_handle', 343: 'dimblk1_handle', 
    344: 'dimblk2_handle', 341: 'dimldrblk_handle', 345: 'dimltype_handle', 346: 'dimltex1_handle', 
    347: 'dimltex2_handle', 371: 'dimlwd', 372: 'dimlwe'}
    '''

    #dimstyle = doc.dimstyles.get('EZDXF1')
    #keep dim line with text
    #dimstyle.dxf.dimtmove=0
    # multyleader
    #mleaderstyle = doc.mleader_styles.new("EZDXF2") #duplicate_entry("Standard","EZDXF2")
    #mleaderstyle.set_mtext_style("OpenSans")
    #mleaderstyle.dxf.char_height = t_scal*scal  # set the default char height of MTEXT
    # Create new table entries (layers, linetypes, text styles, ...).
    ltext = "SVERCHOK_TEXT"
    lvers = "SVERCHOK_VERS"
    ledgs = "SVERCHOK_EDGES"
    lpols = "SVERCHOK_POLYGONS"
    ldims = "SVERCHOK_DIMENTIONS"
    llidr = "SVERCHOK_LEADERS"
    lhatc = "SVERCHOK_HATCHES"

    doc.layers.add(ltext, color=colors.MAGENTA)
    doc.layers.add(lvers, color=colors.CYAN)
    doc.layers.add(ledgs, color=colors.YELLOW)
    doc.layers.add(lpols, color=colors.WHITE)
    doc.layers.add(ldims, color=colors.GREEN)
    doc.layers.add(llidr, color=colors.CYAN)
    doc.layers.add(lhatc, color=colors.WHITE)

    # DXF entities (LINE, TEXT, ...) reside in a layout (modelspace,
    # paperspace layout or block definition).
    msp = doc.modelspace()
    if info:
        #print('INFO!!')
        for d in info[0].items():
            doc.header.custom_vars.append(d[0], d[1]['Value'])

    APPID = "Sverchok"
    doc.appids.add(APPID)
    doc.header["$LWDISPLAY"] = 1
    # Add entities to a layout by factory methods: layout.add_...()

    if do_block == False:
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
            if data[0].__repr__() == '<DXF Circles>':
                circles_draw(data,scal,ldims,msp)
    else:
        lib = BlockLibrary(doc)
        
        # Создаем блок
        lib.make_block('Sverchok', dxf, scal, [lpols,ledgs,lhatc,ldims])
        doc = lib.return_block()
        # Вставляем блок
        #lib.place_block('BOLT_M10', insert=(0, 0))

    '''
    if p and d1:
        polygondance_draw(p,v,d1,d2,scal,lpols,msp,APPID)
    elif v:
        vertices_draw(v,scal,lvers,msp)
    if tv and tt:
        text_draw(tv,tt,scal,ltext,msp,t_scal)
    if angular:
        angular_dimensions_draw(angular,scal,ldims,msp,t_scal)
    if vl and ll:
        leader_draw(ll,vl,scal,llidr,msp)
    '''

    # Save the DXF document.
    doc.saveas(fp[0][0])

class BlockLibrary:
    def __init__(self, doc):
        self.doc = doc
        self.block = []

    def make_block(self, name='Sverchok_block', dxf=[], scal=[], layers=[]):
        """Создает блок"""
        if not dxf:
            return
        lpols,ledgs,lhatc,ldims = layers
        block = self.doc.blocks.new(name=name)
        for data in dxf:
            if data[0].__repr__() == '<DXF Pols>':
                self.pols(block,data,scal,lpols) #(p,v,d1,d2,scal,lpols,msp)
            if data[0].__repr__() == '<DXF Lines>':
                self.edgs(block,data,scal,ledgs)
            if data[0].__repr__() == '<DXF Hatch>':
                pass
                #self.hatc(block,data,scal,lhatc)
            if data[0].__repr__() == '<DXF LinDims>':
                pass
                #self.dims(block,data,scal,ldims)
        self.block = [block]

    def pols(self,block,data,scal,lpols):
        for points_ in data:
            vers = points_.vers
            vers = [[i*scal for i in ver] for ver in vers]
            for i in range(1, len(vers)):
                block.add_line(vers[i-1][:2], vers[i][:2])
        #block.add_circle(center=(0, 0), radius=diameter/2)
    def crcl(self,block,data,scal,ledgs):
        pass

    def edgs(self,block,data,scal,ledgs):
        for points_ in data:
            vers = points_.vers
            vers = [[i*scal for i in ver] for ver in vers]
            block.add_line(vers[0][:2], vers[1][:2])

    def return_block(self):
        return self.doc

    def place_block(self, block_name, insert, rotation=0, scale=1.0):
        """Вставляет блок в чертеж, не использую"""
        block = self.block
        msp = self.doc.modelspace()
        ref = msp.add_blockref(block_name, insert=insert)
        ref.dxf.rotation = rotation
        ref.dxf.xscale = scale
        ref.dxf.yscale = scale



