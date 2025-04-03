Color Out
=========

.. image:: https://user-images.githubusercontent.com/14288520/189633039-ea3d2f29-e400-4383-b643-f13cc745780e.png
  :target: https://user-images.githubusercontent.com/14288520/189633039-ea3d2f29-e400-4383-b643-f13cc745780e.png

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

.. image:: https://user-images.githubusercontent.com/14288520/189633073-cc6a2caf-ec93-484f-aedc-ace6cccad6eb.png
  :target: https://user-images.githubusercontent.com/14288520/189633073-cc6a2caf-ec93-484f-aedc-ace6cccad6eb.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Color-> :doc:`Texture Evaluate </nodes/color/texture_evaluate_mk2>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`