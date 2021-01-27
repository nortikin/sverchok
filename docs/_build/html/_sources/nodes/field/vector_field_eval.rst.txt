Evaluate Vector Field
=====================

Functionality
-------------

This node calculates the values of the provided Vector Field at the given
points. More precisely, given the field VF (which is a function from vectors to
vectors), and point X, it calculates the vector VF(X).

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be evaluated. This input is mandatory.
* **Vertices**. The points at which to evaluate the field. The default value is `(0, 0, 0)`.

Outputs
-------

This node has the following output:

* **Vectors**. The vectors calculated at the provided points.

Examples of usage
-----------------

Replace each point of straight line segment with the result of noise vector field evaluation at that point:

.. image:: https://user-images.githubusercontent.com/284644/79476391-5c0fbc80-8022-11ea-9457-1babe56f4388.png

Visualize vector field vectors by connecting original points of the line segment and the points obtained by moving the original points by the results of vector field evaluation:

.. image:: https://user-images.githubusercontent.com/284644/79476395-5d40e980-8022-11ea-846b-68da09ed2e41.png

