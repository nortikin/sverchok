:orphan:

Populate Mesh (Random points on mesh)
=====================================

.. image:: https://user-images.githubusercontent.com/14288520/201529930-3525fdf2-11d0-47c1-baea-3ca103113a2e.png
  :target: https://user-images.githubusercontent.com/14288520/201529930-3525fdf2-11d0-47c1-baea-3ca103113a2e.png

Functionality
-------------
The node distributes points on given mesh.

.. image:: https://user-images.githubusercontent.com/14288520/201531076-d2b9e049-b229-4065-acbe-a9c735364e3c.png
  :target: https://user-images.githubusercontent.com/14288520/201531076-d2b9e049-b229-4065-acbe-a9c735364e3c.png

Volume:

.. image:: https://user-images.githubusercontent.com/14288520/201530858-6d55519a-b06d-4a90-a15d-a564d7c9e5e6.gif
  :target: https://user-images.githubusercontent.com/14288520/201530858-6d55519a-b06d-4a90-a15d-a564d7c9e5e6.gif

Category
--------

Spatial -> Populate Mesh

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Face weight** (optional, one value per face of mesh) - any value per face, the less value the less number of vertices generates on current face. Values lessen then 0 will be changed to 0. This input can be used as mask. Just assign 0 values to faces on which there is no need in generation points.
- **Number** (one value per mesh) - number of vertices which should be distributed on given mesh
- **Seed** (one value per mesh) - seed for generation random vertices

Parameters
----------

This node has the following parameters:

- **Mode**. The available options are:

  * **Surface**. Generate points on the surface of the mesh.
  * **Volume**. Generate points inside the volume of the mesh. The mesh is
    expected to represent a closed volume in this case. Recomend use 
    [Modifiers->Modifier Change-> :doc:`Recalculate Normals </nodes/modifier_change/recalc_normals>`] before node.
  * **Edges**.  Generate points on the edges of the mesh.

  The default option is **Surface**.

.. image:: https://user-images.githubusercontent.com/14288520/201532406-4edb32da-8636-49c2-bc86-69fee4db753f.png
  :target: https://user-images.githubusercontent.com/14288520/201532406-4edb32da-8636-49c2-bc86-69fee4db753f.png

- **Proportional**. This parameter is available only when **Mode** parameter is
  set to **Surface**. If checked, then the number of points on each face will
  be proportional to the area of the face (and to the weight provided in the
  **Face weight** input). If not checked, then the number of points on each
  face will be only defined by **Face weight** input. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/201532330-384530c4-23b7-4e23-89f7-eef5f533d705.png
  :target: https://user-images.githubusercontent.com/14288520/201532330-384530c4-23b7-4e23-89f7-eef5f533d705.png

- **All Triangles**. Enable if the input mesh is made only of triangles
  (makes node faster). Available in Surfaces and Volume modes (in N-Panel)

- **Safe Check**. Disabling it will make node faster but polygon indices
  referring to unexisting points will crash Blender. Only available in Volume Mode.
  (in N-Panel)

- **Implementation**. Offers two implementations:
  * **Numpy**. Faster
  * **Mathutils**. Old implementation. Slower.
  Only available in Surface Mode (in N-Panel)

- **Output Numpy**. Output NumPy arrays in stead of regular list (makes node faster)
  Only available in Surface and Edges modes (in N-Panel)


Outputs
-------

- **Verts** - random vertices on mesh
- **Face / Edges index** - indexes of faces/edges to which random vertices lays. This input
  is available only when **Mode** parameter is set to **Surface** or **Edges**.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/201532606-a738a7b3-c303-44d6-ab81-3f49b0c11468.gif
  :target: https://user-images.githubusercontent.com/14288520/201532606-a738a7b3-c303-44d6-ab81-3f49b0c11468.gif

.. image:: https://user-images.githubusercontent.com/14288520/201532541-c2446b12-9ed8-40d2-ac5f-52a8346d8061.png
  :target: https://user-images.githubusercontent.com/14288520/201532541-c2446b12-9ed8-40d2-ac5f-52a8346d8061.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Normals of faces of regular solid, located on random points**

.. image:: https://user-images.githubusercontent.com/14288520/201533473-21aabbe1-a6ab-4452-a2f7-c125c3e8da7d.png
  :target: https://user-images.githubusercontent.com/14288520/201533473-21aabbe1-a6ab-4452-a2f7-c125c3e8da7d.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator->Generatots Extended-> :doc:`Regular Solid </nodes/generators_extended/regular_solid>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Distribution of points on sphere surface according distance to floating point**

.. image:: https://user-images.githubusercontent.com/28003269/70341948-7d3ef000-186d-11ea-8136-2fccad23be08.gif

.. image:: https://user-images.githubusercontent.com/14288520/201537083-e6b4cac6-3f2e-428b-84d1-fc4b01f20ef0.png
  :target: https://user-images.githubusercontent.com/14288520/201537083-e6b4cac6-3f2e-428b-84d1-fc4b01f20ef0.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Analyzers-> :doc:`Nearest Point on Mesh </nodes/analyzer/nearest_point_on_mesh>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* List->List Struct-> :doc:`List Sort </nodes/list_struct/sort>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/201537393-153bbaef-d356-4f07-ae61-5647fcdae1af.gif
  :target: https://user-images.githubusercontent.com/14288520/201537393-153bbaef-d356-4f07-ae61-5647fcdae1af.gif

---------

**Voronoi from unevenly distributed points on faces**

.. image:: https://user-images.githubusercontent.com/14288520/201541052-22d3d058-12dc-443d-b823-f3d290adc30c.png
  :target: https://user-images.githubusercontent.com/14288520/201541052-22d3d058-12dc-443d-b823-f3d290adc30c.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Spacial-> :doc:`Voronoi 2D </nodes/spatial/voronoi_2d>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/201540714-bc24a930-2fb8-439a-8883-44525bf9bb74.gif
  :target: https://user-images.githubusercontent.com/14288520/201540714-bc24a930-2fb8-439a-8883-44525bf9bb74.gif
