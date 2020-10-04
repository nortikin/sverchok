Face from Curves (Solid)
========================

Functionality
-------------

This node generates a Solid Face object, i.e. a Surface trimmed with an edge,
from one or several Curves, that form an exactly closed loop - the boundary of
the face.

Solid Face object can be later used for construction of Solids (by extrusion, for example).

**NOTE**: this node supports only NURBS and NURBS-like curves.

Inputs
------

This node has the following input:

* **Edges**. One or several curves that form a boundary of the face. The node
  will create one face from one list of curves. Curves must form a precisely
  closed loop. If **Planar** parameter is checked, then all curves must lie
  precisely in one plane. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Planar**. If checked, then the generated Face will be planar (flat). For
  this, all input curves must lie in one plane. If not checked, then non-planar
  curves are allowed, and the surface will be not flat. Checked by default.
* **Accuracy**. This parameter is only available in the N panel. This defines
  the tolerance for checking if ends of curves coincide. Bigger values mean
  that ends of curves must coincide with better precision. The default value is
  8.

Outputs
-------

This node has the following output:

* **SolidFace**. The generated Solid Face object.

Example of Usage
-----------------

Make a Face from a closed NURBS curve, and then make a solid of revolution from it:

.. image:: https://user-images.githubusercontent.com/284644/92300485-94ce1500-ef74-11ea-83c0-07b3da183f0c.png

