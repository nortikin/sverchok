Matrix Normal
=============

.. image:: https://cloud.githubusercontent.com/assets/619340/4186363/32974f5a-3760-11e4-9be7-5e16ce549d0d.PNG
  :alt: Matrix_Shear.PNG

Functionality
-------------

Similar in behaviour to the ``Transform -> Shear`` tool in Blender (`docs <http://wiki.blender.org/index.php/Doc:2.6/Manual/3D_interaction/Transformations/Advanced/Shear>`_). 

This node calculates a Position Matrix from a location and a Normal Vector. Is usefull to place meshes in custom planes (or polygons)

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

Using the the node to place a mesh acording to a base mesh vertex normal

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/matrix/matrix_normal/matrix_normal_sverchok_blender.png
  :alt: Matrix_Normal_Sverchok.PNG