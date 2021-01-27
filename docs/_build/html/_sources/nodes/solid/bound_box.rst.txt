Solid Bounding Box
==================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node calculates bounding box for a given Solid object.

Inputs
------

This node has the following input:

* **Solid**. The solid object to be analyzed. This input is mandatory.

Parameters
----------

This node has the following parameters:

* Min: **X**, **Y**, **Z**. Whether to show outputs with minimum values of X, Y and Z. Unchecked by default.
* Max: **X**, **Y**, **Z**. Whether to show outputs with maximum values of X, Y and Z. Unchecked by default.
* Size: **X**, **Y**, **Z**. Whether to show outputs with sizes along X, Y and Z. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the bounding box.
* **Center**. Center of the bounding box.
* **Box**. Solid object, which represents bounding box.
* **XMin**, **YMin**, **ZMin**. Minimum values of X, Y and Z.
* **XMax**, **YMax**, **ZMax**. Maximum values of X, Y and Z.
* **XSize**, **YSize**, **ZSize**. Sizes along X, Y and Z.

Min / Max / Size outputs are shown depending on corresponding node parameters.

