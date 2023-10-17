Transform mesh
==============

.. image:: https://user-images.githubusercontent.com/14288520/193476315-46d82a9e-43ea-4e0c-8dac-9e81b9b9c925.png
  :target: https://user-images.githubusercontent.com/14288520/193476315-46d82a9e-43ea-4e0c-8dac-9e81b9b9c925.png

Functionality
-------------
The node takes mesh and transform it according parameters. It can move, scale and rotate parts of mesh.
The logic is close how Blender manipulate with mesh itself. Selection elements determines by mask input.

.. image:: https://user-images.githubusercontent.com/28003269/73249068-98730f80-41cd-11ea-8ae9-a939cfbe94de.gif
    :target: https://user-images.githubusercontent.com/28003269/73249068-98730f80-41cd-11ea-8ae9-a939cfbe94de.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/193644280-57ce17f7-2460-4c95-9bc7-b825b8ab1b3b.png
  :target: https://user-images.githubusercontent.com/14288520/193644280-57ce17f7-2460-4c95-9bc7-b825b8ab1b3b.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

Category
--------

Transforms -> Transform mesh

Inputs
------

- **Verts** - vertices
- **Edges** - edges (optionally), required if selection mode is `edges`  
- **Faces** - faces (optionally), required if selection mode is `faces`
- **Mask** - bool mask or index mask according mask mode
- **Origin** - available with custom origin mode, custom origins
- **Space direction** - available with custom space mode, custom normal
- **Mask index** - available in index mask mode, indexes of mesh parts
- **Direction** - transform vector, axis for rotation mode
- **Factor** - factor of transform vector, radians for rotation mode

Outputs
-------

- **Verts** - transformed vertices

Parameters
----------

+------------------------------+-------+--------------------------------------------------------------------------------+
| Parameters                   | Type  | Description                                                                    |
+==============================+=======+================================================================================+
| Transform mode               | enum  | Move, scale or rotate                                                          |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Mask mode                    | enum  | Bool mask or index mask                                                        |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Origin mode                  | enum  | Bounding box center, median center, individual center,                         |
|                              |       |                                                                                |
|                              |       | custom center                                                                  |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Space mode                   | enum  | Global, normal, custom                                                         |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Selection mode (mask socket) | enum  | Vertexes, edges, faces                                                         |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Direction mode               | enum  | X, Y, Z or custom direction                                                    |
|  (direction socket)          |       |                                                                                |
+------------------------------+-------+--------------------------------------------------------------------------------+

**Boolean mask and values distribution:**
Boolean mask split mesh into selected and unselected parts.
The node apply only one parameter to all selected mesh.
If multiple parameters such as direction vector are given they distributes between selected elements.
Resulting direction vector is calculated by finding average value from distributed among selected elements parameters.

**Index mask and values distribution:**
Index mask marks different parts of mesh with different indexes.
The node apply properties in this mode only for parts of mesh 
with indexes equal to given indexes via `mask index` socket.

For example: 

given indexes - [1, 3], given parameters - [param1, param2]. 

All parts of mesh masked by 1 will be assigned with param1.

All parts of mesh masked by 3 will be assigned param2.

All other parts will be unchanged.

Examples
--------

**Generating and moving lines on mesh level:**

.. image:: https://user-images.githubusercontent.com/14288520/193643631-6ffa24ba-7e09-42ca-a240-29c57ca7fd42.png
    :target: https://user-images.githubusercontent.com/14288520/193643631-6ffa24ba-7e09-42ca-a240-29c57ca7fd42.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Modifiers->Modifier Change-> :doc:`Separate Parts To Indexes </nodes/modifier_change/separate_parts_to_indexes>`
* Set: List-> :doc:`List Modifier </nodes/list_mutators/modifier>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Moving disjoint parts =):**

.. image:: https://user-images.githubusercontent.com/14288520/193647222-a2948853-8180-4870-acc2-b71d1261518c.gif
    :target: https://user-images.githubusercontent.com/14288520/193647222-a2948853-8180-4870-acc2-b71d1261518c.gif

.. image:: https://user-images.githubusercontent.com/14288520/193647813-e456ffc8-0ba1-4f37-957a-653aa96bca31.png
    :target: https://user-images.githubusercontent.com/14288520/193647813-e456ffc8-0ba1-4f37-957a-653aa96bca31.png

* Modifiers->Modifier Change-> :doc:`Separate Parts To Indexes </nodes/modifier_change/separate_parts_to_indexes>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Set: List-> :doc:`List Modifier </nodes/list_mutators/modifier>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`

---------

**Randomly scaled faces:**

.. image:: https://user-images.githubusercontent.com/14288520/193649147-9fe39b7b-2999-466f-ac51-04822a3603d2.png
    :target: https://user-images.githubusercontent.com/14288520/193649147-9fe39b7b-2999-466f-ac51-04822a3603d2.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Randomly scaled loops of torus:**

.. image:: https://user-images.githubusercontent.com/14288520/193651715-cc02f1cb-7fd1-4bcd-99f7-503f7e0f3182.png
    :target: https://user-images.githubusercontent.com/14288520/193651715-cc02f1cb-7fd1-4bcd-99f7-503f7e0f3182.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Flatten monkey by nearby point:**

.. image:: https://user-images.githubusercontent.com/14288520/193666573-41b375bf-b083-4216-aacd-a834375caebb.gif
  :target: https://user-images.githubusercontent.com/14288520/193666573-41b375bf-b083-4216-aacd-a834375caebb.gif

.. image:: https://user-images.githubusercontent.com/14288520/193666541-1a514f6e-735c-4f4a-8b5a-578c79bea253.png
  :target: https://user-images.githubusercontent.com/14288520/193666541-1a514f6e-735c-4f4a-8b5a-578c79bea253.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Matrix-> :doc:`Matrix Out </nodes/matrix/matrix_out_mk2>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`