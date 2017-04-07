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

import bgl
import blf



def draw_rect(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0), color2=None):

    coords = [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]
    
    if not color2:
        # FLAT
        bgl.glBegin(bgl.GL_POLYGON)
        bgl.glColor4f(*color)       
        for coord in coords:
            bgl.glVertex2f(*coord)
    else:
        # GRADIENT
        bgl.glBegin(bgl.GL_QUADS)
        for col, coord in zip((color, color, color2, color2), coords):
            bgl.glColor4f(*col)
            bgl.glVertex2f(*coord)
            
    bgl.glEnd()


def draw_border(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0)):
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    for coord in [(x, y), (x + w, y), (w + x, y - h), (x, y - h)]:
        bgl.glVertex2f(*coord)
    bgl.glEnd()


def draw_string(x, y, packed_strings):
    x_offset = 0
    font_id = 0
    for pstr, pcol in packed_strings:
        pstr2 = ' ' + pstr + ' '
        bgl.glColor4f(*pcol)
        text_width, text_height = blf.dimensions(font_id, pstr2)
        blf.position(font_id, (x + x_offset), y, 0)
        blf.draw(font_id, pstr2)
        x_offset += text_width