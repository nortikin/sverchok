************
Installation
************

.. figure:: https://user-images.githubusercontent.com/5783432/118532321-82d18280-b74f-11eb-8a04-f1205deda82d.jpg
    :width: 250
    :align: right

There are two options from where to install Sverchok. There are outdated releases, used as cut of development
process, you can get zip archive from the `last release page <https://github.com/nortikin/sverchok/releases/latest>`_.
But when you update addon with button inside nodes N panel it takes from main branch. Because active development
occurs inside master `you can download zip archive with latest changes from main GitHub page <https://github.com/nortikin/sverchok/archive/refs/heads/master.zip>`_.
Also watchout on `main page in branches <https://github.com/nortikin/sverchok>`_.

After the Sverchok archive is downloaded open property window in Blender (:kbd:`Ctrl+Alt+U`):

.. image:: https://user-images.githubusercontent.com/5783432/118532329-849b4600-b74f-11eb-9751-5a12446cf6b2.jpg

Choose add-on tab, push *install from file* button and choose downloaded ZIP archive file:

.. image:: https://user-images.githubusercontent.com/28003269/125616217-76604b16-fddc-4d51-b144-127e1443104f.png

And activate Sverchok with flag:

.. image:: https://user-images.githubusercontent.com/28003269/125616257-1c5af6b8-9bae-486b-8bed-cff1210987d9.png

If the add-on was enabled successfully open Sverchok editor and create new node tree. Now you can add new nodes.
If the add-on was not enabled open system console ``Window -> Toggle system console`` and create 
`new issue <https://github.com/nortikin/sverchok/issues/new>`_ with the error message.

.. image:: https://user-images.githubusercontent.com/28003269/125616829-f0462efa-39ad-4b25-b417-3cb9dca00014.png

Though the add-on is installed you can't use its full power now. There are nodes which you won't be able to see
in the menu until extra libraries will be installed. The list of unavailable nodes is printed in the system
console during add-on initialization. Read more about installing the libraries in the next section.

.. toctree::
   :maxdepth: 1

   installing_dependencies

