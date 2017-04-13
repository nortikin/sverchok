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



def route_as_macro(operator, context):

    operator.ensure_nodetree(context)
    tree = context.space_data.edit_tree
    nodes, links = tree.nodes, tree.links

    term = operator.current_string

    if term == 'obj vd':
        obj_in_node = nodes.new('SvObjInLite')
        obj_in_node.dget()
        vd_node = nodes.new('ViewerNode2')
        vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y
        
        links.new(obj_in_node.outputs[0], vd_node.inputs[0])
        links.new(obj_in_node.outputs[2], vd_node.inputs[1])
        links.new(obj_in_node.outputs[3], vd_node.inputs[2])
    else:
        return

    return True
