"""Tests for the step-by-step simplifier. Expectations were worked out by hand from the course sheet."""
import random

import pytest

from app.errors import ParseError
from app.presets import BUILTIN_PRESETS, OperatorDef, PresetDef
from app.rules import RULES, Budget
from app.service import analyze, simplify

UNIVERSAL = BUILTIN_PRESETS["universal"]


def run(expression: str, **budget) -> dict:
    if budget:
        defaults = {"seconds": 5, "max_steps": 300, "max_nodes": 3000}
        defaults.update(budget)
        return simplify(expression, UNIVERSAL, Budget(**defaults))
    return simplify(expression, UNIVERSAL)


def rules_used(result: dict) -> list[str]:
    return [step["rule"] for step in result["steps"]]


def table_of(expression: str, variables: list[str]) -> list[int]:
    """Truth table of an expression over a FIXED variable list (ORing in 0.v forces the variables to exist)."""
    padded = expression + "".join(f" + 0{v}" for v in variables)
    return [row["output"] for row in analyze(padded, UNIVERSAL)["truth_table"]["rows"]]


# -- one rule at a time ------------------------------------------------------------------------
def test_half_absorption():
    # a + a'b = a + b  (T4a)
    result = run("a + a'b")
    assert result["result"] == "a + b"
    assert rules_used(result) == ["T4a"]


def test_half_absorption_dual():
    # a(a' + b) = ab  (T4b)
    result = run("a(a' + b)")
    assert result["result"] == "ab"
    assert rules_used(result) == ["T4b"]


def test_absorption_twice():
    # a + ab + abc: abc and ab are both swallowed by a (T3a twice)
    result = run("a + ab + abc")
    assert result["result"] == "a"
    assert rules_used(result) == ["T3a", "T3a"]


def test_absorption_dual():
    result = run("a(a + b)")
    assert result["result"] == "a"
    assert rules_used(result) == ["T3b"]


def test_consensus():
    # xy + x'z + yz = xy + x'z  (T6a). Hand check, x=1,y=1,z=1: both sides 1; x=0,y=1,z=0: both sides 0.
    result = run("xy + x'z + yz")
    assert result["result"] == "xy + x'z"
    assert rules_used(result) == ["T6a"]


def test_consensus_dual():
    result = run("(a + b)(a' + c)(b + c)")
    assert result["result"] == "(a + b)(a' + c)"
    assert rules_used(result) == ["T6b"]


def test_complement_then_constant():
    # a + a' + b: P5a turns the pair into 1, then T2a: 1 + b = 1
    result = run("a + a' + b")
    assert result["result"] == "1"
    assert rules_used(result) == ["P5a", "T2a"]


def test_complement_product():
    result = run("a a'")
    assert result["result"] == "0"
    assert rules_used(result) == ["P5b"]


def test_identity_constants():
    assert rules_used(run("a + 0")) == ["P1a"]
    assert rules_used(run("a 1")) == ["P1b"]
    assert run("a 0")["result"] == "0" and rules_used(run("a 0")) == ["T2b"]
    assert run("a + 1")["result"] == "1" and rules_used(run("a + 1")) == ["T2a"]


def test_idempotence():
    result = run("a + a")
    assert result["result"] == "a"
    assert rules_used(result) == ["T1a"]
    assert rules_used(run("a b a")) == ["T1b"]


def test_de_morgan_sum_and_product():
    assert rules_used(run("(a + b)'")) == ["T5a"]
    assert run("(a + b)'")["result"] == "a'b'"
    assert rules_used(run("(ab)'")) == ["T5b"]
    assert run("(ab)'")["result"] == "a' + b'"


def test_double_complement_is_flagged_as_not_on_the_sheet():
    result = run("a''")
    assert rules_used(result) == ["INV"]
    assert result["steps"][0]["on_sheet"] is False


def test_nand_is_defined_first_then_de_morgan():
    result = run("a nand b")
    assert rules_used(result) == ["DEF", "T5b"]
    assert result["steps"][0]["after"] == "(ab)'"
    assert result["result"] == "a' + b'"


def test_xor_gets_its_textbook_definition():
    result = run("a ^ b")
    assert rules_used(result) == ["DEF"]
    assert result["result"] == "ab' + a'b"


def test_custom_operator_is_defined_from_its_truth_table():
    # NIMP: table [f(0,0), f(0,1), f(1,0), f(1,1)] = [0,0,1,0] is true only for a=1, b=0, so a NIMP b = a b'
    operators = [
        OperatorDef(name="NOT", fixity="postfix", symbols=["'"], precedence=60, table=[1, 0]),
        OperatorDef(name="NIMP", fixity="infix", symbols=["-/>"], precedence=20, table=[0, 0, 1, 0]),
    ]
    preset = PresetDef(name="mine", operators=operators)
    result = simplify("a -/> b", preset)
    assert rules_used(result) == ["DEF"]
    assert result["result"] == "ab'"


def test_factoring_reads_distributivity_backwards():
    # ab + ab' = a(b + b') = a.1 = a
    result = run("ab + ab'")
    assert rules_used(result) == ["P4b", "P5a", "P1b"]
    assert result["steps"][0]["direction"] == "backward"
    assert result["result"] == "a"


def test_factoring_a_product_of_sums():
    # (a + b)(a + c) = a + bc  (P4a backwards)
    result = run("(a + b)(a + c)")
    assert result["result"] == "a + bc"
    assert rules_used(result) == ["P4a"]


def test_already_simple_has_no_steps():
    result = run("x'y + xy'")
    assert result["steps"] == [] and result["result"] == "x'y + xy'"
    assert run("x")["step_count"] == 0


def test_supporting_rules_are_named_when_terms_are_far_apart():
    # a + b + a: the two a's are not next to each other, so commutativity and associativity are needed
    result = run("a + b + a")
    assert rules_used(result) == ["T1a"]
    assert [x["id"] for x in result["steps"][0]["also"]] == ["P2", "P3"]
    # a + a + b: the first two operands are already a group, nothing extra is needed
    assert run("a + a + b")["steps"][0]["also"] == []


# -- bookkeeping ---------------------------------------------------------------------------------
def test_every_rule_used_is_in_the_catalogue():
    result = run("(a nand b)' + (c ^ d)(c + d') + a''")
    for step in result["steps"]:
        assert step["rule"] in RULES
        assert step["equation"] == RULES[step["rule"]]["equation"]
        for helper in step["also"]:
            assert helper["id"] in ("P2", "P3")


def test_step_numbers_and_literal_counts_are_consistent():
    result = run("(a + b)'(a' + c) + ab'c + a'bc")
    assert [s["number"] for s in result["steps"]] == list(range(1, result["step_count"] + 1))
    assert result["steps"][-1]["literals"] == result["result_literals"]
    assert result["steps"][-1]["after"] == result["result"]


def test_highlight_span_marks_the_changed_part():
    # c(a + a'b): the sum is operand number 1 of the product; "c(" is 2 characters, the sum is 7 long
    result = run("c(a + a'b)")
    step = result["steps"][0]
    assert result["parsed"] == "c(a + a'b)"
    assert step["after"] == "c(a + b)"
    assert tuple(step["before_span"]) == (2, 9)
    assert tuple(step["after_span"]) == (2, 7)


def test_letters_that_would_read_as_an_operator_word_get_dots():
    # n.o.r printed as "nor" would be read back as the NOR operator
    assert run("n o r")["result"] == "n·o·r"
    assert run("n o r")["parsed"] == "n·o·r"


def test_associativity_is_applied_while_reading():
    assert run("a + (b + c)")["parsed"] == "a + b + c"


# -- the answer is always checked ---------------------------------------------------------------
def test_every_step_keeps_the_truth_table():
    """Random expressions: each intermediate expression must parse again and match the original on all rows."""
    rng = random.Random(11)
    operators = ["+", "*", "^", "+", "*", " nand ", " nor ", "->", "<->"]

    def make(depth, variables):
        if depth == 0 or rng.random() < 0.15:
            return rng.choice(variables) + ("'" if rng.random() < 0.4 else "")
        if rng.random() < 0.15:
            return "(" + make(depth - 1, variables) + ")'"
        return "(" + make(depth - 1, variables) + rng.choice(operators) + make(depth - 1, variables) + ")"

    for _ in range(60):
        variables = list("abcd"[: rng.randint(2, 4)])
        expression = make(rng.randint(2, 5), variables)
        result = run(expression)
        assert result["verified"]
        expected = table_of(expression, result["variables"])
        for step in result["steps"]:
            assert table_of(step["after"], result["variables"]) == expected, (expression, step["number"], step["rule"])


def test_big_expression_is_simplified_within_the_limits():
    rng = random.Random(3)
    terms = ["".join(rng.choice("abcde") + ("'" if rng.random() < 0.5 else "") for _ in range(rng.randint(2, 4)))
             for _ in range(120)]
    expression = " + ".join(terms)
    assert len(expression) < 2000
    result = run(expression)
    assert result["verified"] and result["result_literals"] < result["start_literals"]
    assert table_of(expression, result["variables"]) == table_of(result["result"], result["variables"])


# -- budgets ---------------------------------------------------------------------------------------
def test_step_limit_returns_a_correct_partial_result():
    # "a nand b" needs 2 steps; with room for 1 it stops after the definition, still equal to the input
    result = run("a nand b", max_steps=1)
    assert result["stopped"] == "steps"
    assert result["result"] == "(ab)'"
    assert result["verified"] and result["warnings"]


def test_time_limit_returns_the_input_unchanged():
    ticks = iter(range(0, 10**6, 100))                  # a clock that jumps 100 s every time it is read
    result = simplify("a nand b", UNIVERSAL, Budget(1, 300, 3000, clock=lambda: next(ticks)))
    assert result["stopped"] == "time"
    assert result["result"] == "a nand b"
    assert result["steps"] == []


def test_size_limit_skips_the_route_that_grows_but_keeps_the_others():
    # (a + b)(c + d) has 7 nodes; multiplying out gives 13. With a limit of 12 the SOP route gives up.
    result = run("(a + b)(c + d)", max_nodes=12)
    assert result["stopped"] is None
    gave_up = [r for r in result["routes"] if r["status"] == "gave_up"]
    assert [r["reason"] for r in gave_up] == ["size"]
    assert result["warnings"]
    assert result["result"] == "(a + b)(c + d)"


# -- bad input -----------------------------------------------------------------------------------------
def test_parse_errors_carry_a_position():
    with pytest.raises(ParseError) as caught:
        run("(a + b")
    assert caught.value.position == 6


def test_too_many_variables_is_refused():
    with pytest.raises(ParseError):
        run(" + ".join("abcdefghijklm"))
