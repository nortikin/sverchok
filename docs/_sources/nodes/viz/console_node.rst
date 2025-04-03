Console Node
============

.. image:: https://user-images.githubusercontent.com/14288520/190504102-78b69377-4f18-4b10-b085-c6e14691e0ca.png
  :target: https://user-images.githubusercontent.com/14288520/190504102-78b69377-4f18-4b10-b085-c6e14691e0ca.png

This is a developer's node. You probably have no reason to use it, and you should not count on its presence. This node is used to better understand shader fragment and what our options are to display text with a background.

Fortunately along the way the node has acquired some useful features, albeit cosmetic.

This node can syntax highlight incoming string data. At the moment it can display 

- Python syntax (or any C like lexicon)
- randomly coloured chars (this is a debug state..)
- no syntax highlighting, useful for seeing stuff quickly.

It is possible to display only the last n lines, and in ScriptNode mode it will display the 
**script_str** associated with the ScriptNode lite node directly linked to the node.

There is a mode that will automatically cut ultra long lines from being displayed.

