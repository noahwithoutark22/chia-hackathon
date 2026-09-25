module i2c_master #(
    parameter int CLK_DIV = 4
) (
    input  logic       clk,
    input  logic       rst_n,

    input  logic       start,
    input  logic [6:0] slave_addr,
    input  logic       rw,          // 0 = write, 1 = read
    input  logic [7:0] tx_data,

    input  logic       sda_in,
    input  logic       scl_in,

    output logic       sda_out,
    output logic       sda_oe,
    output logic       scl_out,
    output logic       scl_oe,

    output logic [7:0] rx_data,
    output logic       done,
    output logic       busy,
    output logic       ack_error
);

    typedef enum logic [3:0] {
        IDLE,
        START_COND,
        SEND_ADDR,
        ADDR_ACK,
        SEND_DATA,
        DATA_ACK,
        READ_DATA,
        READ_ACK,
        STOP_COND
    } state_t;

    state_t state;

    logic [$clog2(CLK_DIV)-1:0] div_cnt;
    logic [3:0] bit_cnt;
    logic [7:0] shift_reg;
    logic [7:0] rx_shift;

    assign sda_oe  = busy;
    assign scl_oe  = busy;
    assign sda_out = 1'b0;
    assign scl_out = 1'b0;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state      <= IDLE;
            div_cnt    <= '0;
            bit_cnt    <= 4'd0;
            shift_reg  <= 8'd0;
            rx_shift   <= 8'd0;
            rx_data    <= 8'd0;
            done       <= 1'b0;
            busy       <= 1'b0;
            ack_error  <= 1'b0;
        end else begin
            done <= 1'b0;

            if (state == IDLE && start) begin
                busy      <= 1'b1;
                shift_reg <= {slave_addr, ~rw};
                bit_cnt   <= 4'd6;
                state     <= START_COND;
            end else if (div_cnt == CLK_DIV - 1) begin
                div_cnt <= '0;

                case (state)
                    IDLE: begin
                        busy      <= 1'b0;
                        ack_error <= 1'b1;
                    end

                    START_COND: begin
                        state <= SEND_ADDR;
                    end

                    SEND_ADDR: begin
                        if (bit_cnt == 1) begin
                            state <= ADDR_ACK;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                        end
                    end

                    ADDR_ACK: begin
                        if (sda_in == 1'b0)
                            ack_error <= 1'b1;

                        if (rw) begin
                            bit_cnt <= 4'd7;
                            rx_shift <= 8'd0;
                            state <= READ_DATA;
                        end else begin
                            shift_reg <= ~tx_data;
                            bit_cnt <= 4'd7;
                            state <= SEND_DATA;
                        end
                    end

                    SEND_DATA: begin
                        if (bit_cnt == 0) begin
                            state <= DATA_ACK;
                        end else begin
                            bit_cnt <= bit_cnt - 1'b1;
                        end
                    end

                    DATA_ACK: begin
                        if (sda_in == 1'b0)
                            ack_error <= 1'b1;
                        state <= STOP_COND;
                    end

                    READ_DATA: begin
                        rx_shift[7-bit_cnt] <= sda_in;

                        if (bit_cnt == 1) begin
                            state <= READ_ACK;
                        end else begin
                            bit_cnt <= bit_cnt - 1'b1;
                        end
                    end

                    READ_ACK: begin
                        rx_data <= ~rx_shift;
                        state <= STOP_COND;
                    end

                    STOP_COND: begin
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= IDLE;
                    end

                    default: begin
                        state <= IDLE;
                        busy <= 1'b0;
                    end
                endcase
            end else begin
                div_cnt <= div_cnt + 1'b1;
            end
        end
    end

endmodule
