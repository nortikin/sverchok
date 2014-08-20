# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import svgwrite

# Sample dictionary
#    Params can be any ot this: 'Box', 'Slider', 'Enum', 'Enum2', 'Bool', 'Text', 'Button'
#    Params structure is: ('name', 'value', 'type of param')
#    Enum param: (['t1', 't2', 't3'], 't2', 'Enum')
#    One boolean in a row: ('Mode', True, 'Bool')
#    Two booleans in same row: (['Mode', 'Mode2'], [True, False], 'Bool')
#    If value of an input is empty, only socket and name are displayed
#    For more than one slider value in a row: (['A', 'B', 'C'], ['35', '45', '63'], 'Slider')
circle_def = {'name': 'Circle',
              'outputs': [('Vertices', '', 'VerticesSocket'),
                          ('Edges', '', 'StringsSocket'),
                          ('Polygons', '', 'StringsSocket'),],
              'params': [(['Mode'], [True], 'Bool'),
                         (['t1', 't2', 't3'], 't2', 'Enum'),
                         ('Order', 'test', 'Enum2'),
                         (['Mode', 'Mode2'], [True, False], 'Bool'),
                         ('Order', '', 'Box'),
                         ('Testing:', '', 'Text'),
                         ('Button Test', '', 'Button'),
                         (['A', 'B', 'C'], ['35', '45', '63'], 'Slider'),
                         ('Test', '35', 'Slider'),],
              'inputs': [('Radius', '', 'StringsSocket'),
                         ('N Vertices', '24', 'StringsSocket'),
                         ('Degrees', '360º', 'StringsSocket'),]
                         }

#Defaults
col_background = '#a7a7a7'
col_header = '#707070'
col_stroke = '#000'
col_darktext = 'black'
col_whitetext = 'white'
col_slider = '#1a1a1a'
col_arrows = '#777777'
col_boolean = '#414141'
col_enum = '#414141'
col_active = '#5781c3'
col_box = '#bfbfbf'
col_button = '#838383'
VerticesSocket = '#e59933'
StringsSocket = '#99ff99'
MatrixSocket = '#33cccc'
width = 265

def slider(dwg, parameter, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=18, ry=18, fill=col_slider, stroke=col_stroke, stroke_width=1))
    if type(parameter[1]) is list:
        x = (width-40)/len(parameter[1])
        for i, v in enumerate(parameter[0]):
            dwg.add(dwg.text(v+':', insert=(50+x*i, pos+7), fill=col_whitetext, font_size=20))
        for i, v in enumerate(parameter[1]):
            dwg.add(dwg.text(v, insert=(x*i+x-10, pos+7), fill=col_whitetext, font_size=20, text_anchor='end'))
            dwg.add(dwg.path("M "+str(30+x*i)+" "+str(pos)+" l 0 0 l 10 8 l 0 -16 M "+str(x*i+x+10)+" "+str(pos)+" l 0 0 l -10 8 l 0 -16", fill=col_arrows))
        for i in range(len(parameter[1])-1):
            dwg.add(dwg.line(start=(20+x*(i+1), pos+17), end=(20+x*(i+1), pos-17), stroke=col_background, stroke_width=0.5))
    else:
        dwg.add(dwg.path("M 30 "+str(pos)+" l 0 0 l 10 8 l 0 -16 M "+str(width-30)+" "+str(pos)+" l 0 0 l -10 8 l 0 -16", fill=col_arrows))
        dwg.add(dwg.text(parameter[0]+':', insert=(50, pos+7), fill=col_whitetext, font_size=20))
        dwg.add(dwg.text(parameter[1], insert=(width-50, pos+7), fill=col_whitetext, font_size=20, text_anchor='end'))

def boolean(dwg, parameter, pos, width):
    a = [2 if len(parameter[0]) == 2 else 1]
    for i in range(a[0]):
        dwg.add(dwg.rect(insert=(20+i*(width/2-20), pos-14), size=(28, 28), rx=4, ry=4, fill=col_boolean, stroke=col_stroke, stroke_width=0.8))
        dwg.add(dwg.text(parameter[0][i], insert=(60+i*(width/2-20), pos+7), fill=col_darktext, font_size=20))
        if parameter[1][i]:
            dwg.add(dwg.text(u'\u2713', insert=(20+i*(width/2-20), pos+12), fill=col_whitetext, font_size=40))

def enum(dwg, parameter, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=0, ry=0, fill=col_enum, stroke=col_stroke, stroke_width=0.8))
    x = (width-40)/len(parameter[0])
    for i, v in enumerate(parameter[0]):
        if v == parameter[1]:
            dwg.add(dwg.rect(insert=(20+x*i, pos-16.5), size=(x, 33), fill=col_active, stroke=col_stroke, stroke_width=0))
        dwg.add(dwg.text(v, insert=(20+x/2+x*i, pos+7), fill=col_whitetext, font_size=20, text_anchor='middle'))
    for i in range(len(parameter[0])-1):
        dwg.add(dwg.line(start=(20+x*(i+1), pos+17), end=(20+x*(i+1), pos-17), stroke=col_stroke, stroke_width=0.8))

def enum2(dwg, parameter, pos, width):
    dwg.add(dwg.text(parameter[0]+':', insert=(width/2-20, pos+7), fill=col_darktext, font_size=20, text_anchor='end'))
    dwg.add(dwg.rect(insert=(width/2, pos-17), size=(width/2-20, 34), rx=8, ry=8, fill=col_enum, stroke=col_stroke, stroke_width=0.8))
    dwg.add(dwg.text(parameter[1], insert=(width/2+20, pos+7), fill=col_whitetext, font_size=20))
    dwg.add(dwg.path("M "+str(width-35)+" "+str(pos-12)+" l 0 0 l 5 9 l -10 0 z M "+str(width-35)+" "+str(pos+12)+" l 0 0 l 5 -9 l -10 0 z", fill=col_arrows))

def box(dwg, parameter, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=8, ry=8, fill=col_box, stroke=col_stroke, stroke_width=1))
    dwg.add(dwg.text(parameter[0], insert=(40, pos+7), fill=col_darktext, font_size=20))

def text(dwg, parameter, pos, width):
    dwg.add(dwg.text(parameter[0], insert=(30, pos+7), fill=col_darktext, font_size=20))

def button(dwg, parameter, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=8, ry=8, fill=col_button, stroke=col_stroke, stroke_width=1))
    dwg.add(dwg.text(parameter[0], insert=(width/2, pos+7), fill=col_darktext, font_size=20, text_anchor='middle'))

methods = {'Bool': boolean,
           'Enum': enum,
           'Enum2': enum2,
           'Box': box,
           'Slider': slider,
           'Text': text,
           'Button': button}

def draw_node(node):
    for i in node:
        name = node['name']
        outputs = node['outputs']
        params = node['params']
        inputs = node['inputs']

    height = (len(outputs) + len(params) + len(inputs))*40 + 100

    dwg = svgwrite.Drawing(name+'.svg', profile='tiny')
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), rx=18.5, ry=18.5, fill=col_background, stroke=col_stroke, stroke_width=2))
    dwg.add(dwg.path("M 18.7,0.99 c -10.1,0 -17.7,7.7 -17.7,17.7 l 0,21.8 "+str(width-2)+",0 0,-21.9 c 0,-10.0 -7.6,-17.6 -17.7,-17.6 z", fill=col_header))

    dwg.add(dwg.text(name, insert=(40, 30), fill='black', font_size=22))
    dwg.add(dwg.path("M 12 10 l 0 0 l 18 0 l -9 22 z", fill='#c46127'))

    for i, v in enumerate(outputs):
        y = 40 + 40*(i+1)
        col = [VerticesSocket if v[2] == 'VerticesSocket' else MatrixSocket if v[2] == 'MatrixSocket' else StringsSocket]
        dwg.add(dwg.circle(center=(width, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
        dwg.add(dwg.text(v[0], insert=(width-25, y+5), fill='black', font_size=20, text_anchor='end'))

    for i, v in enumerate(params):
        y = 90 + 40*(len(outputs) - 1) + 40*(i+1)
        if v[2] in methods:
            methods[v[2]](dwg, v, y, width)

    for i, v in enumerate(inputs):
        y = 140 + 40*(len(outputs) + len(params) - 2) + 40*(i+1)
        col = [VerticesSocket if v[2] == 'VerticesSocket' else MatrixSocket if v[2] == 'MatrixSocket' else StringsSocket]
        dwg.add(dwg.circle(center=(0, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
        if len(v[1]) == 0:
            dwg.add(dwg.text(v[0], insert=(30, y+7), fill=col_darktext, font_size=20))
        else:
            slider(dwg, v, y, width)            
                
    dwg.save()

#draw_node(circle_def)
