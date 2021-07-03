Voronoi on Surface
==================

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
* **UVPoints**. Points (sites) in U/V space of the surface, for which Voronoi
  diagram is to be generated. Only X and Y coordinates of these points will be
  used. This input is mandatory.
* **MaxSides**. This input is available only when **Mode** parameter is set to
  **UV Space**, and **Make faces** parameter is checked. Maximum number of
  sides of Voronoi polygon, for which this node will generate edges. The
  default value is 10.
* **Thickness**. This input is available only when **Mode** parameter is set to
  **3D Regions** or **3D Regions**. Thickness of Voronoi diagram objects. The
  default value is 1.0.
* **Clipping**. This defines the distance from outermost sites to the clipping
  planes. This input is only available when the **Clip** parameter is checked.
  The default value is 1.0.

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

* **Make faces**. This parameter is only available when **Mode** parameter is
  set to **UV Space**. This defines whether the node should generate polygons
  of Voronoi diagram. If not checked, the node will generate edges only.
  Unchecked by default.
* **Flat output**. This parameter is only available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**. If checked, the node will generate
  one flat list of objects for all sets of input parameters. Otherwise, a
  separate list of objects will be generated for each set of input parameter
  values. In 3D modes, this node generates a separate object for each region of
  Voronoi diagram.
* **Clip**.  This parameter is only available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**. This defines whether the node will
  cut the generated diagram by clipping planes. If not checked, then this node
  can potentially generate very large objects near edges of the surface.
  Checked by default.
* **Correct normals**. This parameter is available when **Mode** parameter is
  set to **3D Ridges** or **3D Regions**, or when **Make faces** parameter is
  checked. This defines whether the node should recalculate the normals of
  generated objects so that they all point outwards. Checked by default.
* **Ordered faces**. This parameter is available in the N palen only, when
  **Mode** parameter is set to **UV Space**, and only if **Make Faces**
  parameter is checked. If enabled, the node will make sure that generated
  faces are in the same order as input vertices. This procedure can take
  additional time. If not checked, the order of faces will not be the same as
  order of initial points.

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

.. image:: https://user-images.githubusercontent.com/284644/100520549-18884e00-31c0-11eb-82ed-c18b84fd6fe8.png

"3D Ridges" mode:

.. image:: https://user-images.githubusercontent.com/284644/100520548-18884e00-31c0-11eb-8843-f721ecfb238d.png

"3D Regions" mode:

.. image:: https://user-images.githubusercontent.com/284644/100520547-17572100-31c0-11eb-9c58-0f2628629031.png

