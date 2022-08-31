Constant List
=============

.. image:: https://user-images.githubusercontent.com/14288520/187515870-f8b16699-e1f4-49bd-b398-5077539e2aba.png
  :target: https://user-images.githubusercontent.com/14288520/187515870-f8b16699-e1f4-49bd-b398-5077539e2aba.png

Functionality
-------------

This node generates a list by repeating a single constant (integer or
floating-point) value. It is "vectorized", so by putting some lists to it's
inputs it is possible to make lists consisting of different numbers repeated
different count of times. Such lists can be useful as generated masks for some geometry.

Inputs
------

This node has the following inputs:

* **IntValue** or **FloatValue** - either integer or floating-point value to be
  repeated. The node expects data of nesting level of 0, 1, or 2 in this inputs
  (number, list of numbers, or list of lists of numbers). The default value is
  0 (or 0.0 in case floating-point mode is used).
* **Length**. Length of list to be generated. The node expects data of nesting
  level 0, 1 or 2 in this input (i.e. a number, a list of numbers, or a list of
  lists of numbers). The default value is 3.

Parameters
----------

This node has the following parameters:

* **Type**. This defines the type of the constant value. Available modes are
  **Integer** and **Float**. Depending on this parameter, either **IntValue**
  or **FloatValue** input / parameter will be used. The default type is
  **Integer**.
* **Output level**. This defines the nesting level of output list. Possible
  values are from 1 (list of numbers) to 3 (list of lists of lists of numbers).
  The default value is 2.

Outputs
-------

This node has the following output:

* **Data**. Generated list. Nesting level of data in this output will be equal
  to the value of the **Output level** parameter.

Examples of usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/14288520/187686031-a9e200c0-de63-4021-950f-c4cff8c855a9.png
  :target: https://user-images.githubusercontent.com/14288520/187686031-a9e200c0-de63-4021-950f-c4cff8c855a9.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`

If **Output level** would be 1 in this setup, the result would be `[0.06,
0.06, 0.06]`. If **Output level** would be 3, the result would be `[[[0.06,
0.06, 0.06]]]`:

.. image:: https://user-images.githubusercontent.com/14288520/187686049-9e05a419-95f7-46c8-bc62-08beaee85589.png
  :target: https://user-images.githubusercontent.com/14288520/187686049-9e05a419-95f7-46c8-bc62-08beaee85589.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`

More complex example:

.. image:: https://user-images.githubusercontent.com/14288520/187686059-70276803-32bd-4855-8bc3-4e2616bb0e0e.png
  :target: https://user-images.githubusercontent.com/14288520/187686059-70276803-32bd-4855-8bc3-4e2616bb0e0e.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`


If **Output level** would be 1 in this setup, the result would be `[1, 1, 1, 2,
2, 2, 2, 2]`. If **Output level** would be 3, the result would be `[[[1, 1, 1],
[2, 2, 2, 2, 2]]]`:

.. image:: https://user-images.githubusercontent.com/14288520/187686070-80366925-2893-470d-b6af-6651d6825b26.png
  :target: https://user-images.githubusercontent.com/14288520/187686070-80366925-2893-470d-b6af-6651d6825b26.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`

Another complex example:

.. image:: https://user-images.githubusercontent.com/14288520/187688679-f97b4d33-989f-4406-8fb7-fec0df09a056.png
  :target: https://user-images.githubusercontent.com/14288520/187688679-f97b4d33-989f-4406-8fb7-fec0df09a056.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`

If **Output level** would be 1 in this setup, the result would be `[1, 1, 1, 2,
2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4]`. If **Output level** would be 2, the
result would be `[[1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3], [4, 4, 4, 4, 4]]`.

.. image:: https://user-images.githubusercontent.com/14288520/187688692-bcf57546-26b8-4f01-85a6-280942092053.png
  :target: https://user-images.githubusercontent.com/14288520/187688692-bcf57546-26b8-4f01-85a6-280942092053.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Text-> :doc:`Data Shape </nodes/text/shape>`