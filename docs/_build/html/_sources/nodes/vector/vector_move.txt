Vector Move
===========

Functionality
-------------

**equivalent to a Translate Transform**

Moves incoming sets of Vertex Lists by a *Vector*. The Vector is bound to a multiplier (Scalar) which amplifies all components of the Vector. The resulting Vector is added to the locations of the incoming Vertices. 

You might use this to translate the center of an object away or towards from [0,0,0] in order to apply other transforms like Rotation and Scale.


Inputs & Parameters
-------------------

+------------+-------------------------------------------------------------------------------------+
|            | Description                                                                         |
+============+=====================================================================================+
| Vertices   | Vertex or Vertex Lists representing one or more objects                             | 
+------------+-------------------------------------------------------------------------------------+
| Vector     | Vector to use for Translation, this is simple element wise addition to the Vector   | 
|            | representations of the incoming vertices. If the input is Nested, it is possible    |
|            | to translate each sub-list by a different Vector.                                   |
+------------+-------------------------------------------------------------------------------------+
| Multiplier | Straightforward ``Vector * Scalar``, amplifies each element in the Vector parameter |
+------------+-------------------------------------------------------------------------------------+


Outputs
-------

A Vertex or nested Lists of Vertices


Examples
--------

This works for one vertice or many vertices

.. image:: VectorMoveDemo1.PNG

*translate back to origin*

.. image:: VectorMoveDemo2.PNG

Move lists of matching nestedness. (whats that?! - elaborate)

.. image:: VectorMoveDemo3.PNG
.. image:: VectorMoveDemo4.PNG

Notes
-------