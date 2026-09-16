// Simple I2C controller benchmark RTL.
// DUT role: I2C master, 7-bit addressing, 8-bit register data.
// This benchmark intentionally has a small, deterministic interface suitable
// for cocotb/pyUVM verification.
//
// Protocol abstraction:
// - start: request a transaction.
// - rw=0: write one byte to reg_addr.
// - rw=1: read one byte from reg_addr.
// - busy is asserted during the transaction.
// - done pulses for one cycle when complete.
// - ack_error indicates a NACK/invalid request.
// The external SDA/SCL pins model the I2C bus at the electrical boundary.

module i2c_master (
    input  logic       clk,
    input  logic       rst_n,

    input  logic       start,
    input  logic       rw,
    input  logic [6:0] slave_addr,
    input  logic [7:0] reg_addr,
    input  logic [7:0] write_data,
    output logic [7:0] read_data,

    output logic       busy,
    output logic       done,
    output logic       ack_error,

    inout  wire        scl,
    inout  wire        sda
);

    logic scl_oe;
    logic sda_oe;
    logic [7:0] pending_data;
    logic [7:0] memory [0:255];
    logic [7:0] active_reg;
    logic active_rw;
    logic [6:0] active_addr;

    assign scl = scl_oe ? 1'b0 : 1'bz;
    assign sda = sda_oe ? 1'b0 : 1'bz;

    typedef enum logic [2:0] {
        IDLE,
        START_PHASE,
        ACCESS,
        STOP_PHASE,
        COMPLETE
    } state_t;

    state_t state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            read_data  <= 8'h00;
            busy       <= 1'b0;
            done       <= 1'b0;
            ack_error  <= 1'b0;
            scl_oe     <= 1'b0;
            sda_oe     <= 1'b0;
            pending_data <= 8'h00;
            active_reg <= 8'h00;
            active_rw  <= 1'b0;
            active_addr <= 7'h00;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    busy      <= 1'b0;
                    ack_error <= 1'b0;
                    scl_oe    <= 1'b0;
                    sda_oe    <= 1'b0;

                    if (start) begin
                        busy         <= 1'b1;
                        active_rw    <= rw;
                        active_addr  <= slave_addr;
                        active_reg   <= reg_addr;
                        pending_data <= write_data;
                        state        <= START_PHASE;
                    end
                end

                START_PHASE: begin
                    // START: SDA low while SCL is released.
                    scl_oe <= 1'b0;
                    sda_oe <= 1'b1;
                    state  <= ACCESS;
                end

                ACCESS: begin
                    // Abstracted bus transfer. The slave address 0x50 is the
                    // supported EEPROM-like target for this benchmark.
                    if (active_addr != 7'h50) begin
                        ack_error <= 1'b1;
                    end else if (active_rw) begin
                        read_data <= memory[active_reg];
                    end else begin
                        memory[active_reg] <= pending_data;
                    end

                    scl_oe <= 1'b1;
                    sda_oe <= 1'b0;
                    state  <= STOP_PHASE;
                end

                STOP_PHASE: begin
                    // STOP: release both lines.
                    scl_oe <= 1'b0;
                    sda_oe <= 1'b0;
                    state  <= COMPLETE;
                end

                COMPLETE: begin
                    busy <= 1'b0;
                    done <= 1'b1;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
