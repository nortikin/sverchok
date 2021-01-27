Vector Field Lines
==================

Functionality
-------------

This node visualizes a Vector Field object by generating lines of that field. More precisely, given the point X and field VF, the node does the following:

* takes original point X
* Applies the field to it with small coefficient, to create a point X1 = X + K * VF(X)
* Applies the field to X1 with small coefficient, to create a point X2 = X1 + K * VF(X1)
* And so on, repeating some number of times.

And then the edges are created between these points. When the coefficient is
small enough, and the number of iterations is big enough, such lines represent
trajectories of material points, when they are moved by some force field.

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be visualized. This input is mandatory.
* **Vertices**. The points at which to start drawing vector field lines. This input is mandatory.
* **Step**. Vector field application coefficient. If **Normalize** parameter is
  checked, then this coefficient is divided by vector norm. The default value
  is 0.1.
* **Iterations**. The number of iterations. The default value is 10.

Parameters
----------

This node has the following parameters:

* **Normalize**. If checked, then all edges of the generated lines will have
  the same length (defined by **Steps** input). Otherwise, length of segments
  will be proportional to vector norms. Checked by default.
* **Join**. If checked, join all lines into single mesh object. Checked by default.

Outputs
-------

* **Vertices**. The vertices of generated lines.
* **Edges**. The edges of generated lines.

Example of usage
----------------

Visualize some vector field:

.. image:: https://user-images.githubusercontent.com/284644/79495842-a56e0500-803e-11ea-91ed-611abf181ec2.png

