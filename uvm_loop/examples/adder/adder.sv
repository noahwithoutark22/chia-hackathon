module adder #(
    parameter WIDTH = 8
) (
    input                     clk,
    input                     rst_n,
    input      [WIDTH-1:0]    a,
    input      [WIDTH-1:0]    b,
    input                     cin,
    output reg [WIDTH-1:0]    sum,
    output reg                cout
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sum  <= {WIDTH{1'b0}};
      cout <= 1'b0;
    end else begin
      {cout, sum} <= a + b + cin;
    end
  end

endmodule
