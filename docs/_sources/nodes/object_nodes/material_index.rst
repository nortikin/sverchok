Set Material Index
==================

Functionality
-------------

In Blender, each object can have a list of associated materials. Once the list
of materials is assigned to the object, the material to be used for specific
face can be identified by the index of the material in that list.

By default, Blender assigns all object's faces with material index of 0.

This node allows to assign the index of material to be used to each of object's
faces. Most common usage scenarios of this node are:

* Assign one material to all faces of the object;
* Assign specific material(s) to some specific faces of the object, and leave all
  other faces with default material (zero index);
* Assign specific different materials to each of object's faces with one node;
* Assign specific material to some faces of the object by one **Set Material
  Index** node, and then assign other materials to other faces of the object
  with another **Set Material Index** node. Several nodes can be "stacked" this
  way.

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
- **Material Index**. The index of the material to be assigned to the specified
  faces. This input can also be provided as a parameter.

Parameters
----------

This node has the following parameters:

- **All Faces**. If checked, then the same material will be assigned to all
  faces of the object; in this case, **FaceIndex** input is not visible..
  Otherwise, materials will be assigned only to faces with indicies provided in
  the **FaceIndex** input. Unchecked by default.
- **Mode**. Material setting mode. This parameter is available only if **All
  Faces** parameter is checked. The following modes are available:

   - **Per Face**. The node will expect one material index for each face of the
     input object. Thus, valid data for **Material Index** input should always
     have nesting level 2, i.e. be list of lists of integers (`[[0, 1, 2]]`,
     for example).
   - **Per Object**. The node will expect one material index for each input
     object. In this case, **Material Index** input can accept input data with
     nesting level of 1 or 2 (`[0, 1, 2]` or `[[0, 1, 2]]`). If input data is a
     list of lists (nesting level of 2), then only the first list will be used.

   The default mode is **Per Face**.


Outputs
-------

This node has the following outputs:

- **Object**. The same object as in the input, but with material indicies assigned.

Examples of usage
-----------------

An example of usage in pair with the **Assign Material List** node:

.. image:: https://user-images.githubusercontent.com/284644/70455381-05bbcb80-1ace-11ea-8b0d-858736ef0bed.png

Assign a material per object:

.. image:: https://user-images.githubusercontent.com/284644/70454084-afe62400-1acb-11ea-9a52-cacf0ee3680a.png

Assign material per face, with the same pattern for all objects:

.. image:: https://user-images.githubusercontent.com/284644/70454143-c3918a80-1acb-11ea-8ba2-e2b4785f3761.png

Assign random material for each face of each object:

.. image:: https://user-images.githubusercontent.com/284644/70454269-f9cf0a00-1acb-11ea-9e1d-af7ddc92ac23.png

Set material for one specific face of each object:

.. image:: https://user-images.githubusercontent.com/284644/70454877-115ac280-1acd-11ea-94c0-3da64908c156.png

