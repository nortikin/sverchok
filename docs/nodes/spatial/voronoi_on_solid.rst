Voronoi on Solid
================

Dependencies
------------

This node requires both SciPy_ and FreeCAD_ libraries to work.

.. _SciPy: https://scipy.org/
.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node creates Voronoi diagram on a given Solid object. The result can be
output as either series of fragments of the shell of Solid object (series of
faces), or as a series of solid bodies.

**Note**: this node uses FreeCAD's functionality of solid boolean operations
internally. This functionality is known to be slow when working with objects
defined by NURBS surfaces, especially when there are a lot of sites used. Also
please be warned that this functionality is known to cause Blender crashes on
some setups.

Inputs
------

This node has the following inputs:

* **Solid**. The solid object, on which the Voronoi diagram is to be generated.
  This input is mandatory.
* **Sites**. List of points, for which Voronoi diagram is to be generated. This
  input is mandatory.
* **Inset**. Percentage of space to leave between generated Voronoi regions.
  Zero means the object will be fully covered by generated regions. Maximum
  value is 1.0. The default value is 0.1. This input can consume either a
  single value per object, or a list of values per object - one value per site.
  In the later case, each value will be used for corresponding cell.  

Parameters
----------

This node has the following parameters:

* **Mode**. The available options are available:

  * **Surface**. The node will split the surface (shell) of the solid body into
    regions of Voronoi diagram.
  * **Volume**. The node will split the volume of the solid body into regions
    of Voronoi diagram.

  The default value is **Surface**.

* **Flat output**. If checked, output single flat list of fragments for all
  output solids. Otherwise, output a separate list of fragments for each solid.
  Checked by default.
* **Accuracy**. This parameter is available in the N panel only. Precision of
  calculations (number of digits after decimal point). The default value is 6.

Outputs
-------

This node has the following outputs:

* **InnerSolid**. Solid objects (or their shells, if **Surface** mode is used)
  calculated as regions of Voronoi diagram.
* **OuterSolid**. Solid object, representing the part of volume or shell, which
  is left between the regions of Voronoi diagram. This object will be empty if
  **Inset** input is set to zero.

Examples of usage
-----------------

Inner solids with **Surface** mode:

.. image:: https://user-images.githubusercontent.com/284644/103175519-411d6980-488c-11eb-86bf-151a4776f6ac.png

Outer solid for the same setup:

.. image:: https://user-images.githubusercontent.com/284644/103175520-424e9680-488c-11eb-99aa-d0ea147c29d6.png

Inner solids with **Volume** mode:

.. image:: https://user-images.githubusercontent.com/284644/103175523-437fc380-488c-11eb-817b-fe5826d184ed.png

Outer solid with **Volume** mode:

.. image:: https://user-images.githubusercontent.com/284644/103175522-42e72d00-488c-11eb-947b-ba57fc3b96f7.png

