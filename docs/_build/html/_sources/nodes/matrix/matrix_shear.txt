Matrix Shear
============

.. image:: Matrix_Shear.PNG

Functionality
-------------

Similar in behaviour to the ``Transform -> Shear`` tool in Blender (`docs <http://wiki.blender.org/index.php/Doc:2.6/Manual/3D_interaction/Transformations/Advanced/Shear>`_). 

Matrix Shear generates a Transform Matrix which can be used to change the locations of vertices in two directions. The amount of transformation to introduce into the Matrix is given by two `Factor` values which operate on the corresponding axes of the selected *Plane*.

Inputs & Parameters
-------------------

+-------------------+--------------------------------------------------------------------------------------------------+
| Parameters        | Description                                                                                      |
+===================+==================================================================================================+
| Plane             | ``options = (XY, XZ, YZ)``                                                                       |
+-------------------+--------------------------------------------------------------------------------------------------+
| Factor1 & Factor2 | these are *Scalar float* values and indicate how much to affect the axes of the transform matrix |
+-------------------+--------------------------------------------------------------------------------------------------+

Outputs
-------

A single ``4*4`` Transform Matrix


Examples
--------

Usage: This is most commonly connected to Matrix Apply to produce the Shear effect.

.. image:: Matrix_Shear_Demo1.PNG