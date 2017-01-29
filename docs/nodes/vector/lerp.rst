Vector Lerp
===========

Functionality
-------------

This node's primary function is perform the linear interpolation between two Vectors, or streams of Vectors.
If we have two Vectors A and B, and a factor 0.5, then the output of the node will be a Vector exactly half way on the imaginary finite-line between A and B. Values beyond 1.0 or lower than 0.0 will be extrapolated to beyond the line A-B.

Inputs
------

Vector Evaluate needs two Vertex stream inputs (each containing 1 or more vertices). If one list is shorter than the other then the shortest stream is extended to match the length of the longer stream by repeating the last valid vector found in the shorter stream.


Parameters
----------

+------------------+---------------+-------------+-------------------------------------------------+
| Param            | Type          | Default     | Description                                     |  
+==================+===============+=============+=================================================+
| Evaluate mode    | Enum          | Lerp        | - **Lerp** will linear interpolate once between |
|                  |               |             |   each corresponding Vector                     |   
|                  |               |             |                                                 | 
|                  |               |             | - **Evaluate** will repeatedly interpolate      |
|                  |               |             |   between each member of vectors A and B for    |
|                  |               |             |   all items in Factor input (see example)       |
+------------------+---------------+-------------+-------------------------------------------------+
| **Vertice A**    | Vertices      | None        | first group of vertices (Stream)                | 
+------------------+---------------+-------------+-------------------------------------------------+
| **Vectice B**    | Vertices      | None        | second group of vertices (Stream)               |
+------------------+---------------+-------------+-------------------------------------------------+
| **Factor**       | Float         | 0.50        | distance ratio between vertices A and B.        |
|                  |               |             | values outside of the 0.0...1.0 range are       |
|                  |               |             | extrapolated on the infinite line A, B          |
+------------------+---------------+-------------+-------------------------------------------------+

Outputs
-------

The content of **EvPoint** depends on the current mode of the node, but it will always be a list (or multiple lists) of Vectors. 


Example of usage
----------------

image 1 0.5

image 2 -0.5

image 3 1.5

image 4 [-1, 0, 1, 2]

image 5 evaluate mode vs lerp mode


.. image:: https://cloud.githubusercontent.com/assets/5990821/4188727/aaceebe4-3775-11e4-85cd-df80606b1509.gif
