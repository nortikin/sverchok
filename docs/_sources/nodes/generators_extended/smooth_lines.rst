Smooth Lines
============

.. image:: https://user-images.githubusercontent.com/14288520/191092102-eb710ef3-c4fd-4d27-8264-04712c0c4119.png
  :target: https://user-images.githubusercontent.com/14288520/191092102-eb710ef3-c4fd-4d27-8264-04712c0c4119.png

Functionality
-------------

This can transform the inputted polyline into a polyline with smooth/curved corners. The curve is generated currently via a bezier interpolation or trigonometric arc. This is an early preview, maybe more modes will be incorporated at a later stage.

.. image:: https://user-images.githubusercontent.com/14288520/198749423-c3afeac5-2cf2-43b4-9c04-298e22e6ca01.png
  :target: https://user-images.githubusercontent.com/14288520/198749423-c3afeac5-2cf2-43b4-9c04-298e22e6ca01.png

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

- **Absolute** mode hopes to use the inputted weight value to give a symmetric curve (think of it as a lazy radius).
- **Relative** mode uses the weights to interpolate between points, and produce a bezier curve that is weighted in a distinct direction if one edge is longer.
- **Arc** mode generates a true trigonometric radial fillet for the corners/weights provided. It uses the weight as the fillet radius.

.. image:: https://user-images.githubusercontent.com/14288520/198749905-0c3811a0-a9e7-490f-9038-9c5694a74569.png
  :target: https://user-images.githubusercontent.com/14288520/198749905-0c3811a0-a9e7-490f-9038-9c5694a74569.png

Outputs
-------

verts and edges, representing the modified polyline with newly curved corners.


Examples and Notes
------------------

see the thread:  https://github.com/nortikin/sverchok/pull/2290