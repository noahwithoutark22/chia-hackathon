# CHIA Generated-TB Validation Updates

This update targets the validated CHIA simulation flow:

- Verilator 5.042
- UVM 1800.2-2020.3.1
- `+define+UVM_NO_DPI`
- `--timing`
- hard per-test timeout
- deterministic `tb_top` watchdog

## What changed

1. **Verilator compatibility contract**
   - The generator is explicitly forbidden from creating parameterized virtual-interface types.
   - Use concrete-width interfaces and `virtual <dut>_if`.
   - Use `uvm_config_db#(virtual <dut>_if)` for interface propagation.
   - The generator prompt distinguishes DUT parameterization from interface-type parameterization.

2. **Deterministic rendered-TB guard**
   - `uvm_generator/verilator_compat.py` scans rendered SystemVerilog and fails closed on the known incompatible patterns.
   - Comments are ignored so documentation examples do not trigger the check.

3. **Manifest contract**
   - `renderer.py` now emits `top_module`, `top_file`, `compile_files`, and exact `test_classes` in `generation_manifest.yaml`.

4. **Simulation diagnostics**
   - The simulator classifies Verilator internal faults separately and records compatibility findings.
   - The diagnosis prompt uses those findings to distinguish a generated-TB compatibility defect from a shared toolchain defect.

5. **Makefile**
   - `sim-generated` now actually invokes `/workspace/workers/sim/run.py`.
   - The example RTL path is corrected to `adder.sv`.

## Important current-TB finding

The uploaded `generated_tb` contains the incompatible pattern:

`virtual adder_if#(WIDTH)`

and corresponding `uvm_config_db#(virtual adder_if#(WIDTH))` usages.

Do not hand-patch this generated environment as the permanent solution. The permanent fix is the generator/template contract above. Regenerate the TB using the updated generator.

## Validation performed

The compatibility unit tests pass:

`2 passed`

The known minimal Verilator experiment also established that the DUT + UVM + concrete-width interface + simple top compiles successfully when `UVM_NO_DPI` is enabled; the internal fault appears when the generated parameterized virtual-interface/config_db pattern is introduced.
