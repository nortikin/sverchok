Input Socket Menus
******************

Good node tree usually has most of it's "vital" parameters defined in "input"
nodes, such as "A Number", "Vector In" and so on. It's better to have separate
nodes for meaningful node parameters, because you can explicitly name them
("Building Height" instead of "Z"). But linking all inputs of all nodes to
separate input nodes and naming those nodes is tiresome process.

Sverchok allows to simplify maninpulation with such nodes, by adding buttons to
input sockets, which show a menu with options to create a new parameter node,
or to link the input to existing parameter node.

In Sverchok preferences, there is a setting named **Show input menus**, with
which you can specify if you want to use such menus. There are three options
available:

* Do not show such menus at all.
* Show the button only in cases where Sverchok thinks there is only one most
  usable option, which is to create additional node and link it to this input.
  "Vector In" and "Matrix In" nodes can be created this way. No menu will be
  shown if this option is selected, the node will be created by click on the
  button. This option is the default one.
* Show "Create Parameter" menu. If this option is selected, there will be a
  button, which opens a menu with options:

   * create new input node and link it to this socket; the node will be
     automatically named with the name of the socket.
   * create new input node and link it to this socket, but instead of direct
     link, create a pair of WiFi nodes and link input node via them;
   * link this input to one of existing parameter nodes of corresponding type;
   * link this input to existing WiFi In node.

.. image:: https://user-images.githubusercontent.com/284644/97737935-811bd680-1aff-11eb-9175-097bb8d6aeaa.png

The menu has a search box, so you can select an option by typing in a part of
it's title.

**Create new parameter** option creates a new parameter node ("A number",
"Vector In" or other, depending on a socket type), and links it to the input.
New node will be automatically given a label equal to the name of the socket.
If the socket has associated parameter, then the value of this parameter will
be copied to the newly created node.

**Create new parameter via WiFi** option is similar, but additionally it
creates a pair of linked "WiFi In" - "WiFi Out" nodes between the parameter
node and existing node. This can be useful in large node trees.

**Link to parameter Node** option just creates a link between existing
parameter node and this input.

**Link to WiFi Node** option links this input to existing "WiFi Out" node. This
option is only shown if there already is a "WiFi Out" node linked to some other
input of the same node.

Some specific nodes can provide additional entries in this menu.

