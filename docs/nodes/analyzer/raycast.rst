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

**Start** - "start" vectors

**End** - "end" vectors

Parameters
----------

**object name** - name of object to analize. (For "object_space" mode only)

**raycast modes** - in "object_space" mode: node works like "bpy.types.Object.ray_cast" (origin of object- center of coordinate for START&END). In "world_space" mode: node works like "bpy.types.Scene.ray_cast".

**iteration modes** - method that achieve the same amount of START and END vectors. "match short"- cuts that list that was longer, "match long repeat"- repeats the last element of the list that was shorter


Output sockets
--------------

**Hitp** - hit location for every raycast

**Hitnorm** - normal of hited polygon (in "object_space" mode- local coordinates, in "world_space"- global)

**Index/succes** - for "object_space" mode- index of hited polygon. For "world_space" mode- TRUE if ray hited mesh object, otherwise FALSE.

**data object** - bpy.data.objects[hited object] or NONE type if ray doesnt hit mesh object. (only in "world_space" mode)

**hitted object matrix** - matrix of hited object. (only in "world_space" mode)


Usage
-----

.. image:: https://cloud.githubusercontent.com/assets/7894950/4437227/4ac2cc4a-4790-11e4-8359-040da4398213.png
  :alt: reycast
  

