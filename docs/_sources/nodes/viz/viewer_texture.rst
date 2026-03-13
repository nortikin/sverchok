Texture Viewer
==============

.. image:: https://user-images.githubusercontent.com/14288520/190494305-9156f4fe-924d-4f25-93f8-5b4d387b9d84.png
  :target: https://user-images.githubusercontent.com/14288520/190494305-9156f4fe-924d-4f25-93f8-5b4d387b9d84.png

Functionality
-------------

This node allows viewing a list of scalar values and Vectors as a texture, very useful
to display data from fractal, noise nodes and others, before outputting to a viewer_draw_mk2.

Uses OpenGl calls to display the data.

Inputs
------

Floats and Vectors input

Parameters
----------

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| Float input | float and Vectors nested list                                                     |
+-------------+-----------------------------------------------------------------------------------+
| Show        | may be *true* or *false*:  display or not the texture                             |
+-------------+-----------------------------------------------------------------------------------+
| Pass        | may be *true* or *false*: transfer data to the internal image viewer              |
+-------------+-----------------------------------------------------------------------------------+
| Set texture | choose the size of the texture to display:                                        |
|             |                                                                                   |
| display     | (64x64px,128x128px, 256x256px, 512x512px, 1024x1024px)                            |
+-------------+-----------------------------------------------------------------------------------+
| Set color   | set the color mode:                                                               |
| mode        |                                                                                   |
|             | * **BW** = grayscale image,                                                       |
|             | * **RGB** = image with red, green, blu channels                                   |
|             | * **RGBA** = image with red, green, blu, alpha channels                           |
+-------------+-----------------------------------------------------------------------------------+
| Custom tex  | may be *true* or *false*: enable custom size of texture                           |
+-------------+-----------------------------------------------------------------------------------+
| Width tex   | must be *int*: set the width of the texture when Custom tex is enabled            |
+-------------+-----------------------------------------------------------------------------------+
| Height tex  | must be *int*: set the height of the texture when Custom tex is enabled           |
+-------------+-----------------------------------------------------------------------------------+


Outputs
-------

Directly into node tree view in a blue bordered square or if you choose the ``Pass`` option the texture
may be transferred to the internal image viewer/editor.

Properties panel
----------------

You can save the texture in the desired folder. You can choose the format:

##### jpeg, jp2, bmp, tiff, tga, tga(raw), exr, exr(multilayer), png

Save the texture clicking on the button ``SAVE``. You can save also passing the image to the blender image
editor with option ``Pass``. This is much preferred because there are more saving options.

Examples
--------
Basic usage:

.. image:: https://user-images.githubusercontent.com/14288520/190496185-ab2d0c5b-85a5-4ede-b110-94762d988a3e.png
  :target: https://user-images.githubusercontent.com/14288520/190496185-ab2d0c5b-85a5-4ede-b110-94762d988a3e.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Fractal </nodes/vector/fractal>`

Important notes
---------------
The ``Texture viewer node`` need adequate data size, this mean that number of input pixels
should be equal to the output. If not you will receive an error. See the image below for an RGBA example:

.. image:: https://user-images.githubusercontent.com/14288520/190494320-9177d7e1-281f-4b0c-a7f4-cd94651d54ad.png
  :target: https://user-images.githubusercontent.com/14288520/190494320-9177d7e1-281f-4b0c-a7f4-cd94651d54ad.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Fractal </nodes/vector/fractal>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

Links
-----

dev. thread: https://github.com/nortikin/sverchok/pull/1255
texture viewer proposal: https://github.com/nortikin/sverchok/issues/1248
Texture script by @ly29: https://github.com/Sverchok/Sverchok/issues/56