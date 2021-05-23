Voronoi on Mesh
===============

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
* **Spacing**. Percent of space to leave between generated fragment meshes.
  Zero means do not leave any space, i.e. regions will fully cover initial
  mesh. The default value is 0. This input can consume either a single value
  per object, or a list of values per object - one value per site. In the later
  case, each value will be used for corresponding cell.

Parameters
----------

This node has the following parameters:

* **Mode**. The available options are:

  * **Split Volume**. Split closed-volume mesh into smaller closed-volume mesh regions.
  * **Split Surface**. Split the surface of a mesh into smaller flat meshes.

  The default value is **Split Volume**.

* **Correct normals**. This parameter is available only when **Mode** parameter
  is set to **Volume**. If checked, then the node will make sure that all
  normals of generated meshes point outside. Otherwise, this is not guaranteed.
  Checked by default.
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

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of generated mesh.
* **Edges**. Edges of generated mesh.
* **Faces**. Faces of generated mesh.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/102384062-190d4b00-3fee-11eb-8405-71e8ed383d26.png

