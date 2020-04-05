***********************
Panels of Sverchok
***********************


Node Tree Panel
===============

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/docs_intro/sverchok_main_panel.png
  :alt: nodetreepanel.ng

This panel allows to manage Sverchok layouts as easy as you press buttons on an elevator.

Update
------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/docs_intro/sverchok_main_panel_01.png
  :alt: nodetreeupdate.png

+-------------------+---------------------------------+
| Update            | description                     |
+===================+=================================+
| all               | Updates all trees of sverchok.  |
+-------------------+---------------------------------+
| Update layout     | Updates currently active layout |
+-------------------+---------------------------------+

Layout manager
--------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/docs_intro/sverchok_main_panel_02.png

Box to quickly pick layout, switch between them with buttons instead of popup list. Also have settings:


+--------------------+----------------------------------------------------------------------------------------+
| Button             | Function                                                                               |
+====================+========================================================================================+
| **B**              | bake this layout - will gather all layout's viewer draw and viewer text to bake them.  |
|                    | Bake only if bakeable button is active on node, else ignore.                           |
+--------------------+----------------------------------------------------------------------------------------+
| **Show layout**    | Controls all OpenGL viewer of this layout. Viewer, Stethoscope and Viewer Indices      |
+--------------------+----------------------------------------------------------------------------------------+
| **Animate layout** | to animate the layout (or not) - may preserve you time.                                |
+--------------------+----------------------------------------------------------------------------------------+
| **Process layout** | Automatically evaluate layout while editing, disable for large or complex layouts (F6) |
+--------------------+----------------------------------------------------------------------------------------+
| **Draft Mode**     | Switch tree to Draft mode (F7)                                                         |
+--------------------+----------------------------------------------------------------------------------------+
| **Fake User**      | Sets fake user so layout isn't deleted on save                                         |
+--------------------+----------------------------------------------------------------------------------------+

Active Tree Properties
----------------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/docs_intro/sverchok_main_panel_03.png
  :alt: tree_properties.png

**Show error in tree**: Display the errors in the node-tree right beside the Node

**Eval dir**: This will give you control over the order in which subset graphs are evaluated

**Remove Stale Drawing**: This will clear the opengl drawing if Sverchok didn't manage to correctly clear it on its own

Check for updates
-----------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512958/8671953c-4b46-11e4-898d-e09eec52b464.png
  :alt: upgradenewversion.png

**Check for updates** - finds if master branch on github has new version of Sverchok. In future there will be releases, but now dangerous update.

**Show Last Commits** - Show lastests commits in info panel and terminal

**Upgrade Sverchok** - upgrades Sverchok from github with new version - button appears only if 'check for updates' finds a new version.


Nodes Toolbar
=============

To see this panel it has to be enabled in the Sverchok properties inside the Blender Preferences Panel -> Add-ons -> Sverchok.
There you can choose if to display it on the "N panel" or the "T panel".
Also you can choose if you want to display only the icons

The panel presents all nodes available, organized in categories with a search menu.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/docs_intro/sverchok_nodes_panel_04.png
  :alt: nodes_panel.png

.. image:: https://github.com/vicdoval/sverchok/blob/docs_images/images_for_docs/docs_intro/sverchok_nodes_panel_only_icons.png
  :alt: nodes_panel.png

You can add node to the tree by clicking corresponding button and dragging placing the node in the node-tree.

Presets Panel
=============

This is a second tab under the *T* panel. This is how it looks by default:

.. image:: https://user-images.githubusercontent.com/284644/34566374-19623d6e-f180-11e7-840a-ec5bb8972e64.png
  :alt: empty-presets.png

Introduction to Presets
-----------------------

Preset is a named set of stored settings of one of several nodes. You can:

* Save settings of one or several selected nodes (links between nodes are saved
  too) under specific name.
* Use saved preset in another node tree later.
* Import and export presets as `.json` files.
* Share presets with other users via gist.github.com service, or import presets
  made by other users.

Each preset belongs to some preset category. By default, all presets are in
special category named "General".

Presets are saved as `.json` files under Blender configuration directory, in
`datafiles/sverchok/presets`. Preset categories are represented as directories
under that one.

It can be good idea to store as a preset (and maybe share) the following things:

* One node with a lot of settings, if you think this is "good" settings and you
  are going to use the same settings many times.
* Scripted node, or "Mesh Expression" node, or one of other nodes that use
  Blender's text blocks as settings. Such nodes are stored together with
  corresponding text.
* Group (monad) node. It is saved with all contents.
* Several linked nodes, that do some completed thing, for later usage "as-is".
* Several linked nodes, that are "sort of going to be needed in this
  combination often", so that later you can start with this preset and add some
  nodes to it or tweak it somehow.

Panel Buttons
-------------

At the top of the Presets panel, there is a drop-down menu, which allows you to
select the category of presets to work with. By default, there is only one
category named "General".
All buttons placed below this menu work inside the selected category.

The Presets panel has the following buttons:

* **Save Preset**. This button is only shown when there are some nodes selected
  in the tree. When you press this button, it asks you for the name under which
  this preset should be known. You need to enter some descriptive name and
  press Ok. After that, the preset will become available in the lower part of
  the panel.
* **Manage Presets**. This is a toggle button. It switches you between "presets
  usage mode" (which is the default, when button is not pressed) and "presets
  management mode" (when the button is pressed).

Contents of lower part of the panel depend on whether the **Manage Presets** button is pressed.

When management mode is disabled, there is a button shown for each preset that you already have:

.. image:: https://user-images.githubusercontent.com/284644/71767705-aa47f680-2f30-11ea-9611-1b7fee9a6f61.png

By pressing such button, you add nodes saved in corresponding preset into
current tree. New nodes are automatically selected, so that you can move them
to another part of the node view.

When management mode is enabled, there are more buttons:

.. image:: https://user-images.githubusercontent.com/284644/71767749-3fe38600-2f31-11ea-9630-3239b903dc07.png

* **Import preset from Gist**. You will be asked for Gist ID or full URL of the
  gist, and preset name. If you have gist URL in the clibpoard, it will be
  pasted automatically.
* **Import preset from file**. File browser will appear to allow you to select
  a `.json` file to import. In the left bottom part of this file browser, there
  is mandatory text field asking you to enter preset name.
* **Create new category**. You will be asked for the name of the category.
  Category name must be correct directory name (for example, it can not contain
  `/` character). Category name must be unique.
* **Delete category {NAME}**. You will be asked for confirmation. Only empty
  category can be deleted.

The following buttons (in this order) are shown for each preset you have:

* **Export preset to Gist**. Preset will be exported to gist service. Gist URL
  will be automatically copied into clipboard.
* **Export preset to outer file**. File browser will appear asking you to
  select where to save the preset.
* **Edit preset properties**. A dialog will appear allowing you to change the
  following properties of preset: Name, Description, Author, License. The
  Description attribute will be used as a tooltip for preset button.

  .. image:: https://user-images.githubusercontent.com/284644/34521620-7ca698dc-f0b0-11e7-94a9-757975ec1ec7.png

* **Delete preset**. You will be asked for confirmation.

3D Panel
========

.. image:: https://user-images.githubusercontent.com/28003269/70139516-16bea400-16ac-11ea-9c77-3125856b4d28.png

With this panel your layout becomes addon itself. So, you making your life easy.
Since Blender 2.8 this panel has two instances. One instance located on `N` panel in `Tool` category of `3D` editor.
Another located in `Active tool and workspace settings` shelf of `Properties` editor.

Scan for props
--------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512955/866461fa-4b46-11e4-8caf-d650d15f5c5f.png
  :alt: scanprops.png

When layout is in, check for next nodes to embad them as properties:
 - A number
 - Color input
 - List Input
 - Objects in
 - Viewer BMesh

Read documentation of this nodes for getting more details about how to enable them on 3D panel.

Sorting them by label, that user defined in node tree panel or if no label, the name of the node is used.

Update all
----------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512955/866461fa-4b46-11e4-8caf-d650d15f5c5f.png
  :alt: updateall.png

Forces update of all layouts.

Clean
-----

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512954/8662fbf8-4b46-11e4-8f67-243a56c48856.png
  :alt: cleanlayout.png

Button to remove sverchok layouts, that has not users (0)

**hard clean**  - boolean flag to remove layouts even if it has users (1,2...), but not fake user (F). Fake user layout will be left.

**Clean layouts** - remove layouts. Button active only if no node tree windiw around. Better to make active layout nothing or fake user layout to prevent blender crash. Easyest way - activate your Faked user layout, on 3D press **ctrl+UP** and press button. than again **ctrl+UP** to go back. No wastes left after sverchok in scene.

Use with care.


Properties
----------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4512956/8666aeba-4b46-11e4-9c13-651e3826f111.png
  :alt: properties.png

Layouts by box. Every layout has buttons:

+--------------------+----------------------------------------------------------------------------------------+
| Button             | Function                                                                               |
+====================+========================================================================================+
| **B**              | bake this layout - will gather all layout's viewer draw and viewer text to bake them.  |
|                    | Bake only if bakeable button is active on node, else ignore.                           |
+--------------------+----------------------------------------------------------------------------------------+
| **Show layout**    | show or hide all viewers - to draw or not to draw OpenGL in window, but bmesh viewer   |
|                    | not handled for now.                                                                   |
+--------------------+----------------------------------------------------------------------------------------+
| **Animate layout** | to animate the layout (or not) - may preserve you time.                                |
+--------------------+----------------------------------------------------------------------------------------+
| **P**              | Process layout, allows safely manupilate monsterouse layouts.                          |
+--------------------+----------------------------------------------------------------------------------------+
| **D**              | Activate Draft mode                                                                    |
+--------------------+----------------------------------------------------------------------------------------+
| **F**              | Fake user of layout to preserve from removing with reloading file or                   |
|                    | with **clean layouts** button.                                                         |
+--------------------+----------------------------------------------------------------------------------------+

Import Export Panel
===================

.. image:: https://cloud.githubusercontent.com/assets/5783432/4519324/9e11b7be-4cb6-11e4-86c9-ee5e136ed088.png
  :alt: panelio.png

location: N panel of any Sverchok Tree.

Import and export of the current state of a Sverchok Tree. This tool stores

 - Node state: location, hidden, frame parent
 - Node parameters: (internal state) like booleans, enum toggles and strings
 - connections and connection order (order is important for dynamic-socket nodes)

Export
------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4519326/9e4320f6-4cb6-11e4-88ba-b6dc3ce48d5a.png
  :alt: panelexport.png

+---------+-------------------------------------------------------------------------------------------------+
| feature | description                                                                                     |
+=========+=================================================================================================+
| Zip     | When toggled to *on* this will perform an extra zip operation when you press Export. The zip    |
|         | can sometimes be a lot smaller that the json. These files can also be read by the import        |
|         | feature.                                                                                        |
+---------+-------------------------------------------------------------------------------------------------+
| Export  | Export to file, opens file browser in blender to let you type the name of the file, Sverchok    |
|         | will auto append the .json or .zip file extention - trust it.                                   |
+---------+-------------------------------------------------------------------------------------------------+

Import
------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4519325/9e2f2c40-4cb6-11e4-8b03-479a411ead3d.png
  :alt: panelimport.png

+-------------+-------------------------------------------------------------------------------------------------+
| feature     | description                                                                                     |
+=============+=================================================================================================+
| Layout name | name of layout to use, has a default but you might want to force a name                         |
+-------------+-------------------------------------------------------------------------------------------------+
| Import      | import to new layout with name (described above). Can import directly from zip file if there is |
|             | only one .json in the zip. Warning to the descerned reader, only import from zip if the source  |
|             | is trusted. If you are not sure, resist the urge and take the time to learn a little bit about  |
|             | what you are doing.                                                                             |
+-------------+-------------------------------------------------------------------------------------------------+

**Warnings**

Consider this whole IO feature experimental for the time being. You use it at your own risk and don't be surprised if certain node trees won't export or import (See bug reporting below). The concept of importing and exporting a node tree is not complicated, but the practical implementation of a working IO which supports dynamic nodes requires a bit of extra work behind the scenes. Certain nodes will not work yet, including (but not limited to) :


+-------------+---------------------------------------------------------------------------------------+
| Node        | Issue                                                                                 |
+=============+=======================================================================================+
| Object In   | the json currently doesn't store geometry but an empty shell without object           |
|             | references instead                                                                    |
+-------------+---------------------------------------------------------------------------------------+
| SN MK1      | currently this auto imports by design, but perhaps some interruption of the import    |
|             | process will be implemented                                                           |
+-------------+---------------------------------------------------------------------------------------+


**Why make it if it's so limited?**

Primarily this is for sharing quick setups, for showing people how to achieve a general result. The decision to not include geometry in the Object In references may change, until then consider it a challenge to avoid it. The way to exchange large complex setups will always be the ``.blend``, this loads faster and stores anything your Tree may reference.

**While importing I see lots of messages in the console!**

Relax, most of these warnings can be ignored, unless the Tree fails to import, then the last couple of lines of the warning will explain the failure.

**Bug Reporting**

By all means if you like using this feature, file issues in `this thread <https://github.com/nortikin/sverchok/issues/422>`_. The best way to solve issues is to share with us a screenshot of the last few lines of the error if we need more then we will ask for a copy of the `.blend`.

Groups Panel
============

Crete a node group (Monad) from selection.
It can have vectorized inputs, adding or removing sockets.
Sverchok groups is a beta feature, use a your own risk and please report bugs. Also while it is in beta old node groups may break.
`Bug reports <https://github.com/nortikin/sverchok/issues/462>`_.

Templates in menu panel of nodes area
=====================================

You can use embedded templates in Sverchok. They are stored in json folder as jsons for import to Sverchok.

.. image:: https://cloud.githubusercontent.com/assets/5783432/19623205/245bcab2-98d2-11e6-810c-ace33de8499b.gif
  :alt: templates.gif
