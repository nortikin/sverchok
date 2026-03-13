Neuro Elman 1 Layer
===================

.. image:: ../../assets/nodes/logic/neuro.png

.. _`Russian translation here`: ./neuro_elman_ru.md

Functionality 
-------------


Layer 1 neuron network with studying. With Inputs and Outputs.
You should study network on data. After studying use node on your tree.

.. _`Algorithm description`: https://kpfu.ru/staff_files/F1493580427/NejronGafGal.pdf  


Tune node before use. Mandatory props first. Additional props can be passed. 
After tuning and connecting links go to study. 
Every update will teach your node. 
You can press update and wait some time. 


Data shape:
-----------

::

    [obj1, obj2, obj3, ...]  
    obj = [...]  
    [[...], [...], [...], ...]  

Object levels 2 levels. Every object contain data for one step of srudying. 
Prepare data that way and link to input. To <b>etalon</b> send same objects count. Output will contain same objects count.


Category
--------

Logic -> Neuro Elman 1 Layer

Inputs
------

* **data** - input data
* **etalon** - expected data


Outputs
-------

* **result** - resulting data


Parameters
----------

+--------------------+--------+--------------------------------------------------------------------------------+
| Parameters         | Type   | Description                                                                    |
+====================+========+================================================================================+
| **A layer**        | int    | First layer neurons count, same as object count                                |
+--------------------+--------+--------------------------------------------------------------------------------+
| **B layer**        | int    | Second layer neurons count, inner layer                                        |
+--------------------+--------+--------------------------------------------------------------------------------+
| **C layer**        | int    | Third layer neurons count, Equal to objects count on output                    |
+--------------------+--------+--------------------------------------------------------------------------------+
| **maximum**        | float  | Maximum possible values, meaning to be used on node                            |
+--------------------+--------+--------------------------------------------------------------------------------+
| **koeff learning** | float  | node learning tempo (change w/o fear)                                          |
+--------------------+--------+--------------------------------------------------------------------------------+
| **gisterezis**     | float  | scheduled to set thresholds for signal processing (not in use yet)             |
+--------------------+--------+--------------------------------------------------------------------------------+
| **cycles**         | int    | Loops count to study by one pass                                               |
+--------------------+--------+--------------------------------------------------------------------------------+
| **epsilon**        | float  | the susceptibility of the node study                                           |
+--------------------+--------+--------------------------------------------------------------------------------+
| **lambda**         | float  | weight coefficients changing's step                                            |
+--------------------+--------+--------------------------------------------------------------------------------+
| **threshold**      | float  | Threshold preserve retraining                                                  |
+--------------------+--------+--------------------------------------------------------------------------------+
| **Reset**          | Button | reset all coeffitients                                                         |
+--------------------+--------+--------------------------------------------------------------------------------+


Usage
-----

**Task statement**
~~~~~~~~~~~~~~~~~~

Please, study for XOR operation:

::

    [1, 1] = [1]  
    [1, 0] = [1]  
    [0, 1] = [1]  
    [0, 0] = [0]  

**Preparations**
~~~~~~~~~~~~~~~~

.. image:: ../../assets/nodes/logic/neuro_data_in.png

* List->List Main-> :doc:`List Delete Levels </nodes/list_main/delete_levels>`
* Text-> :doc:`Viewer Text MK3 </nodes/text/viewer_text_mk3>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

.. image:: ../../assets/nodes/logic/neuro_data_in_text.png

Same with expected data:
""""""""""""""""""""""""

.. image::  ../../assets/nodes/logic/neuro_etalon.png

* List->List Main-> :doc:`List Delete Levels </nodes/list_main/delete_levels>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

**Node preparations**
~~~~~~~~~~~~~~~~~~~~~

* **A layer** - Set value 2, because inputs are pairs
* **B layer** - Let it be 5, but can be any (experiment here)
* **C layer** - Setting 1, because output have to be one number

.. image:: ../../assets/nodes/logic/neuro_ansumble.png

* List->List Main-> :doc:`List Delete Levels </nodes/list_main/delete_levels>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`

Running learning and waiting. Interrupt Studying. I had have that result:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. image:: ../../assets/nodes/logic/neuro_training_result.png

Compare result:
"""""""""""""""

.. image:: ../../assets/nodes/logic/neuro_result.png

* List->List Main-> :doc:`List Delete Levels </nodes/list_main/delete_levels>`
* Text-> :doc:`Viewer Text MK3 </nodes/text/viewer_text_mk3>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`