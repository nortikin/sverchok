Deform by Formula
=================

.. image:: https://user-images.githubusercontent.com/14288520/194043208-cd11b020-2ef5-45d0-b382-ee56fdad8d4e.png
  :target: https://user-images.githubusercontent.com/14288520/194043208-cd11b020-2ef5-45d0-b382-ee56fdad8d4e.png

Functionality
-------------

available variables: **x**, **y**, **z** for access to initial (xyz) coordinates.
MK2 version of this node have second input socket - access its vertices using **X**, **Y** or **Z** variables.
Use **i** for access to index of current vertex to be evaluated. It is also possible
to get index of current object list evaluated as **I** variable.
So **i** for index of vertex, and **I** for index of object.
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

.. image:: https://user-images.githubusercontent.com/14288520/194045265-39a79b9c-3a71-46d1-81e4-2bbdfde44277.png
  :target: https://user-images.githubusercontent.com/14288520/194045265-39a79b9c-3a71-46d1-81e4-2bbdfde44277.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`