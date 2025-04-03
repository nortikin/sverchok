Lathe
=====

.. image:: https://user-images.githubusercontent.com/14288520/198713217-95f76fe7-cd42-4cdf-a39b-d7b3ba841c98.png
  :target: https://user-images.githubusercontent.com/14288520/198713217-95f76fe7-cd42-4cdf-a39b-d7b3ba841c98.png

Functionality
-------------

Analogous to the `spin` operator and the Screw modifier. It takes a profile shape as input in the form of *vertices* and *edges* and produces *vertices* and *faces* based on a rotation axis, angle, center, delta and step count. Internally the node is powered by the `bmesh.spin <http://www.blender.org/documentation/blender_python_api_2_71_release/bmesh.ops.html#bmesh.ops.spin>`_  operator.

Inputs
------

It's vectorized, meaning it accepts nested and multiple inputs and produces multiple sets of output

Parameters
----------

All Vector parameters (except axis) default to (0,0,0) if no input is given.

+-------------+---------------+-----------------------------------------------------------------+
| Param       | Type          | Description                                                     |
+=============+===============+=================================================================+
| **cent**    | Vector        | central coordinate around which to pivot                        |
+-------------+---------------+-----------------------------------------------------------------+
| **axis**    | Vector        | axis around which to rotate around the pivot, default (0, 0, 1) |
+-------------+---------------+-----------------------------------------------------------------+
| **dvec**    | Vector        | is used to push the center Vector by a Vector quantity per step |
+-------------+---------------+-----------------------------------------------------------------+
| **Degrees** | Scalar, Float | angle of the total rotation. Default 360.0                      |
+-------------+---------------+-----------------------------------------------------------------+
| **Steps**   | Scalar, Int   | number of rotation steps. Default 20                            |
+-------------+---------------+-----------------------------------------------------------------+
| **Merge**   | Bool, toggle  | removes double vertices if the geometry can be merged,          |
|             |               |                                                                 |
|             |               | usually used to prevent doubles of first profile and last       |
|             |               |                                                                 |
|             |               | profile copy. Default `off`.                                    |
+-------------+---------------+-----------------------------------------------------------------+


Outputs
-------

**Vertices** and **Poly**. Verts and Polys will be generated. The ``bmesh.spin`` operator doesn't consider the ordering of the Vertex and Face indices that it outputs. This might make additional processing complicated, use IndexViewer to better understand the generated geometry. Faces will however have consistent Normals.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/198734423-e93ae224-512b-4021-8e70-0f3fae0bdf55.png
  :target: https://user-images.githubusercontent.com/14288520/198734423-e93ae224-512b-4021-8e70-0f3fae0bdf55.png

* Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/198873245-034064a0-0ba8-4dfd-820c-5750d6f28e93.gif
  :target: https://user-images.githubusercontent.com/14288520/198873245-034064a0-0ba8-4dfd-820c-5750d6f28e93.gif

---------

.. image:: https://cloud.githubusercontent.com/assets/619340/3172893/08952296-ebdd-11e3-8e9b-574495b1a92c.png

See the progress of how this node came to life `here <https://github.com/nortikin/sverchok/issues/203>`_ (gifs, screenshots)

Glass, Vase.
