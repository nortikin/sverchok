Proportional Edit Falloff
=========================

.. image:: https://user-images.githubusercontent.com/14288520/196805236-0dccf99d-1e35-467d-b5e4-4a108ce8f9be.png
  :target: https://user-images.githubusercontent.com/14288520/196805236-0dccf99d-1e35-467d-b5e4-4a108ce8f9be.png

Functionality
-------------

This node implements Blender's concept of "proportional edit mode" in Sverchok. It converts vertex selection mask into selection coefficients. Vertices selected by mask get the coefficient of 1.0. Vertices that are farther than specified radius from selection, get the coefficient of 0.0. 

Supported falloff modes are basically the same as Blender's.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Mask**
- **Radius**. Proportional edit radius.

Parameters
----------

This node has the following parameters:

- **Falloff type**. Proportional edit falloff type. Supported values are:

  * Smooth
  * Sharp
  * Root
  * Linear
  * Sphere
  * Inverse Square
  * Constant

  The meaning of values is all the same as for standard Blender's proportional edit mode.

- **Radius**. Proportional edit radius. This parameter can be also provided by input.

Outputs
-------

This node has one output: **Coeffs**. It contains one real value for each input vertex. All values are between 0.0 and 1.0.

**See also**:

See also
--------

* Vector-> :doc:`Vector Attraction </nodes/vector/attractor>`

Examples of usage
-----------------

Drag a circle on one side of the box, with Smooth falloff:

.. image:: https://user-images.githubusercontent.com/14288520/196816008-bd51201d-ef3d-45c3-b15f-c99e7ec68c10.png
  :target: https://user-images.githubusercontent.com/14288520/196816008-bd51201d-ef3d-45c3-b15f-c99e7ec68c10.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

All the same, but with Const falloff:

.. image:: https://user-images.githubusercontent.com/14288520/196816329-e4b606cc-d73e-42e7-b30a-5b632f6c50d0.png
  :target: https://user-images.githubusercontent.com/14288520/196816329-e4b606cc-d73e-42e7-b30a-5b632f6c50d0.png

---------

Example of usage with Extrude Separate node:

.. image:: https://user-images.githubusercontent.com/14288520/196819804-6d71e779-fc66-48f9-a4e1-f31f75263057.png
  :target: https://user-images.githubusercontent.com/14288520/196819804-6d71e779-fc66-48f9-a4e1-f31f75263057.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Analyzers-> :doc:`Points Inside Mesh </nodes/analyzer/points_inside_mesh>`
* Modifiers->Modifier Change-> :doc:`Extrude Separate Faces </nodes/modifier_change/extrude_separate>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* SCALAR: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`