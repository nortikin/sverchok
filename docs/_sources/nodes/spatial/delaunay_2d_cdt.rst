Delaunay 2D Cdt
===============

.. image:: https://user-images.githubusercontent.com/14288520/202119249-9400cea6-fe79-4edd-a888-cecbc46a273d.png
  :target: https://user-images.githubusercontent.com/14288520/202119249-9400cea6-fe79-4edd-a888-cecbc46a273d.png

Functionality
-------------
Computes the Constrained Delaunay Triangulation of a set of vertices,
with edges and faces that must appear in the triangulation. Some triangles may be eaten away,
or combined with other triangles, according to output type.
The returned verts may be in a different order from input verts, may be moved slightly,
and may be merged with other nearby verts.

.. image:: https://user-images.githubusercontent.com/14288520/202176663-a507c576-cdc6-45f1-a5e1-a36e2f9ab3e0.png
  :target: https://user-images.githubusercontent.com/14288520/202176663-a507c576-cdc6-45f1-a5e1-a36e2f9ab3e0.png

Category
--------

Modifiers -> Modifier make -> Delaunay 2D Cdt

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Edges** - edges of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Face data** (optional, one value per face of mesh) - Any data related with given faces.


Outputs
-------

- **Verts** - vertices, some can be deleted
- **Edges** - new and old edges
- **Faces** - new and old faces
- **Face data** - filtered according topology changes given face data if was give one or indexes of old faces

Modes
-----

- **Convex** - given mesh will be triangulated into bounding convex face

.. image:: https://user-images.githubusercontent.com/14288520/202145161-3729d719-388b-4c05-af86-822af23b0c06.gif
  :target: https://user-images.githubusercontent.com/14288520/202145161-3729d719-388b-4c05-af86-822af23b0c06.gif
  :width: 300px

- **Inside** - all parts outside given faces or closed edge loops will be ignored by triangulation algorithm

.. image:: https://user-images.githubusercontent.com/14288520/202145218-9b581f27-8e47-46ee-a708-4a4de54a247d.gif
  :target: https://user-images.githubusercontent.com/14288520/202145218-9b581f27-8e47-46ee-a708-4a4de54a247d.gif
  :width: 300px

.. image:: https://user-images.githubusercontent.com/14288520/202153784-a44dc95a-d9c5-4c4b-89a2-e50faa4636a2.gif
  :target: https://user-images.githubusercontent.com/14288520/202153784-a44dc95a-d9c5-4c4b-89a2-e50faa4636a2.gif
  :width: 300px

N panel
-------

- **Epsilon** - For nearness tests; number of figures after coma

.. image:: https://user-images.githubusercontent.com/14288520/202176125-ea2d8f76-b46c-4a70-a95d-ae64e5ce3d40.png
  :target: https://user-images.githubusercontent.com/14288520/202176125-ea2d8f76-b46c-4a70-a95d-ae64e5ce3d40.png

Examples
--------

**Combine of a line and random points into Delaunay triangulation:**

.. image:: https://user-images.githubusercontent.com/14288520/202162212-a0b731ea-0afa-4c23-bbf2-c646090fd805.png
  :target: https://user-images.githubusercontent.com/14288520/202162212-a0b731ea-0afa-4c23-bbf2-c646090fd805.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Random Vector </nodes/spatial/populate_mesh_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Triangulation of points inside given face:**

.. image:: https://user-images.githubusercontent.com/14288520/202170634-f26119f8-bf1c-41a6-881e-cf1d4fdf3739.png
  :target: https://user-images.githubusercontent.com/14288520/202170634-f26119f8-bf1c-41a6-881e-cf1d4fdf3739.png

* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Keeping color initial faces:**

.. image:: https://user-images.githubusercontent.com/14288520/202174338-9f178515-36eb-4110-b851-35f9b6e29471.png
  :target: https://user-images.githubusercontent.com/14288520/202174338-9f178515-36eb-4110-b851-35f9b6e29471.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* BPY Date-> Vertex Color MK3 (No docs)
