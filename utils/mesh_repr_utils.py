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


import itertools


def xjoined(structure):
    """ returns a flat list of vertex indices that represent polygons,
    example input: [[0,1,2], [1,2,3], [2,3,4,5]]
    example output: [3, 0, 1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 5]
                     |           |           |
                     polygon length tokens
    """
    faces = []
    fex = faces.extend
    fap = faces.append
    len_gen = (len(p) for p in structure)
    [(fap(lp), fex(face)) for lp, face in zip(len_gen, structure)]
    return faces


def flatten(data):
    return {
        'Vertices': itertools.chain.from_iterable(data['Vertices']),
        'Edges': itertools.chain.from_iterable(data['Edges']),
        'Polygons': xjoined(data['Polygons']),
        'Matrix': itertools.chain.from_iterable(data['Matrix'])
    }


def unflatten(data, stride=None, constant=True):
    if constant == False:
        # stride is variable, means we are unrolling polygons
        polygons = []
        pap = polygons.append
        index = 0
        while(index < len(data)):
            length = data[index]
            segment = data[index+1: index+1+length]
            pap(segment)
            index += length+1
        return polygons


Test = True
if Test:
    somelist = [[0,1,2], [1,2,3], [2,3,4,5]]

    f = xjoined(somelist)
    print(f)

    xf = unflatten(f, constant=False)
    print(xf)