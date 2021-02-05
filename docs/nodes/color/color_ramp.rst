Color Ramp
==========

Functionality
-------------

This node map all the incoming values turning them to colors using the gradient you define manually through the interface.

Disclaimer
----------

This node creates a Blender material node-group and uses "Color Ramp" nodes to create and store the gradients.
Due the nature of this implementation the changing the gradient will not trigger the node update.
To update the output you need to click in the "Update" button or perform another action that triggers the node-tree update.

Inputs
------

This node has the following input:

* **Value**. The value to be used as an input for the function. The default value is 0.5.

Parameters
----------

* **Animate Node**. Update node on frame change

* **Update**. Update node

* **Use Alpha** Output RGBA or RGB colors


Outputs
-------

This node has the following outputs:

* **Color**. The result of the function application to the input value.


Examples
--------

Basic usage:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/color/color_ramp/color_ramp_sverchok_blender_example.png
