Index To Mask
=============

.. image:: https://user-images.githubusercontent.com/14288520/188234538-c3f3a166-7df1-4e22-883b-319735ded680.png
  :target: https://user-images.githubusercontent.com/14288520/188234538-c3f3a166-7df1-4e22-883b-319735ded680.png

Functionality
-------------

This node generates a mask list ([True, False,..]) based on a index list (the True values) and a length or data-set

Inputs
------

* **Index**: Index of the True values
* **Mask Length**: Length of the mask list
* **data to mask**: when **data masking** is enabled the node will take the shape of the input data

Parameters
----------

* **data masking**: When enabled the length of the mask will be taken from the **data to mask** input.
* **Topo mask**: When enabled the mask will taken from the **data to mask** input but one level above, this is handy to mask vector lists or edge/polygon lists

Outputs
-------

* **Mask:** Mask List

Example
-------

.. image:: https://user-images.githubusercontent.com/14288520/188236911-b358e69b-5c8b-4590-8ac5-95fc9cacecef.png
  :target: https://user-images.githubusercontent.com/14288520/188236911-b358e69b-5c8b-4590-8ac5-95fc9cacecef.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/188235854-53955f0a-4192-40fd-8860-c3479c92bbac.png
  :target: https://user-images.githubusercontent.com/14288520/188235854-53955f0a-4192-40fd-8860-c3479c92bbac.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/188235889-0f7a56c5-7d13-4c5b-8c4b-f7db38138711.png
  :target: https://user-images.githubusercontent.com/14288520/188235889-0f7a56c5-7d13-4c5b-8c4b-f7db38138711.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/188235912-721fbd30-e3d6-4e00-8958-056f0f50fcd0.png
  :target: https://user-images.githubusercontent.com/14288520/188235912-721fbd30-e3d6-4e00-8958-056f0f50fcd0.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/list_mask/index_to_mask/index_to_mask.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/list_mask/index_to_mask/index_to_mask.png
  :alt: index_to_mask_sverchok_blender_example.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
