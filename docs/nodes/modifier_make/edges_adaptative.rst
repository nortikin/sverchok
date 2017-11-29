Adaptive Edges
================

Functionality
-------------

This node takes every edge of one mesh and replace each one with every edge of another mesh.

Mesh, which edges will be changed will be referred as *Recipient*, and mesh which edges will be taken
to change edges of *Recipient* will be referred as *Donor*

Inputs
------

*VersR* - Vertices of *Recipient*. List of vertices.

*EdgeR* - Edges of *Recipient*. List of edges.

*VersD* - Vertices of *Donor*. List of vertices.

*EdgeD* - Edges of *Donor*. List of edges.

Parameters
----------

*Join* - join resulting geometry to output a single mesh.

Outputs
-------

*Vertices* - list of vertices

*Edges* - edge or list of edges

Examples
--------
