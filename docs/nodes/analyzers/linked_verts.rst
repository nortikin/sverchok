Linked Verts
=====

Functionality
-------------

Area node is one of the analyzer type. It is used the vertices that are connected to each vertex.

Inputs
------

**Vertices**: Vertex list (optional)
**Edges**: Edge data. 
**Selection**: Desired index list or mask list. 
**Distance**: Distance to input (measured in number of edges in between)

Parameters
----------

**Selection Type**: choose if you input a index list or as mask list in the **Selection** input


Outputs
-------

**Verts Id**: Index of the linked vertices, refering to the **Vertices** input list 
**Verts**: Linked verts list.
**Mask**: mask of the linked vertices, refering to the **Vertices** input list 


Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4188452/8f9cbf66-3772-11e4-8735-34462b7da54b.png
  :alt: AreaDemo1.PNG

