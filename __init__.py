 #  ***** BEGIN GPL LICENSE BLOCK *****
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
 #  along with this program; if not, see <http://www.gnu.org/licenses/>
 #  and write to the Free Software Foundation, Inc., 51 Franklin Street, 
 #  Fifth Floor, Boston, MA  02110-1301, USA..
 #
 #  The Original Code is Copyright (C) 2013-2014 by Gorodetskiy Nikita	###
 #  All rights reserved.
 #
 #  Contact:      sverchok-b3d@yandex.ru	###
 #  Information:  http://nikitron.cc.ua/sverchok.html	###
 #
 #  The Original Code is: all of this file.
 #
 #  Contributor(s): Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Gimenez.
 #
 #  ***** END GPL LICENSE BLOCK *****
 #
 # -*- coding: utf-8 -*-


bl_info = {
    "name": "Sverchok",
    "author": "Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Jimenez",
    "version": (0, 2, 7),
    "blender": (2, 6, 9), 
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
    imp.reload(node_ScalarMath)
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
    imp.reload(node_ListLength)
    imp.reload(node_ListFunc)
    imp.reload(node_ListSum)
    imp.reload(node_ListStartEnd)
    imp.reload(node_ListItem)
    imp.reload(node_ListRepeater)
    imp.reload(node_ListBoom)
    imp.reload(node_ListSort)
    imp.reload(node_DistancePP)
    imp.reload(node_Series)
    imp.reload(node_Vector)
    imp.reload(node_Vector_out)
    imp.reload(node_VectorNormal)
    imp.reload(node_MatrixApply)
    imp.reload(node_VectorDrop)
    imp.reload(node_RandomVector) 
    imp.reload(node_Random)
    imp.reload(node_Float)
    imp.reload(node_Integer)
    imp.reload(node_Float2Int)
    imp.reload(node_VectorMove)
    imp.reload(node_VectorMath)
    imp.reload(node_MatrixDeform)
    imp.reload(node_MatrixGenerator)
    imp.reload(node_MatrixDestructor)
    imp.reload(node_MatrixShear)
    imp.reload(node_MatrixInterpolation)
    imp.reload(node_WifiOut)
    imp.reload(node_WifiIn)
    imp.reload(node_Formula)
    imp.reload(node_Formula2)
    imp.reload(node_Tools)
    imp.reload(node_AdaptivePolygons)
    imp.reload(node_CrossSection)
    imp.reload(node_Line)
    imp.reload(node_Hilbert)
    imp.reload(node_HilbertImage)
    imp.reload(node_Voronoi2D)
    imp.reload(node_Plane)
    imp.reload(node_Circle)
    imp.reload(node_Cylinder)
    imp.reload(node_Sphere)
    imp.reload(node_EvaluateLine)
    imp.reload(node_MaskList)
    imp.reload(node_Image)
    imp.reload(node_LineConnect)
    imp.reload(node_Area)
    imp.reload(node_Range)
    imp.reload(node_Converter)
    imp.reload(node_ListFlip)
    #imp.reload(node_Test1)
    imp.reload(node_Text)
else:
    import node_s
    import node_ScalarMath
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
    import node_ListLength
    import node_ListFunc
    import node_ListSum
    import node_ListStartEnd
    import node_ListItem
    import node_ListRepeater
    import node_ListBoom
    import node_ListSort
    import node_DistancePP
    import node_Series
    import node_Vector
    import node_Vector_out
    import node_VectorNormal
    import node_MatrixApply
    import node_VectorDrop
    import node_Random
    import node_RandomVector
    import node_Float
    import node_Integer
    import node_Float2Int
    import node_VectorMove
    import node_VectorMath
    import node_MatrixDeform
    import node_MatrixGenerator
    import node_MatrixDestructor
    import node_MatrixShear
    import node_MatrixInterpolation
    import node_WifiOut
    import node_WifiIn
    import node_Formula
    import node_Formula2
    import node_Tools
    import node_AdaptivePolygons
    import node_CrossSection
    import node_Line
    import node_Hilbert
    import node_HilbertImage
    import node_Voronoi2D
    import node_Plane
    import node_Circle
    import node_Cylinder
    import node_Sphere
    import node_EvaluateLine
    import node_MaskList
    import node_Image
    import node_LineConnect
    import node_Area
    import node_Range
    import node_Converter
    import node_ListFlip
    #import node_Test1
    import node_Text

def register():
    import bpy
    import nodeitems_utils
    node_s.register()
    node_ScalarMath.register()
    node_CentersPolsNode.register()
    node_Objects.register()
    node_Viewer.register()
    node_Viewer_text.register()
    node_ListLevels.register()
    node_ListJoin2.register()
    node_Zip.register()
    node_Shift.register()
    node_ListReverse.register()
    node_ListLength.register()
    node_ListFunc.register()
    node_ListSum.register()
    node_ListStartEnd.register()
    node_ListItem.register()
    node_ListRepeater.register()
    node_ListBoom.register()
    node_ListSort.register()
    node_DistancePP.register()
    node_Series.register()
    node_Vector.register()
    node_Vector_out.register()
    node_VectorNormal.register()
    node_MatrixApply.register()
    node_VectorDrop.register()
    node_Random.register()
    node_RandomVector.register()
    node_Float.register()
    node_Integer.register()
    node_Float2Int.register()
    node_VectorMove.register()
    node_VectorMath.register()
    node_MatrixDeform.register()
    node_MatrixGenerator.register()
    node_MatrixDestructor.register()
    node_MatrixShear.register()
    node_MatrixInterpolation.register()
    node_WifiOut.register()
    node_WifiIn.register()
    node_Formula.register()
    node_Formula2.register()
    node_Tools.register()
    node_AdaptivePolygons.register()
    node_CrossSection.register()
    node_Line.register()
    node_Hilbert.register()
    node_HilbertImage.register()
    node_Voronoi2D.register()
    node_Plane.register()
    node_Circle.register()
    node_Cylinder.register()
    node_Sphere.register()
    node_EvaluateLine.register()
    node_MaskList.register()
    node_Image.register()
    node_LineConnect.register()
    node_Area.register()
    node_Range.register()
    node_Converter.register()
    node_ListFlip.register()
    #node_Test1.register()
    node_Text.register()
        
    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", node_s.make_categories())
    
    
def unregister():
    import bpy
    import nodeitems_utils
    
    node_Text.unregister()
    #node_Test1.unregister()
    node_ListFlip.unregister()
    node_Converter.unregister()
    node_Range.unregister()
    node_Area.unregister()
    node_LineConnect.unregister()
    node_Image.unregister()
    node_MaskList.unregister()
    node_EvaluateLine.unregister()
    node_Sphere.unregister()
    node_Cylinder.unregister()
    node_Circle.unregister()
    node_Plane.unregister()
    node_Voronoi2D.unregister()
    node_HilbertImage.unregister()
    node_Hilbert.unregister()
    node_Line.unregister()
    node_CrossSection.unregister()
    node_AdaptivePolygons.unregister()
    node_Tools.unregister()
    node_Formula2.unregister()
    node_Formula.unregister()
    node_WifiIn.unregister()
    node_WifiOut.unregister()
    node_MatrixInterpolation.unregister()
    node_MatrixShear.unregister()
    node_MatrixDestructor.unregister()
    node_MatrixGenerator.unregister()
    node_MatrixDeform.unregister()
    node_VectorMath.unregister()
    node_VectorMove.unregister()
    node_Float2Int.unregister()
    node_Integer.unregister()
    node_Float.unregister()
    node_RandomVector.unregister()
    node_Random.unregister()
    node_VectorDrop.unregister()
    node_MatrixApply.unregister()
    node_VectorNormal.unregister()
    node_Vector_out.unregister()
    node_Vector.unregister()
    node_Series.unregister()
    node_DistancePP.unregister()
    node_ListSort.unregister()
    node_ListBoom.unregister()
    node_ListRepeater.unregister()
    node_ListItem.unregister()
    node_ListStartEnd.unregister()
    node_ListSum.unregister()
    node_ListFunc.unregister()
    node_ListLength.unregister()
    node_ListReverse.unregister()
    node_Shift.unregister()
    node_Zip.unregister()
    node_ListJoin2.unregister()
    node_ListLevels.unregister()
    node_Viewer_text.unregister()
    node_Viewer.unregister()
    node_Objects.unregister()
    node_CentersPolsNode.unregister()
    node_ScalarMath.unregister()
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
