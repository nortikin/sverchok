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
    IMPLICIT_START_RULE,
    # Geometrical transformations
    TranslateX, TranslateY, TranslateZ,
    RotateX, RotateY, RotateZ,
    Scale,
    MatrixTransform,
    MirrorX, MirrorY, MirrorZ,
    # Color transformations (ignored by interpreter)
    HueShift, SaturationMul, BrightnessMul, AlphaMul,
    SetColor, BlendColor,
    # Primitives
    Box, Grid, Sphere, Line, Point, Triangle,
)


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
    """

    def __init__(
        self,
        max_depth: int = 1000,
        max_objects: Optional[int] = None,
        seed: int = 0,
        origin_as_center: bool = True,
    ) -> None:
        self.max_depth = max_depth
        self.max_objects = max_objects
        self.seed = seed
        self.origin_as_center = origin_as_center

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def interpret(
        program: Program,
        origin_as_center: bool = True,
    ) -> InterpreterResult:
        """Create an interpreter and run it on *program*.

        Args:
            program: The EisenScript program to interpret.
            origin_as_center: If True, transformations use (0,0,0) as center
                (legacy LSystem behavior, matches XML interpreter). If False,
                use (0.5,0.5,0.5) per the EisenScript specification.
                Default is True for compatibility with the legacy LSystem.

        Reads ``maxdepth``, ``seed`` and ``maxobjects`` from program
        settings when present.
        """
        global_maxdepth: int = 1000
        seed: int = 0
        max_objects: Optional[int] = None

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

        interp = Interpreter(
            max_depth=global_maxdepth,
            max_objects=max_objects,
            seed=seed,
            origin_as_center=origin_as_center,
        )
        return interp._interpret(program)

    def _interpret(self, program: Program) -> InterpreterResult:
        """Execute *program* and return an :class:`InterpreterResult`."""
        random.seed(self.seed)

        # Build rule lookup: name -> list of Rule (for weighted selection)
        rule_map: Dict[str, List[Rule]] = {}
        for rule in program.rules:
            rule_map.setdefault(rule.name, []).append(rule)

        # Result collector
        result = InterpreterResult()

        # Resolve defines helper
        defines = program.defines

        def _resolve(val):
            if isinstance(val, VariableRef):
                if val.name not in defines:
                    raise ValueError(f"Undefined variable: {val.name}")
                return defines[val.name]
            return val

        # Stack entries: (rule_name, depth, accumulated_matrix)
        entry_rule = _pick_rule(rule_map, IMPLICIT_START_RULE)
        stack: List[Tuple[Rule, int, Matrix]] = [
            (entry_rule, 0, Matrix.Identity(4))
        ]

        total_objects = 0

        while stack:
            if self.max_objects is not None and total_objects > self.max_objects:
                break

            rule, depth, matrix = stack.pop()

            # Per-rule max_depth
            local_max_depth = self.max_depth
            if rule.maxdepth is not None:
                resolved_md = _resolve(rule.maxdepth)
                local_max_depth = round(resolved_md)

            # Stack depth guard
            if len(stack) > self.max_depth:
                continue

            # Retirement check
            if depth > local_max_depth:
                if rule.retirement_rule:
                    succ_rule = _pick_rule(rule_map, rule.retirement_rule)
                    stack.append((succ_rule, 0, matrix.copy()))
                continue

            # Process each branch in the rule
            for branch in rule.body:
                _interpret_branch(
                    branch, rule_map, defines,
                    matrix, depth, stack, result,
                    total_objects, self.max_objects,
                    self.origin_as_center,
                )
                # Update total_objects count after branch
                for mats in result.matrices.values():
                    total_objects = len(mats)

        return result


# ---------------------------------------------------------------------------
# Branch interpretation
# ---------------------------------------------------------------------------

def _interpret_branch(
    branch: Branch,
    rule_map: Dict[str, List[Rule]],
    defines: dict,
    parent_matrix: Matrix,
    depth: int,
    stack: list,
    result: InterpreterResult,
    total_objects: int,
    max_objects: Optional[int],
    origin_as_center: bool,
) -> None:
    """
    Interpret a single Branch AST node.

    Builds the accumulated transform from all repetitions, then
    dispatches to the terminal (RuleRef or Primitive).
    """
    repetitions = branch.repetitions
    terminal = branch.terminal

    def _resolve(val):
        if isinstance(val, VariableRef):
            if val.name not in defines:
                raise ValueError(f"Undefined variable: {val.name}")
            return defines[val.name]
        return val

    # Build per-repetition transform matrices and counts
    rep_info = []  # list of (count, transform_matrix)
    for rep in repetitions:
        count = round(_resolve(rep.count))
        tmat = _build_transform_matrix(
            rep.transformations, defines, _resolve, origin_as_center)
        rep_info.append((count, tmat))

    # Terminal dispatch
    if isinstance(terminal, RuleRef):
        _dispatch_call(
            terminal, rule_map, defines, _resolve,
            parent_matrix, depth, stack, rep_info,
        )
    else:
        _dispatch_instance(
            terminal, result, parent_matrix, rep_info,
            total_objects, max_objects,
        )


def _dispatch_call(
    ref: RuleRef,
    rule_map: Dict[str, List[Rule]],
    defines: dict,
    resolve,
    parent_matrix: Matrix,
    depth: int,
    stack: list,
    rep_info: list,
) -> None:
    """Handle a RuleRef terminal: push called rule(s) onto the stack."""
    target_rule = _pick_rule(rule_map, ref.name)

    # Retirement on the call itself
    call_max_depth = None
    if ref.retirement_depth is not None:
        call_max_depth = ref.retirement_depth
    call_successor = ref.retirement_rule

    if not rep_info:
        # No repetitions — direct call
        cloned = parent_matrix.copy()
        entry = (target_rule, depth + 1, cloned)
        if call_max_depth is not None:
            # Wrap with a retirement rule
            entry = (_make_retirement_wrapper(target_rule, call_max_depth,
                                              call_successor, rule_map),
                     depth + 1, cloned)
        stack.append(entry)
        return

    # Build cumulative transforms for each repetition level
    base_matrix = parent_matrix.copy()

    # For nested repetitions, we need to iterate through all combinations
    _emit_calls_recursive(
        rep_info, 0, base_matrix,
        target_rule, depth, call_max_depth, call_successor,
        rule_map, stack,
    )


def _emit_calls_recursive(
    rep_info: list,
    level: int,
    current_matrix: Matrix,
    target_rule: Rule,
    depth: int,
    call_max_depth: Optional[int],
    call_successor: Optional[str],
    rule_map: Dict[str, List[Rule]],
    stack: list,
) -> None:
    """Recursively emit stack entries for nested repetition levels."""
    if level == len(rep_info):
        # Base case: push the terminal call
        cloned = current_matrix.copy()
        entry = (target_rule, depth + 1, cloned)
        if call_max_depth is not None:
            entry = (_make_retirement_wrapper(target_rule, call_max_depth,
                                              call_successor, rule_map),
                     depth + 1, cloned)
        stack.append(entry)
        return

    count, tmat = rep_info[level]
    cumulative = Matrix.Identity(4)
    for _ in range(count):
        cumulative @= tmat
        _emit_calls_recursive(
            rep_info, level + 1,
            current_matrix @ cumulative,
            target_rule, depth,
            call_max_depth, call_successor,
            rule_map, stack,
        )


def _dispatch_instance(
    terminal,
    result: InterpreterResult,
    parent_matrix: Matrix,
    rep_info: list,
    total_objects: int,
    max_objects: Optional[int],
) -> None:
    """Handle a Primitive terminal: emit placement matrix(es)."""
    shape_name = _primitive_name(terminal)
    if shape_name is None:
        return

    if shape_name not in result.matrices:
        result.matrices[shape_name] = []

    if not rep_info:
        # No repetitions — single instance
        if max_objects is None or total_objects < max_objects:
            result.matrices[shape_name].append(parent_matrix.copy())
        return

    # Build cumulative transforms for each repetition level
    _emit_instances_recursive(
        rep_info, 0, parent_matrix,
        shape_name, result, total_objects, max_objects,
    )


def _emit_instances_recursive(
    rep_info: list,
    level: int,
    current_matrix: Matrix,
    shape_name: str,
    result: InterpreterResult,
    total_objects: int,
    max_objects: Optional[int],
) -> None:
    """Recursively emit instance matrices for nested repetition levels."""
    if max_objects is not None and total_objects >= max_objects:
        return

    if level == len(rep_info):
        # Base case: emit the instance
        result.matrices[shape_name].append(current_matrix.copy())
        return

    count, tmat = rep_info[level]
    cumulative = Matrix.Identity(4)
    for _ in range(count):
        cumulative @= tmat
        new_total = 0
        for mats in result.matrices.values():
            new_total += len(mats)
        _emit_instances_recursive(
            rep_info, level + 1,
            current_matrix @ cumulative,
            shape_name, result, new_total, max_objects,
        )


# ---------------------------------------------------------------------------
# Helpers
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


def _build_transform_matrix(
    transformations: list,
    defines: dict,
    resolve,
    origin_as_center: bool = True,
) -> Matrix:
    """
    Build a 4×4 Matrix from a list of Transformation AST nodes.

    Args:
        transformations: List of Transformation AST nodes.
        defines: Dict of variable names to their values.
        resolve: Function to resolve VariableRef values.
        origin_as_center: If True, use (0,0,0) as transform center
            (legacy LSystem behavior). If False, use (0.5,0.5,0.5)
            per the EisenScript specification for scale, rotation,
            and mirror transforms.
    """
    matrix = Matrix.Identity(4)
    center = mu.Vector((0.5, 0.5, 0.5))
    t_center = Matrix.Translation(center)
    t_neg_center = Matrix.Translation(-center)

    for trans in transformations:
        if isinstance(trans, TranslateX):
            v = resolve(trans.value)
            matrix @= Matrix.Translation((v, 0, 0))
        elif isinstance(trans, TranslateY):
            v = resolve(trans.value)
            matrix @= Matrix.Translation((0, v, 0))
        elif isinstance(trans, TranslateZ):
            v = resolve(trans.value)
            matrix @= Matrix.Translation((0, 0, v))

        elif isinstance(trans, RotateX):
            v = math.radians(resolve(trans.angle))
            rot = Matrix.Rotation(v, 4, 'X')
            if not origin_as_center:
                matrix @= t_center @ rot @ t_neg_center
            else:
                matrix @= rot
        elif isinstance(trans, RotateY):
            v = math.radians(resolve(trans.angle))
            rot = Matrix.Rotation(v, 4, 'Y')
            if not origin_as_center:
                matrix @= t_center @ rot @ t_neg_center
            else:
                matrix @= rot
        elif isinstance(trans, RotateZ):
            v = math.radians(resolve(trans.angle))
            rot = Matrix.Rotation(v, 4, 'Z')
            if not origin_as_center:
                matrix @= t_center @ rot @ t_neg_center
            else:
                matrix @= rot

        elif isinstance(trans, Scale):
            x = resolve(trans.x)
            if trans.is_uniform:
                scale = Matrix.Scale(x, 4)
            else:
                y = resolve(trans.y) if trans.y is not None else 1.0
                z = resolve(trans.z) if trans.z is not None else 1.0
                sx = Matrix.Scale(x, 4, (1.0, 0.0, 0.0))
                sy = Matrix.Scale(y, 4, (0.0, 1.0, 0.0))
                sz = Matrix.Scale(z, 4, (0.0, 0.0, 1.0))
                scale = sx @ sy @ sz
            if not origin_as_center:
                matrix @= t_center @ scale @ t_neg_center
            else:
                matrix @= scale

        elif isinstance(trans, MatrixTransform):
            m = [resolve(v) for v in trans.matrix]
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

        elif isinstance(trans, MirrorX):
            mirror = Matrix.Scale(-1, 4, (1.0, 0.0, 0.0))
            if not origin_as_center:
                matrix @= t_center @ mirror @ t_neg_center
            else:
                matrix @= mirror
        elif isinstance(trans, MirrorY):
            mirror = Matrix.Scale(-1, 4, (0.0, 1.0, 0.0))
            if not origin_as_center:
                matrix @= t_center @ mirror @ t_neg_center
            else:
                matrix @= mirror
        elif isinstance(trans, MirrorZ):
            mirror = Matrix.Scale(-1, 4, (0.0, 0.0, 1.0))
            if not origin_as_center:
                matrix @= t_center @ mirror @ t_neg_center
            else:
                matrix @= mirror

        # Color transformations are ignored by the interpreter
        # (HueShift, SaturationMul, BrightnessMul, AlphaMul, SetColor, BlendColor)

    return matrix


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
