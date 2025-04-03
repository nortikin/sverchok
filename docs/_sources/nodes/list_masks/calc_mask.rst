Calculate Mask
==============

.. image:: https://user-images.githubusercontent.com/14288520/188239156-763c7489-c590-4781-a643-6337ad71a60a.png
  :target: https://user-images.githubusercontent.com/14288520/188239156-763c7489-c590-4781-a643-6337ad71a60a.png

Functionality
-------------

This node calculates masks from two input lists (Set and Subset). For each item
in the Set, it returns True if the item is present in Subset, otherwise it
returns False.

There are nodes, which output, for example, "All faces" and "Processed faces"
or smth like that. To do something with that output, it would be usually more
effective to deal with "All faces" and "Processed faces mask" instead.

The node can work on different levels of data trees. For example, given Subset
= `[[1, 2], [3,4]]` and Set = `[[1, 2], [3, 4], [5, 6]]`:

*   with level = 0 it will output `[True, True, False]`
*   with level = 1 it will output `[[True, True], [True, True], [False, False]]`

Given Subset = `[[1], [5,6]]` and Set = `[[1, 2, 3], [7, 8, 9]]`:

* with level = 0 it will output `[False, False]` (because, for example, there
  is no `[1, 2, 3]` in the `[[1], [5,6]]`)
* with level = 1, it will output `[[True, False, False], [False, False, False]]`

Inputs
------

This node has the following inputs:

* **Subset**. List of "good" data items to be checked against.
* **Set**. The whole set of data items.

Parameters
----------

This node has the following parameters:

* **Negate**. If checked, then the resulting mask will be negated. I.e., the
  node will output True if item of Set is *not* present in Subset. Unchecked by
  default.
* **Ignore order**. If checked, then, while comparing lists, the node will not
  take into account the order of items in these lists. For example, is `[1, 2]`
  the same as `[2, 1]`? No, if **Ignore order** is not checked.

Outputs
-------

This node has only one output: **Mask**. Number of items in this output is
equal to number of items in the **Set** input.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/188239166-059d2c9c-3be4-4bb5-887f-dd8b004e6ad2.png
  :target: https://user-images.githubusercontent.com/14288520/188239166-059d2c9c-3be4-4bb5-887f-dd8b004e6ad2.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

This node can, for example, be used to apply **Inset Special** node iteratively:

.. image:: https://user-images.githubusercontent.com/284644/58757902-82715a00-852d-11e9-9288-369607f5229d.png
  :target: https://user-images.githubusercontent.com/284644/58757902-82715a00-852d-11e9-9288-369607f5229d.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

