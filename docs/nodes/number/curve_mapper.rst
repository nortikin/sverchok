Curve Mapper
============

This node map all the incoming values using the curve you define manually through the interface.

Disclaimer
----------

This node creates a Blender material node-group and uses "RGB Curves" nodes to create and store the curve.
Due the nature of this implementation the changing the curve will not trigger the node update.
To update the output you need to click in the "Update" button or perform another action that triggers the node-tree update.

Examples
--------

Basic range remapping:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_1.png

Using the node to define the column profile:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_2.png 
