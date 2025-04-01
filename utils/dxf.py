# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import math


def arc_points(start, end, bulge, num_points=3, resolution): # вариант 1
    """Генерирует точки на дуге между start и end с заданным bulge."""
    if bulge == 0:
        return [start, end]  # Линейный сегмент

    # 1. Вычисляем параметры дуги
    chord = math.dist(start, end)
    sagitta = abs(bulge) * chord / 2
    radius = (chord**2) / (8 * sagitta) + sagitta / 2

    # 2. Находим центр дуги
    angle_chord = math.atan2(end[1] - start[1], end[0] - start[0])
    angle_apex = angle_chord + math.pi / 2 * (1 if bulge > 0 else -1)
    distance_apex = radius - sagitta if radius > sagitta else sagitta - radius
    center = (
        (start[0] + end[0]) / 2 + distance_apex * math.cos(angle_apex),
        (start[1] + end[1]) / 2 + distance_apex * math.sin(angle_apex)
    )

    # 3. Вычисляем начальный и конечный углы
    start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
    end_angle = math.atan2(end[1] - center[1], end[0] - center[0])

    # Корректируем углы для bulge (направление дуги)
    if bulge > 0 and end_angle <= start_angle:
        end_angle += 2 * math.pi
    elif bulge < 0 and start_angle <= end_angle:
        start_angle += 2 * math.pi

    # 4. Генерируем точки с шагом 5° (минимум 3 точки)
    total_angle = abs(end_angle - start_angle)
    angle_step = int(360/resolution)
    print(angle_step)
    step = math.radians(angle_step)  # Шаг 5°
    steps = max(2, math.ceil(total_angle / step))  # Минимум 3 точки
    delta_angle = (end_angle - start_angle) / steps

    points = []
    for i in range(steps + 1):
        angle = start_angle + i * delta_angle
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y, 0))

    return points

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
    ('1.09', '1.06','1.06 mm',19),
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
