from pathlib import Path

from uvm_generator.verilator_compat import find_forbidden_patterns, assert_verilator_compatible


def test_parameterized_virtual_interface_is_rejected(tmp_path: Path):
    (tmp_path / "bad.sv").write_text(
        "virtual adder_if#(WIDTH) vif;\n"
        "uvm_config_db#(virtual adder_if#(WIDTH))::get(this, \"\", \"vif\", vif);\n"
    )
    findings = find_forbidden_patterns(tmp_path)
    codes = {f["code"] for f in findings}
    assert "parameterized_virtual_interface" in codes
    assert "parameterized_config_db_virtual_interface" in codes


def test_comment_examples_are_ignored(tmp_path: Path):
    (tmp_path / "ok.sv").write_text(
        "// virtual adder_if#(WIDTH) vif;\n"
        "/* uvm_config_db#(virtual adder_if#(WIDTH)) */\n"
        "virtual adder_if vif;\n"
    )
    assert find_forbidden_patterns(tmp_path) == []
    assert_verilator_compatible(tmp_path)
