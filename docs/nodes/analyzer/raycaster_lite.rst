Raycaster
=========

.. image:: https://user-images.githubusercontent.com/14288520/197017155-eeab3d4b-618b-49cf-8443-868f13ca18c7.png
  :target: https://user-images.githubusercontent.com/14288520/197017155-eeab3d4b-618b-49cf-8443-868f13ca18c7.png

Functionality
-------------

Functionality is almost completely analogous to the two built-in blender operators
``bpy.context.scene.ray_cast`` and ``object.ray_cast``.
Ray is casted from "start" vector to "end" vector and can hit polygons of input objects.

see docs:
`bpy.types.Object.ray_cast <http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Object.html#bpy.types.Object.ray_cast>`_ and
`bpy.types.Scene.ray_cast <http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Scene.html#bpy.types.Scene.ray_cast>`_


Input sockets
-------------

* **Verts** - Vectors of objects receiving rays
* **Faces** - Faces of objects receiving rays
* **Start** - Start position of raytracing
* **Direction** - Direction of raytracing

.. image:: https://user-images.githubusercontent.com/14288520/197019680-4183c4b0-cec0-4e81-80d9-10e0696a08ec.png
  :target: https://user-images.githubusercontent.com/14288520/197019680-4183c4b0-cec0-4e81-80d9-10e0696a08ec.png

Output sockets
--------------

+------------------------+----------------------------------------------------------------------------------------+
| socket name            | description                                                                            |
+========================+========================================================================================+
| Location               | Hit location for every raycast                                                         |
+------------------------+----------------------------------------------------------------------------------------+
| Normal                 | Normal of hit polygon                                                                  |
+------------------------+----------------------------------------------------------------------------------------+
| Index                  | index of hit *polygon*                                                                 |
+------------------------+----------------------------------------------------------------------------------------+
| Distance               | Distance between start point and hit location                                          |
+------------------------+----------------------------------------------------------------------------------------+
| Success                | ``True`` or ``False`` if ray doesn't hit any polygon.                                  |
+------------------------+----------------------------------------------------------------------------------------+

.. image:: https://user-images.githubusercontent.com/14288520/197022372-b39810a8-aae8-40fd-83ef-6b8dddaab9d6.png
  :target: https://user-images.githubusercontent.com/14288520/197022372-b39810a8-aae8-40fd-83ef-6b8dddaab9d6.png

Advanced parameters (N-Panel)
-----------------------------

* **All Triangles**: Enable if all the incoming faces are triangles to improve the performance of the algorithm
* **Safe Check**: Checks the mesh for unreferenced polygons (slows the node but prevents some Blender crashes)

Usage
-----

.. image:: https://user-images.githubusercontent.com/14288520/197025123-e1c7f09d-3338-4164-937e-ceae59966a0a.png
  :target: https://user-images.githubusercontent.com/14288520/197025123-e1c7f09d-3338-4164-937e-ceae59966a0a.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* SUB: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/28003269/38853349-08514386-422e-11e8-8444-72101d9b0ade.png
.. image:: https://user-images.githubusercontent.com/28003269/38853243-b2dc87a8-422d-11e8-96df-7d27735a5b67.gif

`calculating shadow.blend.zip <https://github.com/nortikin/sverchok/files/1918431/calculation.of.shadows_2018_04_17_06_58.zip>`_

**Replay with new nodes**

.. image:: https://user-images.githubusercontent.com/14288520/197069114-b458a783-a921-4d34-a4db-8b49b8d6c76e.gif
  :target: https://user-images.githubusercontent.com/14288520/197069114-b458a783-a921-4d34-a4db-8b49b8d6c76e.gif

.. image:: https://user-images.githubusercontent.com/14288520/197073636-3331852c-150d-4883-8c0d-303562d5066b.png
  :target: https://user-images.githubusercontent.com/14288520/197073636-3331852c-150d-4883-8c0d-303562d5066b.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Analyzers-> :doc:`Distance Point Plane </nodes/analyzer/distance_point_plane>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* CAD-> :doc:`Intersect Edges </nodes/CAD/edges_intersect_mk3>`
* CAD-> :doc:`Planar Edgenet to Faces </nodes/modifier_change/planar_edgenet_to_polygons>`
* Analyzer-> :doc:`Mesh Filter </nodes/analyzer/mesh_filter>`
* Modifiers->Modifier Change-> :doc:`Delete Loose </nodes/modifier_change/delete_loose>`
* Analyzers-> :doc:`Distance Point Plane </nodes/analyzer/distance_point_plane>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

* SUB, NEG: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Out </nodes/matrix/matrix_out_mk2>`


* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

