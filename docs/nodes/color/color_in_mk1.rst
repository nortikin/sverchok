Color In
========

Functionality
-------------

.. image:: https://user-images.githubusercontent.com/14288520/189630585-fe6276d3-e81c-4879-9d12-e1a28b7ab089.png
  :target: https://user-images.githubusercontent.com/14288520/189630585-fe6276d3-e81c-4879-9d12-e1a28b7ab089.png

Creates color data from ranges or number values either integer of floats.

With the NumPy implementation the node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)


Inputs and Parameters
---------------------

* **Use Alpha** - Include alpha (transparency) data in the outputs.
* **Color space** - RGB, HSV and HSL inputs are available.

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

**Implementation**: Python or NumPy. Numpy is the default. Python implementation is usually faster if you input regular lists and want to get regular list in RGB mode. The NumPy implementation will be faster if you are using/getting lists of NumPy arrays or in HSV and HSL mode

**Output NumPy**: Get NumPy arrays in stead of regular lists.

Outputs
-------

**Colors** - Color or series of colors (in RGB or RGBA values)


Examples
--------

Differences between HSV and HSL:

.. image:: https://user-images.githubusercontent.com/14288520/189630656-716363b1-02bb-4eee-8538-acb696584375.png
  :target: https://user-images.githubusercontent.com/14288520/189630656-716363b1-02bb-4eee-8538-acb696584375.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Tuning noise into color data:

.. image:: https://user-images.githubusercontent.com/14288520/189630696-415d23f2-a1d8-4995-8000-9beb42ab1006.png
  :target: https://user-images.githubusercontent.com/14288520/189630696-415d23f2-a1d8-4995-8000-9beb42ab1006.png

Gist: https://gist.github.com/cf884ea62f9960d609158ef2d5c994ed

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`