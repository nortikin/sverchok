List Length
===========

.. image:: https://user-images.githubusercontent.com/14288520/187519011-8e55b053-801f-43f1-9d45-727a11633ca1.png
  :target: https://user-images.githubusercontent.com/14288520/187519011-8e55b053-801f-43f1-9d45-727a11633ca1.png

Functionality
-------------

The Node equivalent of the Python ``len()`` function. The length is inspected at the Level needed.

Inputs
------

Takes any kind of data.

Parameters
----------

* **Level:** Set the level at which to observe the List. Min Level is 0.

Outputs
-------

Depends on incoming data and can be nested. Level 0 is top level (totally zoomed out), higher levels get more granular (zooming in) until no higher level is found (atomic). The length of the most atomic level will be 1, for instance single ints or float or characters. The output will reflect the nestedness of the incoming data.


Examples
--------

Often a few experiments with input hooked-up to a debug node will make the exact working of this Node instantly clearer than any explanation. 

.. image:: https://user-images.githubusercontent.com/14288520/187696438-05bf888a-086e-4a49-a6e6-0752ce3ef475.png
  :alt: ListLengthDemo1.PNG
  :target: https://user-images.githubusercontent.com/14288520/187696438-05bf888a-086e-4a49-a6e6-0752ce3ef475.png

* Vector-> :doc:`Vector X/Y/Z </nodes/vector/axis_input_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/187696469-0fba9dff-0423-406c-9a19-7ef0d607d996.png
  :alt: ListLengthDemo2.PNG
  :target: https://user-images.githubusercontent.com/14288520/187696469-0fba9dff-0423-406c-9a19-7ef0d607d996.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`