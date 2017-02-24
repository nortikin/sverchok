Texture Viewer
==============

Functionality
-------------

This node allows viewing a list of scalar values as a texture, very useful
to display data from fractal, noise nodes and others. before outputting to a viewer_draw_mk2.

Uses OpenGl calls to display the data.

Inputs
------

float input

Parameters
----------

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| Float input | float nested list                                                                 |
+-------------+-----------------------------------------------------------------------------------+
| Show        | true or false (to display or not the texture)                                     |
+-------------+-----------------------------------------------------------------------------------+
| Set texture | choose the size of the texture to display:                                        |
| display     | (64x64px,128x128px, 256x256px, 512x512px, 1024x1024px)                            |
+-------------+-----------------------------------------------------------------------------------+

Outputs
-------

Directly into node tree view in a blue bordered square.

Properties panel
----------------

You can save the texture in /tmp folder. You can choose the format (jpeg, bmp, tiff, tgat, png).
Save the texture clicking on the button SAVE.

Examples
--------
Basic usage:

https://cloud.githubusercontent.com/assets/1275858/23259574/0ba15b60-f9ce-11e6-9fd4-75ece759929b.png

Links
-----

dev. thread: https://github.com/nortikin/sverchok/pull/1255
texture viewer proposal: https://github.com/nortikin/sverchok/issues/1248
Texture script by @ly29: https://github.com/Sverchok/Sverchok/issues/56
