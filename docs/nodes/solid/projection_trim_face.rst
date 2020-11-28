Face from Surface (Solid)
=========================

Functionality
-------------

This node generates a Solid Face object, i.e. a Surface trimmed with an edge,
from a Surface and optional cutting curve. 

To define where exactly the provided Curve must trim the Surface, it is
projected onto the surface. Another option is to use trimming curve defined in
U/V space of the Surface.

Solid Face object can be later used for construction of Solids (by extrusion, for example).

**NOTE**: this node supports only NURBS and NURBS-like curves and surfaces.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to make a Face from. This input is mandatory.
* **Cut**. One or several Curves (in 3D space) that are used to cut a Face from
  Surface. The node can use a list of Curves per each Surface. Curves must form
  a precisely closed loop. This input is optional; if it is not connected, then
  the whole surface will be used as a face.
* **Vector**. Parallel projection vector. This input is available only if
  **Projection** parameter is set to **Parallel**. The default value is ``(0,
  0, -1)`` (down along Z axis).
* **Point**. Perspective projection origin point. This input is available only
  if **Projection** parameter is set to **Perspective**. The default value is
  ``(0, 0, 0)`` (global origin).

Parameters
----------

This node has the following parameter:

* **Projection**. This defines what sort of projection will be used to
  calculate the trimming of the Surface. The available options are:

  * **Parallel**. Parallel projection along a provided Vector. This option is the default one.
  * **Perspective**. Perspective projection from a provided origin point.
  * **Orthogonal**. Orthogonal projection (along surface's normals).
  * **UV Trim**. Trim the surface by a curve(s) in U/V space of the surface. It
    is supposed that trimming curve lies in XOY plane.

Outputs
-------

This node has the following outputs:

* **SolidFace**. The generated Solid Face object.
* **Edges**. Curves in 3D space defining edges of the created face.
* **UVCurves**. Curves in U/V space of the surface that are trimming curves of the face.

Example of Usage
----------------

Make a surface from a Bezier curve; make a Face from it, by cutting it with a projected Circle; then make a solid from that face:

.. image:: https://user-images.githubusercontent.com/284644/92300804-4bcb9000-ef77-11ea-9a39-5b87f8e354b9.png

