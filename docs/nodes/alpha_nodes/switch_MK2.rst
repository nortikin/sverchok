Switch
=============

Functionality
-------------
This node allows to use logic of ordinary "if else" function.

Highlight of this node have always been to increase number of input and output sockets instead of creating new additional instances of the node. This logic can spread on other like nodes. Now number of in/out sockets can be controlled by N panel and right click menu. 

This version of node features functionality of both modes of the previous, received more attractive interface and ability to manage with empty objects. In this moment it just ignores empty objects but this logic is not obvious and may should be reconsidered.

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| state  | state that decides which set of sockets to use                           | 
+--------+--------------------------------------------------------------------------+
| A_0    | If state is True this socket is used                                     |
+--------+--------------------------------------------------------------------------+
| B_0    | If state is False this socket  used                                      |
+--------+--------------------------------------------------------------------------+


Parameters
----------


**in/out number**

Number of sockets in each set.

**Flatten list**

Perhaps temporary parameter for deleting nested levels of list in matrix and object types of data, because no one node does not expect nested levels now.

.. image:: https://user-images.githubusercontent.com/28003269/39927639-fcb8ff7c-5543-11e8-9597-47793e088c03.gif

Outputs
-------

Out 0 to Out N depending on count. Socket types are copied from first from the T set.

Examples
--------
Generation of bool sequence easily.

.. image:: https://user-images.githubusercontent.com/28003269/39827448-f8d6c08c-53c8-11e8-864e-b72afd67befb.png

Working with different types of data.

.. image:: https://user-images.githubusercontent.com/28003269/39925828-3fc466fe-553e-11e8-861e-f3e3dfbfc92a.png

It is possible to deal with empty objects.

.. image:: https://user-images.githubusercontent.com/28003269/39926724-225bc0b4-5541-11e8-974f-6efebb68392e.png

Using as filter.

.. image:: https://user-images.githubusercontent.com/28003269/39926961-dccbb1f2-5541-11e8-8337-281510eec5d8.png
