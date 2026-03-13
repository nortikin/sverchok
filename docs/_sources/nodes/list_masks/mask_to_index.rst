Mask To Index
=============

.. image:: https://user-images.githubusercontent.com/14288520/188231993-f6fed026-cf27-4498-9c7b-57f4cf7aae0d.png
  :target: https://user-images.githubusercontent.com/14288520/188231993-f6fed026-cf27-4498-9c7b-57f4cf7aae0d.png

Functionality
-------------

This node use transforms a mask list ( [0,1,0..] or [False, True, False..]) in to two lists, one with the True (or 1) indexes and the other with the false (or 0) indexes.


Inputs
------

* **Mask:** Input socket for True / False Data list.

Outputs
-------

* **True Index:** Input socket for True Data list.
* **False Index:** Input socket for False Data list.


Example
-------

.. image:: https://user-images.githubusercontent.com/14288520/188232004-789ce3b9-b6d9-4a8e-9796-c60f3fcb9b51.png
  :target: https://user-images.githubusercontent.com/14288520/188232004-789ce3b9-b6d9-4a8e-9796-c60f3fcb9b51.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/list_mask/mask_to_index/mask_to_index.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/list_mask/mask_to_index/mask_to_index.png
  :alt: compass_3d_sverchok_blender_example.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`