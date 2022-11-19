Voronoi on Mesh
===============

.. image:: https://user-images.githubusercontent.com/14288520/202569749-761acf3f-2cd4-46e2-9dd5-8ac5fa9c588c.png
  :target: https://user-images.githubusercontent.com/14288520/202569749-761acf3f-2cd4-46e2-9dd5-8ac5fa9c588c.png

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