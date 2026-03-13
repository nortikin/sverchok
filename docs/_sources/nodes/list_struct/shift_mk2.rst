List Shift
==========

.. image:: https://user-images.githubusercontent.com/14288520/187798671-b50c6cfc-d4a9-4f20-8cc5-048b7fd1794f.png
  :target: https://user-images.githubusercontent.com/14288520/187798671-b50c6cfc-d4a9-4f20-8cc5-048b7fd1794f.png

Functionality
-------------

Shifting data in selected level on selected integer value as:
  
  [0,1,2,3,4,5,6,7,8,9] with shift integer 4 will be
  [4,5,6,7,8,9]
  But with enclose flag:
  [4,5,6,7,8,9,0,1,2,3]
  
Inputs
------

* **data** - list of data any type to shift
* **Shift** - value that defines shift

Properties
----------

* **level** - manipulation level, 0 - is objects shifting
* **enclose** - close data when shifting, that way ending cut numbers turns to beginning

Outputs
-------

* **data** - shifter data, adaptive socket

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/187798687-fb5f8564-43f6-40ac-bd87-6e02af1a1649.png
  :target: https://user-images.githubusercontent.com/14288520/187798687-fb5f8564-43f6-40ac-bd87-6e02af1a1649.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Zip </nodes/list_main/zip>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/187798712-9237d83a-3b6b-4f9b-b3e7-f9794208838d.gif
  :alt: shift
  :target: https://user-images.githubusercontent.com/14288520/187798712-9237d83a-3b6b-4f9b-b3e7-f9794208838d.gif

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`