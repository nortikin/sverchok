Overlap Polygons
=================

.. image:: https://user-images.githubusercontent.com/14288520/196555869-ce40a8a7-53dc-4134-acc7-8b16e0e3a79e.png
  :target: https://user-images.githubusercontent.com/14288520/196555869-ce40a8a7-53dc-4134-acc7-8b16e0e3a79e.png

.. image:: https://user-images.githubusercontent.com/14288520/196556486-f189271c-935a-4698-bef5-bb5d98df4789.png
  :target: https://user-images.githubusercontent.com/14288520/196556486-f189271c-935a-4698-bef5-bb5d98df4789.png

Functionality
-------------

For every polygon of one object search intersection at other object. 
Epsilon makes it harder to find intersaction. Based on BVHtree ``mathutils.bvhtree`` (see: `Blender docs <https://docs.blender.org/api/current/mathutils.bvhtree.html>`_). 

Inputs
------

+--------+--------------+--------------------------+
| Mode   | Input Name   | type                     |
+========+==============+==========================+
| All    | Vert(A)      | vertices                 |
+--------+--------------+--------------------------+
| All    | Poly(A)      | polygons                 |
+--------+--------------+--------------------------+
| All    | Vert(B)      | vertices                 |
+--------+--------------+--------------------------+
| All    | Poly(B)      | polygons                 |
+--------+--------------+--------------------------+


Parameters
----------

+---------------+-----------------------------------------------------------------------------------------+
| Mode          | Description                                                                             |
+===============+=========================================================================================+
| all triangles | Boolean to work with triangles makes it faster to calculate                             |
+---------------+-----------------------------------------------------------------------------------------+
| epsilon       | Float threshold for cut weak results                                                    |
+---------------+-----------------------------------------------------------------------------------------+


Outputs
-------


+--------+-------------------+--------------------------+
| Mode   | Input Name        | type                     |
+========+===================+==========================+
| All    | PolyIndex(A)      | indices                  |
+--------+-------------------+--------------------------+
| All    | PolyIndex(B)      | indices                  |
+--------+-------------------+--------------------------+
| All    | OverlapPoly(A)    | polygons                 |
+--------+-------------------+--------------------------+
| All    | OverlapPoly(B)    | polygons                 |
+--------+-------------------+--------------------------+


Examples
--------


.. image:: https://user-images.githubusercontent.com/5783432/30777862-8d369f36-a0cd-11e7-8c8e-a72e7aa8ee7f.png
  :target: https://user-images.githubusercontent.com/5783432/30777862-8d369f36-a0cd-11e7-8c8e-a72e7aa8ee7f.png

https://github.com/nortikin/sverchok/files/1326934/bvhtree-overlap_2017_09_23_23_07.zip

---------

Replay with new nodes

.. image:: https://user-images.githubusercontent.com/14288520/196557744-537fdff5-d2ca-434e-a9ce-467e791e3b40.png
  :target: https://user-images.githubusercontent.com/14288520/196557744-537fdff5-d2ca-434e-a9ce-467e791e3b40.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/196558732-1ecccc43-7705-436e-9eb1-2acd70fe55b6.gif
  :target: https://user-images.githubusercontent.com/14288520/196558732-1ecccc43-7705-436e-9eb1-2acd70fe55b6.gif

Notes
-----

pass

