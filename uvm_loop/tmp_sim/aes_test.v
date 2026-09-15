`timescale 1ns/1ps
module aes_testbench;
    reg clk, rst_n, start;
    reg [127:0] key, plaintext;
    wire [127:0] ciphertext;
    wire busy, done;

    aes128 dut(.clk(clk), .rst_n(rst_n), .start(start),
               .key(key), .plaintext(plaintext),
               .ciphertext(ciphertext), .busy(busy), .done(done));

    initial clk = 0;
    always #5 clk = ~clk;

    integer cycle_count;
    integer start_cyc;

    initial begin
        rst_n = 0;
        start = 0;
        key = 0;
        plaintext = 0;

        repeat(5) @(posedge clk);
        @(negedge clk);
        rst_n = 1;
        @(negedge clk);

        // NIST KAT
        key = 128'h000102030405060708090a0b0c0d0e0f;
        plaintext = 128'h00112233445566778899aabbccddeeff;

        @(negedge clk);
        start = 1;
        @(negedge clk);
        start = 0;
        start_cyc = 0;

        while (!done) begin
            @(negedge clk);
            start_cyc = start_cyc + 1;
            if (start_cyc > 30) begin
                $display("TIMEOUT");
                $finish;
            end
        end

        $display("NIST KAT DUT ciphertext: %032h", ciphertext);
        $display("NIST KAT cycles start->done: %0d", start_cyc);
        $display("  expected correct AES: 69c4e0d86a7b0430d8cdb78070b4c55a");

        // Track done pulse width
        begin
            integer pw1, pw2;
            pw1 = 1;
            @(negedge clk);
            while (done) begin
                pw1 = pw1 + 1;
                @(negedge clk);
            end
            $display("done pulse width measured: %0d", pw1);
        end

        // All-zero test
        key = 128'h0;
        plaintext = 128'h0;
        @(negedge clk);
        start = 1;
        @(negedge clk);
        start = 0;
        start_cyc = 0;
        while (!done) begin
            @(negedge clk);
            start_cyc = start_cyc + 1;
        end
        $display("All-zero DUT ciphertext: %032h", ciphertext);
        $display("All-zero cycles start->done: %0d", start_cyc);
        $display("  expected correct AES: 66e94bd4ef8a2c3b884cfa59ca342b2e");

        // Check busy behavior
        $display("busy at done time: %b", busy);

        $finish;
    end
endmodule
