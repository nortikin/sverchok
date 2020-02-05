Color In
========

Functionality
-------------

Creates color data from ranges or number values either integer of floats.

With the NumPy implementation the node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)


Inputs and Parameters
---------------------

**Use Alpha** - Include alpha (transparency) data in the outputs
**Color space** - RGB, HSV and HSL inputs are available
- RGB:
  **R** - Red value or series of values
  **G** - Green value or series of values
  **B** - Blue value or series of values
- HSV:
  **H** - Hue value or series of values
  **S** - Saturation value or series of values
  **V** - Value value or series of values
- HSL:
  **H** - Hue value or series of values
  **S** - Saturation value or series of values
  **L** - Luminosity value or series of values

**A** - Alpha value or series of values

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Python or NumPy. Numpy is the default. Python implementation is usually faster if you input regular lists and want to get regular list in RGB mode. The NumPy implementation will be faster if you are using/getting lists of NumPy arrays or in HSV and HSL mode

**Output NumPy**: Get NumPy arrays in stead of regular lists.

Outputs
-------

**Colors** - Color or series of colors (in RGB or RGBA values)


Examples
--------

Differences between HSV and HSL:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/color/color_in/color_in_hsv_hsl_sverchok_blender_example.png


Tuning noise into color data:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/color/color_in/color_in_noise_hsv_sverchok_blender_example.png


Gist: https://gist.github.com/cf884ea62f9960d609158ef2d5c994ed
