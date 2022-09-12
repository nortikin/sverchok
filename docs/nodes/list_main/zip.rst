List Zip
========

.. image:: https://user-images.githubusercontent.com/14288520/187516998-eb8d150a-ef02-480b-bb8b-739ed20c4049.png
    :target: https://user-images.githubusercontent.com/14288520/187516998-eb8d150a-ef02-480b-bb8b-739ed20c4049.png

Functionality
-------------

Making pairs of data to mix togather as zip function.

x = [[[1,2],[3,4]]]
y = [[[5,6],[7,8]]]


out level 1 =       [[[[1, 2], [5, 6]], [[3, 4], [7, 8]]]]

out level 1 unwrap = [[[1, 2], [5, 6]], [[3, 4], [7, 8]]]

out level 2 =       [[[[1, 3], [2, 4]], [[5, 7], [6, 8]]]]

out level 2 unwrap = [[[1, 3], [2, 4]], [[5, 7], [6, 8]]]

out level 3 =       [[[[], []], [[], []]]]

Inputs
------

* **data** multisocket

Properties
----------

* **level** integer to operate level of conjunction
* **unwrap** boolean to unwrap from additional level, added when zipped 

Outputs
-------

* **data** adaptable socket


Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/187518702-482dd7e7-0b67-46b8-a68c-c8ad60f4111d.png
    :target: https://user-images.githubusercontent.com/14288520/187518702-482dd7e7-0b67-46b8-a68c-c8ad60f4111d.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Text-> :doc:`Simple Text </nodes/text/simple_text>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
