List Levels
===========

.. image:: https://user-images.githubusercontent.com/14288520/188002611-0f681313-5bf5-4f83-a5c3-4221af3d83ae.png
  :target: https://user-images.githubusercontent.com/14288520/188002611-0f681313-5bf5-4f83-a5c3-4221af3d83ae.png

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

.. image:: https://user-images.githubusercontent.com/14288520/188002648-3e992748-06d7-42a9-aeed-e917b183d1c5.png
  :target: https://user-images.githubusercontent.com/14288520/188002648-3e992748-06d7-42a9-aeed-e917b183d1c5.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Let's wrap each number into a separate list (this is what "Graft" option of output socket menus does as well):

.. image:: https://user-images.githubusercontent.com/14288520/188002682-f598ec87-90f5-46e3-a4c0-2ba0f4de3f23.png
  :target: https://user-images.githubusercontent.com/14288520/188002682-f598ec87-90f5-46e3-a4c0-2ba0f4de3f23.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

By enabling "Wrap" at the next level, we put each vertex into a separate list:

.. image:: https://user-images.githubusercontent.com/14288520/188002711-0a43caf7-cf5a-4e89-9422-9eadd2de44c1.png
  :target: https://user-images.githubusercontent.com/14288520/188002711-0a43caf7-cf5a-4e89-9422-9eadd2de44c1.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

The next level - put each list of vertices (object) into a separate list:

.. image:: https://user-images.githubusercontent.com/14288520/188002729-8e60dcd0-ac12-4d83-97cc-bd9534ffdfb5.png
  :target: https://user-images.githubusercontent.com/14288520/188002729-8e60dcd0-ac12-4d83-97cc-bd9534ffdfb5.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


And the outermost level - put the whole data structure into additional pair of square brackets:

.. image:: https://user-images.githubusercontent.com/14288520/188002754-ff585102-c296-43ba-9041-6b9eb2285be1.png
  :target: https://user-images.githubusercontent.com/14288520/188002754-ff585102-c296-43ba-9041-6b9eb2285be1.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


By enabling "Flatten" at the deepest available level, we concatenate vertices data into lists of numbers:

.. image:: https://user-images.githubusercontent.com/14288520/188003925-ccf47ee0-07f1-4ee5-b1ad-4666f94fea9f.png
  :target: https://user-images.githubusercontent.com/14288520/188003925-ccf47ee0-07f1-4ee5-b1ad-4666f94fea9f.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


By flattening at the outermost level, we concatenate lists of vertices into a single list of vertices:

.. image:: https://user-images.githubusercontent.com/14288520/188003950-3bc52742-46e9-4dca-b508-44ba143604eb.png
  :target: https://user-images.githubusercontent.com/14288520/188003950-3bc52742-46e9-4dca-b508-44ba143604eb.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


If we enable both Flatten flags, we concatenate lists of vertices into lists of numbers, AND we concatenate lists of numbers into a single list of numbers:

.. image:: https://user-images.githubusercontent.com/14288520/188003979-cbfcdc08-8477-4126-a1a2-f38c436fd3f1.png
  :target: https://user-images.githubusercontent.com/14288520/188003979-cbfcdc08-8477-4126-a1a2-f38c436fd3f1.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/188002634-8ff0edf1-da21-4dd9-af2f-503a17ca4eba.png
  :target: https://user-images.githubusercontent.com/14288520/188002634-8ff0edf1-da21-4dd9-af2f-503a17ca4eba.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* List->List Main-> :doc:`List Zip </nodes/list_main/zip>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
