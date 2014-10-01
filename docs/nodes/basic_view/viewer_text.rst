Viewer Text
===========

Functionality
-------------

Looking for data and convert to readable format as:

node name: Viewer text

vertices: 
(1) object(s)
=0=   (8)
[0.5, 0.5, -0.5]
[0.5, -0.5, -0.5]
...

data: 
(1) object(s)
=0=   (12)
[0, 4]
[4, 5]
...

matrixes: 
(1) object(s)
=0=   (4)
(1.0, 0.0, 0.0, 0.0)
(0.0, 1.0, 0.0, 0.0)
(0.0, 0.0, 1.0, 0.0)
(0.0, 0.0, 0.0, 1.0)

**************************************************
                     The End                      

Where
**(1) object(s)** means that we have 1 object
**=0= (8)** means first (zero is first) object consists of 8 lists
if you add sublevels, there will be additional level like **=0= (1)** as vertices in separated sphere or plane generator gives.
**[0.5, 0.5, -0.5]** means vector or other data

Inputs
------

**Verts**
**Edges/Polygons**
**Matrix**

Parameters & Features
---------------------

**V I E W** button will send formatted data to text editor, you have manually open text file called Sverchok_viewer, but after this it will be updated and in upper of text will be name of your node to identify it.

Examples of usage
-----------------
