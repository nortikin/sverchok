Loop Out
========

.. image:: https://user-images.githubusercontent.com/14288520/189755933-5fa724a2-a935-4487-b7cd-2983b8b0f69f.png
  :target: https://user-images.githubusercontent.com/14288520/189755933-5fa724a2-a935-4487-b7cd-2983b8b0f69f.png

This node in conjunction with the Loop In node can create loops with nodes

Offers two different modes 'Range' and 'For Each'


Operators
---------

* **Create Loop In**: creates a Loop In node and links the Loop In - Loop Out socket.


Inputs
------

* **Loop Out**: Socket to link with the Loop Out node.
* **Break**: If a True value is inputted the loop will stop (Only if Loop In is in Range Mode).
* **Skip**: If a True value is inputted the loop the result wont be added to the output, like a internal mask.  (Only if Loop In is in For Each Mode).

Data0, Data1... if working on Range Mode inputs will be created copying the Loop in Outputs. If working in For Each mode they will be created when linking the Loop Out inputs


Outputs
-------


Data0, Data1... In Range mode: inputs will be created copying the Loop in Outputs. In For Each mode they will be copy the Loop Out inputs.


Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/101332093-22234d00-3875-11eb-819a-68e86ef8c2c2.png
    :target: https://user-images.githubusercontent.com/10011941/101332093-22234d00-3875-11eb-819a-68e86ef8c2c2.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* CA: Faces Area: Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Logic-> :doc:`Loop In </nodes/logic/loop_in>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* BIG X: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/10011941/101334215-e047d600-3877-11eb-89df-cfaaf73dd427.png
    :target: https://user-images.githubusercontent.com/10011941/101334215-e047d600-3877-11eb-89df-cfaaf73dd427.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* CA: Faces Area: Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* BIG X: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Logic-> :doc:`Loop In </nodes/logic/loop_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`