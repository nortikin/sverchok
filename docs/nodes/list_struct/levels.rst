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

* **Depth**. This shows the nesting depth of this level, i.e. how deeply nested
  this data is, counting from the outermost list. Outermost list always has
  depth of 0, one that is nested in it has depth of 1, and so on.
* **Nesting**. This shows how many nesting levels are inside each item of data
  at this level. At the innermost nesting level, each item of the list is an
  "atomic object", for example it can be integer number, floating-point number,
  surface or curve, and so on, but not a list or tuple. So, the innermost data
  level has nesting level equal to 0 (zero). A list which consists of atomic
  objects has nesting level of 1, and so on.
* **Shape**. This describes the shape of data at this level. For lists or
  tuples, it shows whether this is a list or tuple, and also the number of
  items in it, in square brackets. For atomic objects, it shows the type of the
  data ("float", or "int", or "SvSurface", and so on).
* **Flatten**. This column contains a checkbox. If checked, the node will
  concatenate all lists contained in list at this nesting level. Obviously,
  atomic objects (nesting of 0) do not contain any nested objects, so for the
  innermost level this checkbox is not available. For lists that contain atomic
  objects (nesting of 1), this checkbox is not available either, as there are
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

.. image:: https://user-images.githubusercontent.com/9460236/129511959-8e17fe20-ce5e-4127-a88b-bb1dc84b916e.png

Let's wrap each number into a separate list (this is what "Graft" option of output socket menus does as well):

.. image:: https://user-images.githubusercontent.com/9460236/129511970-6767616b-7f4f-4672-85d8-2ecf96cc4111.png

By enabling "Wrap" at the next level, we put each vertex into a separate list:

.. image:: https://user-images.githubusercontent.com/9460236/129513146-33f5e2c7-345b-414e-bbf6-561b3dacabd7.png

The next level - put each list of vertices (object) into a separate list:

.. image:: https://user-images.githubusercontent.com/9460236/129511986-c4bf1bac-f8a6-44a9-b187-b532210f89f8.png

And the outermost level - put the whole data structure into additional pair of square brackets:

.. image:: https://user-images.githubusercontent.com/9460236/129511989-bf1b69d4-b916-4771-a289-30d0761cf60c.png

By enabling "Flatten" at the deepest available level, we concatenate vertices data into lists of numbers:

.. image:: https://user-images.githubusercontent.com/9460236/129511997-5fe4d9bd-ce06-40cc-811e-f41de1ec3378.png

By flattening at the outermost level, we concatenate lists of vertices into a single list of vertices:

.. image:: https://user-images.githubusercontent.com/9460236/129512002-d194d402-d80f-4a4f-a3e6-4afb281fd191.png

If we enable both Flatten flags, we concatenate lists of vertices into lists of numbers, AND we concatenate lists of numbers into a single list of numbers:

.. image:: https://user-images.githubusercontent.com/9460236/129512012-38d5314a-d799-4fb5-ad50-b6792e2907e4.png

