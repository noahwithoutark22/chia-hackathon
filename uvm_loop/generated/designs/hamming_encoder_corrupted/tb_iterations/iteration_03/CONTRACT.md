# Hamming Encoder TB Contract

## Top Module Name
- `hamming_encoder`

## DUT Pins
| Pin Name   | Direction | Width | Access Method |
|------------|-----------|-------|---------------|
| data_in    | input     | 64 bits | `dut.data_in` |
| codeword   | output    | 72 bits | `dut.codeword` |

## Transaction Fields
| Field Name | Type       | Description          |
|------------|------------|----------------------|
|------------|------------|----------------------|
| data_in    | int (64-bit) | Input data to encode |
| codeword   | int (72-bit) | Encoded codeword output |

## ConfigDB Sharing
- Key: `dut_helper`
  - Type: `HammingEncoderDUTHelper` (from `dut_helper` module)
  - Description: Helper object providing access to DUT pins (`data_in` and `codeword`).

## Clock and Reset
- The DUT has no clock or reset ports.
- No clock or reset signals are required in the testbench.
- The testbench uses value change events on the input signal (data_in) for synchronization instead of a clock.
