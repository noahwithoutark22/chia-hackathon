`timescale 1ns/1ps
module aes_tb;
    reg clk, rst_n, start;
    reg [127:0] key, plaintext;
    wire [127:0] ciphertext;
    wire busy, done;

    aes128 dut(.clk(clk), .rst_n(rst_n), .start(start),
               .key(key), .plaintext(plaintext),
               .ciphertext(ciphertext), .busy(busy), .done(done));

    initial clk = 0;
    always #5 clk = ~clk;

    integer cycle;
    integer start_cycle;
    reg start_sampled;

    // Monitor values sampled AT each posedge (Preponed perspective)
    // We sample the register state that a testbench checking done at
    // posedge would observe.
    always @(posedge clk) begin
        if (rst_n) begin
            $display("posedge cycle=%0d: done=%b busy=%b state_active=%0d",
                     cycle, done, busy, dut.state);
        end
        if (start_sampled && cycle > 0)
            cycle = cycle + 1;
    end

    initial begin
        cycle = 0;
        start_sampled = 0;
        rst_n = 0; start = 0; key = 0; plaintext = 0;
        repeat(5) @(posedge clk);
        @(negedge clk); rst_n = 1;
        @(negedge clk);

        key = 128'h000102030405060708090a0b0c0d0e0f;
        plaintext = 128'h00112233445566778899aabbccddeeff;
        @(negedge clk);
        start = 1;
        @(posedge clk);   // start sampled here (cycle 0)
        start_cycle = 0;
        start_sampled = 1;
        cycle = 0;
        @(negedge clk);
        start = 0;
        $display("start accepted at posedge #0. Now monitoring...");
        @(posedge clk);  // cycle 1
        @(posedge clk);  // cycle 2
        @(posedge clk);  // cycle 3
        @(posedge clk);  // cycle 4
        @(posedge clk);  // cycle 5
        @(posedge clk);  // cycle 6
        @(posedge clk);  // cycle 7
        @(posedge clk);  // cycle 8
        @(posedge clk);  // cycle 9
        @(posedge clk);  // cycle 10
        @(posedge clk);  // cycle 11
        $display("cycle 11 done=%b busy=%b", done, busy);
        @(posedge clk);  // cycle 12
        $display("cycle 12 done=%b busy=%b", done, busy);
        @(posedge clk);  // cycle 13
        $display("cycle 13 done=%b busy=%b", done, busy);
        $finish;
    end
endmodule
