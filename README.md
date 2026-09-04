# CHIA — LLM-Driven Hardware Automation

CHIA consists of **two independent LLM-driven loops** that are currently being developed separately. They will be interfaced in the final system.

---

## 1. LLM-Driven RTL Verification Loop

The verification loop first generates the **verification infrastructure from the specification and reference model**. The generated environment is then used to verify the RTL. Verification failures can be used to guide **RTL modification**, followed by another verification cycle.

```text
        Specification
              │
        Reference Model
              │
              ▼
         CHIA + LLM
              │
              ▼
   Generate Verification
       Infrastructure
              │
              ▼
      Cocotb + PyUVM
       Verification TB
              │
              ▼
          Verify RTL
              │
        ┌─────┴─────┐
        │           │
      PASS        FAIL
        │           │
        ▼           ▼
 Verification   Analyze Failure
   Complete          │
                     ▼
                Modify RTL
                     │
                     └──────────► Verify RTL
```

### Key capabilities

* Specification and reference-model-driven verification generation
* Automatic Cocotb + PyUVM infrastructure generation
* Reference-model-based scoreboarding
* Directed and randomized testing
* Functional coverage
* Assertions and corner-case checking
* Automatic regression
* Verification failure analysis
* RTL modification and re-verification
* Distributed execution through CHIA/Ray

### Objective

Enable **RTL-independent verification infrastructure generation**, so that the verification environment can be created before the final RTL is available and subsequently used to validate and iteratively improve the RTL.

---

## 2. LLM-Driven RTL-to-GDS Optimization Loop

The second loop independently focuses on **physical implementation and PPA optimization**. It repeatedly runs ORFS, analyzes implementation results, and uses the LLM to propose constrained changes to physical-design parameters.

```text
          RTL
           │
           ▼
      ORFS Flow
           │
           ▼
    PPA / Timing /
       DRC Results
           │
           ▼
       CHIA + LLM
           │
           ▼
  Optimize Flow Parameters
           │
           ▼
       Next ORFS Run
           │
           └──────────────► Repeat
                              │
                              ▼
                     Closure / Best GDS
```

The CHIA driver controls execution while the LLM proposes changes to a predefined, constrained set of tunable parameters.

### Key capabilities

* LLM-guided PPA optimization
* Timing and area optimization
* Constrained/whitelisted tunables
* Hard parameter locking
* Parallel implementation experiments
* Optimization-effect tracking
* Stall diagnosis
* DRC/LVS signoff
* GDS generation and reporting
* Ray-based distributed execution
* Docker-based ORFS environment

---

## Future Integration

The two loops remain **independent during development**:

```text
┌─────────────────────────────────┐
│     RTL VERIFICATION LOOP       │
│                                 │
│ Spec + Reference Model          │
│          ↓                      │
│ Verification Infrastructure     │
│          ↓                      │
│       RTL Verification          │
│          ↓                      │
│   RTL Modification ↺            │
└───────────────┬─────────────────┘
                │
                │ Future Interface
                │
┌───────────────▼─────────────────┐
│      RTL-to-GDS LOOP            │
│                                 │
│          RTL                    │
│          ↓                      │
│        ORFS                     │
│          ↓                      │
│   PPA / Timing / DRC            │
│          ↓                      │
│   LLM Optimization ↺            │
│          ↓                      │
│        Best GDS                 │
└─────────────────────────────────┘
```

The final objective is to interface the two loops so that a **verified RTL can enter the physical-design optimization loop**, while implementation feedback can eventually be incorporated into the broader hardware development process.

**Status:** Active development
