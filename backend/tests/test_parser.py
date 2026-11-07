import string

import pytest

from app.config import MAX_VARIABLES
from app.errors import ParseError
from app.presets import OperatorDef, PresetDef

from helpers import outputs, run


def structure(expression: str, **kw) -> str:
    return run(expression, **kw)["structure"]


# -- precedence: NOT > AND > XOR > OR -------------------------------------------------------
def test_not_then_and_then_or():
    assert structure("x'y + z") == "OR(AND(NOT(x), y), z)"


def test_and_binds_tighter_than_or():
    assert structure("x + y z") == "OR(x, AND(y, z))"


def test_xor_between_and_and_or():
    assert structure("x ^ y z + w") == "OR(XOR(x, AND(y, z)), w)"


def test_implicit_and_chain_becomes_one_node_in_structure():
    assert structure("xyz'") == "AND(x, y, NOT(z))"


def test_prefix_and_postfix_not():
    assert outputs("!x") == outputs("x'") == [1, 0]
    assert outputs("x''") == [0, 1]
    assert outputs("!x'") == [0, 1]
    assert structure("!xy") == "AND(NOT(x), y)"


def test_brackets_override_precedence():
    assert outputs("(x + y)z") != outputs("x + yz")
    assert outputs("(x+y)'") == [1, 0, 0, 0]


def test_implication_is_right_associative():
    assert outputs("a -> b -> c") == outputs("a -> (b -> c)")
    assert outputs("a -> b -> c") != outputs("(a -> b) -> c")


# -- operators and spellings ----------------------------------------------------------------
@pytest.mark.parametrize(
    "expression, expected",
    [
        ("x nand y", [1, 1, 1, 0]),
        ("x NOR y", [1, 0, 0, 0]),
        ("x xnor y", [1, 0, 0, 1]),
        ("x xor y", [0, 1, 1, 0]),
        ("x -> y", [1, 1, 0, 1]),
        ("x ↑ y", [1, 1, 1, 0]),
        ("x ↓ y", [1, 0, 0, 0]),
        ("x ⊕ y", [0, 1, 1, 0]),
        ("x ~& y", [1, 1, 1, 0]),
        ("x ~| y", [1, 0, 0, 0]),
        ("x ~^ y", [1, 0, 0, 1]),
        ("x && y || !x", [1, 1, 0, 1]),
        ("x*y", [0, 0, 0, 1]),
        ("x & y", [0, 0, 0, 1]),
        ("x | y", [0, 1, 1, 1]),
        ("x <-> y", [1, 0, 0, 1]),
    ],
)
def test_operator_spellings(expression, expected):
    assert outputs(expression) == expected


def test_word_operators_are_case_insensitive():
    assert outputs("A AND B OR NOT C") == outputs("a and b or not c")


def test_constants():
    assert outputs("0") == [0]
    assert outputs("1") == [1]
    assert outputs("x + 1") == [1, 1]
    assert outputs("x 0") == [0, 0]


# -- variables ------------------------------------------------------------------------------
def test_variables_sorted_alphabetically():
    assert run("z y + x")["variables"] == ["x", "y", "z"]


def test_variables_are_always_lowercase():
    assert run("A'B")["variables"] == ["a", "b"]
    assert run("aB")["variables"] == ["a", "b"]
    assert outputs("A'B") == outputs("a'b")


def test_too_many_variables():
    with pytest.raises(ParseError) as err:
        run(string.ascii_lowercase[: MAX_VARIABLES + 1])
    assert err.value.message == f"too many variables (max {MAX_VARIABLES})"


def test_maximum_variables_are_fine():
    result = run(string.ascii_lowercase[:MAX_VARIABLES])
    assert len(result["truth_table"]["rows"]) == 1 << MAX_VARIABLES


# -- the long example from the project brief ----------------------------------------------
def test_long_example_reduces_to_not_x():
    assert run("x'y + z*xyz' + x'y'")["minterms"] == [0, 1, 2, 3]


# -- errors --------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "expression, message, position",
    [
        ("(x+y", "missing ')'", 5),
        ("x +", "unexpected end of expression", 4),
        ("x)", "unexpected ')'", 2),
        ("x $ y", "unknown character '$'", 3),
        ("", "empty expression", 1),
        ("()", "unexpected ')'", 2),
        ("+ x", "'+' needs something on its left", 1),
        ("'x", "\"'\" needs something on its left", 1),
    ],
)
def test_error_messages_and_positions(expression, message, position):
    with pytest.raises(ParseError) as err:
        run(expression)
    assert err.value.message == message
    assert err.value.position + 1 == position


def test_programming_preset_has_no_implicit_and():
    with pytest.raises(ParseError) as err:
        run("xy", preset="programming")
    assert "no implicit AND" in err.value.message
    assert outputs("x & y", preset="programming") == [0, 0, 0, 1]


def test_textbook_preset_rejects_programmer_only_symbols():
    with pytest.raises(ParseError):
        run("x ~& y", preset="textbook")


def test_deeply_nested_input_gives_a_clean_error_not_a_crash():
    with pytest.raises(ParseError):
        run("(" * 150 + "x" + ")" * 150)


def test_longest_allowed_inputs_do_not_crash():
    run("x+" * 149 + "x")      # 299 characters, long left-leaning chain
    run("x" * 300)             # 300 characters, long implicit AND chain
    run("a->" * 99 + "a")      # right-associative chain: recursion depth stays under the limit


# -- custom presets ------------------------------------------------------------------------
def test_custom_operator_defined_by_truth_table():
    nimp = OperatorDef(name="NIMP", fixity="infix", symbols=["-/>"], precedence=20, table=[0, 0, 1, 0])
    base = PresetDef(
        name="mine",
        operators=[
            nimp,
            OperatorDef(name="NOT", fixity="postfix", symbols=["'"], precedence=60, table=[1, 0]),
        ],
    )
    assert outputs("x -/> y", custom=base) == [0, 0, 1, 0]
    assert outputs("x' -/> y", custom=base) == [1, 0, 0, 0]


def test_custom_preset_without_implicit_operator():
    preset = PresetDef(
        name="tiny",
        operators=[OperatorDef(name="OR", fixity="infix", symbols=["+"], precedence=10, table=[0, 1, 1, 1])],
    )
    assert outputs("x + y", custom=preset) == [0, 1, 1, 1]
    with pytest.raises(ParseError):
        run("xy", custom=preset)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(symbols=["a"]),                          # single letter is reserved for variables
        dict(symbols=["a&"]),                         # mixes letters and punctuation
        dict(symbols=["1+"]),                         # digits
        dict(symbols=["(+"]),                         # brackets
        dict(symbols=["+"], table=[0, 1, 1]),         # wrong table length
        dict(symbols=["+"], table=[0, 2, 1, 1]),      # not 0/1
        dict(symbols=["+"], nary=True, table=[1, 1, 1, 0]),   # NAND is not associative
    ],
)
def test_invalid_operator_definitions_are_rejected(kwargs):
    fields = dict(name="BAD", fixity="infix", precedence=10, table=[0, 1, 1, 1])
    fields.update(kwargs)
    with pytest.raises(ValueError):
        OperatorDef(**fields)


def test_duplicate_symbols_between_operators_are_rejected():
    a = OperatorDef(name="A1", fixity="infix", symbols=["+"], precedence=10, table=[0, 1, 1, 1])
    b = OperatorDef(name="B1", fixity="infix", symbols=["+"], precedence=20, table=[0, 0, 0, 1])
    with pytest.raises(ValueError):
        PresetDef(name="dup", operators=[a, b])


def test_implicit_must_name_an_infix_operator():
    a = OperatorDef(name="OR", fixity="infix", symbols=["+"], precedence=10, table=[0, 1, 1, 1])
    with pytest.raises(ValueError):
        PresetDef(name="bad", operators=[a], implicit="AND")
