Vector In
=========

Functionality
-------------

Inputs vector from ranges or number values either integer of floats.

With the NumPy implementation the node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)

Inputs
------

**x** - value or series of values
**y** - value or series of values
**z** - value or series of values

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Python or NumPy. Python is the default and is usually faster if you input regular lists and want to get regular list. The NumPy implementation will be faster if you are using/getting lists of NumPy arrays.

**Output NumPy**: Get NumPy arrays in stead of regular lists.

Outputs
-------

**Vector** - Vertex or series of vertices


Operators
---------

This node has two buttons:

- **3D Cursor**. This button is available only when no of inputs are connected. When pressed, this button assigns current location of Blender's 3D Cursor to X, Y, Z parameters.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4905358/0a4e7df4-644f-11e4-8ff1-1530c7aac8dc.png
  :alt: with vector out

.. image:: https://cloud.githubusercontent.com/assets/5783432/4905359/0a56565a-644f-11e4-91b3-24ac4d78cb11.png
  :alt: generating line

.. image:: https://user-images.githubusercontent.com/28003269/34647574-202304d2-f39f-11e7-8113-87047546b81e.gif
  :alt: object mode

Gist: https://gist.github.com/cf884ea62f9960d609158ef2d5c994ed
