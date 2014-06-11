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
 #  The Original Code is Copyright (C) 2013-2014 by Gorodetskiy Nikita  ###
 #  All rights reserved.
 #
 #  Contact:      sverchok-b3d@yandex.ru    ###
 #  Information:  http://nikitron.cc.ua/sverchok.html   ###
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
    "author": "Nedovizin Alexander, Gorodetskiy Nikita, Linus Yng, Agustin Jimenez, Dealga McArdle",
    "version": (0, 3, 0),
    "blender": (2, 7, 0), 
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

    print("Sverchok_nodes: added to pythonpath :-)")
    print("Have a nice day with Sverchok")



if "bpy" in locals():
    import imp
    imp.reload(node_s)
    imp.reload(node_ScalarMath)
    imp.reload(node_CentersPolsNode)
    imp.reload(util)
    imp.reload(node_Objects)
    imp.reload(node_Viewer)
    imp.reload(node_Viewer_text)
    imp.reload(node_IDXview)
    imp.reload(Viewer_draw)
    imp.reload(Index_Viewer_draw)
    imp.reload(node_ListLevels)
    imp.reload(node_ListJoin2)
    imp.reload(node_Zip)
    imp.reload(node_Shift)
    imp.reload(node_ListSlice)
    imp.reload(node_ListShuffle)
    imp.reload(node_ListReverse)
    imp.reload(node_ListLength)
    imp.reload(node_ListFunc)
    imp.reload(node_ListSum)
    imp.reload(node_ListStartEnd)
    imp.reload(node_ListItem)
    imp.reload(node_ListRepeater)
    imp.reload(node_PolygonBoom)
    imp.reload(node_ListSort)
    imp.reload(node_ListMatch)
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
    imp.reload(Tools)
    imp.reload(node_AdaptivePolygons)
    imp.reload(node_AdaptiveEdges)
    imp.reload(node_CrossSection)
    imp.reload(node_Bisect)
    imp.reload(node_Solidify)
    imp.reload(node_Wireframe)
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
    imp.reload(node_FrameNode)
    imp.reload(node_Test1)
    imp.reload(node_Text)
    imp.reload(node_Script)
    imp.reload(node_Pols2Edgs)
    imp.reload(node_Note)
    imp.reload(node_Bakery)
    imp.reload(node_VertsDelDoubles)
    imp.reload(node_RemoveDoubles)
    imp.reload(node_DeleteLoose)
    imp.reload(node_MeshJoin)
    imp.reload(node_VertSort)
    imp.reload(node_ConvexHull)
    imp.reload(node_KDTree)
    imp.reload(text_editor_Submenu)
    imp.reload(node_Intersect_Edges)
    imp.reload(node_Box)
    imp.reload(node_KDTree_Edges)
    imp.reload(node_ListInput)
    imp.reload(text_editor_Plugins)
    imp.reload(node_ListDecompose)
    imp.reload(node_Noise)
    imp.reload(node_BMeshview)
    imp.reload(node_MatrixInput)
    imp.reload(node_ListRangeInt)
    imp.reload(node_DebugPrint)
    imp.reload(node_ListRangeFloat)
    imp.reload(node_BBox)
    imp.reload(node_MapRange)
    imp.reload(node_SeparateMesh)
    imp.reload(node_GText)    
    imp.reload(node_FillHole)
    imp.reload(node_ListSplit)
    imp.reload(node_VertMask)
    imp.reload(node_Interpolation)
    imp.reload(node_Lathe)
    imp.reload(node_MaskJoin)
    
else:
    import node_s
    import node_ScalarMath
    import node_CentersPolsNode
    import util
    import node_Objects
    import node_Viewer
    import node_Viewer_text
    import node_IDXview
    import Viewer_draw
    import Index_Viewer_draw
    import node_ListLevels
    import node_ListJoin2
    import node_Zip
    import node_Shift
    import node_ListSlice
    import node_ListShuffle
    import node_ListReverse
    import node_ListLength
    import node_ListFunc
    import node_ListSum
    import node_ListStartEnd
    import node_ListItem
    import node_ListRepeater
    import node_PolygonBoom
    import node_ListSort
    import node_ListMatch
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
    import Tools
    import node_AdaptivePolygons
    import node_AdaptiveEdges
    import node_CrossSection
    import node_Bisect
    import node_Solidify
    import node_Wireframe
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
    import node_FrameNode
    import node_Test1
    import node_Text
    import node_Script
    import node_Pols2Edgs
    import node_Note
    import node_Bakery
    import node_VertsDelDoubles
    import node_RemoveDoubles
    import node_DeleteLoose
    import node_MeshJoin
    import node_VertSort
    import node_ConvexHull
    import node_KDTree
    import text_editor_Submenu
    import node_Intersect_Edges
    import node_Box
    import node_KDTree_Edges
    import node_ListInput
    import text_editor_Plugins
    import node_ListDecompose
    import node_Noise
    import node_BMeshview
    import node_MatrixInput
    import node_ListRangeInt
    import node_DebugPrint
    import node_ListRangeFloat
    import node_BBox
    import node_MapRange
    import node_SeparateMesh
    import node_GText
    import node_FillHole
    import node_ListSplit
    import node_VertMask
    import node_Interpolation
    import node_Lathe
    import node_MaskJoin
    
import bpy
from bpy.types import AddonPreferences
from bpy.props import  BoolProperty, FloatVectorProperty
import util

def update_debug_mode(self,context):
    util.DEBUG_MODE = self.show_debug

class SverchokPreferences(AddonPreferences):

    bl_idname = __name__
    
    show_debug = BoolProperty(name="Print update timings", 
                        description="Print update timings in console", 
                        default=False, subtype='NONE',
                        update = update_debug_mode)
    
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_debug")
        

def register():
    import bpy
    import nodeitems_utils
    node_s.register()
    node_ScalarMath.register()
    node_CentersPolsNode.register()
    node_Objects.register()
    node_Viewer.register()
    node_Viewer_text.register()
    node_IDXview.register()
    node_ListLevels.register()
    node_ListJoin2.register()
    node_Zip.register()
    node_Shift.register()
    node_ListSlice.register()
    node_ListShuffle.register()
    node_ListReverse.register()
    node_ListLength.register()
    node_ListFunc.register()
    node_ListSum.register()
    node_ListStartEnd.register()
    node_ListItem.register()
    node_ListRepeater.register()
    node_PolygonBoom.register()
    node_ListSort.register()
    node_ListMatch.register()
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
    Tools.register()
    node_AdaptivePolygons.register()
    node_AdaptiveEdges.register()
    node_CrossSection.register()
    node_Bisect.register()
    node_Solidify.register()
    node_Wireframe.register()
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
    node_FrameNode.register()
    node_Test1.register()
    node_Text.register()
    node_Script.register()
    node_Pols2Edgs.register()
    node_Note.register()
    node_Bakery.register()
    node_VertsDelDoubles.register()
    node_RemoveDoubles.register()
    node_DeleteLoose.register()
    node_MeshJoin.register()
    node_VertSort.register()
    node_ConvexHull.register()
    node_KDTree.register()
    text_editor_Submenu.register()
    node_Intersect_Edges.register()
    node_Box.register()
    node_KDTree_Edges.register()
    node_ListInput.register()
    text_editor_Plugins.register()
    node_ListDecompose.register()
    node_Noise.register()
    node_BMeshview.register()
    node_MatrixInput.register()
    node_ListRangeInt.register()
    node_DebugPrint.register()
    node_ListRangeFloat.register()
    node_BBox.register()
    node_MapRange.register()
    node_SeparateMesh.register()
    node_GText.register()
    node_FillHole.register()
    node_ListSplit.register()
    node_VertMask.register()
    node_Interpolation.register()
    node_Lathe.register()
    node_MaskJoin.register()
    
    bpy.utils.register_class(SverchokPreferences)
       
    if 'SVERCHOK' not in nodeitems_utils._node_categories:
        nodeitems_utils.register_node_categories("SVERCHOK", node_s.make_categories())
    
    
def unregister():
    import bpy
    import nodeitems_utils

    node_MaskJoin.unregister()
    node_Lathe.unregister()
    node_Interpolation.unregister()
    node_VertMask.unregister()
    node_ListSplit.unregister()
    node_FillHole.unregister()
    node_GText.unregister()    
    node_SeparateMesh.unregister()
    node_MapRange.unregister()
    node_BBox.unregister()
    node_ListRangeFloat.unregister()
    node_DebugPrint.unregister()
    node_ListRangeInt.unregister()
    node_MatrixInput.unregister()
    node_BMeshview.unregister()
    node_Noise.unregister()
    node_ListDecompose.unregister()    
    text_editor_Plugins.unregister()    
    node_ListInput.unregister()
    node_KDTree_Edges.unregister()
    node_Box.unregister()
    node_Intersect_Edges.unregister()
    text_editor_Submenu.unregister()
    node_KDTree.unregister()
    node_ConvexHull.unregister()
    node_VertSort.unregister()
    node_MeshJoin.unregister()
    node_DeleteLoose.unregister()
    node_RemoveDoubles.unregister()
    node_VertsDelDoubles.unregister()
    node_Bakery.unregister()
    node_Note.unregister()
    node_Pols2Edgs.unregister()
    node_Script.unregister()
    node_Text.unregister()
    node_Test1.unregister()
    node_FrameNode.unregister()
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
    node_Wireframe.unregister()
    node_Solidify.unregister()
    node_Bisect.unregister()
    node_CrossSection.unregister()
    node_AdaptiveEdges.unregister()
    node_AdaptivePolygons.unregister()
    Tools.unregister()
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
    node_ListMatch.unregister()
    node_ListSort.unregister()
    node_PolygonBoom.unregister()
    node_ListRepeater.unregister()
    node_ListItem.unregister()
    node_ListStartEnd.unregister()
    node_ListSum.unregister()
    node_ListFunc.unregister()
    node_ListLength.unregister()
    node_ListReverse.unregister()
    node_ListShuffle.unregister()
    node_ListSlice.unregister()
    node_Shift.unregister()
    node_Zip.unregister()
    node_ListJoin2.unregister()
    node_ListLevels.unregister()
    node_IDXview.unregister()
    node_Viewer_text.unregister()
    node_Viewer.unregister()
    node_Objects.unregister()
    node_CentersPolsNode.unregister()
    node_ScalarMath.unregister()
    node_s.unregister()
    
    bpy.utils.unregister_class(SverchokPreferences)
    
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
        
#if __name__ == "__main__":
    #register()
    #import nodeitems_utils
    #if 'SVERCHOK' in nodeitems_utils._node_categories:
        #unregister()
    #else:
        #register()
