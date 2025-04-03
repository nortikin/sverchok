Triangulate Mesh
================

.. image:: https://user-images.githubusercontent.com/14288520/199673451-2f024398-99ef-4e8c-a946-23eb64fb0edd.png
  :target: https://user-images.githubusercontent.com/14288520/199673451-2f024398-99ef-4e8c-a946-23eb64fb0edd.png

*This node testing is in progress, so it can be found under Beta menu*

Functionality
-------------

This node applies Triangulate operator (Ctrl+T in normal mode) to the mesh. It can triangulate all faces or only selected ones.

.. image:: https://user-images.githubusercontent.com/14288520/199745393-91f9f48a-b2a4-40d5-b58a-eeb814f4caea.png
  :target: https://user-images.githubusercontent.com/14288520/199745393-91f9f48a-b2a4-40d5-b58a-eeb814f4caea.png

This node is useful mainly when other node generates ngons, especially not-convex ones.

.. image:: https://user-images.githubusercontent.com/14288520/199753486-0e465534-02e6-4eb8-827c-7dfa7a55f813.png
  :target: https://user-images.githubusercontent.com/14288520/199753486-0e465534-02e6-4eb8-827c-7dfa7a55f813.png

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **Mask**. List of boolean or integer flags. Zero or False means do not triangulate face with corresponding index. If this input is not connected, then all faces will be triangulated.

Parameters
----------

This node has the following parameters:

* **Quads mode**. Method of quads processing. Available modes are:
   * **Beauty**. Split the quads in nice triangles, slower method. 
   * **Fixed**. Split the quads on the 1st and 3rd vertices. 
   * **Fixed Alternate**. Split the quads on the 2nd and 4th vertices. 
   * **Shortest Diagonal**. Split the quads based on the distance between the vertices. 
* **Ngon mode**. Method of ngons processing. Available modes are:
   * **Beauty**. Arrange the new triangles nicely, slower method. 
   * **Scanfill**. Split the ngons using a scanfill algorithm. 

Outputs
-------

This node has the following outputs:

- **Vertices**. This is just a copy of input vertices for convenience.
- **Edges**.
- **Polygons**.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.
- **NewEdges**. This contains only new edges created by triangulation procedure.
- **NewPolys**. This contains only new faces created by triangulation procedure. If ``Mask`` input is not used, then this output will contain the same as ``Polygons`` output.

See also
--------

* Modifiers->Modifier Change-> :doc:`Split Faces </nodes/modifier_change/split_faces>`

Examples of usage
-----------------

Triangulated cube:

.. image:: https://user-images.githubusercontent.com/14288520/199747483-94750b00-c600-4bc9-847c-294105eca9ee.png
  :target: https://user-images.githubusercontent.com/14288520/199747483-94750b00-c600-4bc9-847c-294105eca9ee.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Triangulate only two faces of extruded polygon:

.. image:: https://user-images.githubusercontent.com/14288520/199759356-78797993-1d9d-4fb8-b3fc-e33b9563c040.png
  :target: https://user-images.githubusercontent.com/14288520/199759356-78797993-1d9d-4fb8-b3fc-e33b9563c040.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Modifier Make-> :doc:`Solidify </nodes/modifier_make/solidify_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`