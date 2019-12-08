Assign Materials List
=====================

Functionality
-------------

In Blender, each object can have a list of associated materials. Once the list
of materials is assigned to the object, the material to be used for specific
face can be identified by the index of the material in that list.

This node assigns the list of materials to the provided Blender object.

This node is most commonly used together with the **Set Material Index** node.

Inputs
------

This node has the following inputs:

- **Object**. The Blender object, for which the list of materials is to be
  assigned. This input can also be specified as a parameter. This input is
  mandatory.

Parameters
----------

This node has only one parameter: the list of materials to be assigned to the
object. One can add or remove items from this list by means of **Plus** /
**Minus** buttons next to the list.

Outputs
-------

This node has the following outputs:

- **Object**. The same object as in the input, but with material list already assigned.

Examples of usage
-----------------

An example of usage in pair with the **Set Material Index** node:

.. image:: https://user-images.githubusercontent.com/284644/70392046-4ef01a80-19fd-11ea-8e4d-5039cf053fed.png

