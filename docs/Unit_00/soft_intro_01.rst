**************************************************************
Unit 00. Introduction to Blender 2.8+, the NodeView and 3DView
**************************************************************

Sverchok Installed, what now?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a tickbox beside the Sverchok add-on in the Add-ons list in User Preferences, then it’s safe to assume the add-on is enabled. To
show the basics you need to have a NodeView open, and it’s useful to have a 3DView open at the same time.

NodeView and 3DView
-------------------

|image1|

1. **Split a View**:

   To do this we can split the existing 3DView into two views, by
   leftclicking into the little triangle/diagonal lines in the bottom
   left of the 3dview, and dragging to the right.

   |splittingawindow|


2. **Switch a View**:

   Now you have two windows, switch one of them in the Editor Type dropdown. If Sverchok is installed correctly it will be listed here as Sverchok Nodes

   |switchview|


3. **Make a new Tree**:

   When you start out you will have to press the New button to make a new node tree called (by default) NodeTree

   |image4|

   becomes

   |image5|


4. **Adding Nodes to the View**:

   From the NodeView, you can use the following ways to add nodes to tree:

   * Use the **Add** menu from menu bar (Sverchok has little control over how this menu is layed out, protip: use the next method instead)

     |image6|

   * Hit *Shift-A* (standard Blender's shortcut for adding things, we inject our own menu into it, with icons!):

     - don't be alarmed if what you see in your menu is not 100% identical to this image, new features are continously added/changed.

     |image7|

   * Hit *Alt-Space*. This shortcut calls for a special search menu, which allows you to search for nodes and macros:

     - once you get to know Sverchok you can type in "trigger" words associated with a node, to quickly narrow down the search list.
     - trigger macros using ``> some word``. More about macros later. If you stick with Sverchok they will be your secret weapon.

     |image8|

   * Use Blender's standard search box, which appears when you hit *F3* in node view:

     - this search box contains Operators for adding any sverchok node to the view, but you'll also find that it contains all other relevant Operators for that view. Sverchok also registers a few general Application Operators, and this is one way to execute them if you know what you're looking for.

     |image9|

.. |image1| image:: https://user-images.githubusercontent.com/619340/81501387-61d28800-92d8-11ea-90cc-fcde07bf5625.png
.. |splittingawindow| image:: https://user-images.githubusercontent.com/619340/81510180-34093580-9310-11ea-93fc-bd06c27f7422.gif
.. |switchview| image:: https://user-images.githubusercontent.com/619340/81510233-982bf980-9310-11ea-935a-37bcc7a3bd8a.gif
.. |image4| image:: https://user-images.githubusercontent.com/619340/81508456-88a6b380-9304-11ea-9cf6-f7e22400a5a6.png
.. |image5| image:: https://user-images.githubusercontent.com/619340/81508498-b0961700-9304-11ea-824b-f9da0118ec4b.png
.. |image6| image:: https://user-images.githubusercontent.com/619340/81508610-59447680-9305-11ea-8d1a-a909a575c42f.png
.. |image7| image:: https://user-images.githubusercontent.com/619340/81508556-079bec00-9305-11ea-8641-286eb27e0963.png
.. |image8| image:: https://user-images.githubusercontent.com/619340/81509102-9eb67300-9308-11ea-9e35-cb4fbc4abff5.png
.. |image9| image:: https://user-images.githubusercontent.com/619340/81508967-a7f31000-9307-11ea-89a1-715832a5ef83.png
