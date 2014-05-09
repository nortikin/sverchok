## Scripted Node (Generator)

aka Script Node or SN. (iteration 1)

- Introduction
- Features
- Examples
- Limitations
- Future

### Introduction

When you want to express an idea in written form, if the concept is suitable for a one line Python expression then you can use the Formula nodes. They require little setup just [plug and play](). However, they are not intended for multi-line python statements, and sometimes that's exactly what you want.

ScriptNode (SN) allows you to write multi-line python programs, it's possible to use the node as a Sandbox for writing full nodes. The only real limitation will be your Python Skills. It's a prototype so bug reports are welcome.

### Features

allows:
- Loading/Reloading scripts currently in TextEditor
- imports and aliasing, ie anything you can import from console works in SN
- nested functions and lambdas
- named inputs and outputs
- named operators (buttons to action something upon button press)

At present all scripts for SN must (strict list - general): 
- have 1 `sv_main` function as the main workhorse
- `sv_main` must take 1 or more arguments (even if you don't use it)
- all function arguments for `sv_main` must have defaults.
- each script shall define 'in_sockets' and 'out_sockets'
- TextEditor has automatic `in_sockets` list creation (`Ctrl+I -> Generate in_sockets`) when the key cursor is over `sv_main`.
- 'ui_operators' is an optional third output parameter

#### `in_sockets`

```python
in_sockets = [
    [type, 'socket name on ui', input_variable],
    [type, 'socket name on ui 2', input_variable2],
    # ...
]
```

#### `out_sockets`

```python
out_sockets = [
    [type, 'socket name on ui', output_variable],
    [type, 'socket name on ui 2', output_variable2],
    # ...
]
```

#### `in_sockets and out_sockets`

- Each `"socket name on ui"` string shall be unique.
- `type` are currently limited to
   - 's' : floats, ints, edges, faces
   - 'v' : vertices, vectors
   - 'm' : matrices

#### `ui_operators`

```python
ui_operators = [
    ['button_name', func1]
] 
```
Here `func1` is the function you want to call when pressing the button.

#### `return`

Simple, only two flavours are allowed at the moment.
```python
return in_sockets, out_sockets
# or
return in_sockets, out_sockets, ui_operators
```

### Examples

The best way to get familiarity with SN is to go through the templates folder. They are intended to be lightweight and educational, but some of them will show
advanced use cases. The [thread on github]() may also provide some pictorial insights and animations.

Sverchok includes a plugin in TextEditor which conveniently adds `sv templates` to the Templates menu.


### Future
SN iteration 1 is itself a prototype and is a testing ground for iteration 2.
