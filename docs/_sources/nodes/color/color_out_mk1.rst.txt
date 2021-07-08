Color In
========

Functionality
-------------

Creates ranges or number values (floats) from color data

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)


Inputs and Parameters
---------------------

**Colors** - Base color data in RGB or RGBA

**Color space** - RGB, HSV and HSL outputs are available

Outputs
-------

- RGB:

  - **R** - Red value or series of values

  - **G** - Green value or series of values

  - **B** - Blue value or series of values

- HSV:

  - **H** - Hue value or series of values

  - **S** - Saturation value or series of values

  - **V** - 'Value' value or series of values

- HSL:

  - **H** - Hue value or series of values

  - **S** - Saturation value or series of values

  - **L** - Luminosity value or series of values

**A** - Alpha value or series of values

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists.

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/color/color_out/color_out_texture_hsv_sverchok_blender_example.png
