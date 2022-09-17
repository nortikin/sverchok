Matrix View
===========

.. image:: https://user-images.githubusercontent.com/14288520/189986754-05e41530-73bf-45dc-bac3-5b4823817fee.png
  :target: https://user-images.githubusercontent.com/14288520/189986754-05e41530-73bf-45dc-bac3-5b4823817fee.png

A quick way to represent matrices, the colour start/end allows you to show the sequence of matrices easily by transitioning from one colour to the next over the full sequence of matrices.

see the development thread may provide more information:
https://github.com/nortikin/sverchok/pull/1572

the alpha mode is not working at the moment. Update: working.

Settings
--------

* **Simple** On/Off

.. image:: https://user-images.githubusercontent.com/14288520/190597368-c3b8adbd-4324-4498-913e-8d21f388d040.png
  :target: https://user-images.githubusercontent.com/14288520/190597368-c3b8adbd-4324-4498-913e-8d21f388d040.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

---------

* **Grid** On/Off

.. image:: https://user-images.githubusercontent.com/14288520/190595427-ef992d0f-dd0f-4425-8d59-95a389bbc262.png
  :target: https://user-images.githubusercontent.com/14288520/190595427-ef992d0f-dd0f-4425-8d59-95a389bbc262.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

---------

* **Alpha** 0/ non 0

.. image:: https://user-images.githubusercontent.com/14288520/190595856-1422ae2c-eb0a-40e7-8709-37134a0205e9.png
  :target: https://user-images.githubusercontent.com/14288520/190595856-1422ae2c-eb0a-40e7-8709-37134a0205e9.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

---------

* **Color start/end** with Alpha is non zero

.. image:: https://user-images.githubusercontent.com/14288520/190596355-b2233861-df1b-4936-8691-2e449eb917c3.png
  :target: https://user-images.githubusercontent.com/14288520/190596355-b2233861-df1b-4936-8691-2e449eb917c3.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190110769-6655af3c-c54b-43f9-a164-a68b5e69e645.png
  :target: https://user-images.githubusercontent.com/14288520/190110769-6655af3c-c54b-43f9-a164-a68b5e69e645.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* MULT X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/190115965-7e9500d5-5924-4ee1-b71a-a79feb3a739b.png
  :target: https://user-images.githubusercontent.com/14288520/190115965-7e9500d5-5924-4ee1-b71a-a79feb3a739b.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`