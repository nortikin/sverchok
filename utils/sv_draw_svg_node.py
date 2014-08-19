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
#    Params can be any ot this: 'Box', 'Slider', 'Enum', 'Enum2', 'Bool'
#    Params structure is: ('name', 'value', 'type of param')
#    For 'Enum2', 'name' value is: ('option1', 'option2', 'option3', etc.)
circle_def = {'name': 'Circle',
              'outputs': [('Vertices', '', 'VerticesSocket'),
                          ('Edges', '', 'StringsSocket'),
                          ('Polygons', '', 'StringsSocket'),],
              'params': [('Mode', True, 'Bool'),
                         (('pr1', 'pr2', 'pr3'), 'pr2', 'Enum'),
                         ('Order', 'pr1', 'Enum2'),
                         ('Order', 'pr1', 'Box'),
                         ('Prueba', '35', 'Slider'),],
              'inputs': [('Radius', '1.00', 'StringsSocket'),
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
width = 265

def slider(dwg, name, value, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=18, ry=18, fill=col_slider, stroke=col_stroke, stroke_width=1))
    dwg.add(dwg.path("M 30 "+str(pos)+" l 0 0 l 10 8 l 0 -16 M "+str(width-30)+" "+str(pos)+" l 0 0 l -10 8 l 0 -16", fill=col_arrows))
    dwg.add(dwg.text(name+':', insert=(50, pos+7), fill=col_whitetext, font_size=20))
    dwg.add(dwg.text(value, insert=(width-50, pos+7), fill=col_whitetext, font_size=20, text_anchor='end'))

def boolean(dwg, name, value, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-14), size=(28, 28), rx=4, ry=4, fill=col_boolean, stroke=col_stroke, stroke_width=0.8))
    dwg.add(dwg.text(name, insert=(60, pos+7), fill=col_darktext, font_size=20))
    if value:
        dwg.add(dwg.text(u'\u2713', insert=(20, pos+12), fill=col_whitetext, font_size=40))

def enum(dwg, name, value, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=0, ry=0, fill=col_enum, stroke=col_stroke, stroke_width=0.8))
    x = (width-40)/len(name)
    for i, v in enumerate(name):
        if v == value:
            dwg.add(dwg.rect(insert=(20+x*i, pos-16.5), size=(x, 33), fill=col_active, stroke=col_stroke, stroke_width=0))
        dwg.add(dwg.text(v, insert=(20+x/2+x*i, pos+7), fill=col_whitetext, font_size=20, text_anchor='middle'))
    for i in range(len(name)-1):
        dwg.add(dwg.line(start=(20+x*(i+1), pos+17), end=(20+x*(i+1), pos-17), stroke=col_stroke, stroke_width=0.8))

def enum2(dwg, name, value, pos, width):
    dwg.add(dwg.text(name+':', insert=(width/2-20, pos+7), fill=col_darktext, font_size=20, text_anchor='end'))
    dwg.add(dwg.rect(insert=(width/2, pos-17), size=(width/2-20, 34), rx=8, ry=8, fill=col_enum, stroke=col_stroke, stroke_width=0.8))
    dwg.add(dwg.text(value, insert=(width/2+20, pos+7), fill=col_whitetext, font_size=20))
    dwg.add(dwg.path("M "+str(width-35)+" "+str(pos-12)+" l 0 0 l 5 9 l -10 0 z M "+str(width-35)+" "+str(pos+12)+" l 0 0 l 5 -9 l -10 0 z", fill=col_arrows))

def box(dwg, name, value, pos, width):
    dwg.add(dwg.rect(insert=(20, pos-17), size=(width-40, 34), rx=8, ry=8, fill=col_box, stroke=col_stroke, stroke_width=1))
    dwg.add(dwg.text(value, insert=(40, pos+7), fill=col_darktext, font_size=20))

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
        col = ['#e59933' if v[2] == 'VerticesSocket' else '#33cccc' if v[2] == 'MatrixSocket' else '#99ff99']
        dwg.add(dwg.circle(center=(width, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
        dwg.add(dwg.text(v[0], insert=(width-25, y+5), fill='black', font_size=20, text_anchor='end'))

    for i, v in enumerate(params):
        y = 90 + 40*(len(outputs) - 1) + 40*(i+1)
        if v[2] == 'Bool':
            boolean(dwg, v[0], v[1], y, width)
        elif v[2] == 'Slider':
            slider(dwg, v[0], v[1], y, width)
        elif v[2] == 'Enum':
            enum(dwg, v[0], v[1], y, width)
        elif v[2] == 'Enum2':
            enum2(dwg, v[0], v[1], y, width)
        elif v[2] == 'Box':
            box(dwg, v[0], v[1], y, width)

    for i, v in enumerate(inputs):
        y = 140 + 40*(len(outputs) + len(params) - 2) + 40*(i+1)
        col = ['#e59933' if v[2] == 'VerticesSocket' else '#33cccc' if v[2] == 'MatrixSocket' else '#99ff99']
        dwg.add(dwg.circle(center=(0, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
        slider(dwg, v[0], v[1], y, width)
                
    dwg.save()

#draw_node(circle_def)
