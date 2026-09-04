# CHIA LLM-Driven Cocotb + PyUVM Verification

An LLM-assisted hardware verification framework that generates a **Cocotb + PyUVM** verification environment from a hardware specification and reference model, and uses the generated environment to validate RTL.

## Flow

```text
Specification + Reference Model
              │
              ▼
        CHIA + LLM Pipeline
              │
              ▼
      Verification Contract
              │
              ▼
     Cocotb + PyUVM Testbench
              │
        ┌─────┴─────┐
        ▼           ▼
   Reference      RTL / DUT
     Model           │
        │            │
        └──────┬─────┘
               ▼
        Scoreboard / Checks
               │
               ▼
       Coverage + Results
```

## Features

* LLM-based verification-plan generation
* Automatic **Cocotb + PyUVM** testbench generation
* Reference-model-based scoreboarding
* Directed and randomized testing
* Functional coverage
* Assertions and corner-case checking
* Regression testing
* Automatic verification contract and simulation manifest
* Ray/CHIA-based distributed execution
* Docker-based simulation environment
* Verilator/Chipyard integration

## Generated Testbench

The generated environment includes:

```text
generated_tb/
├── *_transaction.py
├── *_sequences.py
├── *_driver.py
├── *_monitor.py
├── *_sequencer.py
├── *_agent.py
├── *_env.py
├── *_scoreboard.py
├── *_coverage.py
├── *_assertions.py
├── *_test.py
├── test_top.py
├── test_runner.py
├── CONTRACT.md
└── generation_manifest.yaml
```

## Setup

```bash
./setup.sh
```

The setup script configures the environment and starts the CHIA/Ray-based simulation infrastructure.

## Example

The current example uses an `adder` DUT and demonstrates:

* Basic arithmetic tests
* Carry and overflow cases
* Reset testing
* Randomized transactions
* Reference-model checking
* Functional coverage
* Regression execution

## Project Goal

The long-term goal is to enable **RTL-independent verification generation**, where verification infrastructure can be created from the specification and reference model before the final RTL is available, and subsequently used to validate the RTL.

## Status

🚧 **Active development**

The current repository demonstrates automated generation and execution of a Cocotb + PyUVM verification environment for an example hardware block.
