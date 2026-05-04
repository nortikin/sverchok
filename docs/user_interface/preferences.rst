***********
Preferences
***********

Sverchok preferences are located in general Blender preferences dialog (Edit ->
Preferences). Select **Add-ons** tab in the left pane, and then unroll
**Sverchok** roll (you can use the search bar in the top area of preferences
dialog, if you have many add-ons).

Sverchok preferences are organized into several tabs.

General
=======

.. image:: https://github.com/user-attachments/assets/e1b1673c-cd08-410e-8e73-8dbc9a03fbdf
  :target: https://github.com/user-attachments/assets/e1b1673c-cd08-410e-8e73-8dbc9a03fbdf

Menu Presets
------------

There are a lot of nodes in Sverchok, so the "Add Node" menu (Shift-A) is quite
big. The structure of this menu can be discussed; different people suggested
different variants over the time. Current default structure is what we had
historically. However, one can customize it.

Under **General** tab of Sverchok preferences, there are the following parameters:

* **Preset**. Select a preset of menu structure to be used. The following options are available:

  * **Default (index.yaml)**. The default menu preset.
  * **full_by_data_type.yaml (built-in)**. Alternative menu structure, in which
    nodes are organized according to main type of data with which they are
    dealing: Mesh, Curves, Surfaces and so on. This variant uses more nested
    menu structures than the default one.
  * **full_nortikin.yaml (built-in)**. Another alternative menu structure, by Nortikin.
  * Other options are available if you have custom menu presets. You can make a
    menu preset by copying one of ``*.yaml`` files from Sverchok distribution
    (see ``menus/`` directory), putting it into ``datafiles/sverchok/menus``
    directory under your Blender settings directory (for example,
    ``~/.config/blender/4.4/datafiles/sverchok/menus/`` on Linux) and editing
    according to your wishes. Note that when nodes are added, removed or
    changed in Sverchok distribution, you will have to manually update your
    custom menu preset. On the other hand, in your custom preset you do not
    have to have all Sverchok nodes listed - only those which you are actually
    using; so your custom menu can be smaller and thus easier to use. If you
    think your preset is good, please consider contributing it into Sverchok
    distribution; then Sverchok developers will maintain it.

* **Preset application mode**. The following options are available:

  * **Use preset file**. Sverchok will directly use the selected preset file
    from Sverchok distribution. This is the default option.
  * **Use local copy of preset file**. Sverchok will create a copy of selected
    preset file in your ``datafiles/sverchok/menus`` directory and use that copy. You
    may edit that local copy manually if you wish. Note again that in such case
    you will have to manually update the preset file when nodes are added into
    Sverchok (or you can remove that edited file, so that Sverchok will
    overwrite it with a fresh copy from it's distribution).

Export to Gist
--------------

Sverchok allows you to export your node tree setups to .json file, to be
imported again. If you want, you may share it by use of any pastebin service,
or by use of github's gist service.

To share your node trees, Sverchok has a function to automatically post
exported json to gist.github.com service. This is a very nice and widely used
feature, but since some time GitHub requires authentication for gist creation.
Thus, to use this feature, you have to

* get GitHub account
* set up your GitHub account to enable automate gists creation
* set up Sverchok to tell it about your GitHub account.

For more details, please visit `Wiki page <https://github.com/nortikin/sverchok/wiki/Set-up-GitHub-account-for-exporting-node-trees-from-Sverchok>`_.

This section contains the following parameters:

* **GitHub API token**. The token to be used to access your GitHub accout to publish gists.

Other
-----

* **Frame change handler**. This defines the moment when exactly Sverchok node
  trees are re-evaluated when Blender frame is changed. The available options
  are:

  * **Pre** - re-evaluate node trees before frame change.
  * **Post** - re-evaluate node trees after frame change. This option is the default one.
  * **None** - do not automatically re-evaluate node trees on frame change.

Development
-----------

This section contains parameters which are useful if you want to develop or debug Sverchok.

* **Developer mode**. If this parameter is checked, then there are some
  additional options available in Sverchok GUI, useful for Sverchok developers.
  Unchecked by default.
* **Ext Editor**: a system command for Sverchok to use to launch text editor,
  when you press the **Externally** button under **Edit Source** in the node's
  N panel. For example, ``notepad`` or ``kate``. If you are not going to edit
  node sources, you do not have to fill this setting.
* **Src Directory**. Path to Sverchok sources directory. If you are not going
  to edit node sources, you do not have to fill this setting.

Logging
-------

This section defines where Sverchok writes logs about what it does, and how
complete should be those logs. Such logs are very useful when trying to locate
errors in your node trees or in Sverchok itself.

* **Logging level**. This defines which events are to be logged. The available options are:

  * **Debug**. Log all events, including debug messages.
  * **Information**. Log informational messages, warnings and errors, but do
    not write debug messages. This is the default option.
  * **Warnings**. Write only warnings and errors.
  * **Errors**. Write error messages only.

* **Log exception stacks**. If checked, then for each logged error Sverchok
  will also write it's Python traceback flag into log. Such tracebacks can help
  Sverchok developers to understand the cause of error. Unchecked by default.
  This flag is not visible when **Logging level** is set to Debug, because with
  Debug level exception stacks are always logged.
* **Log to text buffer**. If checked, Sverchok will write log into text buffer
  within current Blender file. The name of that buffer is specified in the
  **Buffer name** parameter (the default is ``sverchok.log``).
* **Clear buffer at saving file**. If checked, text buffer with log will be
  cleared when you are saving Blender file. Without that, the file may grow
  very big due to large amount of text in the log buffer. But you may clear
  that buffer manually if you want. Checked by default.
* **Log to file**. If checked, Sverchok will write the log into file on disk.
  The path to log file is specified in the **File Path** parameter. By default,
  log file is located in your Blender settings directory, under
  ``datafiles/sverchok/sverchok.log``. By default, logs are not written to file.
* **Log to console**. If checked, log events will be written to Blender's
  standard output (system console). Note that events about Sverchok
  initialization are always written to console. Checked by default.

Node Defaults
=============

.. image:: https://github.com/user-attachments/assets/736bb5a5-3a9e-4735-a282-219ea8947d48
  :target: https://github.com/user-attachments/assets/736bb5a5-3a9e-4735-a282-219ea8947d48

This tab contains default settings for some specific nodes:

* **Stethoscope** / **scale**. Scale of text which **Stethoscope** node writes in
  the node editor. The default value is 1.0.
* **Index Viewer** / **scale**. Scale of text which **Index Viewer** node
  writes in 3D view. The default value is 1.0.

Extra Nodes
===========

.. image:: https://github.com/user-attachments/assets/0d7f853d-4b8f-4e87-83c9-4f75f2e4c105
  :target: https://github.com/user-attachments/assets/0d7f853d-4b8f-4e87-83c9-4f75f2e4c105

Sverchok can use several external libraries, that provide some mathematical or
other functions. We call such libraries "Dependencies". When these libraries
are available, you will be able to use much more nodes in Sverchok. If you do
not need all these features, you can skip installation of dependencies, or
install only some of them.

One thing you will have to install anyway if you want to use these external
libraries is `pip <https://pypi.org/project/pip/>`_. All libraries are installed with it.

You can find more information about dependencies on the `Dependencies wiki page
<https://github.com/nortikin/sverchok/wiki/Dependencies>`_.

This tab contains a list of dependency libraries that can be used by Sverchok.
For each library, it is indicated whether it is installed or not; there is a
button to visit library's website. For each package that can be installed by
**pip**, there is **Install with PIP** button.

Theme
=====

.. image:: https://github.com/user-attachments/assets/0b05e780-6965-4c41-9d3b-8e6923e5285e
  :target: https://github.com/user-attachments/assets/0b05e780-6965-4c41-9d3b-8e6923e5285e

This tab allows you to configure colors which are assigned to different types
of nodes by default.

