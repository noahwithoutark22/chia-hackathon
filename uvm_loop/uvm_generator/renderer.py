from __future__ import annotations
import hashlib, json
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader
from .generation_schema import GenerationSpec
from .verilator_compat import assert_verilator_compatible

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
ORDER = [
    ("interface.sv.j2", "_if.sv"), ("ref_model_pkg.sv.j2", "_ref_model_pkg.sv"), ("transaction.sv.j2", "_transaction.sv"),
    ("sequencer.sv.j2", "_sequencer.sv"), ("sequences.sv.j2", "_sequences.sv"),
    ("driver.sv.j2", "_driver.sv"), ("monitor.sv.j2", "_monitor.sv"),
    ("agent.sv.j2", "_agent.sv"), ("scoreboard.sv.j2", "_scoreboard.sv"),
    ("env.sv.j2", "_env.sv"), ("test.sv.j2", "_test.sv"),
    ("tb_top.sv.j2", "_tb_top.sv"),
]

def render(spec: GenerationSpec, out_dir: str, rtl_path: str, plan_path: str, ref_model_path: str) -> list[str]:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    written=[]
    for tmpl, suffix in ORDER:
        text = env.get_template(tmpl).render(spec=spec)
        p=out/f"{spec.dut_name}{suffix}"; p.write_text(text); written.append(str(p))
    cpp = env.get_template('ref_model_adapter.cpp.j2').render(spec=spec)
    cpp_path=out/'ref_model_adapter.cpp'; cpp_path.write_text(cpp); written.append(str(cpp_path))
    fl=out/'filelist.f'; fl.write_text('\n'.join(Path(x).name for x in written)+'\n'); written.append(str(fl))
    ref_copy=out/'ref_model.py'; ref_copy.write_bytes(Path(ref_model_path).read_bytes()); written.append(str(ref_copy))
    sv_files = [Path(x).name for x in written if Path(x).suffix == '.sv']
    test_classes = [
        f"{spec.dut_name}_test_{s.name.lower().replace(' ', '_')}"
        for s in spec.scenarios
    ]
    manifest={
        'generator': 'chia-uvm-generator', 'generator_version':'1.1', 'schema_version':spec.schema_version,
        'dut_name':spec.dut_name,
        'rtl_sha256':_sha(rtl_path), 'plan_sha256':_sha(plan_path), 'reference_model_sha256':_sha(ref_model_path),
        'reference_model':spec.scoreboard.reference_model.model_dump(), 'files':[Path(x).name for x in written],
        'top_module': f'{spec.dut_name}_tb_top',
        'top_file': f'{spec.dut_name}_tb_top.sv',
        'compile_files': sv_files,
        'test_classes': test_classes,
    }
    mp=out/'generation_manifest.yaml'; mp.write_text(yaml.safe_dump(manifest, sort_keys=False)); written.append(str(mp))

    # Fail closed on generated source patterns known to trigger Verilator 5.042
    # internal faults. This is a shared generation contract, not an LLM repair.
    assert_verilator_compatible(out)
    return written

def _sha(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()
