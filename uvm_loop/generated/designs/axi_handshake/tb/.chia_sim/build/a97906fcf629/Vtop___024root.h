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
    VL_IN8(s_valid,0,0);
    VL_OUT8(s_ready,0,0);
    VL_IN8(s_data,7,0);
    VL_OUT8(m_valid,0,0);
    VL_IN8(m_ready,0,0);
    VL_OUT8(m_data,7,0);
    CData/*0:0*/ axi_handshake__DOT__clk;
    CData/*0:0*/ axi_handshake__DOT__rst_n;
    CData/*0:0*/ axi_handshake__DOT__s_valid;
    CData/*0:0*/ axi_handshake__DOT__s_ready;
    CData/*7:0*/ axi_handshake__DOT__s_data;
    CData/*0:0*/ axi_handshake__DOT__m_valid;
    CData/*0:0*/ axi_handshake__DOT__m_ready;
    CData/*7:0*/ axi_handshake__DOT__m_data;
    CData/*7:0*/ axi_handshake__DOT__data_reg;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__axi_handshake__DOT__clk__0;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vtop__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* v__name);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
