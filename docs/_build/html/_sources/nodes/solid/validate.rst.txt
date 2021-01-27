Validate & Fix Solid
====================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node checks if the passed Solid object is "valid" in terms of FreeCAD's
OCCT kernel: all faces have coinciding edges, all normals are pointing outside,
and so on. If it finds that the object is not valid, then, if **FixedSolid**
output is connected, the node will try to automatically fix the object. If this
automatic fix procedure fails, the node will raise an exception (become red)
and processing will stop.

Most Sverchok Solid nodes always produce valid Solid objects. Nodes that can
potentially produce non-valid objects, usually have "Validate" checkbox to make
sure that all produced objects are valid. But scripted nodes can produce
non-valid objects. Also it can be more convinient in some circumstances to work
with non-valid object, and only then fix it.

**NOTE**: some operations with Solid objects which are not "valid" are known to
cause crashes. So if you are working with objects which are not valid, please
make sure you know what you are doing.

Inputs
------

This node has the following input:

* **Solid**. The Solid object to be analyzed. This input is mandatory.

Parameters
----------

This node has the following parameter:

* **Precision*. The precision for automatic fix procedure (applied if the
  object is not valid in the input). The default value is 0.001.

Outputs
-------

This node has the following outputs:

* **FixedSolid**. Fixed Solid object (or the same object as in the input, if it
  already was valid). The node tries to perform automatic fix procedure only if
  this output is connected.
* **IsValid**. This output contains True for Solid objects in the **Solid**
  input, which are valid, and False for objects which are not valid.

