NURBS Curve Out Node
====================

Functionality
-------------

This node generates Blender's NURBS Curve objects from input data. It creates a new Curve object or updates existing on each update of input data or parameters.

**NOTE**: Blender's functionality for NURBS is limited. For example, there is
no way to specify explicit knot vector.
For information about supported features and operations for NURBS Curve
objects, please refer to Blender_ documentation.
For more NURBS-related functions, it is possible to use the Sverchok-Extra_ addon.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/curves/index.html
.. _Sverchok-Extra: https://github.com/portnov/sverchok-extra

Inputs
------

This node has the following inputs:

* **ControlPoints**. Control points of the NURBS curve. This input is mandatory.
* **Weights**. NURBS curve control point weights. This input is optional.
* **Degree**. Degree of the curve. The default value is 3.

Parameters
----------

This node has the following parameters:

* **UPD**. The node will process data only if this button is enabled.
* **Hide View** (eye icon). Toggle visibility of generated object in viewport.
* **Hide Select** (pointer icon). Toggle ability to select for generated object.
* **Hide Render** (render icon). Toggle renderability for generated object.
* **Base name**. Base part of name for Curve object to create (or update).
  Default is "Alpha".
* **Select Toggle**. Select / deselect generated object.
* **Material**. Material to be assigned to created object.
* **Cyclic**. Defines whether the created curve should be cyclic (closed).
  Unchecked by default.
* **Endpoint**. Defines whether the created curve should touch it's end control
  points. This parameter is not available when the **Cyclic** parameter is
  checked. Checked by default.
* **Resolution**. Curve subdivisions per segment. This parameter is available
  in the N panel only.

Outputs
-------

This node has the following output:

* **Object**. Generated NURBS Curve objects.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/284644/75611529-16179b80-5b3d-11ea-99b8-5cfaafaa7c5b.png

