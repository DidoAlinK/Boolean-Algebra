import itertools
import random
import string

import pytest
from fastapi.testclient import TestClient

from app.circuit import simulate
from app.config import MAX_VARIABLES
from app.evaluator import evaluate, row_bits
from app.main import app
from app.parser import Parser
from app.presets import BUILTIN_PRESETS, CompiledPreset
from app.service import synthesize
from app.tokenizer import tokenize

client = TestClient(app)


def names(n):
    return list(string.ascii_lowercase[:n])


def outputs_of_expression(expression, variables):
    """Re-reads the function text with the normal parser and evaluates it on every row."""
    preset = CompiledPreset(BUILTIN_PRESETS["universal"])
    tree = Parser(tokenize(expression, preset), preset).parse()
    n = len(variables)
    return [evaluate(tree, dict(zip(variables, row_bits(i, n)))) for i in range(1 << n)]


# -- the function that comes back is really the function that was drawn in the table -----------
@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize("form", ["sop", "pos", "auto"])
def test_every_function_of_up_to_three_variables_round_trips(n, form):
    for outputs in itertools.product((0, 1), repeat=1 << n):
        result = synthesize(list(outputs), names(n), form)
        assert outputs_of_expression(result["expression"], names(n)) == list(outputs), (outputs, form)


def test_random_four_and_five_variable_functions_round_trip():
    rng = random.Random(7)
    for n in (4, 5):
        for _ in range(60):
            outputs = [rng.randint(0, 1) for _ in range(1 << n)]
            for form in ("sop", "pos"):
                result = synthesize(outputs, names(n), form)
                assert outputs_of_expression(result["expression"], names(n)) == outputs


# -- the circuit computes the table, in every combination of form and circuit mode -----------
@pytest.mark.parametrize("form", ["auto", "sop", "pos"])
@pytest.mark.parametrize("mode", ["expression", "sop", "pos"])
def test_circuit_matches_the_table(form, mode):
    rng = random.Random(11)
    for n in range(1, 6):
        for _ in range(8):
            outputs = [rng.randint(0, 1) for _ in range(1 << n)]
            result = synthesize(outputs, names(n), form, mode)
            circuit = result["circuit"]
            assert circuit is not None
            for index in range(1 << n):
                env = dict(zip(names(n), row_bits(index, n)))
                assert simulate(circuit, env) == outputs[index], (n, outputs, form, mode, index)


# -- exact answers worked out by hand --------------------------------------------------------
def test_xor_table():
    r = synthesize([0, 1, 1, 0], ["a", "b"])
    assert r["expression"] == "a'b + ab'"
    assert r["minterms"] == [1, 2] and r["maxterms"] == [0, 3]
    assert r["forms"]["sigma"]["text"] == "Σ m(1, 2)"
    assert r["forms"]["pi"]["text"] == "Π M(0, 3)"
    assert r["forms"]["shorter"] == "sop"
    assert r["structure"] == "OR(AND(NOT(a), b), AND(a, NOT(b)))"
    assert r["function_label"] == "F(a, b)"
    assert r["circuit"]["gate_count"] == 5 and r["circuit"]["mode"] == "expression"


def test_pos_form_is_used_when_forced_or_shorter():
    assert synthesize([0, 1, 1, 0], ["a", "b"], "pos")["expression"] == "(a + b)(a' + b')"
    # a + bc has 5 ones and 3 zeros, so auto picks the product of sums
    r = synthesize([0, 0, 0, 1, 1, 1, 1, 1], ["a", "b", "c"])
    assert r["forms"]["shorter"] == "pos"
    assert r["expression"] == "(a + b + c)(a + b + c')(a + b' + c)"


def test_custom_variable_names():
    r = synthesize([0, 0, 0, 1], ["x", "y"])
    assert r["variables"] == ["x", "y"] and r["expression"] == "xy"


def test_constant_functions_keep_all_variables():
    zero = synthesize([0, 0, 0, 0], ["a", "b"])
    assert zero["expression"] == "0" and zero["variables"] == ["a", "b"]
    assert len(zero["truth_table"]["rows"]) == 4
    assert [n["kind"] for n in zero["circuit"]["nodes"]] == ["const", "output"]
    one = synthesize([1, 1, 1, 1], ["a", "b"])
    assert one["expression"] == "1" and one["forms"]["shorter"] == "pos"
    assert one["forms"]["pi"]["text"] == "Π M()"


def test_forced_form_on_a_constant_still_works():
    assert synthesize([1, 1], ["a"], "sop")["expression"] == "a' + a"
    assert synthesize([0, 0], ["a"], "pos")["expression"] == "(a)(a')"


def test_kmap_of_a_three_variable_table():
    r = synthesize([0, 0, 1, 1, 1, 1, 0, 0], ["a", "b", "c"])
    k = r["kmap"]
    assert k["col_labels"] == ["00", "01", "11", "10"] and k["corner"] == "a\\bc"
    # index = a*4 + bc, columns in Gray order bc = 00, 01, 11, 10
    assert [[c["value"] for c in row] for row in k["cells"]] == [[0, 0, 1, 1], [1, 1, 0, 0]]
    assert [[c["index"] for c in row] for row in k["cells"]] == [[0, 1, 3, 2], [4, 5, 7, 6]]


def test_large_tables_warn_instead_of_failing():
    outputs = [i % 2 for i in range(32)]
    r = synthesize(outputs, names(5))
    assert r["kmap"] is None and any("K-map" in w for w in r["warnings"])
    rng = random.Random(3)
    big = [rng.randint(0, 1) for _ in range(1 << 10)]
    r = synthesize(big, names(10))
    assert r["circuit"] is None and any("too large" in w for w in r["warnings"])
    assert len(r["truth_table"]["rows"]) == 1024


def test_the_maximum_size_works_and_stays_fast():
    rng = random.Random(5)
    outputs = [rng.randint(0, 1) for _ in range(1 << MAX_VARIABLES)]
    r = synthesize(outputs, names(MAX_VARIABLES))
    assert r["minterms"] == [i for i, v in enumerate(outputs) if v]


# -- the HTTP endpoint -----------------------------------------------------------------------
def post(body):
    return client.post("/api/synthesize", json=body)


def test_endpoint_returns_the_analyze_shape():
    r = post({"outputs": [0, 1, 1, 0]})
    assert r.status_code == 200
    data = r.json()
    analyzed = client.post("/api/analyze", json={"expression": "a'b + ab'"}).json()
    assert set(data) == set(analyzed)
    assert data["expression"] == "a'b + ab'" and data["variables"] == ["a", "b"]
    assert data["forms"] == analyzed["forms"] and data["kmap"] == analyzed["kmap"]
    assert data["truth_table"] == analyzed["truth_table"]
    assert data["circuit"]["gate_count"] == 5


def test_endpoint_options():
    r = post({"outputs": [0, 1, 1, 0], "variables": ["x", "y"], "function_form": "pos", "circuit_mode": "sop"}).json()
    assert r["expression"] == "(x + y)(x' + y')"
    assert r["circuit"]["mode"] == "sop"


@pytest.mark.parametrize(
    "body, fragment",
    [
        ({"outputs": [0, 1, 1]}, "got 3"),
        ({"outputs": [1]}, "got 1"),
        ({"outputs": []}, "got 0"),
        ({"outputs": [0] * (2 ** MAX_VARIABLES * 2)}, f"got {2 ** MAX_VARIABLES * 2}"),
        ({"outputs": [0, 2, 1, 0]}, "outputs.1"),
        ({"outputs": [0, "x", 1, 0]}, "outputs.1"),
        ({"outputs": [0, 1, 1, 0], "variables": ["a"]}, "exactly 2 names"),
        ({"outputs": [0, 1, 1, 0], "variables": ["a", "b", "c"]}, "exactly 2 names"),
        ({"outputs": [0, 1, 1, 0], "variables": ["b", "a"]}, "alphabetical order"),
        ({"outputs": [0, 1, 1, 0], "variables": ["a", "a"]}, "alphabetical order"),
        ({"outputs": [0, 1, 1, 0], "variables": ["A", "B"]}, "lowercase letters"),
        ({"outputs": [0, 1, 1, 0], "variables": ["ab", "c"]}, "lowercase letters"),
        ({"outputs": [0, 1, 1, 0], "variables": ["1", "2"]}, "lowercase letters"),
        ({"outputs": [0, 1, 1, 0], "function_form": "banana"}, "function_form"),
        ({"outputs": [0, 1, 1, 0], "circuit_mode": "banana"}, "circuit_mode"),
        ({}, "outputs"),
    ],
)
def test_endpoint_rejects_bad_tables_with_the_standard_envelope(body, fragment):
    r = post(body)
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "invalid_request"
    assert fragment in error["message"]
    assert "Value error" not in error["message"]


def test_json_booleans_are_normalised_to_plain_bits():
    r = post({"outputs": [True, False, False, True]})
    assert r.status_code == 200
    assert [row["output"] for row in r.json()["truth_table"]["rows"]] == [1, 0, 0, 1]
    assert all(type(row["output"]) is int for row in r.json()["truth_table"]["rows"])


def test_openapi_lists_the_endpoint():
    schema = client.get("/openapi.json").json()
    assert "/api/synthesize" in schema["paths"]
    assert "SynthesizeRequest" in schema["components"]["schemas"]
