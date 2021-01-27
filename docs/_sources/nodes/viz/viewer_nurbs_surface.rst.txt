NURBS Surface Out Node
======================

Functionality
-------------

This node generates Blender's NURBS Surface objects from input data. It creates
a new Surface object or updates existing on each update of input data or
parameters.

**NOTE 1**: Blender's functionality for NURBS is limited. For example, there is
no way to specify explicit knot vector.
For information about supported features and operations for NURBS Surface
objects, please refer to Blender_ documentation.
For more NURBS-related functions, it is possible to use the Sverchok-Extra_ addon.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/surfaces/introduction.html
.. _Sverchok-Extra: https://github.com/portnov/sverchok-extra

**NOTE 2**: In current implementation, this node does not create objects during
scene update events. In many cases you will never even see this problem,
because usually updates of node inputs or parameters happen more frequently. If
at some moment there is no object created by this node in the scene, and you
want it created, just press the **Update All** button in node editor's N panel.

Inputs
------

This node has the following inputs:

* **ControlPoints**. Control points of the NURBS surface. These points are
  expected to form a "rectangular grid" MxN. If the **Input Mode** parameter is
  set to **Single List** value, then this input expects one flat list of
  vertices per surface (i.e., it expects a list of lists of vertices). That
  single list will be split into rows by this node itself. If the **Input
  Mode** parameter is set to **Separated lists** value, then this input expects
  a list of lists of vertices per surface (i.e. it expects a list of lists of
  lists of vertices). This input is mandatory.
* **Weights**. NURBS surface control points weight. The shape of input data
  should correspond to the shape of input data for the **ControlPoints** input:
  it can be either list of lists of floats (in **Single List** mode), or list
  of lists of lists of floats (in **Separated Lists** mode). This input is
  optional.
* **Degree U**. The degree of the surface in the U direction. The default value is 3.
* **Degree V**. The degree of the surface in the V direction. The default value is 3.
* **U Size**. Number of vertices per row. This is used to split the flat list
  of control points into rows, when the **Input Mode** parameter is set to
  **Single List**. Otherwise the input is not available. The default value is
  5.

Parameters
----------

This node has the following parameters:

* **UPD**. The node will process data only if this button is enabled.
* **Hide View** (eye icon). Toggle visibility of generated object in viewport.
* **Hide Select** (pointer icon). Toggle ability to select for generated object.
* **Hide Render** (render icon). Toggle renderability for generated object.
* **Base name**. Base part of name for Surface object to create (or update).
  Default is "Alpha".
* **Select Toggle**. Select / deselect generated object.
* **Material**. Material to be assigned to created object.
* **Input mode**. This defines how control points and their weights are specified:

  * **Single List**: it is expected that **ControlPoints** and **Weights**
    inputs will be provided with one flat list of control points and weights.
    The node will split that list into rows, using the value in the **U Size**
    input.
  * **Separated Lists**: it is expected that **ControlPoints** and **Weights**
    inputs will be provided with lists of control points and their weights,
    that were already split into rows.

* **Cyclic U**. Whether the surface should be cyclic (closed) in the U
  direction. Unchecked by default.
* **Cyclic V**. Whether the surface should be cyclic (closed) in the V
  direction. Unchecked by default.
* **Endpoint U**. Whether the surface should touch it's end control points in
  the U direction. This option is not available if **Cyclic U** is checked.
  Checked by default.
* **Endpoint V**. Whether the surface should touch it's end control points in
  the V direction. This option is not available if **Cyclic V** is checked.
  Checked by default.
* **Smooth**. Whether the created surface should be in smoothed normals mode.
  Checked by default. This parameter is available in the N panel only.
* **Resolution U**, **Resolition V**. Surface subdivisions per segment. This
  parameter is available in the N panel only.

Outputs
-------

This node has the following output:

* **Object**. Generated NURBS Surface objects.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/284644/75611527-144dd800-5b3d-11ea-81e0-5b2b1c8a50c0.png

