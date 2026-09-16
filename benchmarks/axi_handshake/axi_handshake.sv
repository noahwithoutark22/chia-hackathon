// INTENTIONALLY WRONG RTL.
// The specification and ref_model.py define the intended behavior.
// This implementation incorrectly accepts/overwrites data while the output
// side is stalled and therefore violates AXI-Stream VALID/READY semantics.

module axi_handshake (
    input  logic       clk,
    input  logic       rst_n,

    input  logic       s_valid,
    output logic       s_ready,
    input  logic [7:0] s_data,

    output logic       m_valid,
    input  logic       m_ready,
    output logic [7:0] m_data
);

    logic [7:0] data_reg;

    // WRONG: always ready, even when an existing output is stalled.
    assign s_ready = 1'b1;

    assign m_valid = rst_n;
    assign m_data  = data_reg;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            data_reg <= 8'h00;
        end else begin
            // WRONG: updates the stored payload whenever s_valid is high,
            // even when s_ready should not permit a transfer.
            if (s_valid)
                data_reg <= s_data;
        end
    end

endmodule
