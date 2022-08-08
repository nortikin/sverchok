OpenSubdivision Node
====================

Functionality
-------------

This node applies [Catmull-Clark subdivision](https://en.wikipedia.org/wiki/Catmull%E2%80%93Clark_subdivision_surface) (as implemented by the [OpenSubdiv](https://github.com/PixarAnimationStudios/OpenSubdiv)) to the input mesh at the specified number of levels. 

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of input mesh.
- **Edges**. Edges of input mesh (**optional**). 
- **Faces**. Faces of input mesh.

Parameters
----------

This node has the following parameters:

- **Levels**. Maximum subdivision level to be applied to input mesh.

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.

**Note**: **Vertices** and **Faces** inputs **must** be compatible, in that the **Faces** input **may not refer to vertex indices that do not exist in the Vertices list** (e.g. **Faces** cannot refer to vertex 7, provided a list of **Vertices** with only 5 vertices). 

Unexpected behavior may occur if using Faces from one mesh with Vertices from another. 

Indices in **NewEdges**, **NewFaces**, **OldEdges**, **OldFaces** outputs relate to vertices in **Vertices** output.

Examples of usage
-----------------
.. image:: https://user-images.githubusercontent.com/79929629/180858417-dc585075-486a-443b-a618-ae04e281cd90.png

.. image:: https://user-images.githubusercontent.com/79929629/180858569-40b684c8-bdc7-4690-9e74-f0733dd21210.png
