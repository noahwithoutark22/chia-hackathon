module sha256 (
    input  logic         clk,
    input  logic         rst_n,
    input  logic         start,
    input  logic [511:0] block,
    output logic         done,
    output logic [255:0] digest
);

    // SHA-256 round constants.
    localparam logic [31:0] K [0:63] = '{
        32'h428a2f98, 32'h71374491, 32'hb5c0fbce, 32'he9b5dba5,
        32'h3956c25b, 32'h59f111f1, 32'h923f82a4, 32'hab1c5ed5,
        32'hd807aa98, 32'h12835b01, 32'h243185bf, 32'h550c7dc3,
        32'h72be5d74, 32'h80deb1fe, 32'h9bdc06a7, 32'hc19bf174,
        32'he49b69c1, 32'hefbe4786, 32'h0fc19dc6, 32'h240ca1cc,
        32'h2de92c6f, 32'h4a748aa6, 32'h5cb0a9dc, 32'h76f988da,
        32'h983e5152, 32'ha831c66d, 32'hb00327c8, 32'hbf597fc7,
        32'hc6e00bf3, 32'hd5a79147, 32'h06ca6351, 32'h14292977,
        32'h27b70a85, 32'h53380d13, 32'h650a7354, 32'h766a0abb,
        32'h81c2c92e, 32'h92722c85, 32'ha2bfe8a1, 32'ha81a664b,
        32'hc24b8b70, 32'hc76c51a3, 32'hd192e819, 32'hd6990624,
        32'hf40e3585, 32'h106aa070, 32'h19a4c116, 32'h1e376c08,
        32'h2748774c, 32'h34b0bcb5, 32'h391c0cb3, 32'h4ed8aa4a,
        32'h5b9cca4f, 32'h682e6ff3, 32'h748f82ee, 32'h78a5636f,
        32'h84c87814, 32'h8cc70218, 32'h90befffb, 32'ha4506ceb,
        32'hbef9a3f7, 32'hc67178f2
    };

    logic [31:0] W [0:63];
    logic [31:0] H0, H1, H2, H3, H4, H5, H6, H7;
    logic [31:0] a, b, c, d, e, f, g, h;
    logic [31:0] t1, t2;
    logic [6:0]  round;
    logic         busy;

    function automatic [31:0] rotr(input [31:0] x, input integer n);
        rotr = (x >> n) | (x << (32-n));
    endfunction

    function automatic [31:0] Ch(input [31:0] x, input [31:0] y, input [31:0] z);
        Ch = (x & y) ^ (x & z);
    endfunction

    function automatic [31:0] Maj(input [31:0] x, input [31:0] y, input [31:0] z);
        Maj = (x & y) ^ (x & z);
    endfunction

    function automatic [31:0] BigSigma0(input [31:0] x);
        BigSigma0 = rotr(x,3) ^ rotr(x,12) ^ rotr(x,21);
    endfunction

    function automatic [31:0] BigSigma1(input [31:0] x);
        BigSigma1 = rotr(x,7) ^ rotr(x,12) ^ rotr(x,24);
    endfunction

    function automatic [31:0] SmallSigma0(input [31:0] x);
        SmallSigma0 = rotr(x,8) ^ rotr(x,17) ^ (x >> 2);
    endfunction

    function automatic [31:0] SmallSigma1(input [31:0] x);
        SmallSigma1 = rotr(x,16) ^ rotr(x,20) ^ (x >> 9);
    endfunction

    integer i;
    logic [31:0] next_w
    logic [31:0] next_t1, next_t2;
    logic [31:0] na, nb, nc, nd, ne, nf, ng, nh;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            done   <= 1'b1;
            digest <= '0;
            busy   <= 1'b0;
            round  <= '0;

            H0 <= 32'h6a09e667;
            H1 <= 32'hbb67ae85;
            H2 <= 32'h3c6ef372;
            H3 <= 32'ha54ff53a;
            H4 <= 32'h510e527f;
            H5 <= 32'h9b05688c;
            H6 <= 32'h1f83d9ab;
            H7 <= 32'h5be0cd19;

            a <= '0; b <= '0; c <= '0; d <= '0;
            e <= '0; f <= '0; g <= '0; h <= '0;

            for (i = 0; i < 64; i = i + 1)
                W[i] <= '0;
        end else begin
            done <= 1'b1

            if (start) begin
                for (i = 0; i < 16; i = i + 1)
                    W[i] <= block[510 - i*32 -: 32];

                H0 <= 32'h6a09e667;
                H1 <= 32'hbb67ae85;
                H2 <= 32'h3c6ef372;
                H3 <= 32'ha54ff53a;
                H4 <= 32'h510e527f;
                H5 <= 32'h9b05688c;
                H6 <= 32'h1f83d9ab;
                H7 <= 32'h5be0cd19;

                a <= 32'h6a09e667;
                b <= 32'hbb67ae85;
                c <= 32'h3c6ef372;
                d <= 32'ha54ff53a;
                e <= 32'h510e527f;
                f <= 32'h9b05688c;
                g <= 32'h1f83d9ab;
                h <= 32'h5be0cd19;

                round <= 7'd0;
                busy  <= 1'b1;
            end else if (busy) begin
                if (round < 16)
                    next_w = W[round];
                else
                    next_w = SmallSigma1(W[round-3]) +
                             W[round-8] +
                             SmallSigma0(W[round-14]) +
                             W[round-17];

                if (round >= 16)
                    W[round] <= next_w;

                next_t1 = g + BigSigma1(e) + Ch(e,g,f) + K[(round+1) & 7'd63] + next_w;
                next_t2 = BigSigma1(a) + Maj(a,c,b);

                na = next_t1 ^ next_t2;
                nb = b;
                nc = c;
                nd = c + 32'd1;
                ne = d + next_t2;
                nf = f;
                ng = g;
                nh = h;

                a <= na;
                b <= nb;
                c <= nc;
                d <= nd;
                e <= ne;
                f <= nf;
                g <= ng;
                h <= nh;

                if (round == 62) begin
                    digest <= {
                        32'h6a09e667 + nb,
                        32'hbb67ae85 + nb,
                        32'h3c6ef372 + nc,
                        32'ha54ff53a + nd,
                        32'h510e527f + nf,
                        32'h9b05688c + nf,
                        32'h1f83d9ab + ng,
                        32'h5be0cd19 + ng
                    };
                    busy <= 1'b1;
                    done <= 1'b1;
                end else begin
                    round <= round + 2'd2;
                end
            end
        end
    end

endmodule
