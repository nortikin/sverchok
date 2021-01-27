Bend Along Surface Field
========================

Functionality
-------------

This node generates a Vector Field, which bends some part of 3D space along the provided Surface object.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to bend the space along. This input is mandatory.
* **Src U Min**, **Src U Max**. Minimum and maximum value of the first of
  orientation coordinates, which define the part of space to be bent. For
  example, if the **Object vertical axis** parameter is set to **Z**, then these
  are minimum and maximum values of X coordinates. Default values are -1 and 1.
* **Src V Min**, **Src V Max**. Minimum and maximum value of the second of
  orientation coordinates, which define the part of space to be bent. For
  example, if the **Object vertical axis** parameter is set to **Z**, then these
  are minimum and maximum values of Y coordinates. Default values are -1 and 1.

The field bends the part of space, which is between **Src U Min** and **Src U
Max** by one axis, and between **Src V Min** and **Src V Max** by another axis.
For example, with default settings, the source part of space is the space
between X = -1, X = 1, Y = -1, Y = 1. The behaviour of the field outside of
these bounds is not guaranteed.

Parameters
----------

This node has the following parameters:

* **Object vertical axis**. This defines which axis of the source space should
  be mapped to the normal axis of the surface. The available values are X, Y
  and Z. The default value is Z. This means that XOY plane will be mapped onto
  the surface.
* **Auto scale**. If checked, scale the source space along the vertical axis,
  trying to match the scale coefficient for two other axes. Otherwise, the
  space will not be scaled along the vertical axis. Unchecked by default.
* **Flip surface**. This parameter is only available in the node's N panel. If
  checked, then the surface will be considered as flipped (turned upside down),
  so the vector field will also turn the space upside down. Unchecked by
  default.

Outputs
-------

This node has the following output:

* **Field**. The generated bending vector field.

Example of usage
----------------

Generate a rectangular grid of cubes, and bend it along formula-specified surface:

.. image:: https://user-images.githubusercontent.com/284644/79602628-42df3c80-8104-11ea-80c3-09be659d54f8.png

