***********************
Panels of Sverchok
***********************

Node Tree Panel
===============

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512957/866dacd8-4b46-11e4-9cfa-2b78d2a2f8a9.png
  :alt: nodetreepanel.ng

This panel allows to manage sverchok layouts as easy as you press buttons on elevator.

Update
------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512960/868c837e-4b46-11e4-9fba-a5062fd5434f.png
  :alt: nodetreeupdate.png
  
**Update all**

Updates all trees of sverchok.

**Update layout**

Updates current layout, that is active now.

Layout manager
--------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512959/867d395a-4b46-11e4-9419-95ed1479ac72.png
  :alt: manager.png

Box to quickly pick layout, switch between them with buttons, not popup list. Has also buttons:

**B** - bake this layout - will gather all layout's viewer draw and viewer text to bake them. Bake only if bakable button is active on node, else ignore.

**Show layout** - show or hide all viewers - to draw or not to draw OpenGL in window, but bmesh viewer not handled for now.

**Animate layout** - to animate or not what is in layout - may preserve you time.

Check for updates
-----------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512958/8671953c-4b46-11e4-898d-e09eec52b464.png
  :alt: upgradenewversion.png

**Check for updates** - finds if master branch on github has new version of sverchok. In future there will be releases, but now dangerouse update.

**Upgrade Sverchok** - upgrades Sverchok from github with new version - button appears only if 'check for updates' finds new version.


3D Panel
========

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512953/865c3962-4b46-11e4-8dbd-df445f10b808.png
  :alt: panel3d.png

With this panel your layout becomes addon itself. So, you making your life easy.

Scan for props
--------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512955/866461fa-4b46-11e4-8caf-d650d15f5c5f.png
  :alt: scanprops.png


When layout is in, check for next nodes to embad them as properties:
 - float node
 - int node
 - object in node
 
Sorting them by label, that user defined in node tree panel or if no label, it takes name of node.

Update all
----------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512955/866461fa-4b46-11e4-8caf-d650d15f5c5f.png
  :alt: updateall.png

Forces updating all layouts.

Clean
-----

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512954/8662fbf8-4b46-11e4-8f67-243a56c48856.png
  :alt: cleanlayout.png

Button to remove sverchok and blendgraph layouts, that has not users (0)

**hard clean**  - boolean flag to remove layouts even if it has users (1,2...), but not fake user (F). Fake user layout will be left.

**Clean layouts** - remove layouts. Button active only if no node tree windiw around. Better to make active layout nothing or fake user layout to prevent blender crash. Easyest way - activate your Faked user layout, on 3D press **ctrl+UP** and press button. than again **ctrl+UP** to go back. No wastes left after sverchok in scene.

Properties
----------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512956/8666aeba-4b46-11e4-9c13-651e3826f111.png
  :alt: properties.png

Layouts by box. Every layout has buttons:

**B** - bake this layout - will gather all layout's viewer draw and viewer text to bake them. Bake only if bakable button is active on node, else ignore.

**Show layout** - show or hide all viewers - to draw or not to draw OpenGL in window, but bmesh viewer not handled for now.

**Animate layout** - to animate or not what is in layout - may preserve you time.

Properties has also gathered values:

**floats and integers** - digit itself, maximum and minimum vaues.

**object in** - button for object in node to collect selected objects.

