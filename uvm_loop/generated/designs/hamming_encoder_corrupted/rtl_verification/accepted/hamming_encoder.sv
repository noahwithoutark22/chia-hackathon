module hamming_encoder (
    input  logic [63:0] data_in,
    output logic [71:0] codeword
);

    integer pos;
    integer data_idx;

    logic [71:1] hamming_bits;
    logic p1, p2, p4, p8, p16, p32, p64;
    logic overall_parity;

    function automatic logic is_parity_position(input integer p);
        is_parity_position =
            (p == 1)  || (p == 2)  || (p == 4) ||
            (p == 8)  || (p == 16) || (p == 32) ||
            (p == 64);
    endfunction

    always_comb begin
        hamming_bits = '0;
        data_idx = 0;

        for (pos = 1; pos <= 71; pos = pos + 1) begin
            if (!is_parity_position(pos)) begin
                hamming_bits[pos] = data_in[data_idx];
                data_idx = data_idx + 1;
            end
        end

        p1  = 1'b0;
        p2  = 1'b0;
        p4  = 1'b0;
        p8  = 1'b0;
        p16 = 1'b0;
        p32 = 1'b0;
        p64 = 1'b0;

        for (pos = 1; pos <= 71; pos = pos + 1) begin
            if (pos & 1)
                p1 = p1 ^ hamming_bits[pos];

            if (pos & 2)
                p2 = p2 ^ hamming_bits[pos];

            if (pos & 4)
                p4 = p4 ^ hamming_bits[pos];

            if (pos & 8)
                p8 = p8 ^ hamming_bits[pos];

            if (pos & 16)
                p16 = p16 ^ hamming_bits[pos];

            if (pos & 32)
                p32 = p32 ^ hamming_bits[pos];

            if (pos & 64)
                p64 = p64 ^ hamming_bits[pos];
        end

        hamming_bits[1]  = p1;
        hamming_bits[2]  = p2;
        hamming_bits[4]  = p4;
        hamming_bits[8]  = p8;
        hamming_bits[16] = p16;
        hamming_bits[32] = p32;
        hamming_bits[64] = p64;

        for (pos = 1; pos <= 71; pos = pos + 1)
            codeword[pos] = hamming_bits[pos];

        overall_parity = 1'b0;
        for (pos = 1; pos <= 71; pos = pos + 1)
            overall_parity = overall_parity ^ hamming_bits[pos];

        codeword[0] = overall_parity;
    end

endmodule
