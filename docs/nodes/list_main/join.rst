List Join
=========

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

**data** multisocket

Parameters
----------

**Match**: length of lists will be matched before joining
**Match mode**: how length of lists should be matched (Repeat Last, Cycle, Match Short...)
**Mix** to mix (not zip) data inside
**Wrap** to wrap additional level
**Levels** level of joining

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**NumPy Mode**: When enabled the node will expect and produce lists of NumPy arrays. It will be faster when joining NumPy Arrays but due the nature of the implementation it will fail when trying to join arrays with different axis number.


Outputs
-------

**data** adaptable socket
