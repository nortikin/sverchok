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
| Bake *                | operator   | bake text to blender geometry objects                                |
+-----------------------+------------+----------------------------------------------------------------------+
| Font Size *           | float      | size of baked text                                                   |
+-----------------------+------------+----------------------------------------------------------------------+
| Font  *               | string     | font used to bake (import fonts to scene if you wish to use anything |
|                       |            | other than BFont)                                                    |
+-----------------------+------------+----------------------------------------------------------------------+

`* - only used for baking text meshes, not 3dview printing`

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

**font**

With *show bake ui* toggled, the Node unhides a selection of UI elements considered useful for *Baking Text* in preparation for fabrication. If no font is selected the default BFont will be used. BFont won't be visible in this list until you have done at least one bake during the current Blender session.

**Glyph to Geometry**

Font glyph conversion is done by Blender. If it produces strange results then most likely the font contains *invsibile mistakes* in the Glyph construction. Blender's font parser takes no extra precautions to catch inconsistant Glyph definitions.

Outputs
-------

No socket output, but does output to 3d-view as either openGL drawing instructions or proper Meshes when Baking.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/2831444/208e8f30-cfb9-11e3-8b93-cb530684e168.png
