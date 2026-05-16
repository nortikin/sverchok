# EisenScript Grammar Reference

EisenScript is a procedural geometry scripting language based on L-systems.
It defines rules that recursively transform and branch geometric primitives
into complex structures (fractals, trees, architectural forms, etc.).

---

## Table of Contents

1. [Lexical Conventions](#lexical-conventions)
2. [EBNF Grammar](#ebnf-grammar)
3. [Language Elements](#language-elements)
   - [Program Structure](#program-structure)
   - [Define Directives](#define-directives)
   - [Set Statements](#set-statements)
   - [Rule Definitions](#rule-definitions)
   - [Branches](#branches)
   - [Repetitions](#repetitions)
   - [Transformations](#transformations)
   - [Values](#values)
   - [Expressions](#expressions)
   - [Rule References](#rule-references)
   - [Primitives](#primitives)
4. [Reserved Keywords](#reserved-keywords)
5. [Scoping Rules](#scoping-rules)
6. [Examples](#examples)

---

## Lexical Conventions

| Token | Pattern | Examples |
|-------|---------|----------|
| **IDENTIFIER** | `[a-zA-Z_][a-zA-Z0-9_]*` | `r1`, `my_rule`, `a`, `maxdepth` |
| **INTEGER** | `-?(0\|[1-9][0-9]*)` | `0`, `42`, `-10` |
| **FLOAT** | `INTEGER(\.[0-9]*)?([eE][+-]?[0-9]*)?(/\s*INTEGER(\.[0-9]*)?)?` | `3.14`, `-1.5e2`, `1/3` |
| **COLOR** | `#[0-9a-fA-F]{3,8}` or `'...'` or SVG keyword | `#FF0000`, `red`, `'darkgreen'` |
| **WHITESPACE** | Space, tab, newline | — |
| **COMMENTS** | `// line comment` or `/* block comment */` | — |

Case sensitivity: keywords and identifiers are case-sensitive.
`box` is a primitive; `Box` is not recognized.

---

## EBNF Grammar

```ebnf
(* ── Program ───────────────────────────────────────────── *)
program       ::= (define_stmt | set_stmt | rule_def | bare_branch)*

(* ── Define ────────────────────────────────────────────── *)
define_stmt   ::= '#define' IDENTIFIER (number | expression)

(* ── Set statement ─────────────────────────────────────── *)
set_stmt      ::= 'set' setting_name setting_value
setting_name  ::= IDENTIFIER
setting_value ::= number | COLOR | 'initial' | 'random'

(* ── Rule definition ───────────────────────────────────── *)
rule_def      ::= 'rule' IDENTIFIER param_list? modifier* '{' rule_body '}'
param_list    ::= '(' identifier_list? ')'
identifier_list ::= IDENTIFIER {',' IDENTIFIER}
modifier      ::= ('maxdepth' | 'md') value ('>' IDENTIFIER)?
              | ('weight' | 'w') value
rule_body     ::= branch*

(* ── Implicit rule (shorthand) ─────────────────────────── *)
implicit_rule ::= IDENTIFIER param_list? branch
(* Creates: rule IDENTIFIER(params) { branch } *)

(* ── Bare branch (implicit start rule) ─────────────────── *)
bare_branch   ::= branch
(* Creates: rule ###START### { branch } *)

(* ── Branch ────────────────────────────────────────────── *)
branch        ::= (repetition | transform_block)* (rule_ref | primitive)

(* ── Repetition ────────────────────────────────────────── *)
repetition    ::= count '*' '{' transformation+ '}'
count         ::= INTEGER | IDENTIFIER | expression

(* ── Transformation block (no count) ───────────────────── *)
transform_block ::= '{' transformation+ '}'

(* ── Transformations ───────────────────────────────────── *)
transformation::= translate | rotate | mirror | scale | matrix
              | hue_shift | saturation | brightness | alpha
              | set_color | blend_color

translate     ::= ('x' | 'y' | 'z') value
rotate        ::= ('rx' | 'ry' | 'rz') value
mirror        ::= 'fx' | 'fy' | 'fz'
scale         ::= 's' value {value value}    (* 1, 2, or 3 values *)
matrix        ::= 'm' value{9}               (* exactly 9 values *)
hue_shift     ::= ('h' | 'hue') value
saturation    ::= 'sat' value
brightness    ::= ('b' | 'brightness') value
alpha         ::= ('a' | 'alpha') value
set_color     ::= 'color' COLOR
blend_color   ::= 'blend' COLOR value

(* ── Values ────────────────────────────────────────────── *)
value         ::= number | variable_ref | expression
number        ::= INTEGER | FLOAT
variable_ref  ::= IDENTIFIER
(* IDENTIFIER must NOT be a reserved transformation keyword
   (see Reserved Keywords section).  Use expression syntax
   (a) to reference a variable with a keyword name. *)

(* ── Expression ────────────────────────────────────────── *)
expression    ::= '(' python_expr ')'
python_expr   ::= any valid Python expression
(* Evaluated with eval() using a safe namespace:
   all math module functions, e/pi, abs, round, min, max, pow, tuple, list,
   and #define variables. *)

(* ── Rule reference ────────────────────────────────────── *)
rule_ref      ::= retirement? IDENTIFIER arg_list?
retirement    ::= 'md' value ('>' IDENTIFIER)?
arg_list      ::= '(' arg_list_items? ')'
arg_list_items::= value {',' value}

(* ── Primitives ────────────────────────────────────────── *)
primitive     ::= 'box' | 'grid' | 'sphere' | 'line' | 'point'
              | 'Triangle' '[' coord {';' coord} ']'
coord         ::= FLOAT {',' FLOAT}
```

---

## Language Elements

### Program Structure

A program is a sequence of top-level statements:

```
#define a 3.14
set maxdepth 100
rule r1 { {x 1} box }
r1
```

Statements are processed in order.  Multiple bare branches at the top
level are merged into a single implicit start rule (`###START###`).

### Define Directives

`#define` declares a named constant available throughout the program:

```
#define radius 5
#define angle (360 / n)
```

**Values** may be:
- **Numbers**: `3.14`, `100`, `1/3`
- **Expressions**: `(a + b * 2)`, `(sin(theta))`

**Evaluation** is lazy and supports forward references.  If `a` depends on
`b` and `b` depends on `c`, the resolver topologically sorts dependencies
and evaluates in order.  Cycles raise `CyclicDefineError`.

**Scoping**: `#define` variables are global but can be shadowed by
rule parameters (see [Scoping Rules](#scoping-rules)).

### Set Statements

`set` configures global interpreter behavior:

```
set maxdepth 100
set maxobjects 10000
set minsize 0.01
set seed 42
set background #FFFFFF
set color random
```

Known settings: `maxdepth`, `maxobjects`, `minsize`, `maxsize`,
`seed`, `background`, `color`, `colorpool`.

### Rule Definitions

A rule maps a name to one or more branches:

```
rule r1 maxdepth 10 weight 2 {
    {x 1} r1
    {s 0.5} box
}
```

**Components**:

| Component | Syntax | Description |
|-----------|--------|-------------|
| Name | `IDENTIFIER` | Rule identifier |
| Parameters | `(p1, p2, ...)` | Optional parameter list (identifiers) |
| maxdepth | `maxdepth N` or `md N` | Max recursion depth for this rule |
| Retirement | `> successor` | Rule to substitute when maxdepth reached |
| Weight | `weight W` or `w W` | Selection weight for ambiguous rules |
| Body | `{ branch* }` | One or more branches |

**Parameterized rules** allow dynamic behavior:

```
rule branch(angle, length) {
    {rz angle s length 1 1} box
}
branch(30, 5)
```

Parameters shadow `#define` variables with the same name within the
rule body (see [Scoping Rules](#scoping-rules)).

**Implicit rules** (shorthand without `rule` keyword):

```
my_rule(w, h)
{s w h 1} box
```

Equivalent to: `rule my_rule(w, h) { {s w h 1} box }`

### Branches

A branch is a sequence of repetitions/transformation blocks followed by
a terminal (rule reference or primitive):

```
3 * {rz 120} 2 * {x 1} box
{rz 90 s 0.8} r1
box
```

**Structure**: `(repetition | transform_block)* terminal`

| Part | Syntax | Description |
|------|--------|-------------|
| Repetition | `N * { transforms }` | Apply transforms N times cumulatively |
| Transform block | `{ transforms }` | Apply transforms once (count = 1) |
| Terminal | `rule_ref` or `primitive` | What to emit at the end |

Transformations within a branch are applied **right-to-left** (like
function composition).  In repetitions, each iteration accumulates
the transformation matrix.

### Repetitions

`N * { transformations... }` applies the transformations `N` times,
accumulating the matrix:

```
5 * {x 1 rz 72} box
```

Produces 5 copies, each translated by 1 unit and rotated by 72° more
than the previous.  The count can be:

- **Integer**: `5 * {x 1} box`
- **Variable**: `n * {x 1} box` (resolved from `#define`)
- **Expression**: `(n * 2) * {x 1} box`

### Transformations

Transformations are applied inside `{...}` blocks.  They modify the
current transformation matrix.

#### Geometrical

| Syntax | Effect |
|--------|--------|
| `x <v>` | Translate along X by `v` |
| `y <v>` | Translate along Y by `v` |
| `z <v>` | Translate along Z by `v` |
| `rx <v>` | Rotate about X axis by `v` degrees |
| `ry <v>` | Rotate about Y axis by `v` degrees |
| `rz <v>` | Rotate about Z axis by `v` degrees |
| `s <v>` | Uniform scale by `v` |
| `s <v1> <v2>` | Scale X by `v1`, Y by `v2`, Z by `v1` |
| `s <v1> <v2> <v3>` | Scale X, Y, Z by `v1`, `v2`, `v3` |
| `m <f1> ... <f9>` | Apply 3×3 matrix (row-major, 9 values) |
| `fx` | Mirror about X axis |
| `fy` | Mirror about Y axis |
| `fz` | Mirror about Z axis |

#### Color

| Syntax | Effect |
|--------|--------|
| `h <v>` / `hue <v>` | Shift hue by `v` degrees (wraps 0–360) |
| `sat <v>` | Multiply saturation by `v` (clamped 0–1) |
| `b <v>` / `brightness <v>` | Multiply brightness by `v` (clamped 0–1) |
| `a <v>` / `alpha <v>` | Multiply alpha by `v` (clamped 0–1) |
| `color <c>` | Set absolute color to `c` |
| `blend <c> <v>` | Blend with color `c` at strength `v` |

Color transformations affect the color of emitted primitives but do
not affect geometry.

### Values

A **value** is one of:

| Type | Syntax | Example |
|------|--------|---------|
| Number | `INTEGER` or `FLOAT` | `3`, `3.14`, `1/3`, `-1.5e2` |
| Variable | `IDENTIFIER` | `a`, `radius` |
| Expression | `(python_expr)` | `(a + b)`, `(sin(theta))` |

**Keyword restriction**: identifiers that match transformation keywords
(`x`, `y`, `z`, `rx`, `ry`, `rz`, `s`, `m`, `fx`, `fy`, `fz`,
`h`, `hue`, `sat`, `b`, `brightness`, `a`, `alpha`, `color`, `blend`)
are **not** accepted as variable references in value positions.  This
avoids ambiguity in parsing:

```
s 0.9 x 1    →  Scale(0.9) then Translate(x, 1)    (not Scale(0.9, x, 1))
```

To use a variable whose name matches a keyword, wrap it in an expression:

```
s (x) (y) 1  →  Scale(x, y, 1)  where x and y are variables
```

This restriction applies only inside `{...}` transformation blocks.
Parameter names and rule call arguments may use any identifier.

### Expressions

Parenthesized Python expressions provide computed values:

```
{x (a + b * theta)} box
#define scale (base * 0.9)
(n * 2) * {rz (360 / n)} box
```

**Safe namespace** for `eval()`:

| Category | Contents |
|----------|----------|
| Math functions | `sin`, `cos`, `tan`, `sqrt`, `pow`, `log`, `exp`, `floor`, `ceil`, `fabs`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `radians`, `degrees`, `hypot`, `isfinite`, `isinf`, `isnan`, `copysign`, `fmod`, `frexp`, `ldexp`, `modf`, `trunc`, `perm`, `comb`, `gcd`, `lcm`, `erf`, `erfc`, `gamma`, `lgamma`, `dist`, `prod`, `factorial` |
| Math constants | `pi`, `e` |
| Built-ins | `abs`, `round`, `min`, `max`, `pow`, `tuple`, `list` |
| Define vars | All `#define` variables (filtered to exclude conflicts with above) |

**Errors**:
- `SyntaxError` — invalid Python syntax
- `ValueError` — undefined variable at runtime
- `CyclicDefineError` — circular dependency between `#define` variables

### Rule References

A rule reference invokes another rule:

```
r1                              (* plain call *)
r1(3, 5)                        (* with arguments *)
r1(a, (b + 1))                  (* mixed arguments *)
md 10 r1                        (* with retirement depth *)
md 10 > leaf r1                 (* with retirement depth and successor *)
```

**Argument matching**: the number of arguments must match the number of
parameters in every definition of the called rule.  Mismatch raises
`ValueError` at interpretation time.

**Ambiguity**: if a rule has multiple definitions (same name), one is
chosen at random weighted by the `weight` modifier.  All definitions
must have the same parameter count.

### Primitives

Primitives are the geometric shapes emitted by the interpreter:

| Primitive | Description |
|-----------|-------------|
| `box` | Solid cube centered at origin |
| `grid` | Wireframe cube (edges only) |
| `sphere` | Sphere centered at origin |
| `line` | Line segment along X axis |
| `point` | Single point at origin |
| `Triangle[v1;v2;v3]` | Custom triangle with explicit vertices |

**Triangle syntax**:

```
Triangle[0,0,0; 1,0,0; 0.5,1,0]
```

Vertices are `(x, y, z)` triples separated by `;`.  Missing Y or Z
defaults to `0.0`.

---

## Reserved Keywords

The following identifiers are reserved as transformation keywords and
**cannot** be used as variable references in value positions inside
`{...}` blocks:

| Category | Keywords |
|----------|----------|
| Translation | `x`, `y`, `z` |
| Rotation | `rx`, `ry`, `rz` |
| Scale | `s` |
| Matrix | `m` |
| Mirror | `fx`, `fy`, `fz` |
| Hue | `h`, `hue` |
| Saturation | `sat` |
| Brightness | `b`, `brightness` |
| Alpha | `a`, `alpha` |
| Color | `color`, `blend` |

Additionally, the following are reserved as structural keywords:
`rule`, `set`, `md`, `maxdepth`, `weight`, `w`, `#define`.

**Workaround**: use expression syntax `(name)` to reference a variable
with a keyword name: `s (x) (y) 1`.

---

## Scoping Rules

Variable resolution follows this priority (highest to lowest):

1. **Rule parameters** — parameters of the current rule definition
2. **Define variables** — `#define` directives at program level

When a rule is called with arguments, the arguments are bound to the
parameter names, creating a local scope:

```
#define val 100
rule r(val) {
    {s val 1 1} box    (* val = argument, not 100 *)
}
r(5)                   (* produces box scaled by 5 *)
```

Nested rule calls create nested scopes.  Inner parameters shadow outer
parameters with the same name:

```
rule inner(sx) {
    {s sx 1 1} box
}
rule outer(sx) {
    inner(99)          (* inner's sx = 99, not outer's sx *)
}
outer(5)               (* produces box scaled by 99 *)
```

---

## Examples

### Simple tree

```
set maxdepth 100
rule trunk {
    {y 2} trunk
    {y 1 s 0.8} box
}
trunk
```

### Radial pattern with expressions

```
#define n 12
#define angle_step (360 / n)
n * {rz angle_step x 2} box
```

### Parameterized rule

```
rule branch(angle, length) {
    {rz angle s length 1 1} box
}
branch(30, 5)
branch(60, 3)
```

### Forward reference in #define

```
#define base 10
#define derived (base * 2)
#define final (derived + 1)
s final 1 1
```

### Octopus (from original spec)

```
set maxdepth 100
10 * {ry 36 sat 0.9} 30 * {ry 10} 1 * {h 30 b 0.8 sat 0.8 a 0.3} r1

rule r1 w 20 {
    {s 0.9 rz 5 h 5 rx 5 x 1} r1
    {s 1 0.2 0.5} box
}

rule r1 w 20 {
    {s 0.99 rz -5 h 5 rx -5 x 1} r1
    {s 1 0.2 0.5} box
}

rule r1 {}
```

---

## XML Conversion Notes

The XML format (legacy) does **not** support:
- Parameterized rules (`rule name(p) { ... }`)
- Rule calls with arguments (`name(1, 2)`)
- Python expressions (`(a + b)`)

Attempting to convert a program with these features to XML raises
`ExpressionInXmlError`.  Expand rules manually or use the native
EisenScript format.
