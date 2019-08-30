Align mesh by mesh
==================

.. image:: https://user-images.githubusercontent.com/28003269/63994821-088a4600-cb07-11e9-9a3d-583dcd63dc7a.png

Functionality
-------------
This node finds bounding box of input points and calculate vector for moving mesh. 
It means that this node should be used with other nodes such as move or matrix apply. 
According options of the node moving mesh will be aligned accordingly contours of base mesh.

Inputs
------

- **Base mesh** - mesh according which another mesh should be moved.
- **Move mesh** - mesh which should be moved.

Outputs
-------

- **Move vector** - vector which should be applied ot moving mesh.

N panel
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

.. image:: https://user-images.githubusercontent.com/28003269/59979417-ad187500-95f8-11e9-9a7c-063731dbe127.png

**It is possible to set different setting for different axis by using several nodes simultaneously:**

.. image:: https://user-images.githubusercontent.com/28003269/59979527-21074d00-95fa-11e9-9d89-8542de922079.gif

.. image:: https://user-images.githubusercontent.com/28003269/59979532-33818680-95fa-11e9-8e0c-e63ab4ba8fef.png

**Also it is possible to align object only to part of mesh for this just cut unuseful part of mesh before align node.**

.. image:: https://user-images.githubusercontent.com/28003269/59979719-409f7500-95fc-11e9-8df8-62610b36799d.gif

.. image:: https://user-images.githubusercontent.com/28003269/59979724-514feb00-95fc-11e9-9f59-cbf2df8832c7.png