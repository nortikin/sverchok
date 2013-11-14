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

# <pep8 compliant>


# -*- coding: utf-8 -*-
# Gorodetskiy Nikita - basic idea, first script versions
# Nedovzin Alexander - nodes integration, all corrections and script rebuilding
# 2013-09-03 some bugfixes, default max, errors in first start etc. version 0.1.3
# 2013-09-29 complete rebuilding of addon huge work is going to version 0.2.0
# 2013-10-10 viewer nodes addad, bugfixing go on
# http://nikitron.cc.ua


bl_info = {
    "name": "Sverchok",
    "author": "Nedovizin Alexander, Gorodetskiy Nikita",
    "version": (0, 2, 0),
    "blender": (2, 6, 8), 
    "location": "Nodes > CustomNodesTree > Add user nodes",
    "description": "Do parametric node-based geometry programming",
    "warning": "requires nodes window",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Sverchok",
    "tracker_url": "http://www.blenderartists.org/forum/showthread.php?272679-Addon-WIP-Sverchok-parametric-tool-for-architects",
    "category": "Node"}


import sys,os
path = sys.path
flag = False
for item in path:
    if "sverchok" in item:
        flag = True
if flag == False:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sverchok_nodes'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sverchok-master'))
    print("sverchok_nodes: added to phytonpath :-)")



if "bpy" in locals():
    import imp
    imp.reload(node_s)
    imp.reload(node_CentersPolsNode)
    imp.reload(util)
    imp.reload(node_Objects)
    imp.reload(node_Viewer)
    imp.reload(node_Viewer_text)
    imp.reload(Viewer_draw)
    imp.reload(node_ListLevels)
    imp.reload(node_ListJoin2)
    imp.reload(node_Zip)
    imp.reload(node_Shift)
    imp.reload(node_ListReverse)
    imp.reload(node_DistancePP)
    imp.reload(node_Series)
    imp.reload(node_Vector)
    imp.reload(node_Vector_out)
    imp.reload(node_Random)
    imp.reload(node_Float)
    imp.reload(node_Integer)
    imp.reload(node_Number)
    imp.reload(node_Move)
    imp.reload(node_MatrixDeform)
    imp.reload(node_MatrixGenerator)
    imp.reload(node_Formula)
    imp.reload(node_Tools)
else:
    import node_s
    import node_CentersPolsNode
    import util
    import node_Objects
    import node_Viewer
    import node_Viewer_text
    import Viewer_draw
    import node_ListLevels
    import node_ListJoin2
    import node_Zip
    import node_Shift
    import node_ListReverse
    import node_DistancePP
    import node_Series
    import node_Vector
    import node_Vector_out
    import node_Random
    import node_Float
    import node_Integer
    import node_Number
    import node_Move
    import node_MatrixDeform
    import node_MatrixGenerator
    import node_Formula
    import node_Tools

def register():
    import bpy
    import nodeitems_utils
    node_s.register()
    node_CentersPolsNode.register()
    node_Objects.register()
    node_Viewer.register()
    node_Viewer_text.register()
    node_ListLevels.register()
    node_ListJoin2.register()
    node_Zip.register()
    node_Shift.register()
    node_ListReverse.register()
    node_DistancePP.register()
    node_Series.register()
    node_Vector.register()
    node_Vector_out.register()
    node_Random.register()
    node_Float.register()
    node_Integer.register()
    node_Number.register()
    node_Move.register()
    node_MatrixDeform.register()
    node_MatrixGenerator.register()
    node_Formula.register()
    node_Tools.register()
    
        
    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", node_s.make_categories())
    
    
def unregister():
    import bpy
    import nodeitems_utils
    node_Tools.unregister()
    node_Formula.unregister()
    node_MatrixGenerator.unregister()
    node_MatrixDeform.unregister()
    node_Move.unregister()
    node_Number.unregister()
    node_Integer.unregister()
    node_Float.unregister()
    node_Random.unregister()
    node_Vector_out.unregister()
    node_Vector.unregister()
    node_Series.unregister()
    node_DistancePP.unregister()
    node_ListReverse.unregister()
    node_Shift.unregister()
    node_Zip.unregister()
    node_ListJoin2.unregister()
    node_ListLevels.unregister()
    node_Viewer_text.unregister()
    node_Viewer.unregister()
    #node_Objects_out.unregister()
    node_Objects.unregister()
    node_CentersPolsNode.unregister()
    node_s.unregister()
    
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
        
if __name__ == "__main__":
    register()
    #import nodeitems_utils
    #if 'SVERCHOK' in nodeitems_utils._node_categories:
        #unregister()
    #else:
        #register()