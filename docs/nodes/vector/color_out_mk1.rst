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

**Colors** - Base color data
**Color space** - RGB, HSV and HSL inputs are available

Outputs
-------

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

**A** - Alpha value or series of values (only if incoming data has alpha channel)

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists.

Outputs
-------

**Colors** - Color or series of colors (in RGB or RGBA values)


Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4905358/0a4e7df4-644f-11e4-8ff1-1530c7aac8dc.png
  :alt: with vector out

.. image:: https://cloud.githubusercontent.com/assets/5783432/4905359/0a56565a-644f-11e4-91b3-24ac4d78cb11.png
  :alt: generating line

.. image:: https://user-images.githubusercontent.com/28003269/34647574-202304d2-f39f-11e7-8113-87047546b81e.gif
  :alt: object mode

Gist: https://gist.github.com/cf884ea62f9960d609158ef2d5c994ed
