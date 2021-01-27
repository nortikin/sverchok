Linked Verts
============

Functionality
-------------

Linked Verts node is one of the analyzer type. It is used  to get the vertices that are connected to a vertex. It can also get the vertices that are separated by N edges allowing the creation of complex selection patterns.

Inputs
------

- **Vertices**: Vertex list (optional).
- **Edges**: Edge data. 
- **Selection**: Desired index list or mask list. 
- **Distance**: Distance to input (measured in number of edges in between).

Parameters
----------

**Selection Type**: choose if you input a index list or a mask list in the **Selection** input


Outputs
-------

- **Verts Id**: Index of the linked vertices, referring to the **Vertices** input list.
- **Verts**: Linked verts list.
- **Mask**: mask of the linked vertices, referring to the **Vertices** input list. 


Example of usage
----------------

In this example you get the white vertex when asking for the vertex that are connected to the green dot.

.. image:: https://user-images.githubusercontent.com/10011941/57044482-fd173300-6c6a-11e9-9d74-f6e78b20c934.png
  :alt: Linked Verts.PNG

Using a range of integers as Distance input will expand the selection or the creation of patterns.

.. image:: https://user-images.githubusercontent.com/10011941/57044498-030d1400-6c6b-11e9-8059-8319227c4df1.png
  :alt: Linked Verts.PNG

.. image:: https://user-images.githubusercontent.com/10011941/57044502-06a09b00-6c6b-11e9-83fb-ef3873a703f6.png
  :alt: Linked Verts.PNG

.. image:: https://user-images.githubusercontent.com/10011941/57044827-25ebf800-6c6c-11e9-8537-b65948cf158e.png
  :alt: Linked Verts.PNG