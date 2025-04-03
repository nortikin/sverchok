Voronoi 3D
==========

.. image:: https://user-images.githubusercontent.com/14288520/202310354-4f3efcaa-8101-4f4f-a87b-c086256c66fa.png
  :target: https://user-images.githubusercontent.com/14288520/202310354-4f3efcaa-8101-4f4f-a87b-c086256c66fa.png

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

.. image:: https://user-images.githubusercontent.com/14288520/202391716-7165b83a-8153-493c-b911-d388635cd461.gif
  :target: https://user-images.githubusercontent.com/14288520/202391716-7165b83a-8153-493c-b911-d388635cd461.gif

Parameters
----------

This node has the following parameters:

* **Output**. This defines what kind of mesh objects this node will generate. The available values are:

  * **Ridges**. Each output mesh object will represent one ridge, i.e. a part
    of plane which separates to regions of Voronoi diagram.
  * **Regions**. Each output mesh will represent one region of Voronoi diagram,
    with ridges that separate it from neighbours.

  The default option is **Regions**.

.. image:: https://user-images.githubusercontent.com/14288520/202388056-f8212bec-3d87-4e05-b06f-dfc37f222f16.png
  :target: https://user-images.githubusercontent.com/14288520/202388056-f8212bec-3d87-4e05-b06f-dfc37f222f16.png

* **Closed only**. This parameter is available only if **Output** parameter is
  set to **Regions**. If checked, then the node will generate mesh objects only
  for closed regions of Voronoi diagrams. Otherwise, it will generate open
  regions as well. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202388843-88aba02b-1d72-4195-9d8b-d6e38ab3df2e.gif
  :target: https://user-images.githubusercontent.com/14288520/202388843-88aba02b-1d72-4195-9d8b-d6e38ab3df2e.gif

* **Correct normals**. This parameter is available only if **Output** parameter
  is set to **Regions**. If checked, then the node will try to recalculate
  normals of faces of each region, so that they point outside of the region.
  You may uncheck this to save some time in case you do not care about normals.
  Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202390632-d6f11217-58da-48ad-b7ae-37b88fdfb4d1.png
  :target: https://user-images.githubusercontent.com/14288520/202390632-d6f11217-58da-48ad-b7ae-37b88fdfb4d1.png

* **Clip**. If checked, then infinite Voronoi diagram will be clipped by
  horizontal and vertical planes, to generate a finite object. Checked by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/202393512-f3d182a0-ac89-4be2-9be2-612a772b16c4.gif
  :target: https://user-images.githubusercontent.com/14288520/202393512-f3d182a0-ac89-4be2-9be2-612a772b16c4.gif

* **Join**. If checked, then the node will join mesh objects for each ridge or
  region, and output one mesh object for each set of points. Otherwise, the
  node will output a separate mesh object for each ridge or region. Unchecked
  by default.

.. image:: https://user-images.githubusercontent.com/14288520/202403547-0af49b58-c6b6-435a-b07f-3dc23052c431.png
  :target: https://user-images.githubusercontent.com/14288520/202403547-0af49b58-c6b6-435a-b07f-3dc23052c431.png

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated ridges or regions.
* **Edges**. Edges of generated ridges or regions.
* **Faces**. Faces of generated ridges or regions.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/202404824-6656fcd4-4613-44a6-bca1-7b51cd6105bd.png
  :target: https://user-images.githubusercontent.com/14288520/202404824-6656fcd4-4613-44a6-bca1-7b51cd6105bd.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`