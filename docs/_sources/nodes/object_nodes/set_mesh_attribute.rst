Set Mesh Attribute
==================

.. image:: https://user-images.githubusercontent.com/28003269/118392568-5e8c7d80-b64b-11eb-9e0b-34fe624174cb.png

Functionality
-------------
The node can add an attribute to a mesh elements which can be used in Geometry nodes or shader editors (probably not only).
At the moment of writing the documentation the node can't change build in attributes
such as `position`, `normal`, `material_index` etc. If you will try to do this there will be no any effect.
The node memorize and undo its previous action if necessary. It means that if the name of an attribute is changed
the node deletes previous attribute first. Also if the node is disconnected from input data it deletes
previously created attribute. However deletion of the node won't cause removing the attribute.
Use the node with spreadsheet editor to see added attributes.

As any other Blender nodes it can handle multiple objects. It expects usual shape of input `Objects` and `Values`
but shape of input strings does not have matter. The shape of input string values will always be flattened by the node.
It means that it's possible to use format of string values like this `[['attr_name', attr_name', ...]]`
or like this `[['attr_name'], ['attr_name']]`. In both cases the names will be applied to the first and second objects.


Category
--------

BPY Data -> Set Mesh Attribute

Inputs
------

- **Object** - Blender data blocks
- **Attribute name** - any strings
- **Value** - type of the values should be according to Type property

Outputs
-------

- **Object** - Blender data blocks

Parameters
----------

- **Domain** - Type of the mesh element to which the attribute should be added. It can be `Point`, `Face` etc.
- **Type** - Type of the attribute to create.

Usage
-----

Adding a color attribute to the mesh corners to use in a shader editor.

.. image:: https://user-images.githubusercontent.com/28003269/111040947-32882c80-844f-11eb-9ac2-e61eabdc2ee1.png