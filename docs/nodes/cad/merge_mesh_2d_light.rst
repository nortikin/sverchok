Merge mesh 2D light
===================

.. image:: https://user-images.githubusercontent.com/28003269/68123724-2b7e0f80-ff27-11e9-9c81-99037f35141e.png

Functionality
-------------
The node takes mesh determined by faces and returns new mesh with taking in account intersection of given faces.
This means that output can be similar to input if input faces does not have any intersection.
For example output of two intersected squares will be in next view:

.. image:: https://user-images.githubusercontent.com/28003269/68193618-c3820480-ffcc-11e9-8b7b-9b9d65838ec2.png

Also this node can connect not intersecting polygons.
If face is inside another face the one will be connected with boundary face with two extra edges 
(number of edges can be different).

.. image:: https://user-images.githubusercontent.com/28003269/68193732-0c39bd80-ffcd-11e9-9c9d-0b227f1c1bf0.png

Also this node have optional extra output socket of face index mash which should be switched on on N panel.
This output gives index of old face for every new faces.
For example if you merged two squares and each of them had different color 
it is possible to assign old colors to new mesh.
Besides if squares have intersection then overlapping polygon will have color of polygon which was added earlier.

.. image:: https://user-images.githubusercontent.com/28003269/68194735-fcbb7400-ffce-11e9-95e5-ad55d37e7667.gif

**Warning:**

This node is not 100 % robust. Some corner cases can knock it out. If you get an error or unexpected result check:

- did not you try to plug edges instead of faces.
- try to change accuracy parameter on N panel.

Category
--------

CAD -> Merge mesh 2D light

Inputs
------

- **Vertices** - vertices
- **Faces** - faces (don't try to plug edges)

Outputs
-------

- **Vertices** - vertices, can produce new vertices
- **Faces** - faces, also new edges can be added for showing holes
- **Face index** (optionally) - index of old face by which new face was created 

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Show face mask (N-panel) | bool  | Enable of showing face index mask output socket                                |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Accuracy (N-panel)       | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------------+-------+--------------------------------------------------------------------------------+

**Accuracy** - In most cases there is no need in touching this parameter
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error.
This parameter does not have any affect to performance in spite of its name.

Usage
-----

If there is need for example to merge two squares they should be joined in one object before.
This can be done with 'list join' nodes and 'mesh join':

.. image:: https://user-images.githubusercontent.com/28003269/68199389-63dd2680-ffd7-11e9-9418-b822bca3170d.png

According that fact that the node can change topology of a input mesh 
it can be a problem to applying related with faces information to result mesh.
If input faces has for example colors it can be so that the colors should be applied to result mesh.
Face index socket is dedicated to help in this situation `list item` node.

.. image:: https://user-images.githubusercontent.com/28003269/68201729-c506f900-ffdb-11e9-827e-b81c7ed69e77.png


Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/68143481-f683b400-ff4a-11e9-9a39-805e9c7d07d4.png

.. image:: https://user-images.githubusercontent.com/28003269/61684024-f27baf80-ad28-11e9-9f82-38c4ffef8a7f.png

.. image:: https://user-images.githubusercontent.com/28003269/61684160-7897f600-ad29-11e9-8425-3dddba31d951.gif