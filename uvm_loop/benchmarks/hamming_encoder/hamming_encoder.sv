// =============================================================================
// File        : hamming_encoder.sv
// Description : Parameterized Hamming(N,K) encoder, with optional SECDED
//               (single-error-correction, double-error-detection) extra
//               overall-parity bit.
//
//               Given DATA_WIDTH data bits, the module automatically computes
//               the minimum number of parity bits required and constructs the
//               encoded Hamming codeword according to the classic
//               "power-of-two position" algorithm.
//
// Parameters  :
//   DATA_WIDTH : number of input data bits (K).            default = 4
//   SECDED     : 1 = add an extra overall parity bit for    default = 0
//                double-error detection (Hamming(N+1,K)).
//
// Derived (localparam) :
//   PARITY_BITS : number of Hamming parity bits (R), the minimum R such
//                 that 2^R >= DATA_WIDTH + R + 1.
//   CODE_WIDTH  : DATA_WIDTH + PARITY_BITS (+1 if SECDED)  (N)
//
// Bit ordering / position convention (see spec.md for full details) :
//   - Codeword positions are numbered 1..(DATA_WIDTH+PARITY_BITS), MSB-first
//     internally, where any position that is an exact power of two (1,2,4,8,
//     ...) holds a parity bit, and all other positions hold data bits taken
//     in order from data_in[0] upward.
//   - code_out[0] corresponds to Hamming position 1 (the first parity bit).
//   - If SECDED = 1, an extra overall even-parity bit is computed over the
//     whole base Hamming codeword and placed at code_out[0]; the base
//     codeword occupies code_out[CODE_WIDTH-1:1].
// =============================================================================

`ifndef HAMMING_PKG_SV
`define HAMMING_PKG_SV

package hamming_pkg;

  // Minimum number of parity bits R such that 2^R >= k + R + 1
  function automatic int unsigned num_parity_bits(input int unsigned k);
    int unsigned r;
    begin
      r = 0;
      while ((32'(1) << r) < (k + r + 1)) begin
        r = r + 1;
      end
      num_parity_bits = r;
    end
  endfunction

  // Returns 1 if n is an exact power of two (1,2,4,8,...); 0 is not.
  function automatic bit is_power_of_two(input int unsigned n);
    begin
      is_power_of_two = (n != 0) && ((n & (n - 1)) == 0);
    end
  endfunction

endpackage : hamming_pkg

`endif // HAMMING_PKG_SV


module hamming_encoder
  import hamming_pkg::*;
#(
  parameter  int unsigned DATA_WIDTH  = 4,
  parameter  bit          SECDED      = 1'b0,
  localparam int unsigned PARITY_BITS = num_parity_bits(DATA_WIDTH),
  localparam int unsigned BASE_WIDTH  = DATA_WIDTH + PARITY_BITS,
  localparam int unsigned CODE_WIDTH  = BASE_WIDTH + (SECDED ? 1 : 0)
)(
  input  logic [DATA_WIDTH-1:0] data_in,
  output logic [CODE_WIDTH-1:0] code_out
);

  // Compile-time sanity checks
  initial begin
    assert (DATA_WIDTH > 0)
      else $fatal(1, "hamming_encoder: DATA_WIDTH must be > 0");
  end

  // ham[BASE_WIDTH:1] : 1-indexed Hamming codeword prior to any SECDED bit.
  // ham[BASE_WIDTH] is the MSB, ham[1] is the LSB -> code_out[0] = ham[1].
  logic [BASE_WIDTH:1] ham;

  always_comb begin : build_and_encode
    int unsigned data_idx;
    int unsigned pos;
    int unsigned p;
    int unsigned parity_pos;
    logic        par;
    logic        overall_par;

    // 1) Scatter data bits into all non-power-of-two positions, in order.
    data_idx = 0;
    for (pos = 1; pos <= BASE_WIDTH; pos++) begin
      if (is_power_of_two(pos)) begin
        ham[pos] = 1'b0; // placeholder; overwritten by the parity pass below
      end else begin
        ham[pos] = data_in[data_idx];
        data_idx++;
      end
    end

    // 2) Compute each parity bit as the XOR of all positions whose binary
    //    index has that parity bit's bit-position set (excluding itself).
    for (p = 0; p < PARITY_BITS; p++) begin
      parity_pos = (32'(1) << p);
      par        = 1'b0;
      for (pos = 1; pos <= BASE_WIDTH; pos++) begin
        if ((pos != parity_pos) && ((pos & parity_pos) != 0)) begin
          par ^= ham[pos];
        end
      end
      ham[parity_pos] = par;
    end

    // 3) Optionally compute an overall (SECDED) even-parity bit over the
    //    complete base Hamming codeword and prepend it as the new LSB.
    if (SECDED) begin
      overall_par = ^ham;
      code_out    = {ham, overall_par};
    end else begin
      code_out = ham;
    end
  end

endmodule : hamming_encoder
