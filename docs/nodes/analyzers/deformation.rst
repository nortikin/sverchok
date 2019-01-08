Deformation
===========

Functionality
-------------

Deformation node is one of the analyzer type. It is used to get the deformation of one or many meshes between different states. The deformation is measured by the areal variance or the edge elongation


Inputs
------

All inputs need to proceed from an external node


+-------------------+---------------+-------------+-----------------------------------------------+
| Input             | Type          | Default     | Description                                   |
+===================+===============+=============+===============================================+
| **Rest Verts**    | Vertices      | None        | Vertices in relaxed state                     |
+-------------------+---------------+-------------+-----------------------------------------------+
| **Distort Verts** | Vertices      | None        | Vertices in the deformed state                |
+-------------------+---------------+-------------+-----------------------------------------------+
| **Pols**          | Strings       | None        | Polygons referenced to vertices               |
+-------------------+---------------+-------------+-----------------------------------------------+
| **Edges**         | Strings       | None        | Edges referenced to vertices                  |
+-------------------+---------------+-------------+-----------------------------------------------+

In the N-Panel you can use the toggle **Output NumPy** to get NumPy arrays (makes the node faster) 

Outputs
-------
- **Edges Def** :the variation of the length of the edges.
- **Pols Def** : the variation of the areas of each polygon.

- **Vert Pol Def**: Each polygon will distribute its areal variation to its vertices. Each vertex will get the sum of the deformations related to itself.
- **Vert Edge Def**: Each edge will distribute its elongation to its vertices. Each vertex will get the sum of elongations related to itself.


Examples of usage
----------------
Different kinds of tension maps can be created using this node, from any of its outputs, here some basic examples:

.. image:: https://user-images.githubusercontent.com/10011941/50576192-a7da2a80-0e0c-11e9-9be5-e490081822bb.png
  :alt: DefromationNode1.PNG

The elongation can be used to get to the tension of a spring system, in this example the node is used to get one approximation of the needed thickness to sustain the tensions applied to a cloth simulation.

.. image:: https://user-images.githubusercontent.com/10011941/50576196-ba546400-0e0c-11e9-8c5c-15488c9a0d04.png
  :alt: DefromationNode2.PNG

You can compare many different states at the same time.

.. image:: https://user-images.githubusercontent.com/10011941/50576199-d526d880-0e0c-11e9-89cf-12cd8462da41.png
  :alt: DefromationNode3.PNG
