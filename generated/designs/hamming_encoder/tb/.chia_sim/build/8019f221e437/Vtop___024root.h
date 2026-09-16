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
    VL_IN8(data_in,3,0);
    VL_OUT8(code_out,6,0);
    CData/*3:0*/ hamming_encoder__DOT__data_in;
    CData/*6:0*/ hamming_encoder__DOT__code_out;
    CData/*6:0*/ hamming_encoder__DOT__ham;
    CData/*0:0*/ hamming_encoder__DOT__build_and_encode__DOT__par;
    CData/*0:0*/ hamming_encoder__DOT__build_and_encode__DOT__overall_par;
    CData/*0:0*/ hamming_encoder__DOT____Vlvbound_h99aff9ee__0;
    CData/*0:0*/ hamming_encoder__DOT____Vlvbound_h99aff9ee__1;
    CData/*0:0*/ hamming_encoder__DOT____Vlvbound_hc42c46af__0;
    CData/*0:0*/ __Vfunc_is_power_of_two__0__Vfuncout;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    IData/*31:0*/ hamming_encoder__DOT__build_and_encode__DOT__data_idx;
    IData/*31:0*/ hamming_encoder__DOT__build_and_encode__DOT__pos;
    IData/*31:0*/ hamming_encoder__DOT__build_and_encode__DOT__p;
    IData/*31:0*/ hamming_encoder__DOT__build_and_encode__DOT__parity_pos;
    IData/*31:0*/ __Vfunc_is_power_of_two__0__n;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;

    // INTERNAL VARIABLES
    Vtop__Syms* const vlSymsp;

    // PARAMETERS
    static constexpr CData/*0:0*/ hamming_encoder__DOT__SECDED = 0U;
    static constexpr IData/*31:0*/ hamming_encoder__DOT__DATA_WIDTH = 4U;
    static constexpr IData/*31:0*/ hamming_encoder__DOT__PARITY_BITS = 3U;
    static constexpr IData/*31:0*/ hamming_encoder__DOT__BASE_WIDTH = 7U;
    static constexpr IData/*31:0*/ hamming_encoder__DOT__CODE_WIDTH = 7U;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* v__name);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
