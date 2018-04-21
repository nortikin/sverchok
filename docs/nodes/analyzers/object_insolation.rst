Insolation
==========

Functionality
-------------

Thankfully for ``bpy.context.scene.ray_cast`` and ``object.ray_cast``. 
- Having your building object in scene (victim) with a material on it;
- and other buildings objects in scene that shades your (predator);
- and having vectors rays from zero to sun position by hours you will get:
You'll get vertex colors in material, that express shading,
And numbers in hours that left from predator hunted.

see docs: 
`bpy.types.Object.ray_cast <http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Object.html#bpy.types.Object.ray_cast>`_ and 
`bpy.types.Scene.ray_cast <http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Scene.html#bpy.types.Scene.ray_cast>`_


Input sockets
-------------

**Predator** - your predator external buildings (polygons takes)

**Victim** -  your victim projecting building

**SunRays** -  your sun positions direction from zero to find intersection 
    (list of vertices)

Parameters
----------

+-----------------+--------------------------------------------------------------------------------------------------+
| parameter       | description                                                                                      | 
+=================+==================================================================================================+
| limit           | Limit of hours, that will be shown in index viewer                                               |
+-----------------+--------------------------------------------------------------------------------------------------+


Output sockets
--------------

+------------------------+----------------------------------------------------------------------------------------+
| socket name            | description                                                                            |
+========================+========================================================================================+
| Centers                | Centers of victim' polygons                                                            |
+------------------------+----------------------------------------------------------------------------------------+
| Hours                  | Hours text for index viewer node text input                                            |
+------------------------+----------------------------------------------------------------------------------------+


Usage
-----

Open templates - insolation example

.. image:: https://user-images.githubusercontent.com/5783432/37124037-b1b6e7cc-2277-11e8-9a3a-922ca613579c.png

Use objects (materials should be with cycles nodes active for victim)

.. image:: https://user-images.githubusercontent.com/5783432/37124038-b1f1f484-2277-11e8-8682-9f5e9059672f.png
