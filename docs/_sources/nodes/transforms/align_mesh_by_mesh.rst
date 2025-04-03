Align Mesh by Mesh
==================

.. image:: https://user-images.githubusercontent.com/28003269/70231673-36b99a80-1774-11ea-9163-3ffbad2148f7.png
  :target: https://user-images.githubusercontent.com/28003269/70231673-36b99a80-1774-11ea-9163-3ffbad2148f7.png

Functionality
-------------
This node finds bounding box of input points and calculate vector for moving mesh.
It can move `move` mesh by itself or give `move vector` which can be used for moving mesh outside the node. 
`Move vector` is useful when several align nodes are used for calculating resulting vector 
and move ultimate mesh only once.
According options of the node moving mesh will be aligned accordingly contours of base mesh.

Inputs
------

- **Base mesh** - mesh according which another mesh should be moved.
- **Move mesh** - mesh which should be moved.

Outputs
-------

- **Verts** - moved vertices of move input.
- **Move vector** - vector which should be applied to moving mesh.

Options
-------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Axis               | Enum  | axis along which mesh should be moved (multiple selection is allowed)          |
+--------------------+-------+--------------------------------------------------------------------------------+
| Base snap          | Enum  | left, right or middle side of base mesh for snapping                           |
+--------------------+-------+--------------------------------------------------------------------------------+
| Move snap          | Enum  | left, right or middle side of move mesh for snapping                           |
+--------------------+-------+--------------------------------------------------------------------------------+

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/59979409-970ab480-95f8-11e9-99b8-8a49c48a8f3c.gif
    :target: https://user-images.githubusercontent.com/28003269/59979409-970ab480-95f8-11e9-99b8-8a49c48a8f3c.gif

.. image:: https://user-images.githubusercontent.com/28003269/59979417-ad187500-95f8-11e9-9a7c-063731dbe127.png
    :target: https://user-images.githubusercontent.com/28003269/59979417-ad187500-95f8-11e9-9a7c-063731dbe127.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**It is possible to set different setting for different axis by using several nodes simultaneously:**

.. image:: https://user-images.githubusercontent.com/28003269/59979527-21074d00-95fa-11e9-9d89-8542de922079.gif
    :target: https://user-images.githubusercontent.com/28003269/59979527-21074d00-95fa-11e9-9d89-8542de922079.gif

.. image:: https://user-images.githubusercontent.com/28003269/59979532-33818680-95fa-11e9-8e0c-e63ab4ba8fef.png
    :target: https://user-images.githubusercontent.com/28003269/59979532-33818680-95fa-11e9-8e0c-e63ab4ba8fef.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Also it is possible to align object only to part of mesh, for this just cut unnecessary part of mesh before align node.**

.. image:: https://user-images.githubusercontent.com/28003269/59979719-409f7500-95fc-11e9-8df8-62610b36799d.gif
    :target: https://user-images.githubusercontent.com/28003269/59979719-409f7500-95fc-11e9-8df8-62610b36799d.gif

.. image:: https://user-images.githubusercontent.com/28003269/59979724-514feb00-95fc-11e9-9f59-cbf2df8832c7.png
    :target: https://user-images.githubusercontent.com/28003269/59979724-514feb00-95fc-11e9-9f59-cbf2df8832c7.png

* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Modifiers->Modifier Change-> :doc:`Delete Loose </nodes/modifier_change/delete_loose>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`