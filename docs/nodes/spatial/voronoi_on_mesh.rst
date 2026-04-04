Voronoi on Mesh
===============

.. image:: https://github.com/user-attachments/assets/85e2b2e4-0dea-4f85-9466-7b5848c4e620
  :target: https://github.com/user-attachments/assets/85e2b2e4-0dea-4f85-9466-7b5848c4e620

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node creates Voronoi diagram on a given mesh, from specified set of
initial points (sites). More specifically, it subdivides the mesh into regions
of such Voronoi diagram. It is possible to subdivide:

* either surface of the mesh, generating a series of flat meshes,
* or the volume of the mesh, generating a series of closed-body meshes. In this
  mode, it is required that the mesh represents a closed volume.

Addition
--------

The number of resulting objects can differ from the number of sites you set, both smaller and larger. Example of smaller number:


  .. image:: https://github.com/user-attachments/assets/f02be360-304f-432b-95a5-406f7e1a7e71
    :target: https://github.com/user-attachments/assets/f02be360-304f-432b-95a5-406f7e1a7e71

Example of bigger number:

  .. image:: https://github.com/user-attachments/assets/8d419553-3e13-4704-8608-41c52dc2b318
    :target: https://github.com/user-attachments/assets/8d419553-3e13-4704-8608-41c52dc2b318


Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the mesh to generate Voronoi diagram on. This input is mandatory.
* **Polygons**. Faces of the mesh to generate Voronoi diagram on. This input is mandatory.

  .. image:: https://github.com/user-attachments/assets/09b2accd-7f8b-46e9-aa3a-254f1e1518d7
    :target: https://github.com/user-attachments/assets/09b2accd-7f8b-46e9-aa3a-254f1e1518d7

* **Matrices of Meshes**. Matrices of input objects.

    .. image:: https://github.com/user-attachments/assets/2661d9ef-b5d3-486b-9cf7-00f666f7218d
      :target: https://github.com/user-attachments/assets/2661d9ef-b5d3-486b-9cf7-00f666f7218d
      :width: 500px

  Used in complex multi-object scenarios. If you have several input objects and set postprocess property "Join Mode" to "Split (disconnect)" then you mess up the corresponding matrices for the resulting objects


* **Voronoi Sites**. The points to generate Voronoi diagram for. Usually you want for
  this points to lie either inside the mesh or on it's surface, but this is not
  necessary. This input is mandatory. If list of Voronoi sites is Zero length then source object will not processed
  and transfer it params to output sockets.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/4353aec1-e4f5-4cb4-a9ec-f3e8c6435c0b
    :target: https://github.com/nortikin/sverchok/assets/14288520/4353aec1-e4f5-4cb4-a9ec-f3e8c6435c0b

* **Matrices of meshes**. Matrices of input meshes if meshes placed not in the zero. For example: if you using "Get Objects Data" with "Apply matrices" parameter off then real coords can be calculated with "Get Objects Data" Matrices output
  
  .. image:: https://github.com/user-attachments/assets/1bf85e83-12c2-4469-8d35-526be6e5b0c8
    :target: https://github.com/user-attachments/assets/1bf85e83-12c2-4469-8d35-526be6e5b0c8

* **Voronoi Sites**. Points of Voronoi. If using Source Join Mode as "Merge" then sites merged only what in input "Voronoi Sites". For example: if objects are 3 and sites are 2 then sites will not recalculate for object number 3.

  .. image:: https://github.com/user-attachments/assets/862468b6-bd4d-4503-8436-a3013e0bbb77
    :target: https://github.com/user-attachments/assets/862468b6-bd4d-4503-8436-a3013e0bbb77

  If mode is split then every unconnected object will get sites of original mesh:

  .. image:: https://github.com/user-attachments/assets/f153ae9c-a0c2-4d2a-a4d3-dacb43c74844
    :target: https://github.com/user-attachments/assets/f153ae9c-a0c2-4d2a-a4d3-dacb43c74844

* **Mask of sites**. List of True/False or indexes. What Sites will be show in result.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/61bd23e3-3a8e-47e2-b18f-1c7272b71679
    :target: https://github.com/nortikin/sverchok/assets/14288520/61bd23e3-3a8e-47e2-b18f-1c7272b71679

* **invert** Invert list **Mask of Sites**.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/b8360826-c678-4b47-b783-3e05a71f1275
    :target: https://github.com/nortikin/sverchok/assets/14288520/b8360826-c678-4b47-b783-3e05a71f1275

* **Spacing**. Percent of space to leave between generated fragment meshes.
  Zero means do not leave any space, i.e. regions will fully cover initial
  mesh. The default value is 0. This input can consume either a single value
  per object, or a list of values per object - one value per site. In the later
  case, each value will be used for corresponding cell.

  .. image:: https://user-images.githubusercontent.com/14288520/202571726-e7ecbf0a-72ad-48bd-b3c5-cd800b86b524.gif
    :target: https://user-images.githubusercontent.com/14288520/202571726-e7ecbf0a-72ad-48bd-b3c5-cd800b86b524.gif

The list of values per object - one value per site:

  .. image:: https://user-images.githubusercontent.com/14288520/202572900-c82edfd3-6634-4425-b33a-b4f09f87ecc9.png
    :target: https://user-images.githubusercontent.com/14288520/202572900-c82edfd3-6634-4425-b33a-b4f09f87ecc9.png

Parameters
----------

This node has the following parameters:

* **Mode**. The available options are:

  * **Split Volume**. Split closed-volume mesh into smaller closed-volume mesh regions.
  * **Split Surface**. Split the surface of a mesh into smaller flat meshes.

  The default value is **Split Volume**.

.. image:: https://user-images.githubusercontent.com/14288520/202573307-cd8f42e1-6909-47d0-bf37-9211dbafb69a.png
  :target: https://user-images.githubusercontent.com/14288520/202573307-cd8f42e1-6909-47d0-bf37-9211dbafb69a.png

* **Correct normals**. This parameter is available only when **Mode** parameter
  is set to **Volume**. If checked, then the node will make sure that all
  normals of generated meshes point outside. Otherwise, this is not guaranteed.
  Checked by default.

    .. image:: https://user-images.githubusercontent.com/14288520/202575356-5ece8f0e-4787-4d85-846e-c8fb525e732b.png
      :target: https://user-images.githubusercontent.com/14288520/202575356-5ece8f0e-4787-4d85-846e-c8fb525e732b.png

    .. image:: https://user-images.githubusercontent.com/14288520/202574847-5343b0d1-61f3-4313-a8a1-7efce49f1405.gif
      :target: https://user-images.githubusercontent.com/14288520/202574847-5343b0d1-61f3-4313-a8a1-7efce49f1405.gif

* **Pre processing**. This define preprocessing original objects, sites, matrices and masks.

  - **Split**. Separate unconnected meshes independently before process. Sites, matrices and masks keep the same for every separated element.
  - **Keep**. Do nothing. All original meshes stay unchanged before process
  - **Merge**. Merge original meshes, sites, masks. Spacing gets first.

    .. image:: https://github.com/user-attachments/assets/2619e606-f96d-4ef8-8f7f-324b6a8f5b8d
      :target: https://github.com/user-attachments/assets/2619e606-f96d-4ef8-8f7f-324b6a8f5b8d

    .. image:: https://github.com/user-attachments/assets/11a1b295-83b4-4a9a-a62f-9760a93ae680
      :target: https://github.com/user-attachments/assets/11a1b295-83b4-4a9a-a62f-9760a93ae680

    .. image:: https://github.com/user-attachments/assets/9961c060-f60d-4e7d-a40e-730e6861fa4a
      :target: https://github.com/user-attachments/assets/9961c060-f60d-4e7d-a40e-730e6861fa4a

    .. image:: https://github.com/user-attachments/assets/a0a2de0a-ded9-408e-9609-24373e5c51f5
      :target: https://github.com/user-attachments/assets/a0a2de0a-ded9-408e-9609-24373e5c51f5


* **Post processing**. This defines nesting structure of result meshes. The available options are:

  * **Split (disconnect)**. Separate the result meshes into individual unconnected meshes. Every unconnected part get matrix of original meshes.
  * **Split (sites)**. Separate the result meshes into meshes of original sites (can keep several unconnected objects). Every part get matrix of original meshes.
  * **Keep**. Keep parts of preprocessed meshes. Also keep matrices of original objects unchanged.
  * **Merge**. Join all results meshes into a single mesh.

    .. image:: https://github.com/user-attachments/assets/ad754124-d6e2-4371-95d4-cfd9a14c7bb5
      :target: https://github.com/user-attachments/assets/ad754124-d6e2-4371-95d4-cfd9a14c7bb5

    .. image:: https://github.com/user-attachments/assets/58e43bce-4428-4210-b0a9-3234d7b1a7ff
      :target: https://github.com/user-attachments/assets/58e43bce-4428-4210-b0a9-3234d7b1a7ff

* **Accuracy**. This parameter is available in the N panel only. This defines
  the precision of mesh calculation (number of digits after decimal point). The
  default value is 6.

    .. image:: https://github.com/user-attachments/assets/c871ef28-fbf2-46ae-8707-bbfb72497ca2
      :target: https://github.com/user-attachments/assets/c871ef28-fbf2-46ae-8707-bbfb72497ca2


Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated mesh.
* **Vertices Outer**.
* **Vertices Inner**.
* **Vertices Border**.
* **Vertices Outer Indexes**.
* **Vertices Inner Indexes**.
* **Vertices Border Indexes**.

    .. image:: https://github.com/user-attachments/assets/1dc196b6-0f89-4677-ae62-90555ce6a0f7
      :target: https://github.com/user-attachments/assets/1dc196b6-0f89-4677-ae62-90555ce6a0f7

    .. image:: https://github.com/user-attachments/assets/ebb8817f-6a5d-4903-b808-e4931a5695ea
      :target: https://github.com/user-attachments/assets/ebb8817f-6a5d-4903-b808-e4931a5695ea

* **Edges**. Edges of generated mesh.
* **Edges Outer**.
* **Edges Inner**.
* **Edges Border**.
* **Edges Outer Indexes**.
* **Edges Inner Indexes**.
* **Edges Border Indexes**.

    .. image:: https://github.com/user-attachments/assets/cf0b2c90-c04c-458f-9ba5-85c26f5fa783
      :target: https://github.com/user-attachments/assets/cf0b2c90-c04c-458f-9ba5-85c26f5fa783

    .. image:: https://github.com/user-attachments/assets/c6dda949-a694-4ddf-81e9-4bd9d153ff85
      :target: https://github.com/user-attachments/assets/c6dda949-a694-4ddf-81e9-4bd9d153ff85

* **Polygons**. Faces of generated mesh.
* **Polygons Outer Inner Mask**.
* **Polygons Outer**.
* **Polygons Inner**.
* **Polygons Border**.


* **Polygons Outer Indexes**.
* **Polygons Inner Indexes**.
* **Polygons Border Indexes**.

    .. image:: https://github.com/user-attachments/assets/e51f9fd8-071d-4e71-b970-f0b09560531b
      :target: https://github.com/user-attachments/assets/e51f9fd8-071d-4e71-b970-f0b09560531b

    .. image:: https://github.com/user-attachments/assets/99db0125-e62b-4818-b181-2a90f50bbb3b
      :target: https://github.com/user-attachments/assets/99db0125-e62b-4818-b181-2a90f50bbb3b

  Additionally:

    .. image:: https://github.com/user-attachments/assets/5fde423b-ad47-4bc8-8b4d-9758b6c92477
      :target: https://github.com/user-attachments/assets/5fde423b-ad47-4bc8-8b4d-9758b6c92477


* **Used Sites idx**. Indices of sources sites for further using (after apply Mask of sites). (from sverchok 1.3-alpha-master)
* **Used Sites Verts**. Values of used sites. Keep of source struct of input socket "Voronoi sites" lists (after apply Mask of sites). (from sverchok 1.3-alpha-master)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/91ccb203-e0bb-49a0-a626-e403ee30be3c
      :target: https://github.com/nortikin/sverchok/assets/14288520/91ccb203-e0bb-49a0-a626-e403ee30be3c

    * Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

* **Matrices**. Matrices or results meshes by join mode. 

    .. image:: https://github.com/user-attachments/assets/59580680-401d-44d3-98fa-20ff6e718541
      :target: https://github.com/user-attachments/assets/59580680-401d-44d3-98fa-20ff6e718541

    .. image:: https://github.com/user-attachments/assets/2edd54d3-cb90-4d20-8a26-a70be84044ec
      :target: https://github.com/user-attachments/assets/2edd54d3-cb90-4d20-8a26-a70be84044ec

Addition info
-------------

From version of sverchok 1.3.0-alpha sites can be any configurations: Line, Plane, Circle, Sphere

.. image:: https://github.com/nortikin/sverchok/assets/14288520/20df452e-be1e-47b2-acda-f2b7a1a8553e
  :target: https://github.com/nortikin/sverchok/assets/14288520/20df452e-be1e-47b2-acda-f2b7a1a8553e

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/22ab225c-a8b5-4596-bee1-85a6412c8bb1
  :target: https://github.com/nortikin/sverchok/assets/14288520/22ab225c-a8b5-4596-bee1-85a6412c8bb1

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/8fa05903-0244-441a-87a3-aa42415e6b30
  :target: https://github.com/nortikin/sverchok/assets/14288520/8fa05903-0244-441a-87a3-aa42415e6b30

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/27e4c0a4-e56d-4f4f-9db5-04a92c0c7180
  :target: https://github.com/nortikin/sverchok/assets/14288520/27e4c0a4-e56d-4f4f-9db5-04a92c0c7180

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/202578440-c713aac3-c787-456a-b796-190204bf297a.png
  :target: https://user-images.githubusercontent.com/14288520/202578440-c713aac3-c787-456a-b796-190204bf297a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Modifiers->Modifier Change-> :doc:`Inset Faces </nodes/modifier_change/inset_faces>`
* Modifiers->Modifier Make-> :doc:`Subdivide </nodes/modifier_change/subdivide_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

Inspired by https://www.youtube.com/watch?v=Ip6JI6Qiiwg

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5d01e61f-9743-4a07-a2c8-2866a7191e73
  :target: https://github.com/nortikin/sverchok/assets/14288520/5d01e61f-9743-4a07-a2c8-2866a7191e73

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Modifiers->Modifier Change-> :doc:`Inset Faces </nodes/modifier_change/inset_faces>`
* Number-> :doc:`Curve Mapper </nodes/number/curve_mapper>`
* LEN, DIV, MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Particles MK2 </nodes/scene/particles_MK2>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c4153ae0-ca18-4f29-968c-ede4d2197008
  :target: https://github.com/nortikin/sverchok/assets/14288520/c4153ae0-ca18-4f29-968c-ede4d2197008

--------

Like the previous example but node "Particle System" replaced by node "Spiral":

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b5704476-fbc4-4c0a-a116-d7a1738567fe
  :target: https://github.com/nortikin/sverchok/assets/14288520/b5704476-fbc4-4c0a-a116-d7a1738567fe

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Reparametrize Curve </nodes/curve/reparametrize>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Modifiers->Modifier Change-> :doc:`Inset Faces </nodes/modifier_change/inset_faces>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`A Number </nodes/number/mix_inputs>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Number-> :doc:`Curve Mapper </nodes/number/curve_mapper>`
* LEN, DIV, MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2ad77100-6630-4a27-aa36-a88a7b2d7f5b
  :target: https://github.com/nortikin/sverchok/assets/14288520/2ad77100-6630-4a27-aa36-a88a7b2d7f5b

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4e963254-251d-441d-808f-f30c9af55d62
  :target: https://github.com/nortikin/sverchok/assets/14288520/4e963254-251d-441d-808f-f30c9af55d62

blend file: https://github.com/nortikin/sverchok/files/12342712/Voronoi.Tower.006.blend.zip

--------

Show external surface as frame:

.. image:: https://github.com/user-attachments/assets/569e0afe-619b-450b-8c9f-df1583b894a9
  :target: https://github.com/user-attachments/assets/569e0afe-619b-450b-8c9f-df1583b894a9

See also example
----------------

* Pulga Physics-> :ref:`Pulga Springs Force <PULGA_SPRINGS_FORCE_EXAMPLES>`
