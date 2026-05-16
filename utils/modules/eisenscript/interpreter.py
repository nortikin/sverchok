# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Interpreter for EisenScript AST.

Executes an EisenScript :class:`Program` and produces a mapping of
primitive names to lists of 4×4 transformation matrices
(:class:`mathutils.Matrix`).

Usage::

    from sverchok.utils.modules.eisenscript.interpreter import Interpreter
    result = Interpreter.interpret(program)
    # result.matrices['box']  -> list of Matrix
    # result.matrices['sphere'] -> list of Matrix
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import mathutils as mu
from mathutils import Matrix

from sverchok.utils.modules.eisenscript.ast import (
    Program,
    Rule,
    Branch,
    Repeat,
    RuleRef,
    VariableRef,
    Expr,
    IMPLICIT_START_RULE,
    # Axis constants
    AXIS_X, AXIS_Y, AXIS_Z,
    # Geometrical transformations
    Translate,
    Rotate,
    Scale,
    MatrixTransform,
    Mirror,
    # Color transformations (ignored by interpreter)
    HueShift, SaturationMul, BrightnessMul, AlphaMul,
    SetColor, BlendColor,
    # Primitives
    Box, Grid, Sphere, Line, Point, Triangle,
)


# ---------------------------------------------------------------------------
# Safe evaluation namespace for Python expressions
# ---------------------------------------------------------------------------

def _make_safe_names():
    """Build the safe namespace for ``eval()`` of EisenScript expressions.

    Includes all functions from the ``math`` module, plus a handful of
    built-in functions and constants.
    """
    safe = {}
    # All callable names from the math module
    import math as _math
    for _name in dir(_math):
        if not _name.startswith('_'):
            _obj = getattr(_math, _name)
            if callable(_obj):
                safe[_name] = _obj
    # Math constants
    safe['e'] = math.e
    safe['pi'] = math.pi
    # Useful built-ins
    safe['abs'] = abs
    safe['round'] = round
    safe['min'] = min
    safe['max'] = max
    safe['pow'] = pow
    safe['tuple'] = tuple
    safe['list'] = list
    return safe


SAFE_NAMES = _make_safe_names()


# ---------------------------------------------------------------------------
# Lazy #define resolver with topological sort and caching
# ---------------------------------------------------------------------------

class DefineResolver:
    """
    Lazy evaluator for ``#define`` values with caching and topological sort.

    Supports:
    - Plain numeric values (``#define n 10``)
    - Expression values (``#define n (a * 2 + 1)``)
    - Forward references (expressions can reference variables defined later)
    - Caching (each expression is evaluated at most once)
    - Topological ordering (dependencies are resolved before dependents)
    - External variables (``#input`` params) available to expressions

    Raises ``ValueError`` on undefined variables or circular dependencies.
    """

    def __init__(
        self,
        raw_defines: Dict[str, object],
        external_vars: Optional[Dict[str, float]] = None,
    ):
        """
        Args:
            raw_defines: Dict mapping variable names to either ``float``
                or :class:`Expr` nodes.
            external_vars: Dict of externally-provided variable values
                (e.g. resolved #input parameters).  These are available to
                #define expressions but do NOT participate in the
                topological sort — they are treated as always-available
                constants.
        """
        self._raw = dict(raw_defines)
        self._external = dict(external_vars or {})
        self._cache: Dict[str, float] = {}
        self._topo_order: Optional[List[str]] = None

    # ---- public API ----------------------------------------------------

    def resolve(self, name: str) -> float:
        """
        Resolve a variable name to its numeric value.

        Returns:
            The computed float value.

        Raises:
            ValueError: If the variable is undefined or a circular
                dependency is detected.
        """
        if name in self._cache:
            return self._cache[name]

        # External variables (e.g. #input) are always available
        if name in self._external:
            return self._external[name]

        if name not in self._raw:
            raise ValueError(f"Undefined variable: {name}")

        # First access — build topo order and evaluate all expressions
        if self._topo_order is None:
            self._build_and_evaluate()

        if name in self._cache:
            return self._cache[name]

        # Plain numeric value (not an Expr) — store and return
        val = self._raw[name]
        if not isinstance(val, Expr):
            self._cache[name] = float(val)
            return self._cache[name]

        raise ValueError(f"Undefined variable: {name}")

    def get_all(self) -> Dict[str, float]:
        """
        Force evaluation of all defines and return the complete mapping.
        """
        for name in self._raw:
            self.resolve(name)
        return dict(self._cache)

    # ---- internal ------------------------------------------------------

    def _build_and_evaluate(self):
        """Build dependency graph, topo-sort, and evaluate in order."""
        from sverchok.utils.topo import stable_topo_sort

        # Separate plain values from expressions
        expr_names = [
            name for name, val in self._raw.items() if isinstance(val, Expr)
        ]
        plain_names = [
            name for name, val in self._raw.items() if not isinstance(val, Expr)
        ]

        # Cache plain values immediately
        for name in plain_names:
            self._cache[name] = float(self._raw[name])

        if not expr_names:
            self._topo_order = []
            return

        # Build dependency graph for expressions
        # Each expression depends on the variables it references
        name_to_idx = {name: i for i, name in enumerate(expr_names)}

        edges = []
        # Names that are NOT variables (math functions, constants, built-ins)
        _safe_names = set(SAFE_NAMES.keys())

        for i, name in enumerate(expr_names):
            expr = self._raw[name]
            for dep in expr.get_variables():
                if dep in _safe_names:
                    # Math function or constant — not a variable dependency
                    continue
                if dep in self._cache:
                    # Plain value — already available, no edge needed
                    continue
                if dep in self._external:
                    # External variable (e.g. #input) — always available
                    continue
                if dep in name_to_idx:
                    j = name_to_idx[dep]
                    if i != j:
                        edges.append((j, i))  # j must come before i (i depends on j)
                elif dep not in self._raw:
                    raise ValueError(f"Undefined variable: {dep}")
                # else: dep is a plain value, already cached

        # Topological sort
        sorted_names = stable_topo_sort(expr_names, edges)
        self._topo_order = sorted_names

        # Evaluate in topo order
        for name in sorted_names:
            expr = self._raw[name]
            env = dict(SAFE_NAMES)
            # Add external variables (e.g. #input) — always available
            env.update(self._external)
            # Add all currently cached values
            env.update(self._cache)
            env["__builtins__"] = {}
            try:
                result = eval(
                    compile(expr.ast_node, "<eisenscript>", "eval"), env
                )
            except NameError as e:
                raise ValueError(f"Undefined variable in expression: {e}")
            self._cache[name] = float(result)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

class InterpreterResult:
    """
    Holds the output of an EisenScript interpretation.

    Attributes:
        matrices: Dict mapping primitive name (str) to a list of
            :class:`mathutils.Matrix` (4×4) transforms.
            E.g. ``result.matrices['sphere']`` gives the list of
            placement matrices for all sphere instances.
    """

    __slots__ = ('matrices',)

    def __init__(self) -> None:
        self.matrices: Dict[str, List[Matrix]] = {}


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class Interpreter:
    """
    Stack-based interpreter for EisenScript AST.

    Walks the rule graph starting from the implicit entry-point
    (``IMPLICIT_START_RULE``) and accumulates primitive placements.

    Attributes:
        max_depth: Global recursion depth limit (from ``set maxdepth``).
        max_objects: Hard cap on the total number of primitive instances.
        seed: Random seed for weighted rule selection.
        origin_as_center: If True, transformations use (0,0,0) as center
            (legacy LSystem behavior). If False (default), use (0.5,0.5,0.5)
            per the EisenScript specification.
        min_size: Minimum diagonal length of the unit cube before terminating
            a branch. None means no lower bound.
        max_size: Maximum diagonal length of the unit cube before terminating
            a branch. None means no upper bound.
    """

    def __init__(
        self,
        max_depth: int = 1000,
        max_objects: Optional[int] = None,
        seed: int = 0,
        origin_as_center: bool = True,
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
    ) -> None:
        self.max_depth = max_depth
        self.max_objects = max_objects
        self.seed = seed
        self.origin_as_center = origin_as_center
        self.min_size = min_size
        self.max_size = max_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def interpret(
        program: Program,
        origin_as_center: bool = True,
        input_values: Optional[Dict[str, float]] = None,
    ) -> InterpreterResult:
        """Create an interpreter and run it on *program*.

        Args:
            program: The EisenScript program to interpret.
            origin_as_center: If True, transformations use (0,0,0) as center
                (legacy LSystem behavior, matches XML interpreter). If False,
                use (0.5,0.5,0.5) per the EisenScript specification.
                Default is True for compatibility with the legacy LSystem.
            input_values: Optional dict mapping #input parameter names to
                their runtime values.  Missing keys fall back to the default
                value from the #input directive (if any).  If a parameter has
                no default and is not provided, a ValueError is raised.

        Reads ``maxdepth``, ``seed``, ``maxobjects``, ``minsize`` and
        ``maxsize`` from program settings when present.
        """
        global_maxdepth: int = 1000
        seed: int = 0
        max_objects: Optional[int] = None
        min_size: Optional[float] = None
        max_size: Optional[float] = None

        for s in program.settings:
            if s.name == "maxdepth":
                global_maxdepth = int(s.value)
            elif s.name == "seed":
                val = s.value
                if isinstance(val, str) and val == "initial":
                    seed = 0
                else:
                    seed = int(val)
            elif s.name == "maxobjects":
                max_objects = int(s.value)
            elif s.name == "minsize":
                min_size = float(s.value)
            elif s.name == "maxsize":
                max_size = float(s.value)

        interp = Interpreter(
            max_depth=global_maxdepth,
            max_objects=max_objects,
            seed=seed,
            origin_as_center=origin_as_center,
            min_size=min_size,
            max_size=max_size,
        )
        return interp._interpret(program, input_values=input_values)

    # ------------------------------------------------------------------
    # Internal entry point
    # ------------------------------------------------------------------

    def _interpret(
        self, program: Program, input_values: Optional[Dict[str, float]] = None
    ) -> InterpreterResult:
        """Execute *program* and return an :class:`InterpreterResult"."""
        random.seed(self.seed)

        # Resolve #input values: runtime values override defaults
        resolved_inputs: Dict[str, float] = {}
        for name, inp_def in program.inputs.items():
            if name in (input_values or {}):
                resolved_inputs[name] = input_values[name]
            elif inp_def.default_value is not None:
                resolved_inputs[name] = inp_def.default_value
            else:
                raise ValueError(
                    f"#input parameter '{name}' has no default value "
                    f"and was not provided in input_values."
                )

        # Build rule lookup: name -> list of Rule (for weighted selection)
        rule_map: Dict[str, List[Rule]] = {}
        for rule in program.rules:
            rule_map.setdefault(rule.name, []).append(rule)

        # Validate parameter count consistency across rule definitions
        for rule_name, rules in rule_map.items():
            if len(rules) > 1:
                param_counts = [len(r.params) for r in rules]
                if len(set(param_counts)) > 1:
                    raise ValueError(
                        f"Rule '{rule_name}' has inconsistent parameter counts "
                        f"across definitions: {param_counts}. "
                        f"All definitions of the same rule must have the same "
                        f"number of parameters."
                    )

        # Result collector
        result = InterpreterResult()

        # Lazy define resolver with topo sort and caching
        # Pass resolved inputs as external variables so #define expressions
        # can reference them without participating in the topo sort.
        resolver = DefineResolver(program.defines, external_vars=resolved_inputs)

        def _resolve_scoped(val, params_scope):
            """Resolve a value with parameter scoping.

            Priority: params_scope > #input > #define.
            Expr: evaluate with params_scope + #input + #define in namespace.
            """
            if isinstance(val, VariableRef):
                if val.name in params_scope:
                    return params_scope[val.name]
                if val.name in resolved_inputs:
                    return resolved_inputs[val.name]
                return resolver.resolve(val.name)
            if isinstance(val, Expr):
                resolver.get_all()
                env = dict(SAFE_NAMES)
                env.update(resolver._cache)
                # #input variables are available
                env.update(resolved_inputs)
                # Parameters shadow #input and #define variables
                env.update(params_scope)
                env["__builtins__"] = {}
                return eval(compile(val.ast_node, "<eisenscript>", "eval"), env)
            return val

        # Stack entries: (rule, depth, accumulated_matrix, params_scope)
        entry_rule = _pick_rule(rule_map, IMPLICIT_START_RULE)
        stack: List[Tuple[Rule, int, Matrix, Dict[str, float]]] = [
            (entry_rule, 0, Matrix.Identity(4), {})
        ]

        total_objects = 0

        while stack:
            if self.max_objects is not None and total_objects > self.max_objects:
                break

            rule, depth, matrix, params_scope = stack.pop()

            # Per-rule max_depth
            local_max_depth = self.max_depth
            if rule.maxdepth is not None:
                resolved_md = _resolve_scoped(rule.maxdepth, params_scope)
                local_max_depth = round(resolved_md)

            # Stack depth guard
            if len(stack) > self.max_depth:
                continue

            # Retirement check
            if depth > local_max_depth:
                if rule.retirement_rule:
                    succ_rule = _pick_rule(rule_map, rule.retirement_rule)
                    stack.append((succ_rule, 0, matrix.copy(), params_scope))
                continue

            # Process each branch in the rule
            for branch in rule.body:
                self._interpret_branch(
                    branch, rule_map, resolver,
                    matrix, depth, stack, result,
                    total_objects, params_scope, _resolve_scoped,
                )
                # Update total_objects count after branch
                for mats in result.matrices.values():
                    total_objects = len(mats)

        return result

    # ------------------------------------------------------------------
    # Branch interpretation
    # ------------------------------------------------------------------

    def _interpret_branch(
        self,
        branch: Branch,
        rule_map: Dict[str, List[Rule]],
        resolver: DefineResolver,
        parent_matrix: Matrix,
        depth: int,
        stack: list,
        result: InterpreterResult,
        total_objects: int,
        params_scope: dict,
        resolve,
    ) -> None:
        """
        Interpret a single Branch AST node.

        Builds the accumulated transform from all repetitions, then
        dispatches to the terminal (RuleRef or Primitive).
        Terminates the branch if the current size is outside [min_size, max_size].
        """
        repetitions = branch.repetitions
        terminal = branch.terminal

        # Build per-repetition transform matrices and counts
        rep_info = []  # list of (count, transform_matrix)
        for rep in repetitions:
            count = round(resolve(rep.count, params_scope))
            tmat = self._build_transform_matrix(rep.transformations, resolver, params_scope, resolve)
            rep_info.append((count, tmat))

        # Terminal dispatch
        if isinstance(terminal, RuleRef):
            self._dispatch_call(
                terminal, rule_map, resolver, resolve,
                parent_matrix, depth, stack, rep_info,
                params_scope,
            )
        else:
            self._dispatch_instance(
                terminal, result, parent_matrix, rep_info,
                total_objects,
            )

    # ------------------------------------------------------------------
    # Rule call dispatch
    # ------------------------------------------------------------------

    def _dispatch_call(
        self,
        ref: RuleRef,
        rule_map: Dict[str, List[Rule]],
        resolver: DefineResolver,
        resolve,
        parent_matrix: Matrix,
        depth: int,
        stack: list,
        rep_info: list,
        params_scope: dict,
    ) -> None:
        """Handle a RuleRef terminal: push called rule(s) onto the stack."""
        target_rule = _pick_rule(rule_map, ref.name)

        # Validate and resolve arguments
        new_params_scope = dict(params_scope)
        if ref.args:
            # Check that the rule has parameters
            if not target_rule.params:
                raise ValueError(
                    f"Rule '{ref.name}' is called with {len(ref.args)} argument(s) "
                    f"but has no parameters. Use '{ref.name}' without parentheses."
                )
            if len(ref.args) != len(target_rule.params):
                raise ValueError(
                    f"Rule '{ref.name}' expects {len(target_rule.params)} parameter(s) "
                    f"but got {len(ref.args)}. "
                    f"Expected: ({', '.join(target_rule.params)}), "
                    f"got {len(ref.args)} argument(s)."
                )
            # Resolve arguments and bind to parameters
            for param_name, arg_val in zip(target_rule.params, ref.args):
                new_params_scope[param_name] = resolve(arg_val, params_scope)

        # Retirement on the call itself
        call_max_depth = None
        if ref.retirement_depth is not None:
            call_max_depth = resolve(ref.retirement_depth, params_scope)
            if isinstance(call_max_depth, float) and call_max_depth == int(call_max_depth):
                call_max_depth = int(call_max_depth)
        call_successor = ref.retirement_rule

        if not rep_info:
            # No repetitions — direct call
            cloned = parent_matrix.copy()
            if self._size_in_bounds(cloned):
                entry = (target_rule, depth + 1, cloned, new_params_scope)
                if call_max_depth is not None:
                    # Wrap with a retirement rule
                    entry = (_make_retirement_wrapper(target_rule, call_max_depth,
                                                      call_successor, rule_map),
                             depth + 1, cloned, new_params_scope)
                stack.append(entry)
            return

        # Build cumulative transforms for each repetition level
        base_matrix = parent_matrix.copy()

        # For nested repetitions, we need to iterate through all combinations
        self._emit_calls_recursive(
            rep_info, 0, base_matrix,
            target_rule, depth, call_max_depth, call_successor,
            rule_map, stack, new_params_scope,
        )

    def _emit_calls_recursive(
        self,
        rep_info: list,
        level: int,
        current_matrix: Matrix,
        target_rule: Rule,
        depth: int,
        call_max_depth: Optional[int],
        call_successor: Optional[str],
        rule_map: Dict[str, List[Rule]],
        stack: list,
        params_scope: dict,
    ) -> None:
        """Recursively emit stack entries for nested repetition levels."""
        if level == len(rep_info):
            # Base case: push the terminal call
            if self._size_in_bounds(current_matrix):
                cloned = current_matrix.copy()
                entry = (target_rule, depth + 1, cloned, params_scope)
                if call_max_depth is not None:
                    entry = (_make_retirement_wrapper(target_rule, call_max_depth,
                                                      call_successor, rule_map),
                             depth + 1, cloned, params_scope)
                stack.append(entry)
            return

        count, tmat = rep_info[level]
        cumulative = Matrix.Identity(4)
        for _ in range(count):
            cumulative @= tmat
            self._emit_calls_recursive(
                rep_info, level + 1,
                current_matrix @ cumulative,
                target_rule, depth,
                call_max_depth, call_successor,
                rule_map, stack, params_scope,
            )

    # ------------------------------------------------------------------
    # Primitive instance dispatch
    # ------------------------------------------------------------------

    def _dispatch_instance(
        self,
        terminal,
        result: InterpreterResult,
        parent_matrix: Matrix,
        rep_info: list,
        total_objects: int,
    ) -> None:
        """Handle a Primitive terminal: emit placement matrix(es)."""
        shape_name = _primitive_name(terminal)
        if shape_name is None:
            return

        if shape_name not in result.matrices:
            result.matrices[shape_name] = []

        if not rep_info:
            # No repetitions — single instance
            if self._size_in_bounds(parent_matrix):
                if self.max_objects is None or total_objects < self.max_objects:
                    result.matrices[shape_name].append(parent_matrix.copy())
            return

        # Build cumulative transforms for each repetition level
        self._emit_instances_recursive(
            rep_info, 0, parent_matrix,
            shape_name, result, total_objects,
        )

    def _emit_instances_recursive(
        self,
        rep_info: list,
        level: int,
        current_matrix: Matrix,
        shape_name: str,
        result: InterpreterResult,
        total_objects: int,
    ) -> None:
        """Recursively emit instance matrices for nested repetition levels."""
        if self.max_objects is not None and total_objects >= self.max_objects:
            return

        if level == len(rep_info):
            # Base case: emit the instance if size is in bounds
            if self._size_in_bounds(current_matrix):
                result.matrices[shape_name].append(current_matrix.copy())
            return

        count, tmat = rep_info[level]
        cumulative = Matrix.Identity(4)
        for _ in range(count):
            cumulative @= tmat
            new_total = 0
            for mats in result.matrices.values():
                new_total += len(mats)
            self._emit_instances_recursive(
                rep_info, level + 1,
                current_matrix @ cumulative,
                shape_name, result, new_total,
            )

    # ------------------------------------------------------------------
    # Transform / size helpers (instance methods)
    # ------------------------------------------------------------------

    def _build_transform_matrix(
        self,
        transformations: list,
        resolver: DefineResolver,
        params_scope: dict,
        resolve,
    ) -> Matrix:
        """
        Build a 4×4 Matrix from a list of Transformation AST nodes.

        Uses ``self.origin_as_center`` to decide the transform center.
        """
        matrix = Matrix.Identity(4)
        center = mu.Vector((0.5, 0.5, 0.5))
        t_center = Matrix.Translation(center)
        t_neg_center = Matrix.Translation(-center)

        _axis_vec = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        _axis_letter = ('X', 'Y', 'Z')

        for trans in transformations:
            if isinstance(trans, Translate):
                v = resolve(trans.value, params_scope)
                vec = list(_axis_vec[trans.axis])
                vec[trans.axis] = v
                matrix @= Matrix.Translation(tuple(vec))

            elif isinstance(trans, Rotate):
                v = math.radians(resolve(trans.angle, params_scope))
                rot = Matrix.Rotation(v, 4, _axis_letter[trans.axis])
                if not self.origin_as_center:
                    matrix @= t_center @ rot @ t_neg_center
                else:
                    matrix @= rot

            elif isinstance(trans, Scale):
                x = resolve(trans.x, params_scope)
                if trans.is_uniform:
                    scale = Matrix.Scale(x, 4)
                else:
                    y = resolve(trans.y, params_scope) if trans.y is not None else 1.0
                    z = resolve(trans.z, params_scope) if trans.z is not None else 1.0
                    sx = Matrix.Scale(x, 4, (1.0, 0.0, 0.0))
                    sy = Matrix.Scale(y, 4, (0.0, 1.0, 0.0))
                    sz = Matrix.Scale(z, 4, (0.0, 0.0, 1.0))
                    scale = sx @ sy @ sz
                if not self.origin_as_center:
                    matrix @= t_center @ scale @ t_neg_center
                else:
                    matrix @= scale

            elif isinstance(trans, MatrixTransform):
                m = [resolve(v, params_scope) for v in trans.matrix]
                # Build 4×4 from 9 values (3×3 + translation)
                new_matrix = Matrix([
                    [m[0], m[1], m[2], m[3]],
                    [m[4], m[5], m[6], m[7]],
                    [m[8], m[9], m[10], m[11]],
                    [0, 0, 0, 1],
                ]) if len(m) >= 12 else Matrix.Identity(4)
                # If only 9 values, treat as 3×3 linear transform
                if len(m) == 9:
                    new_matrix = Matrix([
                        [m[0], m[1], m[2], 0],
                        [m[3], m[4], m[5], 0],
                        [m[6], m[7], m[8], 0],
                        [0, 0, 0, 1],
                    ])
                matrix @= new_matrix

            elif isinstance(trans, Mirror):
                mirror = Matrix.Scale(-1, 4, _axis_vec[trans.axis])
                if not self.origin_as_center:
                    matrix @= t_center @ mirror @ t_neg_center
                else:
                    matrix @= mirror

            # Color transformations are ignored by the interpreter
            # (HueShift, SaturationMul, BrightnessMul, AlphaMul, SetColor, BlendColor)

        return matrix

    def _size_in_bounds(self, matrix: Matrix) -> bool:
        """
        Return True if the current size is within [self.min_size, self.max_size].

        If both are None, always returns True.
        """
        if self.min_size is None and self.max_size is None:
            return True

        size = _compute_size(matrix)

        if self.min_size is not None and size < self.min_size:
            return False
        if self.max_size is not None and size > self.max_size:
            return False
        return True


# ---------------------------------------------------------------------------
# Module-level helpers (no interpreter state needed)
# ---------------------------------------------------------------------------

def _pick_rule(rule_map: Dict[str, List[Rule]], name: str) -> Rule:
    """Select a rule by name, respecting weights (random weighted choice)."""
    candidates = rule_map.get(name)
    if not candidates:
        raise ValueError(f"No rule found with name '{name}'")

    if len(candidates) == 1:
        return candidates[0]

    # Weighted random selection
    total_weight = sum(r.weight for r in candidates)
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    for rule in candidates:
        cumulative += rule.weight
        if r < cumulative:
            return rule
    return candidates[-1]


def _make_retirement_wrapper(
    target_rule: Rule,
    max_depth: int,
    successor: Optional[str],
    rule_map: Dict[str, List[Rule]],
) -> Rule:
    """
    Return a new Rule that wraps *target_rule* with call-site
    retirement parameters (max_depth and successor).

    When a RuleRef specifies ``md N > successor rule``, the wrapper
    overrides the target rule's own maxdepth/retirement_rule so that
    the call-site retirement takes effect.
    """
    return Rule(
        name=target_rule.name,
        maxdepth=max_depth,
        retirement_rule=successor,
        weight=target_rule.weight,
        body=target_rule.body,
    )


def _compute_size(matrix: Matrix) -> float:
    """
    Compute the "size" of the unit cube under *matrix*.

    The size is the length of the diagonal of a unit cube (from (0,0,0)
    to (1,1,1)) after applying the linear part of *matrix*.

    Per spec: "The 'size' parameter refers to the length of the diagonal
    of a unit cube in the current local state."
    """
    # Transform the diagonal vector (1,1,1) by the linear part of the matrix
    diag = mu.Vector((
        matrix[0][0] + matrix[0][1] + matrix[0][2],
        matrix[1][0] + matrix[1][1] + matrix[1][2],
        matrix[2][0] + matrix[2][1] + matrix[2][2],
    ))
    return diag.length


def _primitive_name(terminal) -> Optional[str]:
    """Map a Primitive AST node to its XML shape name."""
    if isinstance(terminal, Box):
        return "box"
    if isinstance(terminal, Grid):
        return "grid"
    if isinstance(terminal, Sphere):
        return "sphere"
    if isinstance(terminal, Line):
        return "line"
    if isinstance(terminal, Point):
        return "point"
    if isinstance(terminal, Triangle):
        return "triangle"
    return None
