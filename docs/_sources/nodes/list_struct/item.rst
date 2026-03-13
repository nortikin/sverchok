List Item
=========

.. image:: https://user-images.githubusercontent.com/14288520/187971764-8db7c649-349a-4641-8eb5-7177e89875cd.png
  :target: https://user-images.githubusercontent.com/14288520/187971764-8db7c649-349a-4641-8eb5-7177e89875cd.png

Functionality
-------------

Select items from list based on index. The node is *data type agnostic*, meaning it makes no assumptions about the data you feed it. It should accepts any type of data native to Sverchok..

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| Data   | The data - can be anything                                               |
+--------+--------------------------------------------------------------------------+
| Index  | Index of Item(s) to select, allows negative index python index           |
+--------+--------------------------------------------------------------------------+

Parameters
----------


**Level**

It is essentially how many chained element look-ups you do on a list. If ``SomeList`` has a considerable *nestedness* then you might access the most atomic element of the list doing ``SomeList[0][0][0][0]``. Levels in this case would be 4.

**Index**

A list of indexes of the items to select, allow negative index python indexing so that -1 the last element. The items doesn't have to be in order and a single item can be selected more than a single time.

Outputs
-------

* **Item**, the selected items on the specified level.
* **Other**, the list with the selected items deleted.

Examples
--------

Trying various inputs, adjusting the parameters, and piping the output to a *Debug Print* (or stethoscope) node will be the fastest way to acquaint yourself with the inner workings of the *List Item* Node.

.. image:: https://user-images.githubusercontent.com/14288520/187971779-869195ac-8805-4a96-acee-48660b6096a8.png
  :target: https://user-images.githubusercontent.com/14288520/187971779-869195ac-8805-4a96-acee-48660b6096a8.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/187973547-84721898-e7e1-4a98-b3ce-aa8ab9cf9165.png
  :target: https://user-images.githubusercontent.com/14288520/187973547-84721898-e7e1-4a98-b3ce-aa8ab9cf9165.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
