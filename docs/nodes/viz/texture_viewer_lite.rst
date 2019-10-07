Texture Viewer lite
===================

Functionality
-------------

This node allows viewing a list of scalar values and Vectors as a texture, very useful
to display data from fractal, noise nodes and others, before outputting to a viewer_draw_mk2.
Lite version of node Texture Viewer

Uses OpenGl calls to display the data OR use existing UV image in blender to store texture.

Inputs
------

pixel value - raw of values from 0 to 1 express bw,rgb or rgba data

Parameters
----------

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| Image/bgl   | Output method - to blender existing image with replacement or to screen only      |
+-------------+-----------------------------------------------------------------------------------+
| Width Tex   | width of new texture in pixels                                                    |
+-------------+-----------------------------------------------------------------------------------+
| Height Tex  | height of new texture in pixels                                                   |
+-------------+-----------------------------------------------------------------------------------+
| bw/rgb/rgba | output black-white/red-green-blue/red-green-blue-alpha images                     |
+-------------+-----------------------------------------------------------------------------------+



Outputs
-------

None   

