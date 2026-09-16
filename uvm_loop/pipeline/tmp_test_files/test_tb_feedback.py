from pathlib import Path
import tempfile
import yaml

from pipeline.tb_feedback import ensure_simulation_manifest


def test_manifest_bootstrap():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "generation_manifest.yaml").write_text(
            yaml.safe_dump({"dut_name": "adder", "WIDTH": 8})
        )
        (root / "filelist.f").write_text(
            "adder_if.sv\nadder_transaction.sv\nadder_test.sv\nadder_tb_top.sv\n"
        )
        (root / "adder_if.sv").write_text("interface adder_if; endinterface\n")
        (root / "adder_transaction.sv").write_text("class adder_transaction; endclass\n")
        (root / "adder_test.sv").write_text(
            "class adder_test_smoke #(parameter int WIDTH = 8) extends uvm_test; endclass\n"
        )
        (root / "adder_tb_top.sv").write_text(
            "module adder_tb_top; initial begin run_test(); end endmodule\n"
        )

        manifest = yaml.safe_load(ensure_simulation_manifest(str(root)).read_text())
        assert manifest["top_module"] == "adder_tb_top"
        assert manifest["top_file"] == "adder_tb_top.sv"
        assert manifest["compile_files"] == [
            "adder_if.sv",
            "adder_transaction.sv",
            "adder_test.sv",
            "adder_tb_top.sv",
        ]
        assert manifest["test_classes"] == ["adder_test_smoke#(8)"]
