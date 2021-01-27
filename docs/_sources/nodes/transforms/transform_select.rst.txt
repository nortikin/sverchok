Transform Select
================

Functionality
-------------

This node splits the vertex data in two groups, applies one different matrix to each group and joins it again.
It would work as a standard transformation of the selected geometry when working on "Edit Mode".

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
- **PolyEdge O**. PolyEdge data with vertices which are true and false (index referred to "Vertices" output)
- **Vertices T**. Only the vertices marked as true
- **PolyEdge T**. PolyEdge data with vertices which are true (index referred to "Vertices T" output)
- **Vertices F**. Only the vertices marked as false
- **PolyEdge F**. PolyEdge data with vertices which are false (index referred to "Vertices F" output)


Examples of usage
-----------------

Showing the different edges groups:

.. image:: https://user-images.githubusercontent.com/10011941/56385208-c975eb00-621e-11e9-9b6f-6578ac91b704.png
  :alt: Transform_Select_edges groups_node.png
  
You can input multiple matrices and they will be paired with the verts:
  
.. image:: https://user-images.githubusercontent.com/10011941/56385210-cda20880-621e-11e9-855f-dd387794873c.png
  :alt: Transform_Select_procedural_node.png
