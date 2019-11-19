Matrix Normal
=============

Functionality
-------------

This node calculates a Position Matrix from a location and a Normal Vector. Is useful to place meshes in custom planes (or polygons)

Inputs & Parameters
-------------------

+-------------------+--------------------------------------------------------------------------------------------------+
| Parameters        | Description                                                                                      |
+===================+==================================================================================================+
| Track             | Determine with axis should match the given normal                                                |
+-------------------+--------------------------------------------------------------------------------------------------+
| Up                | Parameter to sort the other axis                                                                 |
+-------------------+--------------------------------------------------------------------------------------------------+

Outputs
-------

One (or many) Transform Matrix


Examples
--------

Using the the node to place a mesh according to a base mesh vertex normals.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/matrix/matrix_normal/matrix_normal_sverchok_blender.png
  :alt: Matrix_Normal_Sverchok.PNG