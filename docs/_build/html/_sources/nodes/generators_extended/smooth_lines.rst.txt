Smooth Lines
============

Functionality
-------------

This can transform the inputted polyline into a polyline with smooth/curved corners. The curve is generated currently via a bezier interpolation or trigonometric arc. This is an early preview, maybe more modes will be incorporated at a later stage.

Inputs & Parameters
-------------------

+----------------+---------------------------------------------------------------------------------------+
| name           | descriptor                                                                            | 
+================+=======================================================================================+
| verts          | lists of lists of verts                                                               |
+----------------+---------------------------------------------------------------------------------------+
| weights        | lists of weights, or lists of lists of weights, or single weight                      |
+----------------+---------------------------------------------------------------------------------------+
| attributes     | a yet to be defined input dictionary to pass unique params to accompany each polyline |
+----------------+---------------------------------------------------------------------------------------+
| num verts      | number of segments for each corner                                                    |
+----------------+---------------------------------------------------------------------------------------+
| mode           | absolute, relative or arc                                                             |
+----------------+---------------------------------------------------------------------------------------+
| type           | cycle or open                                                                         |
+----------------+---------------------------------------------------------------------------------------+

- Absolute mode hopes to use the inputted weight value to give a symmetric curve (think of it as a lazy radius).
- Relative mode uses the weights to interpolate between points, and produce a bezier curve that is weighted in a distinct direction if one edge is longer.
- Arc mode generates a true trigonometric radial fillet for the corners/weights provided. It uses the weight as the fillet radius.


Outputs
-------

verts and edges, representing the modified polyline with newly curved corners.


Examples and Notes
--------

see the thread:  https://github.com/nortikin/sverchok/pull/2290
