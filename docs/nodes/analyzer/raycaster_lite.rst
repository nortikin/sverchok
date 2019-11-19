Raycast
=======

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

**Verts** - Vectors of objects receiving rays

**Faces** - Faces of objects receiving rays

**Start** - Start position of raytracing

**Direction** - Direction of raytracing

Output sockets
--------------

+------------------------+----------------------------------------------------------------------------------------+
| socket name            | description                                                                            |
+========================+========================================================================================+
| Location               | Hit location for every raycast                                                         |
+------------------------+----------------------------------------------------------------------------------------+
| Normal                 | Normal of hit polygon                                                                  |
+------------------------+----------------------------------------------------------------------------------------+
| Index                  | index of hit polygon                                                                   |
+------------------------+----------------------------------------------------------------------------------------+
| Distance               | Distance between start point and hit location                                          |
+------------------------+----------------------------------------------------------------------------------------+
| Success                | ``True`` or ``False`` if ray doesn't hit any polygon.                                  |
+------------------------+----------------------------------------------------------------------------------------+


Usage
-----

.. image:: https://user-images.githubusercontent.com/28003269/38853137-5a0b6e50-422d-11e8-97bc-8d5046387e25.png
.. image:: https://user-images.githubusercontent.com/28003269/38853349-08514386-422e-11e8-8444-72101d9b0ade.png
.. image:: https://user-images.githubusercontent.com/28003269/38853243-b2dc87a8-422d-11e8-96df-7d27735a5b67.gif

`calculating shadow.blend.zip <https://github.com/nortikin/sverchok/files/1918431/calculation.of.shadows_2018_04_17_06_58.zip>`_
