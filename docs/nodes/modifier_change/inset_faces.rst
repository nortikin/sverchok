Inset Faces
===========

.. image:: https://user-images.githubusercontent.com/14288520/198664663-2d7b6f52-e955-4078-8a13-27a42d860aba.png
  :target: https://user-images.githubusercontent.com/14288520/198664663-2d7b6f52-e955-4078-8a13-27a42d860aba.png

Functionality
-------------
The node has similar functionality with `Blender inset command <https://docs.blender.org/manual/en/latest/modeling/meshes/editing/face/inset_faces.html>`_, so it just insert face into face.
In spite of Blender inset command the node can apply different values per face in most cases.

.. image:: https://user-images.githubusercontent.com/14288520/198678410-7781881d-a942-40f4-9fec-5b25d09f1602.png
  :target: https://user-images.githubusercontent.com/14288520/198678410-7781881d-a942-40f4-9fec-5b25d09f1602.png

Category
--------

CAD -> Inset faces

Inputs
------

- **Verts** - vertices of base mesh.
- **Faces** - edges of base mesh (optionally).
- **Edges** - faces of base mesh.
- **Face data** - any data related with given faces like material indexes (optionally).
- **Face mask** - selection list to mark faces in which the node should insert faces, in all daces by default.
- **Thickness** - Set the size of the offset. Can get multiple values - one value per face.
- **Depth** - Raise or lower the newly inset faces to add depth. Can get multiple values - one value per face.

Outputs
-------

- **Verts** - vertices
- **Edges** - edges, one can generate them from faces.
- **Faces** - faces.
- **Face data** - give values according topological changes if face data was given via input socket else give indexes of old faces.
- **Mask** - give selection mask according chosen option(s).

.. image:: https://user-images.githubusercontent.com/14288520/198688719-9e5f5fca-d749-460e-910d-86e15cc0f766.png
  :target: https://user-images.githubusercontent.com/14288520/198688719-9e5f5fca-d749-460e-910d-86e15cc0f766.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`

Parameters
----------

+--------------------------+--------+--------------------------------------------------------------------------------+
| Parameters               | Type   | Description                                                                    |
+==========================+========+================================================================================+
| Individual / Region      | switch | Switch between to modes                                                        |
+--------------------------+--------+--------------------------------------------------------------------------------+

.. image:: https://user-images.githubusercontent.com/14288520/201482623-51d72d35-db63-4d5d-8a65-52e102249d2c.png
  :target: https://user-images.githubusercontent.com/14288520/201482623-51d72d35-db63-4d5d-8a65-52e102249d2c.png

N panel
-------

+--------------------------+--------+--------------------------------------------------------------------------------+
| Parameters               | Type   | Description                                                                    |
+==========================+========+================================================================================+
| Offset even              | bool   | Scale the offset to give a more even thickness                                 |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Offset Relative          | bool   | Scale the offset by lengths of surrounding geometry                            |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Boundary                 | bool   | Determines whether open edges will be inset or not                             |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Edge Rail                | bool   | Created vertices slide along the original edges of the inner                   |
|                          |        |                                                                                |
|                          |        | geometry, instead of the normals                                               |
+--------------------------+--------+--------------------------------------------------------------------------------+
| Outset                   | bool   | Create an outset rather than an inset. Causes the geometry to be               |
|                          |        |                                                                                |
|                          |        | created surrounding selection (instead of within)                              |
+--------------------------+--------+--------------------------------------------------------------------------------+

* offset even:

.. image:: https://user-images.githubusercontent.com/14288520/198692610-3c5f55a7-d781-4f4c-8539-1a6fa4aae88b.gif
  :target: https://user-images.githubusercontent.com/14288520/198692610-3c5f55a7-d781-4f4c-8539-1a6fa4aae88b.gif

* Offset Relative

.. image:: https://user-images.githubusercontent.com/14288520/198694750-95eb0beb-5246-498e-9d66-3eb915d895a3.gif
  :target: https://user-images.githubusercontent.com/14288520/198694750-95eb0beb-5246-498e-9d66-3eb915d895a3.gif

* Outset

.. image:: https://user-images.githubusercontent.com/14288520/198709376-f9510293-bf9c-463c-b2fa-236de2677cbd.gif
  :target: https://user-images.githubusercontent.com/14288520/198709376-f9510293-bf9c-463c-b2fa-236de2677cbd.gif

Usage
-----

Inserting faces with different thickness per face:

.. image:: https://user-images.githubusercontent.com/14288520/198697606-43ab8b0c-e141-433a-8330-2690442facbb.png
  :target: https://user-images.githubusercontent.com/14288520/198697606-43ab8b0c-e141-433a-8330-2690442facbb.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Shuffle </nodes/list_struct/shuffle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using face data node for setting color to faces:

.. image:: https://user-images.githubusercontent.com/14288520/198701958-1aa3d8e9-a43b-4786-8989-bb83f42e2a69.png
  :target: https://user-images.githubusercontent.com/14288520/198701958-1aa3d8e9-a43b-4786-8989-bb83f42e2a69.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Shuffle </nodes/list_struct/shuffle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* BPY Data->Vertex Color MK3 (No in docs. TODO)

---------

Mask can be used ofr filtering output mesh with `list mask out` node for example:

.. image:: https://user-images.githubusercontent.com/14288520/198705342-3cd37bed-c44f-47a2-9d9b-55c002b548ce.png
  :target: https://user-images.githubusercontent.com/14288520/198705342-3cd37bed-c44f-47a2-9d9b-55c002b548ce.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Shuffle </nodes/list_struct/shuffle>`
* **List**-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* BPY Data->Vertex Color MK3 (No in docs. TODO)

.. image:: https://user-images.githubusercontent.com/14288520/198705028-1566d419-c9fe-40fa-a70e-9a14a8b8d159.gif
  :target: https://user-images.githubusercontent.com/14288520/198705028-1566d419-c9fe-40fa-a70e-9a14a8b8d159.gif

---------

Insert region mode can be used with multiple input values of thickness and depth
but in this case sometimes result can be unexpected.
The logic of work in this mode is next: mesh split into islands divided by faces with 0 values or 0 mask,
then for each island average thickness and depth is calculated and then faces are inserted.

In this mode outset is not supported.

.. image:: https://user-images.githubusercontent.com/14288520/198709953-733864cb-6d0f-443c-8de4-1def3704ea45.png
  :target: https://user-images.githubusercontent.com/14288520/198709953-733864cb-6d0f-443c-8de4-1def3704ea45.png

.. image:: https://user-images.githubusercontent.com/28003269/70794911-2e86de00-1db8-11ea-8e13-1dd8d52fe38b.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/70851464-f0b8b100-1eae-11ea-840c-f4d61e44826b.png