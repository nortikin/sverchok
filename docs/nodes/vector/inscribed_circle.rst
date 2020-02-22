Inscribed Circle
================

Functionality
-------------

This node calculates the center and the radius of the inscribed circle for each
triangular face of the input mesh. For non-tri faces, the node will either skip
them or give an error, depending on a setting.

Inputs
------

This node has the following inputs:

- **Vertices**. The vertices of the input mesh. This input is mandatory.
- **Faces**. The faces of the input mesh. This input is mandatory.

Parameters
----------

This node has the following parameter:

- **On non-tri faces**. Defines what the node should do if it encounters a
  non-triangular face. There are following options available:

   - **Skip**. Just skip such faces - do not generate inscribed circles for them.
   - **Error**. Stop processing and give an error (turn the node red).

   The default option is **Skip**.

Outputs
-------

This node has the following outputs:

- **Center**. Centers of the inscribed circles.
- **Radius**. Radiuses of the inscribed circles.
- **Normal**. Normals of the planes where inscribed circles lie - i.e., face normals.
- **Matrix**. For each inscribed circle, this contains a matrix, Z axis of
  which points along face normal, and the translation component equals to the
  center of the inscribed circle. This output can be used to actually place
  circles at their places.

Examples of usage
-----------------

Inscribed circles for icosphere:

.. image:: https://user-images.githubusercontent.com/284644/75060084-02968000-5500-11ea-933b-db77e8359961.png

Inscribed circles for (triangulated) Suzanne:

.. image:: https://user-images.githubusercontent.com/284644/75060086-03c7ad00-5500-11ea-970a-bf87a4df7c61.png

