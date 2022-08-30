Loop In
=======

This node in conjunction with the Loop out node can create loops with nodes

Offers two different modes 'Range' and 'For Each'

Range
-----

In this mode the all the data inputted to the Loop In node will be processed every iteration.

For Each
--------

In this mode the inputted data will be split before being processed and there will be one loop per every level 1 object.

Operators
---------

**Create Loop Out**: creates a Loop out node and links the Loop In - Loop Out socket.


Inputs
------

**Iterations**: Number of repetitions (only in Range mode).

Data0, Data1... inputs will be created when the last one is linked

Options
-------

**Max Iterations**: Maximum iterations (in N-panel and Contextual Sverchok Menu)
**Socket Labels**: To change sockets names (in N-panel)

Outputs
-------

**Loop Out**: Socket to link with the Loop Out node.

**Loop Number / Item Number**: Actual Repetition / Item.

**Total Loops / Total Items**: Total Repetitions / Items.

Data0, Data1... output sockets will be created when the last input is linked

Examples
--------

Range mode example, Break used to control the maximum vertices.

.. image:: https://user-images.githubusercontent.com/10011941/101332093-22234d00-3875-11eb-819a-68e86ef8c2c2.png

For Each mode example, Skip input used to mask the results.

.. image:: https://user-images.githubusercontent.com/10011941/101334215-e047d600-3877-11eb-89df-cfaaf73dd427.png

You can change the socket labels in the N-Panel

.. image:: https://user-images.githubusercontent.com/10011941/101360702-519a7f80-389e-11eb-826d-0e1c5a7152d1.png
