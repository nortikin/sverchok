Transform Select
================

Functionality
-------------

This node splits the vertex data in two groups, applies one different matrix to each group and joins it again
This node is useful mainly when other node generates ngons, especially not-convex ones.

Inputs
------

This node has the following inputs:

- **Mask**: List of boolean or integer flags. If this input is not connected, a True, False, True.. mask will be created.
- **Verts**: Vertex list.
- **PolyEdge** : It can be Polygon or Edge data.
- **Matrix T** : Matrix applied to the vertex flaged as true.
- **Matrix F** : Matrix applied to the vertex flaged as false.

Parameters
----------

This node has the following parameters:

- **Mask Type**: Specifies if the supplied mask refers to the Vertex data or to the PoleEdge data



Outputs
-------

This node has the following outputs:

- **Vertices**. The whole group of vertices
- **PolyEdge**. A copy of the PolyEdge data supplyed
- **PolyEdge O**. PolyEdge data with vertices which are true and false (index refering to Vertices output)
- **Vertices T**. Only the vertices marked as true
- **PolyEdge T**. PolyEdge data with vertices which are true (index refering to Vertices T output)
- **Vertices F**. Only the vertices marked as false
- **PolyEdge F**. PolyEdge data with vertices which are false (index refering to Vertices F output)


Examples of usage
-----------------


