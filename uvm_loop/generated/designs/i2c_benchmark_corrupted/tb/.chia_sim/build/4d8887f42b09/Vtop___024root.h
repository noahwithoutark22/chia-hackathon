// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtop.h for the primary calling header

#ifndef VERILATED_VTOP___024ROOT_H_
#define VERILATED_VTOP___024ROOT_H_  // guard

#include "verilated.h"


class Vtop__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtop___024root final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(rst_n,0,0);
    VL_IN8(start,0,0);
    VL_IN8(slave_addr,6,0);
    VL_IN8(rw,0,0);
    VL_IN8(tx_data,7,0);
    VL_IN8(sda_in,0,0);
    VL_IN8(scl_in,0,0);
    VL_OUT8(sda_out,0,0);
    VL_OUT8(sda_oe,0,0);
    VL_OUT8(scl_out,0,0);
    VL_OUT8(scl_oe,0,0);
    VL_OUT8(rx_data,7,0);
    VL_OUT8(done,0,0);
    VL_OUT8(busy,0,0);
    VL_OUT8(ack_error,0,0);
    CData/*0:0*/ i2c_master__DOT__clk;
    CData/*0:0*/ i2c_master__DOT__rst_n;
    CData/*0:0*/ i2c_master__DOT__start;
    CData/*6:0*/ i2c_master__DOT__slave_addr;
    CData/*0:0*/ i2c_master__DOT__rw;
    CData/*7:0*/ i2c_master__DOT__tx_data;
    CData/*0:0*/ i2c_master__DOT__sda_in;
    CData/*0:0*/ i2c_master__DOT__scl_in;
    CData/*0:0*/ i2c_master__DOT__sda_out;
    CData/*0:0*/ i2c_master__DOT__sda_oe;
    CData/*0:0*/ i2c_master__DOT__scl_out;
    CData/*0:0*/ i2c_master__DOT__scl_oe;
    CData/*7:0*/ i2c_master__DOT__rx_data;
    CData/*0:0*/ i2c_master__DOT__done;
    CData/*0:0*/ i2c_master__DOT__busy;
    CData/*0:0*/ i2c_master__DOT__ack_error;
    CData/*3:0*/ i2c_master__DOT__state;
    CData/*1:0*/ i2c_master__DOT__div_cnt;
    CData/*3:0*/ i2c_master__DOT__bit_cnt;
    CData/*7:0*/ i2c_master__DOT__shift_reg;
    CData/*7:0*/ i2c_master__DOT__rx_shift;
    CData/*0:0*/ i2c_master__DOT__start_hold;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__i2c_master__DOT__clk__0;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vtop__Syms* const vlSymsp;

    // PARAMETERS
    static constexpr IData/*31:0*/ i2c_master__DOT__CLK_DIV = 4U;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* v__name);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
