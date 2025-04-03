Dissolve Mesh Elements
======================

.. image:: https://user-images.githubusercontent.com/14288520/199957635-d432411b-f465-4f2d-b861-78896ed70b73.png
  :target: https://user-images.githubusercontent.com/14288520/199957635-d432411b-f465-4f2d-b861-78896ed70b73.png

Functionality
-------------
Dissolve will remove the geometry and fill in the surrounding geometry. 
Instead of removing the geometry, which may leave holes that you have to fill in again.

.. image:: https://user-images.githubusercontent.com/14288520/199959865-333bfc63-fe19-47b2-8920-826965f4fe83.png
  :target: https://user-images.githubusercontent.com/14288520/199959865-333bfc63-fe19-47b2-8920-826965f4fe83.png

* Analyzers-> :ref:`Component Analyzer/Vertices/Interior <VERTICES_IS_INTERIOR>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199963152-e3f375d2-77de-4cbc-b503-2921d16ba53e.png
  :target: https://user-images.githubusercontent.com/14288520/199963152-e3f375d2-77de-4cbc-b503-2921d16ba53e.png

Category
--------

Modifiers -> Modifier change -> Dissolve Mesh Elements

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Edges** - edges of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Mask** - mask of vertices, edges or faces which should be dissolved

Parameters
----------

* **Mode** 
   - **Verts**. Remove the vertex, merging all surrounding faces. In the case of two edges, merging them into a single edge
   - **Edges**. Removes edges sharing two faces (joining those faces)
   - **Faces**. Merges regions of faces that share edges into a single face
* **Use face split**. When dissolving vertices into surrounding faces, you can often end up with very large, uneven n-gons. The face split option limits dissolve to only use the corners of the faces connected to the vertex.
* **Use boundary tear**. Split off face corners instead of merging faces.
* **Use verts**. Undocumented

.. image:: https://user-images.githubusercontent.com/28003269/89491528-87303e80-d7c0-11ea-99ad-63335902a996.png

1) Original mesh.
2) Face Split: Off, Tear Boundaries: Off.
3) Face Split: On, Tear Boundaries: Off. 
4) Face Split: On/Off, Tear Boundaries: On.

Outputs
-------

- **Verts** - vertices of dissolved mesh
- **Edges** - edges of dissolved mesh
- **Faces** - faces of dissolved mesh
- **Verts ind** - vertices indexes of mesh before dissolving operation
- **Edges ind** - edges indexes of mesh before dissolving operation
- **Faces ind** - faces indexes of mesh before dissolving operation
- **Loops ind** - loops indexes of mesh before dissolving operation

*Note: `Index` sockets can map data of mesh elements from mesh before operation to mesh after operation. 
For mapping operation `list item` node can be used.*

.. image:: https://user-images.githubusercontent.com/28003269/89492923-d88dfd00-d7c3-11ea-974c-440472e0bb92.png

Examples
--------

**Dissolve random border faces**

.. image:: https://user-images.githubusercontent.com/14288520/199965580-e20b169a-5ced-4e06-b12f-2a36a16eabb3.png
  :target: https://user-images.githubusercontent.com/14288520/199965580-e20b169a-5ced-4e06-b12f-2a36a16eabb3.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers-> :ref:`Component Analyzer/Faces/Is_Boundary <FACES_IS_BOUNDARY>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* AND: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/199966076-4434102c-7f62-4548-b27d-efc3e21ed42e.gif
  :target: https://user-images.githubusercontent.com/14288520/199966076-4434102c-7f62-4548-b27d-efc3e21ed42e.gif

---------

**Dissolve random edges**

.. image:: https://user-images.githubusercontent.com/28003269/89445808-af8a4f80-d764-11ea-8d00-66c8d58f7519.gif

---------

**Dissolve all edges except vertical and horizontal**

.. image:: https://user-images.githubusercontent.com/28003269/89520787-70eda700-d7ef-11ea-9a61-b2e8d8b9fd74.gif
  :target: https://user-images.githubusercontent.com/28003269/89520787-70eda700-d7ef-11ea-9a61-b2e8d8b9fd74.gif

.. image:: https://user-images.githubusercontent.com/28003269/89520841-8531a400-d7ef-11ea-9c2d-67d43caeb09a.png
  :target: https://user-images.githubusercontent.com/28003269/89520841-8531a400-d7ef-11ea-9c2d-67d43caeb09a.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* COMPONENT-WISE: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Spatial-> :doc:`Delaunay 2D </nodes/spatial/delaunay_2d>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* OR, NOT: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Temporal Viewer: Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Dissolve faces by area**

.. image:: https://user-images.githubusercontent.com/28003269/89521871-561c3200-d7f1-11ea-8c5b-6e1e38b4549b.gif
  :target: https://user-images.githubusercontent.com/28003269/89521871-561c3200-d7f1-11ea-8c5b-6e1e38b4549b.gif


.. image:: https://user-images.githubusercontent.com/28003269/89521875-56b4c880-d7f1-11ea-98e4-a79ff30fecb0.png
  :target: https://user-images.githubusercontent.com/28003269/89521875-56b4c880-d7f1-11ea-98e4-a79ff30fecb0.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Analyzers-> :doc:`Area </nodes/analyzer/area>`
* Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask Converter </nodes/list_masks/mask_convert>`
* LESS X: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Logic-> :doc:`Switch </nodes/logic/switch_MK2>`
* Temporal Viewer: Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`