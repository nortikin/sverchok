List Item Insert
================

.. image:: https://user-images.githubusercontent.com/14288520/189765700-332fba58-4671-4508-8c86-0756934ef8fc.png
  :target: https://user-images.githubusercontent.com/14288520/189765700-332fba58-4671-4508-8c86-0756934ef8fc.png

Functionality
-------------

Inserts items in a list at desired index. It can replace that index or move all the elements of the list to the right.

The node is *data type agnostic*, meaning it makes no assumptions about the data you feed it. It should accepts any type of data native to Sverchok...

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| Data   | The data - can be anything                                               |
+--------+--------------------------------------------------------------------------+
| Item   | Item(s) to insert                                                        |
+--------+--------------------------------------------------------------------------+
| Index  | Index  in which element will be inserted, allows negative index          |
+--------+--------------------------------------------------------------------------+

Parameters
----------

**Level**

It is essentially how many chained element look-ups you do on a list. If ``SomeList`` has a considerable *nestedness* then you might access the most atomic element of the list doing ``SomeList[0][0][0][0]``. Levels in this case would be 4.

**Replace**

When activated the node will replace the item at desired index. When disabled the element will be added and all the element after the index will move to the right.

**Index**

A list of items to select, allow negative index python indexing so that -1 the last element. The items doesn't have to be in order and a single item can be selected more than a single time.

Advanced Parameters
-------------------

Available in the N-panel and in the Right-click Menu:

**List Match Local**

In case of having different list lengths between Index and Item inputs the data will be matched according to the selected behavior. The default behavior is to match the longest list by repeating the last element of the short list (Match Long Repeat).

Outputs
-------

**Data**: the list with the items inserted.


Examples
--------

Trying various inputs, adjusting the parameters, and piping the output to a *Debug Print* (or stethoscope) node will be the fastest way to acquaint yourself with the inner workings of the *List Item Insert* Node.

.. image:: https://user-images.githubusercontent.com/14288520/189765911-020958bb-b660-46fd-a635-8616858cecb6.png
  :target: https://user-images.githubusercontent.com/14288520/189765911-020958bb-b660-46fd-a635-8616858cecb6.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`