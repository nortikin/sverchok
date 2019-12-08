Set Material Index
==================

Functionality
-------------

In Blender, each object can have a list of associated materials. Once the list
of materials is assigned to the object, the material to be used for specific
face can be identified by the index of the material in that list.

This node allows to assign the index of material to be used to each of object's faces.

This node is most commonly used together with the **Assign Materials List** node.

Inputs
------

This node has the following inputs:

- **Object**. The Blender object, for which material indicies are to be
  assigned. This input can also be specified as a parameter. This input is
  mandatory.
- **FaceIndex**. The list of indicies of faces, for which the materials are to
  be assigned. This input can also be provided as a parameter. This input is
  available only when the **All Faces** parameter is unchecked.
- **Material Index". The index of the material to be assigned to the specified
  faces. This input can also be provided as a parameter.

Parameters
----------

This node has the following parameters:

- **All Faces**. If checked, then the same material will be assigned to all
  faces of the object; in this case, **FaceIndex** input is not visible..
  Otherwise, materials will be assigned only to faces with indicies provided in
  the **FaceIndex** input. Unchecked by default.

Outputs
-------

This node has the following outputs:

- **Object**. The same object as in the input, but with material indicies assigned.

Examples of usage
-----------------

An example of usage in pair with the **Assign Material List** node:

.. image:: https://user-images.githubusercontent.com/284644/70392046-4ef01a80-19fd-11ea-8e4d-5039cf053fed.png

