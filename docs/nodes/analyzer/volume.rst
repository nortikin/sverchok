Volume
======

.. image:: https://github.com/user-attachments/assets/cca9273d-ca11-4dfe-acd0-908c3c94a82f
  :target: https://github.com/user-attachments/assets/cca9273d-ca11-4dfe-acd0-908c3c94a82f

*Alias: Volume*

Functionality
-------------

Count Volume of every object. Output list of values

Inputs
------

- Vers vertices of object(s)
- Pols polygons of object(s)
- Group Id (per object). If an object has more than one group, the first element is taken.

  .. image:: https://github.com/user-attachments/assets/8bbbfaaf-b1d6-4c06-9618-066a8fa72c85
    :target: https://github.com/user-attachments/assets/8bbbfaaf-b1d6-4c06-9618-066a8fa72c85


Outputs
-------

- Volume, corresponding to count of objects it outputs volumes in list.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/195329977-1e98401a-3575-4934-8542-692fba546afd.png
  :target: https://user-images.githubusercontent.com/14288520/195329977-1e98401a-3575-4934-8542-692fba546afd.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`

Grouped volumes
===============

.. image:: https://github.com/user-attachments/assets/5816d0f7-7d60-4a40-aa59-8a11c28d563f
  :target: https://github.com/user-attachments/assets/5816d0f7-7d60-4a40-aa59-8a11c28d563f