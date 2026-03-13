Set Collection
==============

.. image:: https://user-images.githubusercontent.com/28003269/118350859-e8fcb080-b569-11eb-8342-c8987bd4c523.png

Functionality
-------------
It puts objects into collection. One node can put one object only into one collection.
It is possible to use several nodes in a chain in this case
it's possible to put objects into several collections.
When the node is disconnected from objects or the collection is changed it will remove last objects from collections
which was previously assigned. When the node links an object to a collection
it always try to unlink it from scene collection.
`Unlink others` button will remove the objects from all other collections except collections of the node.

Category
--------

BPY Data -> Set Collection

Inputs
------

- **Object** - Blender object data blocks
- **Collection** - Blender collection data blocks

Outputs
-------

- **Object** - Blender object data blocks

Usage
-----

Link objects form different courses to a collection.

.. image:: https://user-images.githubusercontent.com/28003269/118350568-8eaf2000-b568-11eb-9761-8fdff98aea9c.png
