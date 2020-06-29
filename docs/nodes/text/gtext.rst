GText
=====

This node is designed to allow to to make single or multi-line annotations using a mostly single-stroke monospaced font. This default font is similar to the ISO standard fonts available in CAD packages. Currently the node is limited to only one font family and one weight.


Functionality
-------------

Creates Text in NodeView using GreasePencil strokes. 
It has full basic English and Cyrillic Character map and several extended character types::

    [ ] \ / ( ) ~ ! ? @ # $ % & ^ > < | 1234567890 - + * = _



The workflow
------------

1. Write your comment in a text editor or blender's TextEditor and copy the desired text to the system clipboard. (Ctrl+C, or the mac equivalent) 
2. Use the icon-button that should the Clipboard and an array pointing away from it. 
3. - setting the colour can be done from the nodeview UI
   - setting the line height and character scale can be done from the NPanel in the Node Item panel. 


UI & Parameters
---------------

**Node UI**

+------------+---------------------------------------------------------------------------------+
| Parameter  | Function                                                                        |
+============+=================================================================================+
| Set        | If clipboard has text, then Set will display that text beside the GText node.   |
+------------+---------------------------------------------------------------------------------+
| Clear      | This erases the GreasePencil strokes                                            |
+------------+---------------------------------------------------------------------------------+

GText Node will display the context of the clipboard after pressing the `Set` button. If no text is found in the clipboard
it will write placeholder 'your text here'.

**N-panel**

+---------------------+-------------------------------------------------------------------------------------------------+
| Parameter           | Function                                                                                        |
+=====================+=================================================================================================+
| Get from Clipboard  | Gets and sets in one action, takes text from clipboard and writes to NodeView with GreasePencil |
+---------------------+-------------------------------------------------------------------------------------------------+
| Thickness           | sets pixel width of the GreasePencil strokes                                                    | 
+---------------------+-------------------------------------------------------------------------------------------------+
| Font Size           | Scales up text and line-heights                                                                 |
+---------------------+-------------------------------------------------------------------------------------------------+
| Relative Line Height| adds "leading" between lines                                                                    |
+---------------------+--------------------------------------------------------------------------------------------------

**Moving GText**

To move GText strokes around in NodeView you must move the GText Node then press Set again. This may not be entirely intuitive but it hasn't bugged us enough to do anything about it.


Outputs
-------

Outputs only to NodeView
