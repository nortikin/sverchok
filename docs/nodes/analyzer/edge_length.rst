Edge Lengths
============

Functionality
-------------

This node calculates lengths of edges of the provided mesh. It can output either the length of each edge, or total sum of all edge lengths.

Inputs
------

This node has the following inputs:

- **Vertices**. Object vertices. This input is mandatory.
- **Edges**. Object edges.  Note that this input should be connected in order for output lengths to be in correct order.
- **Faces**. Object faces.

Parameters
----------

This node has the following parameters:

- **Sum**. If checked, then the node will calculate total sum of all object edges. Otherwise, it will output length of each edge. Unchecked by default.

Outputs
-------

This node has the following outputs:

- **Length**. Lengths of each edge, if **Sum** parameter is not checked; otherwise, total sum of all edge lengths.

Example of usage
----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/284644/70642102-7bf03780-1c60-11ea-941c-e207a2a1e825.png

