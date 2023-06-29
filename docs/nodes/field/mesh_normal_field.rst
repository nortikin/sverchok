Mesh Nearest Normal
===================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/33796495-8674-47b6-a227-f4b4231c69db
  :target: https://github.com/nortikin/sverchok/assets/14288520/33796495-8674-47b6-a227-f4b4231c69db

Dependencies
------------

This node optionally uses SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Vector Field, that, for each point in space, returns a
normal vector of the nearest face of the given mesh. Optionally, the node can
interpolate between these face normals, so that the field will be smooth.
Interpolation is done with RBF_ method.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f3b1da19-f184-4748-8a1d-f7c4fbd1d48f
  :target: https://github.com/nortikin/sverchok/assets/14288520/f3b1da19-f184-4748-8a1d-f7c4fbd1d48f

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the mesh. This input is mandatory.
* **Faces**. Faces of the mesh. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Interpolate**. This parameter is available only when the SciPy library is
  available. If checked, then the node will interpolate between nearest mesh
  normals to generate a smooth field. Unchecked by default.
* **Function**. This parameter is available only when **Interpolate** parameter
  is available. The specific function used by the node. The available values
  are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

  The default function is Multi Quadric.
* **Signed**. This parameter is available only when **Interpolate** parameter is unchecked. 

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples
========

.. image:: https://github.com/nortikin/sverchok/assets/14288520/026d932d-3519-454d-a0bf-1bcd16c85192
  :target: https://github.com/nortikin/sverchok/assets/14288520/026d932d-3519-454d-a0bf-1bcd16c85192

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Modifiers->Modifier Make-> :doc:`Subdivide </nodes/modifier_change/subdivide_mk2>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
