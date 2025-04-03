Vector Interpolation Stripes
============================

.. image:: https://user-images.githubusercontent.com/14288520/189498648-71764116-89a3-489d-9806-a17974710d5d.png
  :target: https://user-images.githubusercontent.com/14288520/189498648-71764116-89a3-489d-9806-a17974710d5d.png

Functionality
-------------

Performs cubic spline STRIPES interpolation based on input points by creating a function ``x,y,z = f(t)`` with ``tU=[0,1]``, ``tU=[0,1]`` and attractor vertex.
The interpolation is based on the distance between the input points.
Stripes outputs as two lines of points for each object, so UVconnect node can handle it and make polygons for stripes.


Input & Output
--------------

+--------+-----------+---------------------------------------------+
| socket | name      | Description                                 |
+========+===========+=============================================+    
| input  | Vertices  | Points to interpolate                       |
+--------+-----------+---------------------------------------------+
| input  | tU        | Values to interpolate in U direction        |
+--------+-----------+---------------------------------------------+
| input  | tV        | Values to interpolate in V direction        |
+--------+-----------+---------------------------------------------+    
| input  | Attractor | Vertex point as attractor of influence      |
+--------+-----------+---------------------------------------------+
| output | vStripes  | Interpolated points as grouped stripes      |
|        |           |                                             |
|        |           | [[a,b],[a,b],[a,b]], where a and b groups   |
|        |           |                                             |
|        |           | [v,v,v,v,v], where v - is vertex            |
+--------+-----------+---------------------------------------------+
| output | vShape    | Interpolated points simple interpolation    |
+--------+-----------+---------------------------------------------+
| output | sCoefs    | String of float coefficients for each point |
+--------+-----------+---------------------------------------------+

Parameters
----------

* **Factor** - is multiplyer after produce function as sinus/cosinus/etc.
* **Scale** - is multiplyer before produce function as sinus/cosinus/etc.
* **Function** - popup function between Simple/Multiplied/Sinus/Cosinus/Power/Square

Parameters extended
-------------------

* **minimum** - minimum value of stripe width (0.0 to 0.5)
* **maximum** - maximum value of stripe width (0.5 to 1.0)

Examples
--------

Making surface with stripes separated in two groups of nodes for UVconnect node to process:

.. image:: https://cloud.githubusercontent.com/assets/5783432/20041842/bc459a26-a488-11e6-98ec-345e58bbcdc9.png
    :target: https://cloud.githubusercontent.com/assets/5783432/20041842/bc459a26-a488-11e6-98ec-345e58bbcdc9.png
    :alt: interpolation stripes

* Modifiers->Modifier Change :doc:`Separate Loose Parts </nodes/modifier_change/mesh_separate>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

.. image:: https://user-images.githubusercontent.com/14288520/189498715-ce12c260-ea62-46de-8a03-c304b6ccedd0.png
  :target: https://user-images.githubusercontent.com/14288520/189498715-ce12c260-ea62-46de-8a03-c304b6ccedd0.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Curve Frame </nodes/curve/curve_frame>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Out </nodes/matrix/matrix_out_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


.. image:: https://user-images.githubusercontent.com/14288520/189498730-a8dbe296-f0f3-4db2-8492-2beb7dc54304.gif
  :target: https://user-images.githubusercontent.com/14288520/189498730-a8dbe296-f0f3-4db2-8492-2beb7dc54304.gif