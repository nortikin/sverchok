Refine Solid
============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node refines a Solid object, by removing unnecessary edges. Standard
Sverchok Solid nodes, that can potentially produce bodies with unnecessary
edges, usually have "Refine Solid" checkbox to perform such refinement by
themself. But sometimes it is more convinient pass non-refined Solid object
through several other nodes, and only then refine it.

Inputs
------

This node has the following input:

* **Solid**. The Solid object to be refined. This input is mandatory.

Outputs
-------

* **Solid**. The refined Solid object.

