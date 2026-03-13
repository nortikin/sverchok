Dictionary In
=============

.. image:: https://user-images.githubusercontent.com/14288520/189837947-bf79c883-37d8-4d11-b670-005289870408.png
  :target: https://user-images.githubusercontent.com/14288520/189837947-bf79c883-37d8-4d11-b670-005289870408.png

Functionality
-------------

The node creates dictionary with costume keys and given data.
It can be used for preparing data structure which is required for some nodes.

Category
--------

Dictionary -> dictionary In

Inputs
------

- **-----** - can be connected with any other output socket of any type (10 maximum connections)

Outputs
-------

- **Dict** - dictionary(ies)


Examples
--------

**Creating complex data structure:**

.. image:: https://user-images.githubusercontent.com/14288520/189847314-c3b94fd2-b9df-4c1f-9f35-0f9143b897d2.png
    :target: https://user-images.githubusercontent.com/14288520/189847314-c3b94fd2-b9df-4c1f-9f35-0f9143b897d2.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Dictionary-> :doc:`Dictionary Out </nodes/dictionary/dictionary_out>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

**Does not use the same keys:**

.. image:: https://user-images.githubusercontent.com/28003269/71763737-be700180-2ef8-11ea-8cf9-4f8cf94286cb.png
    :target: https://user-images.githubusercontent.com/28003269/71763737-be700180-2ef8-11ea-8cf9-4f8cf94286cb.png

**Does not try join dictionaries with different keys, only keys of first dictionary in a list are taken in account:**

.. image:: https://user-images.githubusercontent.com/28003269/71763756-fe36e900-2ef8-11ea-8ae0-300aebc95ad1.png
    :target: https://user-images.githubusercontent.com/28003269/71763756-fe36e900-2ef8-11ea-8ae0-300aebc95ad1.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Dictionary-> :doc:`Dictionary Out </nodes/dictionary/dictionary_out>`