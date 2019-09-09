Mask To Index
=============

Functionality
-------------

This node generates a mask list ([True, False,..]) based on a index list (the True values) and a length or data-set

Inputs
------

**Index**: Index of the True values

**Mask Length**: Length of the mask list

**data to mask**: when **data masking** is enabled the node will take the shape of the input data

Parameters
----------

**data masking**: When enabled the length of the mask will be taken from the **data to mask** input.

**Topo mask**: When enabled the mask will taken from the **data to mask** input but one level above, this is handy to mask vector lists or edge/polygon lists

Outputs
-------

**Mask:** Mask List

Example
-------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/list_mask/index_to_mask/index_to_mask.png
  :alt: index_to_mask_sverchok_blender_example.png
