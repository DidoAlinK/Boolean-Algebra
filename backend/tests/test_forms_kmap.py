from helpers import run


def forms(expression):
    return run(expression)["forms"]


def test_xor_forms():
    f = forms("x'y + xy'")
    assert f["sigma"]["text"] == "Σ m(1, 2)"
    assert f["pi"]["text"] == "Π M(0, 3)"
    assert f["sop"]["text"] == "x'y + xy'"
    assert f["pos"]["text"] == "(x + y)(x' + y')"
    assert f["sop"]["terms"][0] == {"index": 1, "bits": "01", "term": "x'y"}


def test_x_or_yz():
    r = run("x + yz")
    assert r["minterms"] == [3, 4, 5, 6, 7]
    assert r["maxterms"] == [0, 1, 2]
    assert r["forms"]["shorter"] == "pos"


def test_three_variable_terms_follow_alphabetical_msb_first():
    assert forms("x'y'z' + xyz")["sop"]["text"] == "x'y'z' + xyz"
    assert forms("xyz")["pos"]["text"] == "(x + y + z)(x + y + z')(x + y' + z)(x + y' + z')(x' + y + z)(x' + y + z')(x' + y' + z)"


def test_tautology_has_no_maxterms():
    f = forms("x + x'")
    assert f["pi"]["text"] == "Π M()"
    assert f["pos"]["text"] == "1"
    assert f["sop"]["text"] == "x' + x"


def test_contradiction_has_no_minterms():
    f = forms("x x'")
    assert f["sigma"]["text"] == "Σ m()"
    assert f["sop"]["text"] == "0"


def test_constants_without_variables():
    assert forms("0")["sop"]["text"] == "0"
    assert forms("0")["pos"]["text"] == "0"
    assert forms("1")["sop"]["text"] == "1"
    assert forms("1")["pos"]["text"] == "1"


def test_shorter_prefers_sop_on_a_tie():
    assert forms("x'y + xy'")["shorter"] == "sop"


# -- K-map ----------------------------------------------------------------------------------
def test_kmap_two_variables():
    k = run("x^y")["kmap"]
    assert k["row_labels"] == ["0", "1"] and k["col_labels"] == ["0", "1"]
    assert [[c["value"] for c in row] for row in k["cells"]] == [[0, 1], [1, 0]]
    assert k["corner"] == "x\\y"


def test_kmap_three_variables_uses_gray_code_columns():
    k = run("x + yz")["kmap"]
    assert k["col_labels"] == ["00", "01", "11", "10"]
    assert k["row_vars"] == ["x"] and k["col_vars"] == ["y", "z"]
    row0 = k["cells"][0]
    assert [c["index"] for c in row0] == [0, 1, 3, 2]
    assert [c["value"] for c in row0] == [0, 0, 1, 0]
    assert [c["value"] for c in k["cells"][1]] == [1, 1, 1, 1]


def test_kmap_four_variables():
    k = run("ab + cd")["kmap"]
    assert k["row_labels"] == ["00", "01", "11", "10"]
    assert k["col_labels"] == ["00", "01", "11", "10"]
    values = {c["index"]: c["value"] for row in k["cells"] for c in row}
    assert values == {i: int(bool(i & 0b1100 == 0b1100 or i & 0b0011 == 0b0011)) for i in range(16)}


def test_kmap_one_variable():
    k = run("x'")["kmap"]
    assert k["row_labels"] == [""] and k["col_labels"] == ["0", "1"]
    assert [[c["value"] for c in row] for row in k["cells"]] == [[1, 0]]


def test_kmap_skipped_above_four_variables_with_warning():
    r = run("abcde")
    assert r["kmap"] is None
    assert any("K-map" in w for w in r["warnings"])


def test_kmap_skipped_without_variables():
    assert run("1")["kmap"] is None
