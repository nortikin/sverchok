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
circle_def = {'name': 'Circle',
              'outputs': ['Vertices', 'Edges', 'Polygons'],
              'params': [('Mode', True),],
              'inputs': [('Radius', '1.00', 'String'),
              			 ('N Vertices', '24', 'String'),
              			 ('Degrees', '360º', 'String'),]
              				}

def draw_node(node):
    #Defaults
    col_background = '#a7a7a7'
    col_header = '#707070'
    col_stroke = '#000'
    width = 265

    for i in node:
        name = node['name']
        outputs = node['outputs']
        params = node['params']
        inputs = node['inputs']

    height = (len(outputs) + len(params) + len(inputs))*40 + 80

    dwg = svgwrite.Drawing(name+'.svg', profile='tiny')
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), rx=18.5, ry=18.5, fill=col_background, stroke=col_stroke, stroke_width=2))
    dwg.add(dwg.path("M 18.7,0.99 c -10.1,0 -17.7,7.7 -17.7,17.7 l 0,21.8 "+str(width-2)+",0 0,-21.9 c 0,-10.0 -7.6,-17.6 -17.7,-17.6 z", fill=col_header))

    dwg.add(dwg.text(name, insert=(40, 30), fill='black', font_size=22))
    dwg.add(dwg.path("M 12 10 l 0 0 l 18 0 l -9 22 z", fill='#c46127'))

    for i, v in enumerate(outputs):
    	y = 40 + 40*(i+1)
    	col = ['#e59933' if v == 'Vertices' else '#33cccc' if v == 'Matrix' else '#99ff99']
    	dwg.add(dwg.circle(center=(width, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
    	dwg.add(dwg.text(v, insert=(width-25, y+5), fill='black', font_size=20, text_anchor='end'))

    for i,v in enumerate(params):
    	y = 70 + 40*(len(outputs) - 1) + 40*(i+1)
    	dwg.add(dwg.rect(insert=(30, y), size=(28, 28), rx=4, ry=4, fill='#414141', stroke=col_stroke, stroke_width=0.8))
    	dwg.add(dwg.text(v[0], insert=(70, y+20), fill='black', font_size=20))
    	if v[1]:
    		dwg.add(dwg.text(u'\u2713', insert=(30, y+25), fill='white', font_size=40))

    for i, v in enumerate(inputs):
    	y = 130 + 40*(len(outputs) + len(params) - 2) + 40*(i+1)
    	col = ['#e59933' if v[2] == 'Vertices' else '#33cccc' if v[2] == 'Matrix' else '#99ff99']
    	dwg.add(dwg.circle(center=(0, y), r=10, fill=col[0], stroke=col_stroke, stroke_width=1))
    	dwg.add(dwg.rect(insert=(20, y-17), size=(width-40, 34), rx=18, ry=18, fill='#1a1a1a', stroke=col_stroke, stroke_width=1))
    	dwg.add(dwg.path("M 30 "+str(y)+" l 0 0 l 10 8 l 0 -16 M "+str(width-30)+" "+str(y)+" l 0 0 l -10 8 l 0 -16", fill='#666666'))
    	dwg.add(dwg.text(v[0]+':', insert=(50, y+7), fill='white', font_size=20))
    	dwg.add(dwg.text(v[1], insert=(width-50, y+5), fill='white', font_size=20, text_anchor='end'))
    
    dwg.save()

#draw_node(circle_def)
