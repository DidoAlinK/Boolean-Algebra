from app.presets import PresetDef
from app.service import analyze, resolve_preset


def run(expression: str, preset: str = "universal", mode: str = "expression", custom: PresetDef | None = None) -> dict:
    return analyze(expression, resolve_preset(preset, custom), mode)


def outputs(expression: str, **kw) -> list[int]:
    return [row["output"] for row in run(expression, **kw)["truth_table"]["rows"]]
