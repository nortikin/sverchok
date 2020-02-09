Sweep Modulator
===============

Functionality
-------------

behind the scenes this node takes a given trajectory, and two shape curves, and duplicates the trajectory two times, and attaches a bevel object (shape A and B) to the individual trajectories. Then using the factors property, it will interpolate (mix) between the two "extrusions" (of Lofted / Swept ) objects.

Because it's a pain to figure out how many points are in the trajectory (so that you can match the number of factors to pass), the node will automatically extend/trim the input Factor sequence, or even interpolate linearly.

currently the node will not hide the "dummy objects", you can do that in the outliner.

Inputs
------

It's not vectorized, meaning it does not accept multiple factor lists, or multiple object lists / trajectories.

+-------------+-----------+-----------------------------------------------------------------+
| Inputs      | Name      | Description                                                     |  
+=============+===========+=================================================================+
| **cent**    | Vector    | central coordinate around which to pivot                        | 
+-------------+-----------+-----------------------------------------------------------------+



Parameters
----------

+-------------+---------------+-----------------------------------------------------------------+
| Param       | Type          | Description                                                     |  
+=============+===============+=================================================================+
| **cent**    | Vector        | central coordinate around which to pivot                        | 
+-------------+---------------+-----------------------------------------------------------------+
| **axis**    | Vector        | axis around which to rotate around the pivot, default (0, 0, 1) |  
+-------------+---------------+-----------------------------------------------------------------+
| **dvec**    | Vector        | is used to push the center Vector by a Vector quantity per step | 
+-------------+---------------+-----------------------------------------------------------------+
| **Degrees** | Scalar, Float | angle of the total rotation. Default 360.0                      |
+-------------+---------------+-----------------------------------------------------------------+
| **Steps**   | Scalar, Int   | numer of rotation steps. Default 20                             | 
+-------------+---------------+-----------------------------------------------------------------+
| **Merge**   | Bool, toggle  | removes double vertices if the geometry can be merged,          |  
|             |               | usually used to prevent doubles of first profile and last       |
|             |               | profile copy. Default `off`.                                    | 
+-------------+---------------+-----------------------------------------------------------------+


Outputs
-------

**Vertices** and **Edges** and **Poly** will be generated. 


Example of usage
----------------

See the progress of how this node came to life `here <https://github.com/nortikin/sverchok/pull/2864>`_ (gifs, screenshots)
and a discussion about other techniques for producing similar results: `here <https://github.com/nortikin/sverchok/issues/2863>`_ (gifs, screenshots)
