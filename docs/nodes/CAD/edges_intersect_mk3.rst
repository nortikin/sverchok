Intersect Edges
===============

.. image:: https://user-images.githubusercontent.com/28003269/70894030-a7c74080-2005-11ea-8594-dced40b05c03.png

Functionality
-------------

The node is designed for finding intersections of inputs edges and returns mesh based on intersection result.

This node contains several algorithm of finding edge intersections:

**3D algorithm:**

This is a brute force algorithm written in NumPy, it is pretty fast and pretty consistent but can produce double points that can be
removed with the remove doubles toggle. It ignores overlapping edges.

**2D algorithms**

**Alg_1**

Brute force algorithm that exposes every pair of edges to a mathutils function called 'intersect_line_line'. Does not check
if there are repeated points. It ignores overlapping edges

**Np**

This is a brute force algorithm written in NumPy, it is pretty fast and pretty consistent but can produce double points that can be
removed with the remove doubles toggle. It ignores overlapping edges

**Sweep line algorithm**

This algorithm is based on `sweep line <https://en.wikipedia.org/wiki/Sweep_line_algorithm>`_ approach:

It can handle big number of edges but if there are too much intersection the performance can slow down dramatically.
For example if each input edge intersect with every others. In this case only few edges can be handled by this node.

- The algorithm does not produce double points.
- It is less robust and can give an error.
- For this algorithm epsilon parameter on N panel is more important. If you get an error you can try to change the parameter to fix.

Prefix 2D means that the node expects from input any kind of flatten mesh
but it does not mean that the mesh should only lay on XY surface.
Input mesh can below or above XY surface or even can be tilted relative one.

The algorithm of finding new intersection is like this:

It takes two edges, removes Z coordinates and finds their intersection.
But after intersection is found it projects intersection point back onto one of the given edges.
This means that input mesh still should be flat but it can be located in space however you like.
Only location of input flatten mesh along Z coordinate will bring the error.

**Blender mode**

This mode is using internal Blender function from `mathutils` module.
It is pretty fast with not big number of intersections (about 1000)
but is quite unstable and can cause crash of Blender easily.
Also it is not design for such cases where one edge is intersect with all or most of all other edges. Use with care.
It's available only with Blender 2.81+


Benchmark of 2D algorithms
--------------------------

Three different test to determine the efficiency of the algorithms.
- Random Segments: Segments between random vectors
- Star Segments: Rotated segments from a center point (every segments intersects with the rest of segments in the center)
- Spine Segments: Parallel Segments intersected with a middle segment that cuts them in the center.

.. image:: https://user-images.githubusercontent.com/10011941/120835106-30bc9980-c564-11eb-93c5-bdbabd1a63fe.png

+-----------+-----------------------------------+-----------------------------+-----------------------------+
|Test       | Random Segments                   | Star segments               | Spine Segments              |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Edges In   |   100  |   1000   | 10000         |    100 |    1000 |    10000 | 100    | 1000    | 10000    |
|Intersec.  |   1299 |   127892 | 12355630      |      1 |       1 |        1 | 100    | 1000    | 10000    |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Alg_1      |   6 ms |   694 ms |      74872 ms | 15 ms  | 2125 ms |      SC* | 3 ms   | 226 ms  | 22618 ms |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Alg_1 + RD*|  10 ms |  1477 ms |     226240 ms | 25 ms  | 3300 ms |      SC* | 4 ms   | 246 ms  | 22626 ms |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Sweep Line | 900 ms | 76700 ms | SC*           | 53 ms  | 778ms   | 2000 ms  | 81 ms  | 1200 ms | 15500 ms |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Blender    |   3 ms |   650 ms | 112240 ms/BC* | 0.6 ms | 20ms    | 10643 ms | 0.8 ms | 12 ms   | 1100 ms  |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Np         |   4 ms |   635 ms |     316970 ms |   6 ms | 1760ms  |      SC* |   3 ms | 160 ms  | 6466 ms  |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+
|Np + RD*   |   9 ms |  1281 ms | 419789 ms/BC* |  18 ms | 3052 ms |      SC* |   5 ms | 168 ms  | 6580 ms  |
+-----------+--------+----------+---------------+--------+---------+----------+--------+---------+----------+

*BC = Blender Crash*
*SC = Blender Crash + Partial System Crash*


Inputs
------

Verts and Edges only. Warning: Does not support faces


Parameters
----------

**Include 'On touch'** : consider a valid intersection when one end of the edge lays on another edge.
    Generates double points so if active "remove doubles" switch is recommended. Only for Np and 3d mode

**Doubles**: Merges points that are closer than the defined distance. Only for Alg_1, Np and 3d mode


Parameters N-panel
------------------

Epsilon - For comparing float figures. Does not effect on performance.

Big data Limit - Number of incoming edges where the node will switch to a slower-but-safer implementation of the algorithm (for Alg_1)


Outputs
-------

Vertices and Edges, the mesh does not preserve any old vertex or edge index ordering due to the Hashing algorithm used for fast intersection lookups.


Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/2811581/16032c72-ce26-11e3-9055-925d2cd03719.png

See the progress of how this node came to life `here <https://github.com/nortikin/sverchok/issues/109>`_ (gifs, screenshots)
