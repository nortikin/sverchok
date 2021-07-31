Skin Mesher
===========


.. image:: https://user-images.githubusercontent.com/619340/127733080-a0e2c470-9a72-4c72-88c6-41a814c45d17.png

.. image:: https://user-images.githubusercontent.com/619340/127733292-c7019c45-492d-4c85-b713-931063bac9b4.png


Functionality
-------------

This node is an interpretation of the current features of the Skin Modifier. During manual editing you would use
alt+s to scale up the size of individual vertices, this node offers the ability to scale vertices by accepting two 
lists of scalar values, one for x scale and one for y scale.

settings roots: Depending on how complicated and disjoint your mesh is you may find the result of the modifier can be made more natural by adjusting the way the node sets the roots. This option is placed in the N Panel. 


.. image:: https://user-images.githubusercontent.com/619340/127733402-9a806e90-ded3-43d0-988f-96ee9df626d2.png


Category
--------

Viz -> Skin Mesher

Inputs
------

This node takes ``verts``, ``edges``, and optionally ``matrices``, as inputs.
Additionally it accepts ``scale X`` and ``scale Y``

Outputs
-------

Outputs a mesh with a SkinModifier added to it, directly into the scene.

Caution
-------

You do not want to manually edit the product of this node, that would break the procedural nature of the node. Manual editing after creation can result in undefined behaviour and is likely overwritten as soon as you update the Sverchok node tree again by moving upstream sliders etc.


