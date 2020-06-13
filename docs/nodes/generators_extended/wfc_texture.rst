WFC Texture
===========

.. image:: https://user-images.githubusercontent.com/28003269/84559527-5f86a200-ad4c-11ea-94e1-e8b7091a6085.png

Functionality
-------------
This node get sample image and generate new texture of custom size.
Be warning it can take time to calculate new texture so you have to try with low resolution.
It is limited by default 100x100 pixels.

The node uses wave function collapse algorithm. More information you can look here:
https://github.com/mxgmn/WaveFunctionCollapse
Also on this website (in samples directory) you can get a lot of samples
with which you can try out how the node is working. I would recommend to do this before drawing your own samples.

Performance of the node is dependent on output size but also on complexity of the sample image.
The more patterns can be found in sample image the more low performance.
Also it depends on the node preferences especially on pattern size.

Dependent on sample image some properties should be changed for getting desire result.
For example for getting like maze texture  rotate patterns option should enabled and on the contrary
if expecting result will be getting independent items (cat heads) most likely the option should be off.

*Notes:*

The node is not vectorized and unlikely would.

The node can cause an error. The reason is that the nature of the algorithm is not robust.
Such errors does not consider as a bug. You can increase robustness by increasing `number of tries` parameter.

Category
--------

generators extended -> WFC texture

Inputs
------

- **Sample image** - image from which to create patterns

Outputs
-------

- **image** - row of pixels in such format: [row1[p1, p2, ... ,pn], row2[...], ..., row n] where number of rows is height and number of pixel in a row is width

Parameters
----------

- **height** - resolution of output image
- **width** - resolution of output image
- **seed** - number for random functions
- **pattern size** - size of pattern square in pixels [1-5] usually 2 or 3
- **rotate patterns** - extracted patterns will be multiplied by their rotation
- **periodic input** - more patterns will be extracted by shifting sample image along UV directions
- **tiling output** - The node will try to generate seamless texture

N panel
-------

- **tries number** - maximum number of fails until the node will give up

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/84426844-f2ccb400-ac34-11ea-8801-476dde8921d2.gif

.. image:: https://user-images.githubusercontent.com/28003269/84426850-f4967780-ac34-11ea-8d20-155b5cbe26ad.gif

.. image:: https://user-images.githubusercontent.com/28003269/84426853-f6603b00-ac34-11ea-8bf1-7fe89bf92845.gif

.. image:: https://user-images.githubusercontent.com/28003269/84571061-1e20e180-ada2-11ea-96b0-7a5ea5f5ea9b.gif

**Creating mesh of the generated maze:**

.. image:: https://user-images.githubusercontent.com/28003269/84426856-f8c29500-ac34-11ea-9d3e-8ee321894382.png
