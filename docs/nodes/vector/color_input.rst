Color Input
===========

Functionality
-------------

This node allows you to specify color by using a colorpicker widget. In a sense, this is an analog of "Matrix Input" or "List Input" nodes, but for colors.

Inputs
------

This node does not have any inputs.

Parameters
----------

This node has the following parameters:

* **Color**. Edited by using standard Blender's color picking widget.
* **Use Alpha**. If checked, then this node outputs 4-vector (R, G, B, A). Otherwise, it outputs 3-vector (R, G, B). By default this is not checked.
* **To 3D Panel**. If checked, then this node is recognized and collected as node tree parameter when you press "Scan for props" in Sverchok's T panel in the 3D View. By default this is checked. This parameter is only available in the N panel.

Outputs
-------

This node has only one output: **Color**. It is RGB or RGBA vector, depending on **Use Alpha** parameter.

Examples
--------

.. image:: https://user-images.githubusercontent.com/284644/36633499-b5b7108a-19b8-11e8-8e39-243d9dd42e7e.png

