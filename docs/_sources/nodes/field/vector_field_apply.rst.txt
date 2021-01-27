Apply Vector Field
==================

Functionality
-------------

This node applies the Vector Field to provided points. More precisely, given
the vector field VF (which is a function from points to vectors) and a point X,
it calculates new point as `X + K * VF(X)`.

This node can also apply the field iteratively, by calculating `X + K*VF(X) +
K*VF(X + K*VF(X)) + ...`. In other words, it can apply the field to the result
of the first application, and repeat that several times.

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be applied. This input is mandatory.
* **Vertices**. The points to which the field is to be applied. The default value is `(0, 0, 0)`.
* **Coefficient**. The vector field application coefficient. The default value is 1.0.
* **Iterations**. Number of vector field application iterations. For example, 2
  will mean that the node returns the result of field application to the result
  of first application. The default value is 1.

Outputs
-------

This node has the following output:

* **Vertices**. The result of the vector field application to the original points.

Examples of usage
-----------------

Apply noise vector field to the points of straight line segment:

.. image:: https://user-images.githubusercontent.com/284644/79487691-15c25980-8032-11ea-93e9-51f9b54bd36e.png

Apply the same field to the same points, by only by a small amount; then apply the same field to the resulting points, and repeat that 10 times:

.. image:: https://user-images.githubusercontent.com/284644/79487987-7b164a80-8032-11ea-8197-c78314843ffa.png

