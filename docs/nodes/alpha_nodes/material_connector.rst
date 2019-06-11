Material connector
==================

.. image:: https://user-images.githubusercontent.com/28003269/59091674-e1b1de80-8920-11e9-8fe3-5b0232089165.png

Functionality
-------------

Main idea of this node is setting values from Sverchok to material node editor.
This node consists form two parts. First part named material connector node locates in Sverchok layout.
Second part is Sverchok agent which is located in node tree of material.

In spite of Blender render also has node tree editor for materials this node supports only cycle engine.
This node allows both to produce new materials and to connect to existing materials.
Also it allows produce quite big number of materials - thousands.

Inputs of material connector and outputs of Sverchok agent node
---------------------------------------------------------------

- **Color** - color
- **Value** - number
- **Vector** - vector

+------------------+--------+------------+-------------------------------------------------------------------+
| Parameters       | Type   | Location   | Description                                                       |
+==================+========+============+===================================================================+
|      UPD         | Bool   | SV node    | Do nothing if turned off                                          |
+------------------+--------+------------+-------------------------------------------------------------------+
|     OpenGL       | Bool   | SV node    | Check if there is a screen with mode of material shader           |
+------------------+--------+------------+-------------------------------------------------------------------+
| Material name    | string | SV node    | Name of main material                                             |
+------------------+--------+------------+-------------------------------------------------------------------+
| Create agent /   | button | SV node    | Create agent in shader layout or                                  |
| switch to mat    |        |            | if agent already created switch current screen to shader type     |
+------------------+--------+------------+-------------------------------------------------------------------+
| Suffix of child  | string | N panel    |                                                                   |
+------------------+--------+------------+-------------------------------------------------------------------+
| Edit in Sverchok | button | Agent node |                                                                   |
+------------------+--------+------------+-------------------------------------------------------------------+
| Update children  | button | Agent node |                                                                   |
+------------------+--------+------------+-------------------------------------------------------------------+