Vector Interpolation
====================

Functionality
-------------

Performs linear or cubic spline interpolation based on input points by creating a function ``x,y,z = f(t)`` with ``t=[0,1]``. The interpolation is based on the distance between the input points.


Input & Output
--------------

+--------+----------+------------------------------------------------+
| socket | name         | Description                                |
+========+==============+============================================+
| input  | Vertices     | Points to interpolate                      |
+--------+--------------+--------------------------------------------+
| input  | t            | Value to interpolate                       |
+--------+--------------+--------------------------------------------+
| output | Vertices     | Interpolated points                        |
+--------+--------------+--------------------------------------------+
| output | Tangent      | Tangents at outputted vertices             |
+--------+--------------+--------------------------------------------+
| output | Tangent Norm | Normalized Tangents at outputted vertices  |
+--------+--------------+--------------------------------------------+

Parameters
----------

  - *Mode* : Interpolation method. Can be Linear or Cubic
  - *Cyclic*: Treat the input vertices as a cyclic path.
  - *Int Range*: When activated the node will expect a Integer Value in the 't' input and will create a range from 0 to 1 with the inputted steps.
  - *End Point*: (Only when Int Range is activated) If active the generated range will exclude 1. Useful when the value 0 and 1 of the interpolation is the same

Extra Parameters
----------------

  - *Knot Mode*: Used for different cubic interpolations. Can be 'Manhattan', 'Euclidan', 'Points' and 'Chebyshev'
  - *List Match*: How List should be matched
  - *Output Numpy*: Outputs numpy arrays in stead of regular python lists (makes node faster)

Examples
--------
.. image:: https://cloud.githubusercontent.com/assets/619340/4185874/ca99927c-375b-11e4-8cc8-451456bfb194.png
   :alt: interpol-simple.png

Sine interpolated from 5 points. The input points are shown with numbers.

.. image:: https://cloud.githubusercontent.com/assets/619340/4185875/ca9f56ee-375b-11e4-83fd-a746c8cc690b.png
   :alt: interpol-surface.png

An interpolated surface between sine and cosine.

Notes
-------

The node doesn't extrapolate. Values outside of ``[0, 1]`` are ignored.
