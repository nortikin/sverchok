**************
User interface
**************

If you are new to Blender node tree interface it is worth to have a look at
`Blender docs <https://docs.blender.org/manual/en/dev/interface/controls/nodes/index.html>`_ first.

.. figure:: https://user-images.githubusercontent.com/28003269/125752203-078aab31-889f-4745-a43a-950c5cfb4f0c.jpg
    :width: 800

#. Menu of editor types
#. Name of the current node tree
#. Menu of embedded templates in Sverchok. The template will be created in current tree otherwise new tree will be
   created
#. Processing shows whether current tree is in Live update mode
#. Git branch - if you clone and link repository - it will show current branch

There are several ways to create nodes in Sverchok:

* From "Add Node" menu, which can be invoked from top menu bar, or by pressing
  Shift-A.
* From "Sverchok Nodes" toolbox under Tools (T) panel.
* From standard Blender's search menu (F3).

.. toctree::
    :maxdepth: 2

    All panels <panels>
    Input socket menus <input_menus>
    Output socket menus <socket_menus>
    node_shields
    preferences
    shortcuts


.. figure:: https://cloud.githubusercontent.com/assets/5783432/19623205/245bcab2-98d2-11e6-810c-ace33de8499b.gif
    
    Example of importing a template

.. Note::
    *Add node* menu, *Search node* menu and *Context node* menu are not covered currently.
    Any contributions are welcome.
