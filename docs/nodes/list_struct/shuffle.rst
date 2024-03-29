List Shuffle
============

.. image:: https://user-images.githubusercontent.com/14288520/187994149-88dec5a7-e39c-4752-b736-80d0c01f9327.png
  :target: https://user-images.githubusercontent.com/14288520/187994149-88dec5a7-e39c-4752-b736-80d0c01f9327.png

Functionality
-------------

Shuffle (randomize) the order of input lists.

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| Data   | The data - can be anything                                               |
+--------+--------------------------------------------------------------------------+
| Seed   | Seed setting used by shuffle operation                                   |
+--------+--------------------------------------------------------------------------+

Parameters
----------


**Level**

It is essentially how many chained element look-ups you do on a list. If ``SomeList`` has a considerable *nestedness* then you might access the most atomic element of the list doing ``SomeList[0][0][0][0]``. Levels in this case would be 4.

**Seed**

Affects the output order.


Outputs
-------

* **Item**, the selected items on the specified level.
* **Other**, the list with the selected items deleted.

Examples
--------


The shuffle operation is based on the python random.shuffle. https://docs.python.org/3.4/library/random.html?highlight=shuffle#random.shuffle

Trying various inputs, adjusting the parameters, and piping the output to a *Debug Print* (or stethoscope) node will be the fastest way to acquaint yourself with the inner workings of the *List Shuffle* Node.

.. image:: https://user-images.githubusercontent.com/14288520/187994179-bbc77d38-d352-48d6-add8-7346645fba0d.png
  :target: https://user-images.githubusercontent.com/14288520/187994179-bbc77d38-d352-48d6-add8-7346645fba0d.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`