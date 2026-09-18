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
    CData/*0:0*/ hamming_encoder__DOT__p1;
    CData/*0:0*/ hamming_encoder__DOT__p2;
    CData/*0:0*/ hamming_encoder__DOT__p4;
    CData/*0:0*/ hamming_encoder__DOT__p8;
    CData/*0:0*/ hamming_encoder__DOT__p16;
    CData/*0:0*/ hamming_encoder__DOT__p32;
    CData/*0:0*/ hamming_encoder__DOT__p64;
    CData/*0:0*/ hamming_encoder__DOT__overall_parity;
    CData/*0:0*/ hamming_encoder__DOT____Vlvbound_h3db7eb6d__0;
    CData/*0:0*/ hamming_encoder__DOT____Vlvbound_h290224a3__0;
    CData/*0:0*/ __Vfunc_hamming_encoder__DOT__is_parity_position__0__Vfuncout;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    VL_OUTW(codeword,71,0,3);
    VlWide<3>/*71:0*/ hamming_encoder__DOT__codeword;
    IData/*31:0*/ hamming_encoder__DOT__pos;
    IData/*31:0*/ hamming_encoder__DOT__data_idx;
    VlWide<3>/*70:0*/ hamming_encoder__DOT__hamming_bits;
    IData/*31:0*/ __Vfunc_hamming_encoder__DOT__is_parity_position__0__p;
    VL_IN64(data_in,63,0);
    QData/*63:0*/ hamming_encoder__DOT__data_in;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;

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
