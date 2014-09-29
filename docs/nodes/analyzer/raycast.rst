Raycast
=======
Functionality
-------------

functionality is almost completely analogous to the two built-in blender operators: "bpy.context.scene.ray_cast" and "object.ray_cast"
http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Object.html#bpy.types.Object.ray_cast
http://www.blender.org/documentation/blender_python_api_2_71_0/bpy.types.Scene.html#bpy.types.Scene.ray_cast

Ray is casted from "start" vector to "end" vector and can hit polygons of mesh objects

Input sockets
-------------

**Start** - vertices ...

**End** - vertices ...

Parameters
----------

**object name** - name of object to analize

**match case** - enumerate property popup list ...

**iterations** - enumerate property popup list ...


Output sockets
--------------

**Hitp** - vertices ...

**Hitnorm** - vertices ...

**Index** - indexes ...

**data object** - vertices ...

**hitted object matrix** - matrix ...


Usage
-----

.. image:: https://cloud.githubusercontent.com/assets/7894950/4437227/4ac2cc4a-4790-11e4-8359-040da4398213.png
  :alt: reycast
  

