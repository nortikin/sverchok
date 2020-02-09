Sweep Modulator
===============

Functionality
-------------

This node is not massively/extensively tested yet. Consider it a proof of concept. It's not even coded for efficiency.

behind the scenes this node takes a given trajectory, and two shape curves, and duplicates the trajectory two times, and attaches a bevel object (shape A and B) to the individual trajectories. Then using the factors property, it will interpolate (mix) between the two "extrusions" (of Lofted / Swept ) objects. 

Because it's a pain to figure out how many points are in the trajectory (so that you can match the number of factors to pass), the node will automatically extend/trim the input Factor sequence, or even interpolate linearly. When the node is adjusting the values found in Factors to match the required length, the Interpolate button will show as alerted.

currently the node will not hide the "dummy objects", you can do that in the outliner.

Inputs
------

It's not vectorized, meaning it does not accept multiple factor lists, or multiple object lists / trajectories.

+----------------+-----------+-----------------------------------------------------------------+
| Inputs         | Name      | Description                                                     |  
+================+===========+=================================================================+
| **Factors**    | Numbers   | for each slice of the extrusion, this socket will provide the   | 
|                |           | mix ratio between shape A and B. A list of floats, usually (but |
|                |           | not limited to) in a range between 0.0 and 1.0.                 | 
+----------------+-----------+-----------------------------------------------------------------+
| **Shape A**    | Object    | this is a simple zero thickness Curve Object, use the output of |
|                |           | a polyline node.                                                |
+----------------+-----------+-----------------------------------------------------------------+
| **Shape B**    | Object    | this is a simple zero thickness Curve Object, use the output of |
|                |           | a polyline node.                                                |
+----------------+-----------+-----------------------------------------------------------------+
| **Trajectory** | Object    | this can be a bezier, zero thickness Curve Object               |
+----------------+-----------+-----------------------------------------------------------------+


Parameters
----------

+---------------------+---------+------------------------------------------------------------------+
| Param               | Type    | Description                                                      |  
+=====================+=========+==================================================================+
| **update**          | bool    | node is on or off                                                |  
+---------------------+---------+------------------------------------------------------------------+
| **construct name ** | string  | use this name to generate a set of dummy objects                 |
|                     |         |  - two trajectories inside a collection                          | 
+---------------------+---------+------------------------------------------------------------------+
| **interpolate**     | bool    | if the number of elements in the factor socket doesn't           |
|                     |         | match the number needed to perform the mix between shapes        |
|                     |         | then the node will automatically extend or trim the factor       |
|                     |         | list. With Interpolate On, instead of trimming or repeating      |
|                     |         | the last value, the node will perform linear interpolation       |
|                     |         | using the supplied values as a guide.                            | 
+---------------------+---------+------------------------------------------------------------------+


Outputs
-------

**Vertices** and **Edges** and **Poly** will be generated. 


Example of usage
----------------

See the progress of how this node came to life `here <https://github.com/nortikin/sverchok/pull/2864>`_ (gifs, screenshots)
and a discussion about other techniques for producing similar results: `here <https://github.com/nortikin/sverchok/issues/2863>`_ (gifs, screenshots)
