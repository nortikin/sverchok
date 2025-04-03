Voronoi on Surface
==================

.. image:: https://user-images.githubusercontent.com/14288520/202536634-cd7aa231-b742-4435-b2d5-e6a9751007d4.png
  :target: https://user-images.githubusercontent.com/14288520/202536634-cd7aa231-b742-4435-b2d5-e6a9751007d4.png

This node can require SciPy_ library to work, depending on selected operation mode.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Voronoi_ diagram for given set of points on a Surface object.

.. _Voronoi: https://en.wikipedia.org/wiki/Voronoi_diagram

This node can operate in different modes:

* In UV space (2D voronoi). Voronoi diagram is generated in the U/V space of
  the surface and then mapped onto the surface. Since mapping defined by the
  curve can be very non-uniform, this can be very different from real Voronoi
  diagram calculated by Euclidean metric in 3D space. But for not-too-curved
  surfaces, this can be used as "good enough" approximation.
* In 3D space. Voronoi diagram is calculated in 3D space for points on the
  surface. 3D Voronoi diagram is volumetric structure, not flat, so in this
  mode the node produces either regions or ridges of Voronoi diagram.

As Voronoi diagram is an infinite structure, this node can only generate it's
finite part. Only finite polygons / regions are generated, but even these can
be very large. To generate a smaller object, clipping by vertical / horizontal
planes can be applied.

Inputs
------

This node has the following parameters:

* **Surface**. The surface to generate Voronoi diagram on. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202553503-d38a9107-0c9a-49cd-bde8-b128244f2a70.png
  :target: https://user-images.githubusercontent.com/14288520/202553503-d38a9107-0c9a-49cd-bde8-b128244f2a70.png

* **UVPoints**. Points (sites) in U/V space of the surface, for which Voronoi
  diagram is to be generated. Only X and Y coordinates of these points will be
  used. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202553842-bc6f9c7b-19b8-4ffd-ae41-cf9f32ad0894.png
  :target: https://user-images.githubusercontent.com/14288520/202553842-bc6f9c7b-19b8-4ffd-ae41-cf9f32ad0894.png

* **MaxSides**. This input is available only when **Mode** parameter is set to
  **UV Space**, and **Make faces** parameter is checked. Maximum number of
  sides of Voronoi polygon, for which this node will generate edges. The
  default value is 10.

.. image:: https://user-images.githubusercontent.com/14288520/202554721-5f228bd1-e6af-4ff6-89a7-0ac304745926.png
  :target: https://user-images.githubusercontent.com/14288520/202554721-5f228bd1-e6af-4ff6-89a7-0ac304745926.png

* **Thickness**. This input is available only when **Mode** parameter is set to
  **3D Ridges** or **3D Regions**. Thickness of Voronoi diagram objects. The
  default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202865737-49786eee-d580-45bb-8967-14d36bc41196.png
  :target: https://user-images.githubusercontent.com/14288520/202865737-49786eee-d580-45bb-8967-14d36bc41196.png

.. image:: https://user-images.githubusercontent.com/14288520/202555250-d8e9b12d-2469-40b2-8641-1f008fd2b410.gif
  :target: https://user-images.githubusercontent.com/14288520/202555250-d8e9b12d-2469-40b2-8641-1f008fd2b410.gif

* **Clipping**. This defines the distance from outermost sites to the clipping
  planes. This input is only available when the **Clip** parameter is checked.
  The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202556515-6b5f47d5-69aa-4d86-a3a5-8bbf042156fc.gif
  :target: https://user-images.githubusercontent.com/14288520/202556515-6b5f47d5-69aa-4d86-a3a5-8bbf042156fc.gif

Parameters
----------

This node has the following parameters:

* **Mode**. Operation mode of the node. The available modes are:

  * **UV Space**. Voronoi diagram will be calculated in U/V space of the
    surface, and then mapped onto the surface.
  * **3D Ridges**. Voronoi diagram will be calculated in 3D space. Only ridges
    that separate sites on the surface will be generated. This mode is only
    available when SciPy library is installed.
  * **3D Regions**. Voronoi diagram will be calculated in 3D space. Only
    regions surrounding sites on the surface will be generated. This mode is
    only available when SciPy library is installed.

  The default mode is **UV Space**.

.. image:: https://user-images.githubusercontent.com/14288520/202538580-e4564d08-caed-44e9-8bbf-9b2989d24877.png
  :target: https://user-images.githubusercontent.com/14288520/202538580-e4564d08-caed-44e9-8bbf-9b2989d24877.png

* **Make faces**. This parameter is only available when **Mode** parameter is
  set to **UV Space**. This defines whether the node should generate polygons
  of Voronoi diagram. If not checked, the node will generate edges only.
  Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202539745-bf3dd460-198e-40ff-b11d-41be7b3f7c81.png
  :target: https://user-images.githubusercontent.com/14288520/202539745-bf3dd460-198e-40ff-b11d-41be7b3f7c81.png

* **Flat output**. This parameter is only available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**. If checked, the node will generate
  one flat list of objects for all sets of input parameters. Otherwise, a
  separate list of objects will be generated for each set of input parameter
  values. In 3D modes, this node generates a separate object for each region of
  Voronoi diagram.

.. image:: https://user-images.githubusercontent.com/14288520/202548155-84b76d0f-0aac-4036-a75c-2893734f6579.png
  :target: https://user-images.githubusercontent.com/14288520/202548155-84b76d0f-0aac-4036-a75c-2893734f6579.png

* **Clip**.  This parameter is only available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**. This defines whether the node will
  cut the generated diagram by clipping planes. If not checked, then this node
  can potentially generate very large objects near edges of the surface.
  Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202549190-4c9c458b-5cfa-48e3-bae8-ed188b331bc0.gif
  :target: https://user-images.githubusercontent.com/14288520/202549190-4c9c458b-5cfa-48e3-bae8-ed188b331bc0.gif

* **Correct normals**. This parameter is available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**, or when **Make faces** parameter is
  checked. This defines whether the node should recalculate the normals of
  generated objects so that they all point outwards. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202551772-c64ceccc-0754-41d7-a6e8-f7828f8751ca.png
  :target: https://user-images.githubusercontent.com/14288520/202551772-c64ceccc-0754-41d7-a6e8-f7828f8751ca.png

.. image:: https://user-images.githubusercontent.com/14288520/202550834-0b0cea53-47af-4cdf-a0e1-8c15100f0947.gif
  :target: https://user-images.githubusercontent.com/14288520/202550834-0b0cea53-47af-4cdf-a0e1-8c15100f0947.gif

* **Ordered faces**. This parameter is available in the N palen only, when
  **Mode** parameter is set to **UV Space**, and only if **Make Faces**
  parameter is checked. If enabled, the node will make sure that generated
  faces are in the same order as input vertices. This procedure can take
  additional time. If not checked, the order of faces will not be the same as
  order of initial points.

.. image:: https://user-images.githubusercontent.com/14288520/202552963-54333d18-f83f-4e78-85f0-cdd5632b897a.gif
  :target: https://user-images.githubusercontent.com/14288520/202552963-54333d18-f83f-4e78-85f0-cdd5632b897a.gif

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated ridges or regions.
* **Edges**. Edges of generated ridges or regions.
* **Faces**. Faces of generated ridges or regions.
* **UVVertices**. This output is available only when **Mode** parameter is set
  to **UV Space**. Vertices of Voronoi diagram in U/V space of the surface. Z
  coordinate of these vertices will always be zero.

Examples of Usage
-----------------

"UV Space** mode:

.. image:: https://user-images.githubusercontent.com/14288520/202558311-606e5fc4-6ab0-424b-9310-b9d3ea29efb3.png
  :target: https://user-images.githubusercontent.com/14288520/202558311-606e5fc4-6ab0-424b-9310-b9d3ea29efb3.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Surfaces-> :doc:`Build NURBS Surface </nodes/surface/nurbs_surface>`
* Spatial-> :doc:`Populate Surface </nodes/spatial/populate_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

"3D Ridges" mode:

.. image:: https://user-images.githubusercontent.com/14288520/202559021-dd66eab4-2b6f-4f8b-9bdf-b133a523d1db.png
  :target: https://user-images.githubusercontent.com/14288520/202559021-dd66eab4-2b6f-4f8b-9bdf-b133a523d1db.png

---------

"3D Regions" mode:

.. image:: https://user-images.githubusercontent.com/14288520/202563636-8632b4f8-2e1d-4ec2-aa85-b1697f9b12fa.png
  :target: https://user-images.githubusercontent.com/14288520/202563636-8632b4f8-2e1d-4ec2-aa85-b1697f9b12fa.png
