Custom switcher
===============

.. image:: https://user-images.githubusercontent.com/28003269/59678662-11dd6500-91de-11e9-9b28-a08aebaea8b8.png

Functionality
-------------
Simple node which convert input sequence to buttons. It is useful for creating custom switcher.  
Added Mask feature to handle switch templates. So you can have configuration switcher in 3D panel.


Inputs
------

- **Data** - any data you wish.There is no limitation of length of input data but all items above **32** will be ignored.
- **Mask** - Mask for selection templates.

Outputs
-------

- **Item** - index of selected items.

N panel
-------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Multiple selection | Bool  | Allowed to select several items simultaneously                                 |
+--------------------+-------+--------------------------------------------------------------------------------+
| Show in 3d panel   | Bool  | Won't be ignored for adding parameter of the node to 3d panel                  |
+--------------------+-------+--------------------------------------------------------------------------------+
| Size of buttons    | float | controlling of size of buttons                                                 |
+--------------------+-------+--------------------------------------------------------------------------------+
| Masked             | Bool  | To use mask or not to use mask                                                 |
+--------------------+-------+--------------------------------------------------------------------------------+

3D panel
--------

It consists dropdown list of items and button for activation of multiple selection mode.

Examples
--------

**Mask usage pipeline (new feature 2026)**

.. image:: https://github.com/user-attachments/assets/5bf6adf6-41fb-47fb-bbc9-f7be59f1e352


**Controlling of light from 3d panel:**

.. image:: https://user-images.githubusercontent.com/28003269/59653042-7deda800-91a1-11e9-892f-f3e927612d72.gif

.. image:: https://user-images.githubusercontent.com/28003269/59653046-80500200-91a1-11e9-8314-3c7ebe98d3f8.png

**controlling of material from 3d panel:**

.. image:: https://user-images.githubusercontent.com/28003269/59654477-5d285100-91a7-11e9-8a9b-f436d6de57db.gif

.. image:: https://user-images.githubusercontent.com/28003269/59654483-644f5f00-91a7-11e9-92cb-70da3cc641b0.png
