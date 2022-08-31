List Levels
===========

Functionality
-------------

This node allows the user to manipulate with nesting structure of data by setting checkboxes. It allows to:

* Remove a level of nesting by concatenating nested lists of some level, or
* Add a level of nesting by adding another pair of square brackets around nested list of some level, or
* do both things at the same or at different nesting levels.

This node works with nested lists or tuples. Numpy arrays are considered to be atomic objects.

Inputs
------

This node has the following input:

* **Data**. Input data. This node supports data of any standard type (numbers,
  vertices, surfaces and so on), with arbitrary nesting level. This input is
  mandatory.

Parameters
----------

When **Data** input is connected, the interface of the node presents a table.
Each row of the table describes one nesting level of input data, and defines
what do you want to do with data at this nesting level. The table has the
following columns:

* **Level**. This shows the nesting depth of this level, i.e. how deeply nested
  this data is, counting from the outermost list. Outermost list always has
  depth of 1, one that is nested in it has depth of 2, and so on.
* **Shape**. This describes the shape of data at this level. For lists or
  tuples, it shows whether this is a list or tuple, and also the number of
  items in it, in square brackets. For atomic objects, it shows the type of the
  data ("float", or "int", or "SvSurface", and so on).
* **Flatten**. This column contains a checkbox. If checked, the node will
  concatenate all lists contained in list at this nesting level. Obviously,
  atomic objects (integers, floats etc.) do not contain any nested objects, so for the
  innermost level this checkbox is not available. For lists that contain atomic
  objects, this checkbox is not available either, as there are
  no nested lists too. This checkbox does transform data only at one level, it
  does not "go deeper" automatically. So, if you check this checkbox, you
  always decrease nesting level of whole data by 1. To give some examples,

   * ``[[1, 2], [3, 4]]`` is transformed into ``[1, 2, 3, 4]``.
   * ``[[[1], [2]], [[3], [4]]]`` is transformed into ``[[1], [2], [3], [4]]``.

* **Wrap**. This column contains a checkbox. If checked, the node will put the
  data at this nesting level in a separate list, i.e. wrap it in additional
  pair of square brackets. So, by checking this checkbox, you always increase
  the nesting level of whole data by 1. For example, if you check this
  parameter at the innermost level (nesting of 0), the node will create a
  separate list for each atomic object (wrap each atomic object into a list). 

For simple shapes of data, many combinations of checkboxes will give identical
results; but for more deeply nested data, or when having more items at
outermost levels, there will be more different options. You can also connect
several "List Levels" nodes to do even more complex manipulations with data
structure.

Examples of Usage
-----------------

By default, all checkboxes are disabled, so the node does nothing:

.. image:: https://user-images.githubusercontent.com/28003269/187598033-b1489f12-a949-4a14-842c-b77b4d1a94c0.png

Let's wrap each number into a separate list (this is what "Graft" option of output socket menus does as well):

.. image:: https://user-images.githubusercontent.com/28003269/187598129-4cd1cb55-4122-43dd-b175-d5ed36b353d9.png

By enabling "Wrap" at the next level, we put each vertex into a separate list:

.. image:: https://user-images.githubusercontent.com/28003269/187598191-b9da1499-c19b-46b4-8564-6e548ca2a2a0.png

The next level - put each list of vertices (object) into a separate list:

.. image:: https://user-images.githubusercontent.com/28003269/187598252-75720f20-48a9-4760-8c97-661867e9843a.png

And the outermost level - put the whole data structure into additional pair of square brackets:

.. image:: https://user-images.githubusercontent.com/28003269/187598332-9e6ef1a8-80de-4ca4-9991-659c24c6fdc9.png

By enabling "Flatten" at the deepest available level, we concatenate vertices data into lists of numbers:

.. image:: https://user-images.githubusercontent.com/28003269/187598388-c978e176-e697-4535-ba5b-c7e7612182d4.png

By flattening at the outermost level, we concatenate lists of vertices into a single list of vertices:

.. image:: https://user-images.githubusercontent.com/28003269/187598453-09121868-9fc0-4078-90f9-21d5dc50a40c.png

If we enable both Flatten flags, we concatenate lists of vertices into lists of numbers, AND we concatenate lists of numbers into a single list of numbers:

.. image:: https://user-images.githubusercontent.com/28003269/187598519-c849fde8-352a-43a5-b638-787e0e9d425c.png

