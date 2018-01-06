Deform by formula
========

Functionality
-------------

available variables: **x**, **y**, **z** for access to initial (xyz) coordinates.
And **i** for access to index of current vertex to be evaluated.
Internally imported everything from Python **math** module.
Blender Py API also accessible (like **bpy.context.scene.frame_current**)

Inputs
------

- **Verts**

Outputs
-------

**Verts**.
resulted vertices to X,Y,Z elements of which was applied expression.

Example of usage
----------------
