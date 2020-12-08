Loop In
=======

This node in conjunction with the Loop In node can create loops with nodes

Offers two different modes 'Range' and 'For Each'


Operators
---------

**Create Loop In**: creates a Loop In node and links the Loop In - Loop Out socket.


Inputs
------

**Loop Out**: Socket to link with the Loop Out node.

**Break**: If a True value is inputted the loop will stop (Only if Loop In is in Range Mode).

**Skip**: If a True value is inputted the loop the result wont be added to the output, like a internal mask.  (Only if Loop In is in For Each Mode).

Data0, Data1... inputs will be created coping the Loop in Outputs


Outputs
-------


Data0, Data1... inputs will be created coping the Loop in Outputs


Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/101332093-22234d00-3875-11eb-819a-68e86ef8c2c2.png

.. image:: https://user-images.githubusercontent.com/10011941/101334215-e047d600-3877-11eb-89df-cfaaf73dd427.png
