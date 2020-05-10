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

   * Use the **Add** menu from menu bar (sverchok has little control over how this menu is layed out, protip: use the next method instead)

     |image6|

   * Hit *Shift-A* (standard Blender's shortcut for adding things, we inject our own menu into it, with icons!):

     |image7|

   * Hit *Alt-Space*. This shortcut calls for a special search menu, which allows you to search for nodes and macros:

     |image8|

   * Use Blender's standard search box, which appears when you hit *Space* in node view:

     |image9|

   * You can as well open the Tools panel by pressing *T* in node view. There
     is a special panel for each category of nodes. By pressing a button you
     add specific node to the tree:

     |image10|


.. |image1| image:: https://user-images.githubusercontent.com/619340/81501387-61d28800-92d8-11ea-90cc-fcde07bf5625.png
.. |splittingawindow| image:: https://cloud.githubusercontent.com/assets/619340/18806709/f7659ea6-8234-11e6-9ac8-b566bf8b2eca.gif
.. |switchview| image:: https://cloud.githubusercontent.com/assets/619340/18806724/75f30fd8-8235-11e6-9319-40888ca49337.gif
.. |image2| image:: https://cloud.githubusercontent.com/assets/619340/18806728/98b24bb0-8235-11e6-8455-c382fb0686c9.png
.. |image3| image:: https://cloud.githubusercontent.com/assets/619340/18806345/41d59726-822a-11e6-96c6-2ed9a986923e.png
.. |image4| image:: https://user-images.githubusercontent.com/619340/81508456-88a6b380-9304-11ea-9cf6-f7e22400a5a6.png
.. |image5| image:: https://user-images.githubusercontent.com/619340/81508498-b0961700-9304-11ea-824b-f9da0118ec4b.png
.. |image6| image:: https://user-images.githubusercontent.com/619340/81508610-59447680-9305-11ea-8d1a-a909a575c42f.png
.. |image7| image:: https://user-images.githubusercontent.com/619340/81508556-079bec00-9305-11ea-8641-286eb27e0963.png
.. |image8| image:: https://user-images.githubusercontent.com/284644/34564128-499d91b2-f177-11e7-9259-d042ce8b9de6.png
.. |image9| image:: https://user-images.githubusercontent.com/284644/34564221-9fb3acee-f177-11e7-9b0a-d64103d0ba0e.png
.. |image10| image:: https://user-images.githubusercontent.com/284644/34564322-08f15328-f178-11e7-8b0d-76f49c7e3afe.png
