List Split
==========

.. image:: https://user-images.githubusercontent.com/14288520/187968085-a2e503ea-5173-40b2-add1-ded7aa2dcc22.png
  :target: https://user-images.githubusercontent.com/14288520/187968085-a2e503ea-5173-40b2-add1-ded7aa2dcc22.png

Functionality
-------------

Split list into chunks. The node is *data type agnostic*, meaning it makes no assumptions about the data you feed it. It should accepts any type of data native to Sverchok.

Inputs
------

+--------------+---------------------------------------------------+
| Input        | Description                                       |
+==============+===================================================+
| Data         | The data - can be anything                        |
+--------------+---------------------------------------------------+
| Split size   | Size of individual chunks                         |
+--------------+---------------------------------------------------+

Parameters
----------


**Level**

It is essentially how many chained element look-ups you do on a list. If ``SomeList`` has a considerable *nestedness* then you might access the most atomic element of the list doing ``SomeList[0][0][0][0]``. Levels in this case would be 4.

**unwrap**

Unrwap the list if possible, this generally what you want.
[[1, 2, 3, 4]] size 2.

+--------+-------------------+
| Unwrap | Result            |
+========+===================+
| On     | [[1, 2], [3, 4]]  |
+--------+-------------------+
| Off    | [[[1, 2], [3, 4]]]|
+--------+-------------------+

**Split size**

Size of output chunks.

Outputs
-------

**Split**

The list split on the selected level into chunks, the last chunk will be what is left over.    

Examples
--------

Trying various inputs, adjusting the parameters, and piping the output to a *Debug Print* (or stethoscope) node will be the fastest way to acquaint yourself with the inner workings of the *List Item* Node.

.. image:: https://user-images.githubusercontent.com/14288520/187968105-3093b440-92a3-4ed2-9359-8f8ef1567fab.png
  :target: https://user-images.githubusercontent.com/14288520/187968105-3093b440-92a3-4ed2-9359-8f8ef1567fab.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`