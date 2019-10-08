Selection graber
================

.. image:: https://user-images.githubusercontent.com/28003269/66333434-06a67480-e948-11e9-98d3-b32130db68d2.png

Functionality
-------------

The idea of node is to save selection mask from selected object in blender scene. 
It can keep selection of vertex, edges and faces of one object.

Usage
-----
- Generate object via Sverchok.
- Bake the object on stage when topology won't be changed.
- Select required elements of mesh.
- Bake selection in the node by pressing 'Get form selection' button.
- Continue working with selected part of the object.

Note: selection will be keeped in blender file and will be available after rebooting Blender.

Outputs
-------

- **Vertex mask** - sequence of 0 and 1 in order of base mesh where 1 means that element is selected
- **Edge mask** - sequence of 0 and 1 in order of base mesh where 1 means that element is selected
- **Face mask** - sequence of 0 and 1 in order of base mesh where 1 means that element is selected

Properties
----------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Vertex             | Bool  | If active pressing the button will rewrite vertex mask output                  |
+--------------------+-------+--------------------------------------------------------------------------------+
| Edge               | Bool  | If active pressing the button will rewrite edge mask output                    |
+--------------------+-------+--------------------------------------------------------------------------------+
| Face               | Bool  | If active pressing the button will rewrite face mask output                    |
+--------------------+-------+--------------------------------------------------------------------------------+

Note: The button will rewright selection data in sockets according settings of node.


Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/59754212-b91dd300-9296-11e9-9891-e7dd387f1182.png

.. image:: https://user-images.githubusercontent.com/28003269/59756403-b329f100-929a-11e9-93c9-04b53c9c95e9.png