from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def post(body):
    return client.post("/api/analyze", json=body)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_success_shape():
    r = post({"expression": "x'y + xy'"})
    assert r.status_code == 200
    data = r.json()
    assert data["variables"] == ["x", "y"]
    assert data["function_label"] == "F(x, y)"
    assert data["minterms"] == [1, 2] and data["maxterms"] == [0, 3]
    assert data["forms"]["sigma"]["text"] == "Σ m(1, 2)"
    assert data["truth_table"]["rows"][1] == {"index": 1, "inputs": [0, 1], "output": 1}
    assert data["kmap"]["corner"] == "x\\y"
    assert data["circuit"]["gate_count"] == 5
    assert data["circuit"]["mode"] == "expression"
    assert data["warnings"] == []


def test_parse_error_envelope():
    r = post({"expression": "(x+y"})
    assert r.status_code == 422
    assert r.json() == {"error": {"code": "parse_error", "message": "missing ')'", "position": 5}}


def test_unknown_preset():
    r = post({"expression": "x", "preset": "nope"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "unknown_preset"


def test_preset_selection_changes_behaviour():
    assert post({"expression": "xy", "preset": "programming"}).status_code == 422
    assert post({"expression": "x & y", "preset": "programming"}).status_code == 200


def test_circuit_mode_parameter():
    r = post({"expression": "x^y", "circuit_mode": "sop"}).json()
    assert r["circuit"]["mode"] == "sop" and r["circuit"]["gate_count"] == 5


def test_invalid_circuit_mode():
    r = post({"expression": "x", "circuit_mode": "banana"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_expression_length_limit():
    r = post({"expression": "x" * 301})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_missing_expression():
    r = client.post("/api/analyze", json={})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_kmap_warning_for_five_variables():
    r = post({"expression": "abcde"}).json()
    assert r["kmap"] is None and r["warnings"]


def test_list_presets():
    presets = client.get("/api/presets").json()
    assert [p["name"] for p in presets][0] == "universal"
    assert {"universal", "textbook", "programming"} <= {p["name"] for p in presets}
    universal = presets[0]
    names = {(o["name"], o["fixity"]) for o in universal["operators"]}
    assert {("NOT", "prefix"), ("NOT", "postfix"), ("AND", "infix"), ("NAND", "infix"), ("NOR", "infix"),
            ("XOR", "infix"), ("XNOR", "infix"), ("OR", "infix"), ("IMP", "infix"), ("EQV", "infix")} <= names
    assert universal["implicit"] == "AND"


CUSTOM = {
    "name": "mine",
    "operators": [
        {"name": "NIMP", "fixity": "infix", "symbols": ["-/>"], "precedence": 20, "table": [0, 0, 1, 0]},
        {"name": "NOT", "fixity": "postfix", "symbols": ["'"], "precedence": 60, "table": [1, 0]},
    ],
}


def test_custom_preset_in_request():
    r = post({"expression": "x -/> y", "custom_preset": CUSTOM})
    assert r.status_code == 200
    assert r.json()["minterms"] == [2]
    assert r.json()["preset"] == "mine"


def test_validate_endpoint_accepts_and_normalises():
    body = {**CUSTOM, "operators": [{**CUSTOM["operators"][0], "symbols": [" NIMP "]}, CUSTOM["operators"][1]]}
    r = client.post("/api/presets/validate", json=body)
    assert r.status_code == 200
    assert r.json()["operators"][0]["symbols"] == ["nimp"]


def test_validate_endpoint_rejects_bad_preset():
    bad = {**CUSTOM, "operators": [{**CUSTOM["operators"][0], "symbols": ["a"]}]}
    r = client.post("/api/presets/validate", json=bad)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_request"
    assert "single letter" in r.json()["error"]["message"]


def test_openapi_documents_the_contract():
    schema = client.get("/openapi.json").json()
    assert "/api/analyze" in schema["paths"]
    assert "AnalyzeResponse" in schema["components"]["schemas"]
