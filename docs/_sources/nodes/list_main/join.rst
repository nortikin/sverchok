List Join
=========

.. image:: https://user-images.githubusercontent.com/14288520/187512380-c7e79c39-f868-489a-879d-dd3a063dea53.png
    :target: https://user-images.githubusercontent.com/14288520/187512380-c7e79c39-f868-489a-879d-dd3a063dea53.png

Functionality
-------------

This node joins different list into a single one.

level 1:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ (1,2,3), (4,5,6), (7,8,9), (10,11,12) ] ]

level 2 mix:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ (1,2,3),(7,8,9),(4,5,6),(10,11,12) ] ]

level 2 wrap:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [ (1,2,3),(4,5,6) ], [ (7,8,9),(10,11,12) ] ] ]

level 2 mix + wrap:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [ (1,2,3),(7,8,9) ], [ (4,5,6),(10,11,12) ] ] ]

level 3:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [1,2,3,4,5,6,7,8,9,10,11,12] ] ]

level 3 mix:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [1,7,2,8,3,9,4,10,5,11,6,12] ] ]

level 3 wrap:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [1,2,3,4,5,6],[7,8,9,10,11,12] ] ]

level 3 mix + wrap:
[ [ (1,2,3), (4,5,6) ] ] + [ [ (7,8,9), (10,11,12) ] ] = [ [ [1,7],[2,8],[3,9],[4,10],[5,11],[6,12] ] ]

level 2 Match:
[[1, 2, 3], [4, 5, 6]] + [[7, 8, 9]] = [[1, 2, 3, 7, 8, 9], [4, 5, 6, 7, 8, 9]]

level 2 Match + Mix:
[[1, 2, 3], [4, 5, 6]] + [[7, 8, 9]] = [[1, 7, 2, 8, 3, 9], [4, 7, 5, 8, 6, 9]]

level 2 Match + Mix:
[[1, 2, 3], [4, 5, 6]] + [[7, 8, 9]] = [[1, 7, 2, 8, 3, 9], [4, 7, 5, 8, 6, 9]]

level 2 Match + Wrap:
[[1, 2, 3], [4, 5, 6]] + [[7, 8, 9]] = [[[1, 2, 3], [7, 8, 9]], [[4, 5, 6], [7, 8, 9]]]

level 2 Match + Mix + Wrap:
[[1, 2, 3], [4, 5, 6]] + [[7, 8, 9]] = [[(1, 7), (2, 8), (3, 9)], [(4, 7), (5, 8), (6, 9)]]

Inputs
------

* **data** multisocket

Parameters
----------

* **Match**: length of lists will be matched before joining
* **Match mode**: how length of lists should be matched (Repeat Last, Cycle, Match Short...)
* **Mix** to mix (not zip) data inside
* **Wrap** to wrap additional level
* **Levels** level of joining

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **NumPy Mode**: When enabled the node will expect and produce lists of NumPy arrays. It will be faster when joining NumPy Arrays but due the nature of the implementation it will fail when trying to join arrays with different axis number.


Outputs
-------

* **data** adaptable socket

Examples
--------

**Combine Bezier Spline Curves with 'List Join' node to Create a Surface**

.. image:: https://user-images.githubusercontent.com/14288520/187514973-08b68caf-2024-4316-b2d5-834d49f96712.png
    :target: https://user-images.githubusercontent.com/14288520/187514973-08b68caf-2024-4316-b2d5-834d49f96712.png

* Curves->Bezier-> :doc:`Bezier Spline (Curve) </nodes/curve/bezier_spline>`
* Surfaces-> :doc:`Surface from Curves </nodes/surface/interpolating_surface>`
* Surfaces-> :doc:`Evaluate Surfaces </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`