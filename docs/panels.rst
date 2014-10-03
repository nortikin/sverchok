***********************
Panels of Sverchok
***********************

Node Tree Panel
===============

This panel allows to manage sverchok layouts as easy as you press buttons on elevator.

Update
------

**Update all**

Updates all trees of sverchok.

**Update layout**

Updates current layout, that is active now.

Layout manager
--------------

Box to quickly pick layout, switch between them with buttons, not popup list. Has also buttons:

**B** - bake this layout - will gather all layout's viewer draw and viewer text to bake them. Bake only if bakable button is active on node, else ignore.

**Show layout** - show or hide all viewers - to draw or not to draw OpenGL in window, but bmesh viewer not handled for now.

**Animate layout** - to animate or not what is in layout - may preserve you time.

Check for updates
-----------------

**Check for updates** - finds if master branch on github has new version of sverchok. In future there will be releases, but now dangerouse update.

**Upgrade Sverchok** - upgrades Sverchok from github with new version - button appears only if 'check for updates' finds new version.


3D Panel
========

With this panel your layout becomes addon itself. So, you making your life easy.

Scan for props
--------------

When layout is in, check for next nodes to embad them as properties:
 - float node
 - int node
 - object in node
 
Sorting them by label, that user defined in node tree panel or if no label, it takes name of node.

Update all
----------

Forces updating all layouts.

Clean
-----

Button to remove sverchok and blendgraph layouts, that has not users (0)

**hard clean**  - boolean flag to remove layouts even if it has users (1,2...), but not fake user (F). Fake user layout will be left.

**Clean layouts** - remove layouts. Button active only if no node tree windiw around. Better to make active layout nothing or fake user layout to prevent blender crash. Easyest way - activate your Faked user layout, on 3D press **ctrl+UP** and press button. than again **ctrl+UP** to go back. No wastes left after sverchok in scene.

Properties
----------

Layouts by box. Every layout has buttons:

**B** - bake this layout - will gather all layout's viewer draw and viewer text to bake them. Bake only if bakable button is active on node, else ignore.

**Show layout** - show or hide all viewers - to draw or not to draw OpenGL in window, but bmesh viewer not handled for now.

**Animate layout** - to animate or not what is in layout - may preserve you time.

Properties has also gathered values:

**floats and integers** - digit itself, maximum and minimum vaues.

**object in** - button for object in node to collect selected objects.


Notes
=====

All this stuff including upgrade and check for updates situates on /utils/sv_tools.py file
