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

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6567015b-3981-4332-a5d1-cc8f1f18b2a6
  :target: https://github.com/nortikin/sverchok/assets/14288520/6567015b-3981-4332-a5d1-cc8f1f18b2a6

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

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/865eb1fc-b0ba-4226-8e74-d5ca4f39bd75
      :target: https://github.com/nortikin/sverchok/assets/14288520/865eb1fc-b0ba-4226-8e74-d5ca4f39bd75

* **Function**. This parameter is available only when **Interpolate** parameter
  is available. The specific function used by the node. The available values
  are:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/402016d9-a345-4db4-bd3f-8e99a6c73d36
      :target: https://github.com/nortikin/sverchok/assets/14288520/402016d9-a345-4db4-bd3f-8e99a6c73d36

  * **Multi Quadric**
  * **Inverse**
  * **Gaussian**
  * **Cubic**
  * **Quintic**
  * **Thin Plate**

  The default function is **Multi Quadric**.
* **Signed**. This parameter is available only when **Interpolate** parameter is unchecked. If signed is ON then some normals may
  get opposite normals of mesh:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c3292e20-b407-4c0c-a31f-50c28fd8f4af
  :target: https://github.com/nortikin/sverchok/assets/14288520/c3292e20-b407-4c0c-a31f-50c28fd8f4af

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b57dbe15-3bb1-4ede-9d66-c7b2ceba0d13
  :target: https://github.com/nortikin/sverchok/assets/14288520/b57dbe15-3bb1-4ede-9d66-c7b2ceba0d13

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`