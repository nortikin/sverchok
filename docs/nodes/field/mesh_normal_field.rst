Mesh Nearest Normal
===================

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

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the mesh. This input is mandatory.
* **Faces**. Faces of the mesh. This input is mandatory.

Parmeters
---------

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

