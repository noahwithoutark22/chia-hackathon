# AXI Handshake Benchmark

Files:
- `axi_handshake.sv` — intentionally incorrect DUT RTL.
- `spec.md` — intended AXI-Stream handshake behavior.
- `ref_model.py` — correct Python behavioral reference model.

This is a good benchmark for testing whether a verification-generation loop keeps
functional intent independent from the candidate RTL.

Expected outcome:
- The generated environment should compile and run against `axi_handshake.sv`.
- Tests that stall `m_ready` while changing `s_data`/holding `s_valid` should expose
  the incorrect RTL.
- The scoreboard should obtain expected behavior from `ref_model.py`, not from
  observed RTL behavior.
- The benchmark RTL should remain unchanged by verification generation.
