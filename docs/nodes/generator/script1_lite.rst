Script Node Lite
================

Functionality
-------------

This node allows the user to write arbitrary node logic in Python. It is useful
when there is no standard node in Sverchok for your particular purpose; you may
want to use this if you want some complex piece of logic to be used in a couple
of your own projects, or if you are prototyping a new standard node for
Sverchok itself.

The script node implementation is intended for quick, non serious, experimentation.

Features
--------

- easy template importing directly to node, or to text block (the latter is useful for making changes to a template before loading... 
as is needed with the ``custom_draw_complex`` example )

.. image:: https://cloud.githubusercontent.com/assets/619340/25421401/ff29eed2-2a5c-11e7-9594-f85295178f57.png

- doesn't force an output socket, but an input socket is expected (else how does it update?!)
- does allow you to set some defaults : numbers, and lists of stuff
- does allow you to set the level of nestedness; means you don't need to unwrap/index stuff via code
- does allow you to declare an override to the node's draw_button function, well... think of it more like an ``append`` to the draw code. There's an example of how you might make a light weight Curve mapping node by using the ui component of a RGB curve from a material node tree. it's a little convoluted, but it's usefulness musn't be dismissed.
- has the option to **auto inject** the list of variable references as **parameters** much like javascript does for **arguments** inside a function. In essence implemented like this ::

    parameters = eval("[" + ", ".join([i.name for i in self.inputs]) + "]")


To enable this feature add the word "inject" on its own line in the header. If you have 3 input sockets, called ``radius, amplitude, num_verts``,  then the variable ``parameters`` will be ::

    parameters = [radius, amplitude, num_verts]

This is handy for inner functions that are arranged to take arguments in exactly that order. See <https://github.com/nortikin/sverchok/issues/942#issuecomment-264705956>_ for an example use. Usually you'll use the 'vectorize' function with this to zip through each pair of arguments. see https://github.com/nortikin/sverchok/issues/942#issuecomment-263912890

- added a helper function ``from sverchok.utils.snlite_utils import vectorize`` , and this is made available to scripts without the need to import it now. Also see https://github.com/nortikin/sverchok/issues/942#issuecomment-263912890

- added an include directive::

    """
    ...
    include <your_text_name>
    """

The include directive ensures the dependency is also stored in the gist when exported as json. The file named in angle brackets must be present in the current .blend file's text blocks.

- added two (semi) customizable enums to make the custom draw a bit more useful, called **self.custom_enum** and **self.custom_enum_2**. No spaces in the elements, yes spaces between the elements.::

    """
    enum = word1 word2 word3
    enum2 = raw clean
    """
you make them visible on the ui by doing::

    def ui(self, context, layout):
        layout.prop(self, 'custom_enum', expand=True)
        layout.prop(self, 'custom_enum_2', expand=True)

in your code you might use them this way::

    if self.custom_enum_2 == "clean":        
        v_out, f_out = join_tris(b_verts, rawdata[1], params)
    else:
        v_out = b_verts
        f_out = rawdata[1]

see a working script: https://github.com/nortikin/sverchok/pull/3455

- add ``ddir`` (a dunderless dir() function) to local namespace.  ``ddir(object, filter_str="some_string")`` . filter_str is optional::

    def ddir(content, filter_str=None):
        vals = []
        if not filter_str:
            vals = [n for n in dir(content) if not n.startswith('__')]
        else:
            vals = [n for n in dir(content) if not n.startswith('__') and filter_str in n]
        return vals

- There are several aliases provided so they don't need to be imported manually::

     bmesh_from_pydata
     pydata_from_bmesh
     ddir
     np
     bpy
     vectorize

- add operator callback. See: https://github.com/nortikin/sverchok/issues/942#issuecomment-300162017 ::

   """
   in verts v
   """

   def my_operator(self, context):
       print(self, context, self.inputs['verts'].sv_get())
       return {'FINISHED'}

   self.make_operator('my_operator')

   def ui(self, context, layout):
       cb_str = 'node.scriptlite_custom_callback'
       layout.operator(cb_str, text='show me').cb_name='my_operator'

- `statefull` (like Processing's setup() ):  see this `Reaction Diffusion thread / example <https://github.com/nortikin/sverchok/issues/1734#issuecomment-313844934>`_.
- 'reloading / imports' :  see `importlib example here <https://github.com/nortikin/sverchok/issues/1570>`_, this is especially useful for working with more complex code where you define classes outside of the snlite main script.

Syntax
------

The syntax might look something like this::

    """   (tripple quote marks to demark the header)
    in socketname  type  default=x nested=n
    in socketname2 type  default=x nested=n
    out socketname type  # (optional)
    """
    < any python code >

This tripple quoted area (a "directive comment", or *header*) must be the first thing in the ``.py`` file.  It helps declare sockets and defaults and is a space to enable certain options (more about this later). The above example header can be written slightly less verbose::

    """
    in socketname   type  d=x n=i
    in socketname2  type  d=x n=i
    out socketname  type
    """
    < any python code >
    ```

A few things to notice:
 - i've dropped the words ``default`` and ``nested`` in favour or ``d`` and ``n``, but you'll also see examples where I just write  ``in socketname type .=200 .=2``  , the ``d`` and ``n`` don't mean anything, the only real requirement there is that there's a single character directly to the left of the ``=``.
 - Socket names will be injected into the local scope, for example:
    - if you have an input socket called 'normals', then there will be a variable called normals available to read from.
    - if you have an output socket called 'edges_out', then that variable is also automatically available for you to insert data into - behind the scene snlite will do `edges_out = []` prior to executing your code. At the end of your code SNLite will read whatever the content of your `edges_out` is and use that as the output values for that socket.

- **inputs**::

    direction    socketname     sockettype     default     nestedness
    in           radius         s              .=1.2       .=2

- `direction` ``in`` means "make an input".
- `socketname` means "give this socket a name / identifier"
- `sockettype` declares what kind of socket is to be used. The supported types are:
        - Vertices (``v``)
        - Strings/Lists (``s``)
        - Matrices (``m``)
        - Curves (``C``)
        - Surfaces (``S``)
        - Solids (``So``)
        - Scalar fields (``SF``)
        - Vector fields (``VF``)
        - Objects (``o``)
        - File Path (``FP``)
- `default` is where you give a default initialization value. A list, tuple, float, or int..
        - **warning**:  don't include any spaces in the iterables - this will break parsing
- `nestedness` deserves some explanation. In sverchok every data structure is nested in some way.

Some familiarity with python or the concept of sublists (lists of lists) is needed to understand this. It's harder to explain than to use.

.. image:: https://cloud.githubusercontent.com/assets/619340/23399114/639cdc34-fd9f-11e6-8aa2-0238f2020373.png


- `n=2` means ``named_input.sv_get()[0][0]`` - means you only want a single value. ::

            named_input = [[20, 30, 40], .....]  #  or  [[20]]
            value_to_use = named_input[0][0]  # 20

- `n=1` means ``named_input.sv_get()[0]``
            -  You would use `n=1` if you only ever plan to work with the first incoming sublist. This will essentially ignore the rest of the incoming data on that socket.
- `n=0` means ``named_input.sv_get()``
            - Generally you would use this if you plan to do something with each sublist coming in, for example if the input contains several lists of verts like here:

.. image:: https://cloud.githubusercontent.com/assets/619340/20454350/d1c8861e-ae3e-11e6-9de6-501f07a58606.png


- **outputs**::

    direction    socketname     sockettype
    out          verts          v

- `direction` ``out`` means "make an output".
- `socketname` means "give this socket a name / identifier"
- `sockettype` declares what kind of socket: Vertices (v), Strings/Lists (s), Matrices (m), Objects (o)

    There's no _default_ or _nested_ value for output sockets, generally speaking the default inputs will suffice to generate a default outputs.

Learn by example, the best way to get a feel for what works and doesn't is to have a look at the existing examples in several places:

 - this thread:  https://github.com/nortikin/sverchok/issues/942
 - in ``node_scripts/SNLite_templates``
 - the ``draw_buttons_ext`` (Right side panel of the NodeView -> Properties)

The templates don't have much defensive code, and some nodes that expect input
will turn _red_ until they get input via a socket. You can add code to defend
against this, but I find it useful to be notified quickly if the input is
unexpected, the node will gracefully fail.

Inputs / Outputs
----------------

All inputs and outputs of this node are defined in the script.

Parameters
----------

This node has two states:

1. When no script is loaded, it shows:

   * a drop-down box, where you have to select a Blender's text block with script text;
   * and a "Plug" button.

   When you select the script and press "Plug", the script is loaded, and the node changes it's appearance.


2. When a script is loaded, the node displays all inputs and parameters defined by the script; Additionally, the following buttons are shown:

   * **Animate Node**. When checked, the node is updated during animation playback, on each frame change event.
   * **Update Node**. Click this to manually trigger execution of the node.
   * **Reload**. Click this to parse and load the script text again - this makes sense if you've changed the script.
   * **Clear**. Reset the node to the state when no script was loaded, so you will be able to select another script.

Examples of usage
-----------------

Please refer to the initial thread: https://github.com/nortikin/sverchok/issues/942.

In the N panel of the node there is a drop-down menu allowing you to select one
of example scripts which are distributed with Sverchok.
