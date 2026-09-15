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
    VL_OUT8(busy,0,0);
    VL_OUT8(done,0,0);
    CData/*0:0*/ aes128__DOT__clk;
    CData/*0:0*/ aes128__DOT__rst_n;
    CData/*0:0*/ aes128__DOT__start;
    CData/*0:0*/ aes128__DOT__busy;
    CData/*0:0*/ aes128__DOT__done;
    CData/*3:0*/ aes128__DOT__round;
    CData/*1:0*/ aes128__DOT__state;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__2__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__2__a;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__3__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__3__a;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__4__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__4__a;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__5__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__5__a;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__7__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__sbox__7__a;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__10__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__10__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__11__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__11__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__12__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__12__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__13__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__13__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__14__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__14__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__15__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__15__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__16__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__16__x;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__17__Vfuncout;
    CData/*7:0*/ __Vfunc_aes128__DOT__xtime__17__x;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__aes128__DOT__clk__0;
    CData/*0:0*/ __Vtrigprevexpr___TOP__aes128__DOT__rst_n__0;
    VL_INW(key,127,0,4);
    VL_INW(plaintext,127,0,4);
    VL_OUTW(ciphertext,127,0,4);
    VlWide<4>/*127:0*/ aes128__DOT__key;
    VlWide<4>/*127:0*/ aes128__DOT__plaintext;
    VlWide<4>/*127:0*/ aes128__DOT__ciphertext;
    VlWide<4>/*127:0*/ aes128__DOT__state_reg;
    VlWide<4>/*127:0*/ aes128__DOT__round_key;
    VlWide<4>/*127:0*/ aes128__DOT__rk_next;
    VlWide<4>/*127:0*/ aes128__DOT__sb_next;
    VlWide<4>/*127:0*/ aes128__DOT__sr_next;
    VlWide<4>/*127:0*/ aes128__DOT__mc_next;
    VlWide<4>/*127:0*/ aes128__DOT__state_next;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__6__y;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__8__y;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__9__y;
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
