***************************
Node tree evaluation system
***************************

.. figure:: https://user-images.githubusercontent.com/28003269/125029133-3b55db80-e09a-11eb-8bea-3e631ad763eb.gif

    Highlighting nodes which were effected by property changes in an initial node

Sverchok layout is a tree of nodes connected with each other by links. The tree represents an algorithm.
Typically, in the left side a tree has nodes which generate some data. In the middle there are nodes
which manipulate with data. And in the right side there are output nodes which save/show the result.
The role of the evaluation system is to combine work of every single node into a meaningful work of an algorithm.


Control flow
============

In general execution process of a tree is happening from left to right. There is a rule that a node can be executed
before all previous nodes are executed. However it does not make execution process fully ordered. Consider next example.

.. figure:: https://user-images.githubusercontent.com/28003269/124717678-6c0d0800-df16-11eb-83fa-b9f6d21c417a.png
    :align: center

    Simple tree

Possible order of execution is A -> B -> C -> D -> E -> F. However D -> B -> A -> C -> E -> F is also possible.
And there are another variants. If there are two or more disjoint nets of nodes their execution,
relatively to each other, also is unordered.

.. note::
    In the future Sverchok may get a execution system which would be able to evaluate some parts of a tree concurrently.
    In this case A, B, D nodes could be executed concurrently if more than two processors were available.
    But now Sverchok can use only one processor.

There are nodes which can change control flow in some way.


Group nodes
-----------

If there is a pattern of nodes which is repeated several times in a tree it can be converted into a group node.
Group node encapsulates bunch of nodes inside a subtree. Evaluation system of main tree evaluate group nodes
in the same way as regular nodes except that their work can be cancelled. Cancelling of group nodes happen between
execution of its nodes.


:doc:`Loop nodes <nodes/logic/loop_out>`
----------------------------------------

Loop nodes can evaluate the same nodes multiple times. In current state the loop node takes control of the flow and
return it to evaluation system after their part is done.


:doc:`Wifi nodes<nodes/layout/wifi_in>`
---------------------------------------

.. figure:: https://user-images.githubusercontent.com/28003269/125024249-6f78ce80-e091-11eb-836f-1f8a9fcad205.png
    :align: right
    :figwidth: 400px

    Connection between ``A number`` and ``Stethoscope`` nodes via wifi nodes

In case if you have links which go through all your tree and spoil the tree readability it's possible
to hide the links by using wifi nodes. ``Wifi In`` and ``Wifi Out`` nodes act as if they had a link between each other.
``Wifi In`` can be connected to multiple ``Wifi Out`` nodes.


Reroute nodes
-------------

This is |reroute| `standard Blender nodes`_ which are used for links organization. They just pass data to next nodes.

.. |reroute| image:: https://user-images.githubusercontent.com/28003269/125025744-4574db80-e094-11eb-9f1a-16f8f9191ef0.png
.. _`standard Blender nodes`: https://docs.blender.org/manual/en/latest/interface/controls/nodes/reroute.html

Other nodes
-----------

Also there are other nodes which can evaluate nodes on their own accord. Here is at least one of them
:doc:`Evolver node <nodes/logic/evolver>`.


Muting links
------------

.. figure:: https://user-images.githubusercontent.com/28003269/125027738-c681a200-e097-11eb-9033-8b8924a76661.gif
    :align: right
    :figwidth: 300px

This is `standard Blender functionality`_ which allows temporary to mute links. A muted link acts as if it did not
exist. Muting links connected to reroute nodes mutes also the link from opposite side.

.. _`standard Blender functionality`: https://docs.blender.org/manual/en/latest/interface/controls/nodes/editing.html?#mute-links


Muting nodes
------------
It's partly supported (not for all nodes yet). You are welcome to report if you
find that some node is muting improperly.

.. warning::
   Currently there are cases when internal inks of a node does not fit to how
   data really paths through the node. It's limitation of Blender which API
   does not give control of displaying internal links properly.


.. _sv_triggers:

Triggers
========

Each evaluation starts with update event (trigger). Each event has information about what was previously changed.
Evaluation system use this information to evaluate only those nodes which have been effected by the change.
Evaluation process is next. The evaluation system scans nodes from left to right. If it finds outdated nodes 
it updates them. Also it checks whether current node has previous nodes updated in current session and if so it also
goes to update.

Update events can be cancelable or not. Events, which are cancelable, can be canceled either by user by pressing Escape
button or by another event. For example if to change property of a node too rapidly in a heavy tree
it causes stopping update in the middle of the tree and starting update from the node again.

For now execution system can cancel execution only between nodes.
It means if there is very slow node you won't be able to cancel the update until the node will do its work.
All events are cancelable except events triggered by frame change
otherwise heavy trees will never be able to be evaluated entirely.

Tree topology changes
    Any changes in tree topology (add/remove nodes, add/remove/relink links) trigger its revaluation. The update
    can be suppress by disabled live update option of a tree. If new link was added
    then node, from which the link is going, is marked as outdated by the event
    (actual rules are a bit more complicated in this case).
    If a link was removed then node, to which the link was going, is marked as outdated.
    If new node is added it's going to be evaluated. If a node is removed nothing happens.

Node property / socket property changes
    Node property changes or changes in a property of one of its sockets make the node outdated
    and trigger its reevaluation. The update can be suppress by disabled live update option of a tree.

`Re-update all nodes` operator (:ref:`active_tree_panel`)
    It reevaluates a whole tree regardless to updated state of its nodes and the
    `live update` option.

`Update all` operator (:ref:`layout_manager`)
    It is the same as `re-update all nodes` operator but effect all trees in a file.

Frame changes
    Update upon frame changes. Extra information `Animation`_.

.. tip::
    If you have heavy tree and auto-update makes the work with the tree inefficient you can disable the `Live update`
    property and update the tree manually with `Re-update all nodes` operator whenever you need.
    Also you can add shortcut for the operator by pressing :kbd:`RMB` on the button of the operator (active tree panel).
    Another way to update is enabling `Live update` mode. In this case only changed put of the tree will be updated.

Scene changes
    This trigger reacts on arbitrary changes in scene. Those can be: moving
    objects, changing edit / object mode, mesh editing, assign materials etc.


Modes (:ref:`active_tree_panel`)
--------------------------------

Live update
    If enabled it means that the tree will be evaluated upon changes in its
    topology, changes in node properties or scene changes made by user.
    This property does not effect evaluation upon frame changes or by
    `re-update all nodes` operator.
    Enabling the property will call the tree topology changes trigger.

Animate
    If enabled the tree will be reevaluated upon frame change. The update can effect not all nodes but only those
    which have property `to_animate` enabled.

Scene update
    If enabled togather with Live Update the tree will be reevaluated upon
    changes in the scene. It will effect only nodes with `interactive`
    property enabled.


Animation
=========

.. figure:: https://user-images.githubusercontent.com/28003269/124884635-83fe8d80-dfe3-11eb-903d-e6c2922e41ca.gif
    :align: right
    :figwidth: 300px

    Example of how a tree can be recalculated after editing base object by changing current frame pressing the arrow
    button on keyboard.

With Sverchok it's possible to create animations. Some nodes have `Animate node` option |option|. If the option is
enabled the node will be update each frame change. This can serve two purposes.

.. |option| image:: https://user-images.githubusercontent.com/28003269/124885639-87464900-dfe4-11eb-8796-a54ff5f84e58.png

- Firstly this can be used for generating animations. In this case
  :doc:`Frame Info node <nodes/scene/frame_info_mk2>` will be most useful.
- **(Deprecated, the Scene trigger is used instead now)** Secondly updating
  nodes upon frame change can be used for refreshing nodes which take data from
  Blender data blocks. For frame change the left/right arrow buttons can be
  used.


.. warning::
    Blender does not support keyframes for custom trees. It's possible to inset keyframes to node properties but
    they won't react upon actual frame changes and you won't find them in the graph editor.


Handling errors
===============

.. figure:: https://user-images.githubusercontent.com/28003269/124915446-9805b780-e002-11eb-8df0-b0b9e53d91dc.png
    :align: right
    :figwidth: 300px

    Displaying an error happen during the node execution

It can happen that during execution of a tree some nodes won't be able to be evaluated properly.
In this case the node will be marked by a color and it will got an error massage nearby itself.
An error can have two parts - a name of the error and optionally some message.

There are 3 basic exceptions:
    - Node error (actually it can be any Python error like ``IndexError``, ``LookUpError`` etc.) Sometimes the error
      can help to understand what is wrong but sometimes not. The reason of the error also can be due some bug in
      its implementation, or the type of data is wrong, or shape of the data is unexpected or something else.
    - ``NoDataError`` it can happen when previous node does not have any data in output sockets. It's considered
      as deprecated behaviour and in the future nodes should be able to handle empty data without raising the error.
    - ``CancelError`` this marks nodes which execution was interrupted.

If a node raises an error it prevents next nodes to be executed. If there is an error node you can determine whether
any other node can be executed by searching path from that node to the node with error in backward direction.
If there is no such a path then the node will be executed. It means that errors in detached groups of nodes
won't effect each other execution. This also is true about separate branches of nodes which don't have connections
after nodes with errors.


.. note::
    This behaviour may be changed in the future iterations and nodes with errors won't cause stopping execution
    of next nodes.


Progress message
================

.. figure:: https://user-images.githubusercontent.com/28003269/124924441-84f7e500-e00c-11eb-9b5f-c91329f635cd.gif
    :align: right
    :figwidth: 350px

    Showing progress of execution of a tree

Cancellable events show execution progress of a tree in the header of the tree editor. The message displays
name of a node which is currently executed. Not all nodes get into the message.
