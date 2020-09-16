Hollow Solid
============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node does the following procedure:

* takes a Solid object
* removes some of it's faces (defined by mask input)
* of remaining faces, makes a hollow thick shell.

In FreeCAD, this operation is known as Thickness_. If no faces are marked for
removal, this node will operate the same way as "Offset Solid".

.. _Thickness: https://wiki.freecadweb.org/PartDesign_Thickness

**NOTES**:

1. If thickness goes inwards, the value must be smaller than the smallest
   height of the Body. Otherwise the node will fail.
2. The node may fail with complex shapes. In this context the surface of e.g. a
   cone has already to be regarded as complex. 

Inputs
------

This node has the following inputs:

* **Solid**. Solid object to be operated on. This input is mandatory.
* **Thickness**. Thickness value. Negative values mean offset towards inside of
  the solid. The default value is 0.1.
* **FaceMask**. Mask which defines which faces will be removed and which will
  be used to make a shell. Exact meaning of this input is defined by **Mask
  Usage** parameter, which is located near the input.

Parameters
----------

This node  has the following parameters:

* **Tolerance**. Operation tolerance. The smaller this value is, the more
  precise operation will be, but the more time it will take. The default value
  is 0.01.
* **Mask usage** (two buttons near **FaceMask** input). This defines how values
  in the **FaceMask** input are interpreted. Possible options are:

   * **Removed** (minus sign). `True` or `1` in the mask will indicate faces
     that are to be removed; `False` or `0` will indicate faces from which to
     make the shell.
   * **Shell** ("thickness" icon). `True` or `1` will in the mask indicate
     faces from which to make the shell; `False` or `0` will indicate faces
     that are to be removed.

   The default value is "Shell".

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Examples of usage
-----------------

This node will be usually used together with "Select Solid Elements" node, to
indicate which faces to use for the shell.

Make a solid of revolution from a pentagon, then remove two of it's faces on
the top, and make a hollow shell from other faces:

.. image:: https://user-images.githubusercontent.com/284644/92967625-033e3600-f493-11ea-8bf3-181f85ea8434.png


More complex example:

.. image:: https://user-images.githubusercontent.com/284644/92967627-046f6300-f493-11ea-86ed-3e2bbc164b40.png

