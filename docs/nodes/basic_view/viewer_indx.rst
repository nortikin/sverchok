Viewer Index
============

Functionality
-------------

Displays indices of incoming geometry, much like what is possible in the debug mode of Blender. The individual indices of 
*Vertices, Edges and Faces* can be displayed with and without a small background polygon to help contrast the index numbers and the 3d view color.

Inputs
------

This node Accepts sets of `Verts, Edges, Faces, and Matrices`. In addition it accepts a Text input to display Strings at 
the locations passed in through the `Vertices` socket.

Parameters
----------

**default**

+-----------------------+------------+----------------------------------------------------------------------+
| parameters            | type       | description                                                          |
+=======================+============+======================================================================+
| show                  | bool       | *activation* of the node                                             | 
+-----------------------+------------+----------------------------------------------------------------------+
| background            | bool       | display *background polygons* beneath each numeric (element of text) |
+-----------------------+------------+----------------------------------------------------------------------+
| verts, edges, faces   | multi bool | set of toggles to choose which of the inputs are displayed.          |
+-----------------------+------------+----------------------------------------------------------------------+
| Bake *                | operator   | to bake text in blender objects                                      |
+-----------------------+------------+----------------------------------------------------------------------+
| Font_Size *           | float      | size of baked text                                                   |
+-----------------------+------------+----------------------------------------------------------------------+
| Font  *               | string     | font, that used to bake (import fonts to scene first)                |
+-----------------------+------------+----------------------------------------------------------------------+
  * - only used for baking text meshes, not 3dview printing

In the *Properties Panel* (N-Panel) of this active node, it is possible to specifiy the colors of text and background polygons.

**extended**

+-----------------------+------------+----------------------------------------------------------------------+
| parameters            | type       | description                                                          |
+=======================+============+======================================================================+
| bakebuttonshow        | bool       | *activation* of bake button in default parameters                    | 
+-----------------------+------------+----------------------------------------------------------------------+
| colors font           | color      | colors for vertices, edges, polygons                                 |
+-----------------------+------------+----------------------------------------------------------------------+
| colors background     | color      | colors for vertices, edges, polygons background                      |
+-----------------------+------------+----------------------------------------------------------------------+

We added a way to show extended features in the main Node UI. 
From here one can choose a font and bake specific *Text* to meshes as preparation for fabrication. 
Font glyph conversion is done by Blender. 
If it produces strange results then most likely the font contains *invsibile mistakes* in the Glyph construction.
Some font parsers might take extra percautions to catch inconsistant Glyph definitions. 
Blender's font parser assumes no mistakes.

Outputs
-------

No socket output, but does output to 3d-view as either openGL drawing instructions or proper Meshes when Baking.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/2831444/208e8f30-cfb9-11e3-8b93-cb530684e168.png
