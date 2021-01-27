Solid from Faces
================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node takes several Solid Face objects (i.e. Surfaces trimmed by some
edges), and "glues" them to construct a Solid object. In order to make a proper
Solid object, the faces must already have their edges and vertices exactly
coinciding. Usually the only way to guarantee that is to construct all these
Faces from the same set of Edges.

By default, the node will check that the Solid object it constructed is "valid"
in terms of FreeCAD's OCCT kernel: all faces have coinciding edges, all normals
are pointing outside, and so on. If the node will find that the solid is not
valid, it will try to automatically fix it.  If this automatic fix process
fails, the node will raise an exception (become red) and processing will stop.

**NOTE**: some operations with Solid objects which are not "valid" are known to
cause crashes. So it is strongly recomended to have "Validate" parameter turned
on.

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

Inputs
------

This node has the following input:

* **SolidFaces**. Solid Face objects to make a Solid from. This input can
  consume data with nesting level from 1 (list of faces) to 3 (list of lists of
  lists of faces).  The node will make one Solid object from each list of
  faces. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Body is closed**. If checked, the node will check that the constructed
  Solid object is closed, i.e. does not have open edges. If it finds that the
  body is not closed, the node will raise an exception (become red) and
  processing will stop. So if this parameter is checked, you can be sure that
  all Solid objects it generates are closed. If not checked, the node will not
  perform such check, and can generate not-closed objects. Checked by default.
* **Validate**. This parameter is available in the N panel only. If checked,
  the node will check that the Solid object it constructed is "valid" in terms
  of FreeCAD's OCCT kernel: all faces have coinciding edges, all normals are
  pointing outside, and so on. If the node will find that the solid is not
  valid, it will try to automatically fix it.  If this automatic fix process
  fails, the node will raise an exception (become red) and processing will
  stop. So if this parameter is checked, you can be sure that the generated
  Solid object is "valid". If not checked, the node will not validate the
  created object. In most cases, you have to check this parameter; it is
  checked by default. **NOTE**: some operations with Solid objects which are
  not "valid" are known to cause crashes.
* **Tolerance**. This parameter is available in the N panel, only if
  **Validate** parameter is checked. Tolerance for automatic "fix" process. The
  default value is 0.001.

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Example of usage
----------------

Make a side surface by lofting between three cubic splines; make top and bottom
faces with "Frame from Curve" node from the first and the last spline; then
build the Solid object from these three surfaces:

.. image:: https://user-images.githubusercontent.com/284644/93717249-f5249f80-fb8d-11ea-9fcb-9b780c7623a7.png

