Voronoi 3D
==========

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Voronoi_ diagram for given set of points in 3D space.

As Voronoi diagram is an infinite structure, this node can only generate it's
finite part. Only finite polygons / regions are generated, but even these can
be very large. To generate a smaller object, clipping by vertical / horizontal
planes can be applied.

.. _Voronoi: https://en.wikipedia.org/wiki/Voronoi_diagram

Inputs
------

This node has the following inputs:

* **Vertices**. Set of input vertices (sites) to build Voronoi diagram for.
* **Clipping**. This defines the distance from outermost initial points to the
  clipping planes. This input is only available when the **Clipping** parameter
  is checked. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Output**. This defines what kind of mesh objects this node will generate. The available values are:

  * **Ridges**. Each output mesh object will represent one ridge, i.e. a part
    of plane which separates to regions of Voronoi diagram.
  * **Regions**. Each output mesh will represent one region of Voronoi diagram,
    with ridges that separate it from neigbours.

  The default option is **Regions**.

* **Closed only**. This parameter is available only if **Output** parameter is
  set to **Regions**. If checked, then the node will generate mesh objects only
  for closed regions of Voronoi diagrams. Otherwise, it will generate open
  regions as well. Checked by default.
* **Correct normals**. This parameter is available only if **Output** parameter
  is set to **Regions**. If checked, then the node will try to recalculate
  normals of faces of each region, so that they point outside of the region.
  You may uncheck this to save some time in case you do not care about normals.
  Checked by default.
* **Clip**. If checked, then infinite Voronoi diagram will be clipped by
  horizontal and vertical planes, to generate a finite object. Checked by
  default.
* **Join**. If checked, then the node will join mesh objects for each ridge or
  region, and output one mesh object for each set of points. Otherwise, the
  node will output a separate mesh object for each ridge or region. Unchecked
  by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated ridges or regions.
* **Edges**. Edges of generated ridges or regions.
* **Faces**. Faces of generated ridges or regions.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87224915-90391600-c3a2-11ea-9646-a124b3d1e06a.png

