Voronoi on Mesh
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3782710e-2a14-4bea-a835-37ac6ff715b4
  :target: https://github.com/nortikin/sverchok/assets/14288520/3782710e-2a14-4bea-a835-37ac6ff715b4

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

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the mesh to generate Voronoi diagram on. This input is mandatory.
* **Faces**. Faces of the mesh to generate Voronoi diagram on. This input is mandatory.
* **Sites**. The points to generate Voronoi diagram for. Usually you want for
  this points to lie either inside the mesh or on it's surface, but this is not
  necessary. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202571362-7f047b5b-64a9-489c-8167-5fcb125f7fdf.png
  :target: https://user-images.githubusercontent.com/14288520/202571362-7f047b5b-64a9-489c-8167-5fcb125f7fdf.png

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

* **Output nesting**. This defines nesting structure of output sockets. The available options are:

   * **Flat list**. Output a single flat list of mesh objects (Voronoi diagram
     ridges / regions) for all input meshes.
   * **Separate lists**. Output a separate list of mesh objects (Voronoi
     diagram ridges / regions) for each input mesh.
   * **Join meshes**. Output one mesh, joined from ridges / edges of Voronoi
     diagram, for each input mesh.

* **Accuracy**. This parameter is available in the N panel only. This defines
  the precision of mesh calculation (number of digits after decimal point). The
  default value is 6.

.. image:: https://user-images.githubusercontent.com/14288520/202577600-9f0e8eb6-2782-4a3b-9e58-f915823c9dfa.png
  :target: https://user-images.githubusercontent.com/14288520/202577600-9f0e8eb6-2782-4a3b-9e58-f915823c9dfa.png


Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated mesh.
* **Edges**. Edges of generated mesh.
* **Faces**. Faces of generated mesh.
* **Sites_idx**. Indices of sources sites for further using. (from sverchok 1.3-alpha-master)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/4d60e90e-19af-4600-88dc-92b67896967a
      :target: https://github.com/nortikin/sverchok/assets/14288520/4d60e90e-19af-4600-88dc-92b67896967a

    * Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

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
* Spatial-> :doc:`Populate Mesh </nodes/spatial/random_points_on_mesh>`
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

See also example
----------------

* Pulga Physics-> :ref:`Pulga Springs Force <PULGA_SPRINGS_FORCE_EXAMPLES>`