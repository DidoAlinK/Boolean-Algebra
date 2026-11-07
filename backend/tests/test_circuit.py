import itertools

import pytest

from app.circuit import simulate

from helpers import run

EXPRESSIONS = [
    "x'y + xy'", "x^y", "x + yz", "x'y + z*xyz' + x'y'", "(x + y)'(z + w)", "a nand b nor c",
    "a -> b -> c", "x xnor y xor z", "x + x'", "x x'", "0", "1", "x", "x'", "((a))", "!(a & b) | c ^ d",
    "a b c d e", "a + b + c + d + e + f", "a eqv b",
]


def check_circuit(result):
    circuit = result["circuit"]
    variables = result["variables"]
    expected = {row["index"]: row["output"] for row in result["truth_table"]["rows"]}
    for index, bits in enumerate(itertools.product((0, 1), repeat=len(variables))):
        assert simulate(circuit, dict(zip(variables, bits))) == expected[index], (result["expression"], bits)


@pytest.mark.parametrize("mode", ["expression", "sop", "pos"])
@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_circuit_computes_the_same_function_as_the_truth_table(expression, mode):
    check_circuit(run(expression, mode=mode))


def test_xor_is_one_gate():
    c = run("x^y")["circuit"]
    assert c["gate_count"] == 1
    gate = next(n for n in c["nodes"] if n["kind"] == "gate")
    assert gate["gate"] == "XOR" and gate["shape"] == "xor"


def test_expression_form_of_xor_uses_five_gates():
    assert run("x'y + xy'")["circuit"]["gate_count"] == 5


def test_equal_subexpressions_share_a_gate():
    c = run("x'y + x'y'")["circuit"]
    nots = [n for n in c["nodes"] if n["kind"] == "gate" and n["gate"] == "NOT"]
    assert len(nots) == 2            # x' once (used twice) and y' once


def test_and_chain_is_one_multi_input_gate():
    c = run("xyz")["circuit"]
    gates = [n for n in c["nodes"] if n["kind"] == "gate"]
    assert len(gates) == 1 and len(gates[0]["inputs"]) == 3 and gates[0]["nary"]


def test_non_associative_operators_stay_two_input():
    c = run("a nand b nand c")["circuit"]
    assert c["gate_count"] == 2


def test_sop_mode_is_two_level():
    c = run("x^y", mode="sop")["circuit"]
    kinds = sorted(n["gate"] for n in c["nodes"] if n["kind"] == "gate")
    assert kinds == ["AND", "AND", "NOT", "NOT", "OR"]
    assert c["mode"] == "sop"


def test_pos_mode_is_two_level():
    c = run("x^y", mode="pos")["circuit"]
    kinds = sorted(n["gate"] for n in c["nodes"] if n["kind"] == "gate")
    assert kinds == ["AND", "NOT", "NOT", "OR", "OR"]


def test_layout_is_consistent():
    c = run("x'y + z*xyz' + x'y'")["circuit"]
    by_id = {n["id"]: n for n in c["nodes"]}
    # inputs in column 0, output alone in the last column, every wire goes left to right
    assert all(n["col"] == 0 for n in c["nodes"] if n["kind"] == "input")
    assert by_id[c["output"]]["col"] == c["cols"] - 1
    for edge in c["edges"]:
        assert by_id[edge["source"]]["col"] < by_id[edge["target"]]["col"]
    # no two nodes on the same grid cell
    cells = [(n["col"], n["row"]) for n in c["nodes"]]
    assert len(cells) == len(set(cells))
    assert all(0 <= n["row"] <= c["rows"] - 1 for n in c["nodes"])
    assert len(c["edges"]) == sum(len(n["inputs"]) for n in c["nodes"])


SHAPES = ["x'y + z*xyz' + x'y'", "a ^ b ^ c ^ d", "(a + b)'(c + d)", "a b + c d + e f", "x + yz + x'z'"]


@pytest.mark.parametrize("mode", ["expression", "sop", "pos"])
@pytest.mark.parametrize("expression", SHAPES)
def test_long_wires_get_their_own_lane(expression, mode):
    c = run(expression, mode=mode)["circuit"]
    by_id = {n["id"]: n for n in c["nodes"]}

    # a wire that skips columns has exactly one waypoint in every skipped column, in order
    for edge in c["edges"]:
        a, b = by_id[edge["source"]]["col"], by_id[edge["target"]]["col"]
        assert [p["col"] for p in edge["route"]] == list(range(a + 1, b))

    # every slot in a column (gate, terminal or waypoint) is at least 1 row away from the others,
    # so a wire can never run through a gate
    slots: dict[int, set[float]] = {}
    for n in c["nodes"]:
        slots.setdefault(n["col"], set()).add(n["row"])
    for edge in c["edges"]:
        for p in edge["route"]:
            slots.setdefault(p["col"], set()).add(p["row"])
    for col, rows in slots.items():
        ordered = sorted(rows)
        assert all(b - a >= 0.999 for a, b in zip(ordered, ordered[1:])), (col, ordered)
        assert ordered[0] >= 0 and ordered[-1] <= c["rows"] - 1


def test_wires_from_the_same_source_share_waypoints():
    c = run("a ^ b ^ c ^ d", mode="sop")["circuit"]
    longest = {}
    for edge in c["edges"]:
        key = (edge["source"], tuple((p["col"], p["row"]) for p in edge["route"]))
        longest[key] = longest.get(key, 0) + 1
    assert any(count > 1 for count in longest.values())


def test_input_rail_order_follows_variable_order():
    c = run("z y + x")["circuit"]
    inputs = sorted((n for n in c["nodes"] if n["kind"] == "input"), key=lambda n: n["row"])
    assert [n["label"] for n in inputs] == ["x", "y", "z"]


def test_constant_function_circuit():
    c = run("1")["circuit"]
    assert [n["kind"] for n in c["nodes"]] == ["const", "output"]


def test_huge_circuit_is_skipped_with_a_warning():
    r = run("abcdefgh", mode="sop")       # 8 variables, 1 minterm: small
    assert r["circuit"] is not None
    big = run("a ^ b ^ c ^ d ^ e ^ f ^ g ^ h ^ i ^ j", mode="sop")   # 512 minterms
    assert big["circuit"] is None
    assert any("too large" in w for w in big["warnings"])
