// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

void Vtop___024root___eval_triggers__ico(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_triggers__ico\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VicoTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VicoTriggered
                                      [0U]) | (IData)((IData)(vlSelfRef.__VicoFirstIteration)));
    vlSelfRef.__VicoFirstIteration = 0U;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
}

bool Vtop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__ico\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void Vtop___024root___ico_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ico_sequent__TOP__0\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.aes128__DOT__clk = vlSelfRef.clk;
    vlSelfRef.aes128__DOT__rst_n = vlSelfRef.rst_n;
    vlSelfRef.aes128__DOT__start = vlSelfRef.start;
    vlSelfRef.aes128__DOT__key[0U] = vlSelfRef.key[0U];
    vlSelfRef.aes128__DOT__key[1U] = vlSelfRef.key[1U];
    vlSelfRef.aes128__DOT__key[2U] = vlSelfRef.key[2U];
    vlSelfRef.aes128__DOT__key[3U] = vlSelfRef.key[3U];
    vlSelfRef.aes128__DOT__plaintext[0U] = vlSelfRef.plaintext[0U];
    vlSelfRef.aes128__DOT__plaintext[1U] = vlSelfRef.plaintext[1U];
    vlSelfRef.aes128__DOT__plaintext[2U] = vlSelfRef.plaintext[2U];
    vlSelfRef.aes128__DOT__plaintext[3U] = vlSelfRef.plaintext[3U];
    vlSelfRef.done = vlSelfRef.aes128__DOT__done;
    vlSelfRef.ciphertext[0U] = vlSelfRef.aes128__DOT__ciphertext[0U];
    vlSelfRef.ciphertext[1U] = vlSelfRef.aes128__DOT__ciphertext[1U];
    vlSelfRef.ciphertext[2U] = vlSelfRef.aes128__DOT__ciphertext[2U];
    vlSelfRef.ciphertext[3U] = vlSelfRef.aes128__DOT__ciphertext[3U];
}

void Vtop___024root___eval_ico(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_ico\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VicoTriggered[0U])) {
        Vtop___024root___ico_sequent__TOP__0(vlSelf);
    }
}

bool Vtop___024root___eval_phase__ico(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__ico\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    Vtop___024root___eval_triggers__ico(vlSelf);
    __VicoExecute = Vtop___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        Vtop___024root___eval_ico(vlSelf);
    }
    return (__VicoExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

void Vtop___024root___eval_triggers__act(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_triggers__act\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                    ((IData)(vlSelfRef.aes128__DOT__clk) 
                                                     & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__clk__0)))));
    vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__clk__0 
        = vlSelfRef.aes128__DOT__clk;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
}

bool Vtop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

void Vtop___024root___nba_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_sequent__TOP__0\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__0__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__0__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__0__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__0__k);
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__r;
    __Vfunc_aes128__DOT__next_round_key__0__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w0;
    __Vfunc_aes128__DOT__next_round_key__0__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w1;
    __Vfunc_aes128__DOT__next_round_key__0__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w2;
    __Vfunc_aes128__DOT__next_round_key__0__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w3;
    __Vfunc_aes128__DOT__next_round_key__0__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__t;
    __Vfunc_aes128__DOT__next_round_key__0__t = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n0;
    __Vfunc_aes128__DOT__next_round_key__0__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n1;
    __Vfunc_aes128__DOT__next_round_key__0__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n2;
    __Vfunc_aes128__DOT__next_round_key__0__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n3;
    __Vfunc_aes128__DOT__next_round_key__0__n3 = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__1__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__1__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__1__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__1__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__1__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__1__k);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__1__t;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__1__t);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__2__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__2__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__2__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__2__k);
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__r;
    __Vfunc_aes128__DOT__next_round_key__2__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__w0;
    __Vfunc_aes128__DOT__next_round_key__2__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__w1;
    __Vfunc_aes128__DOT__next_round_key__2__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__w2;
    __Vfunc_aes128__DOT__next_round_key__2__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__w3;
    __Vfunc_aes128__DOT__next_round_key__2__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__t;
    __Vfunc_aes128__DOT__next_round_key__2__t = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__n0;
    __Vfunc_aes128__DOT__next_round_key__2__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__n1;
    __Vfunc_aes128__DOT__next_round_key__2__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__n2;
    __Vfunc_aes128__DOT__next_round_key__2__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__2__n3;
    __Vfunc_aes128__DOT__next_round_key__2__n3 = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__3__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__3__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__3__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__3__s);
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__3__b;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__3__b[__Vi0] = 0;
    }
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__3__o;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__3__o[__Vi0] = 0;
    }
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__4__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__4__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__18__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__18__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__18__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__18__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__18__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__18__k);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__18__t;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__18__t);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__19__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__19__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__19__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__19__k);
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__r;
    __Vfunc_aes128__DOT__next_round_key__19__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__w0;
    __Vfunc_aes128__DOT__next_round_key__19__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__w1;
    __Vfunc_aes128__DOT__next_round_key__19__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__w2;
    __Vfunc_aes128__DOT__next_round_key__19__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__w3;
    __Vfunc_aes128__DOT__next_round_key__19__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__t;
    __Vfunc_aes128__DOT__next_round_key__19__t = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__n0;
    __Vfunc_aes128__DOT__next_round_key__19__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__n1;
    __Vfunc_aes128__DOT__next_round_key__19__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__n2;
    __Vfunc_aes128__DOT__next_round_key__19__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__19__n3;
    __Vfunc_aes128__DOT__next_round_key__19__n3 = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__20__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__20__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__20__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__20__s);
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__20__b;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__20__b[__Vi0] = 0;
    }
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__20__o;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__20__o[__Vi0] = 0;
    }
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__21__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__21__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__35__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__35__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__35__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__35__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__35__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__35__k);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__aes_round__35__t;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__aes_round__35__t);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__36__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__36__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__36__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__36__k);
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__r;
    __Vfunc_aes128__DOT__next_round_key__36__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__w0;
    __Vfunc_aes128__DOT__next_round_key__36__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__w1;
    __Vfunc_aes128__DOT__next_round_key__36__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__w2;
    __Vfunc_aes128__DOT__next_round_key__36__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__w3;
    __Vfunc_aes128__DOT__next_round_key__36__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__t;
    __Vfunc_aes128__DOT__next_round_key__36__t = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__n0;
    __Vfunc_aes128__DOT__next_round_key__36__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__n1;
    __Vfunc_aes128__DOT__next_round_key__36__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__n2;
    __Vfunc_aes128__DOT__next_round_key__36__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__36__n3;
    __Vfunc_aes128__DOT__next_round_key__36__n3 = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__37__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__37__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__37__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__37__s);
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__37__b;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__37__b[__Vi0] = 0;
    }
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__shift_rows__37__o;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__shift_rows__37__o[__Vi0] = 0;
    }
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__38__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__38__s);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__39__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__39__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__39__s;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__39__s);
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__mix_columns__39__b;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__mix_columns__39__b[__Vi0] = 0;
    }
    VlUnpacked<CData/*7:0*/, 16> __Vfunc_aes128__DOT__mix_columns__39__o;
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        __Vfunc_aes128__DOT__mix_columns__39__o[__Vi0] = 0;
    }
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__40__Vfuncout;
    __Vfunc_aes128__DOT__gm2__40__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__40__a;
    __Vfunc_aes128__DOT__gm2__40__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__41__Vfuncout;
    __Vfunc_aes128__DOT__gm3__41__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__41__a;
    __Vfunc_aes128__DOT__gm3__41__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__42__Vfuncout;
    __Vfunc_aes128__DOT__gm2__42__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__42__a;
    __Vfunc_aes128__DOT__gm2__42__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__43__Vfuncout;
    __Vfunc_aes128__DOT__gm2__43__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__43__a;
    __Vfunc_aes128__DOT__gm2__43__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__44__Vfuncout;
    __Vfunc_aes128__DOT__gm3__44__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__44__a;
    __Vfunc_aes128__DOT__gm3__44__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__45__Vfuncout;
    __Vfunc_aes128__DOT__gm2__45__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__45__a;
    __Vfunc_aes128__DOT__gm2__45__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__46__Vfuncout;
    __Vfunc_aes128__DOT__gm2__46__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__46__a;
    __Vfunc_aes128__DOT__gm2__46__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__47__Vfuncout;
    __Vfunc_aes128__DOT__gm3__47__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__47__a;
    __Vfunc_aes128__DOT__gm3__47__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__48__Vfuncout;
    __Vfunc_aes128__DOT__gm2__48__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__48__a;
    __Vfunc_aes128__DOT__gm2__48__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__49__Vfuncout;
    __Vfunc_aes128__DOT__gm3__49__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm3__49__a;
    __Vfunc_aes128__DOT__gm3__49__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__50__Vfuncout;
    __Vfunc_aes128__DOT__gm2__50__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__50__a;
    __Vfunc_aes128__DOT__gm2__50__a = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__51__Vfuncout;
    __Vfunc_aes128__DOT__gm2__51__Vfuncout = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__gm2__51__a;
    __Vfunc_aes128__DOT__gm2__51__a = 0;
    VlWide<4>/*127:0*/ __Vdly__aes128__DOT__state;
    VL_ZERO_W(128, __Vdly__aes128__DOT__state);
    VlWide<4>/*127:0*/ __Vdly__aes128__DOT__round_key;
    VL_ZERO_W(128, __Vdly__aes128__DOT__round_key);
    CData/*3:0*/ __Vdly__aes128__DOT__round;
    __Vdly__aes128__DOT__round = 0;
    CData/*0:0*/ __Vdly__aes128__DOT__busy;
    __Vdly__aes128__DOT__busy = 0;
    // Body
    __Vdly__aes128__DOT__state[0U] = vlSelfRef.aes128__DOT__state[0U];
    __Vdly__aes128__DOT__state[1U] = vlSelfRef.aes128__DOT__state[1U];
    __Vdly__aes128__DOT__state[2U] = vlSelfRef.aes128__DOT__state[2U];
    __Vdly__aes128__DOT__state[3U] = vlSelfRef.aes128__DOT__state[3U];
    __Vdly__aes128__DOT__round_key[0U] = vlSelfRef.aes128__DOT__round_key[0U];
    __Vdly__aes128__DOT__round_key[1U] = vlSelfRef.aes128__DOT__round_key[1U];
    __Vdly__aes128__DOT__round_key[2U] = vlSelfRef.aes128__DOT__round_key[2U];
    __Vdly__aes128__DOT__round_key[3U] = vlSelfRef.aes128__DOT__round_key[3U];
    __Vdly__aes128__DOT__round = vlSelfRef.aes128__DOT__round;
    __Vdly__aes128__DOT__busy = vlSelfRef.aes128__DOT__busy;
    if (vlSelfRef.aes128__DOT__rst_n) {
        vlSelfRef.aes128__DOT__done = 0U;
        if (((IData)(vlSelfRef.aes128__DOT__start) 
             & (~ (IData)(vlSelfRef.aes128__DOT__busy)))) {
            __Vdly__aes128__DOT__state[0U] = (vlSelfRef.aes128__DOT__plaintext[0U] 
                                              ^ vlSelfRef.aes128__DOT__key[0U]);
            __Vdly__aes128__DOT__state[1U] = (vlSelfRef.aes128__DOT__plaintext[1U] 
                                              ^ vlSelfRef.aes128__DOT__key[1U]);
            __Vdly__aes128__DOT__state[2U] = (vlSelfRef.aes128__DOT__plaintext[2U] 
                                              ^ vlSelfRef.aes128__DOT__key[2U]);
            __Vdly__aes128__DOT__state[3U] = (vlSelfRef.aes128__DOT__plaintext[3U] 
                                              ^ vlSelfRef.aes128__DOT__key[3U]);
            __Vdly__aes128__DOT__round_key[0U] = vlSelfRef.aes128__DOT__key[0U];
            __Vdly__aes128__DOT__round_key[1U] = vlSelfRef.aes128__DOT__key[1U];
            __Vdly__aes128__DOT__round_key[2U] = vlSelfRef.aes128__DOT__key[2U];
            __Vdly__aes128__DOT__round_key[3U] = vlSelfRef.aes128__DOT__key[3U];
            __Vdly__aes128__DOT__round = 0U;
            __Vdly__aes128__DOT__busy = 1U;
        } else if (vlSelfRef.aes128__DOT__busy) {
            __Vfunc_aes128__DOT__next_round_key__0__r 
                = vlSelfRef.aes128__DOT__round;
            __Vfunc_aes128__DOT__next_round_key__0__k[0U] 
                = vlSelfRef.aes128__DOT__round_key[0U];
            __Vfunc_aes128__DOT__next_round_key__0__k[1U] 
                = vlSelfRef.aes128__DOT__round_key[1U];
            __Vfunc_aes128__DOT__next_round_key__0__k[2U] 
                = vlSelfRef.aes128__DOT__round_key[2U];
            __Vfunc_aes128__DOT__next_round_key__0__k[3U] 
                = vlSelfRef.aes128__DOT__round_key[3U];
            __Vfunc_aes128__DOT__next_round_key__0__w0 
                = __Vfunc_aes128__DOT__next_round_key__0__k[3U];
            __Vfunc_aes128__DOT__next_round_key__0__w1 
                = __Vfunc_aes128__DOT__next_round_key__0__k[2U];
            __Vfunc_aes128__DOT__next_round_key__0__w2 
                = __Vfunc_aes128__DOT__next_round_key__0__k[1U];
            __Vfunc_aes128__DOT__next_round_key__0__w3 
                = __Vfunc_aes128__DOT__next_round_key__0__k[0U];
            __Vfunc_aes128__DOT__next_round_key__0__t 
                = (((vlSelfRef.aes128__DOT__SBOX[(0x000000ffU 
                                                  & (__Vfunc_aes128__DOT__next_round_key__0__w3 
                                                     >> 0x10U))] 
                     << 0x00000018U) | (vlSelfRef.aes128__DOT__SBOX
                                        [(0x000000ffU 
                                          & (__Vfunc_aes128__DOT__next_round_key__0__w3 
                                             >> 8U))] 
                                        << 0x00000010U)) 
                   | ((vlSelfRef.aes128__DOT__SBOX[
                       (0x000000ffU & __Vfunc_aes128__DOT__next_round_key__0__w3)] 
                       << 8U) | vlSelfRef.aes128__DOT__SBOX
                      [(__Vfunc_aes128__DOT__next_round_key__0__w3 
                        >> 0x18U)]));
            __Vfunc_aes128__DOT__next_round_key__0__t 
                = ((0x00ffffffU & __Vfunc_aes128__DOT__next_round_key__0__t) 
                   | (0xff000000U & ((0xff000000U & __Vfunc_aes128__DOT__next_round_key__0__t) 
                                     ^ (((9U >= (0x0000000fU 
                                                 & __Vfunc_aes128__DOT__next_round_key__0__r))
                                          ? vlSelfRef.aes128__DOT__RCON
                                         [(0x0000000fU 
                                           & __Vfunc_aes128__DOT__next_round_key__0__r)]
                                          : 0U) << 0x00000018U))));
            __Vfunc_aes128__DOT__next_round_key__0__n0 
                = (__Vfunc_aes128__DOT__next_round_key__0__w0 
                   ^ __Vfunc_aes128__DOT__next_round_key__0__t);
            __Vfunc_aes128__DOT__next_round_key__0__n1 
                = (__Vfunc_aes128__DOT__next_round_key__0__w1 
                   ^ __Vfunc_aes128__DOT__next_round_key__0__n0);
            __Vfunc_aes128__DOT__next_round_key__0__n2 
                = (__Vfunc_aes128__DOT__next_round_key__0__w2 
                   ^ __Vfunc_aes128__DOT__next_round_key__0__n1);
            __Vfunc_aes128__DOT__next_round_key__0__n3 
                = (__Vfunc_aes128__DOT__next_round_key__0__w3 
                   ^ __Vfunc_aes128__DOT__next_round_key__0__n2);
            __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[0U] 
                = __Vfunc_aes128__DOT__next_round_key__0__n3;
            __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[1U] 
                = __Vfunc_aes128__DOT__next_round_key__0__n2;
            __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[2U] 
                = (IData)((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__0__n0)) 
                            << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__0__n1))));
            __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[3U] 
                = (IData)(((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__0__n0)) 
                             << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__0__n1))) 
                           >> 0x00000020U));
            __Vdly__aes128__DOT__round_key[0U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[0U];
            __Vdly__aes128__DOT__round_key[1U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[1U];
            __Vdly__aes128__DOT__round_key[2U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[2U];
            __Vdly__aes128__DOT__round_key[3U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[3U];
            if ((9U == (IData)(vlSelfRef.aes128__DOT__round))) {
                __Vfunc_aes128__DOT__next_round_key__2__r 
                    = vlSelfRef.aes128__DOT__round;
                __Vfunc_aes128__DOT__next_round_key__2__k[0U] 
                    = vlSelfRef.aes128__DOT__round_key[0U];
                __Vfunc_aes128__DOT__next_round_key__2__k[1U] 
                    = vlSelfRef.aes128__DOT__round_key[1U];
                __Vfunc_aes128__DOT__next_round_key__2__k[2U] 
                    = vlSelfRef.aes128__DOT__round_key[2U];
                __Vfunc_aes128__DOT__next_round_key__2__k[3U] 
                    = vlSelfRef.aes128__DOT__round_key[3U];
                __Vfunc_aes128__DOT__next_round_key__2__w0 
                    = __Vfunc_aes128__DOT__next_round_key__2__k[3U];
                vlSelfRef.aes128__DOT__done = 1U;
                __Vdly__aes128__DOT__busy = 0U;
                __Vfunc_aes128__DOT__next_round_key__2__w1 
                    = __Vfunc_aes128__DOT__next_round_key__2__k[2U];
                __Vfunc_aes128__DOT__next_round_key__2__w2 
                    = __Vfunc_aes128__DOT__next_round_key__2__k[1U];
                __Vfunc_aes128__DOT__next_round_key__2__w3 
                    = __Vfunc_aes128__DOT__next_round_key__2__k[0U];
                __Vfunc_aes128__DOT__next_round_key__2__t 
                    = (((vlSelfRef.aes128__DOT__SBOX
                         [(0x000000ffU & (__Vfunc_aes128__DOT__next_round_key__2__w3 
                                          >> 0x10U))] 
                         << 0x00000018U) | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__next_round_key__2__w3 
                                                 >> 8U))] 
                                            << 0x00000010U)) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & __Vfunc_aes128__DOT__next_round_key__2__w3)] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(__Vfunc_aes128__DOT__next_round_key__2__w3 
                            >> 0x18U)]));
                __Vfunc_aes128__DOT__next_round_key__2__t 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__next_round_key__2__t) 
                       | (0xff000000U & ((0xff000000U 
                                          & __Vfunc_aes128__DOT__next_round_key__2__t) 
                                         ^ (((9U >= 
                                              (0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__2__r))
                                              ? vlSelfRef.aes128__DOT__RCON
                                             [(0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__2__r)]
                                              : 0U) 
                                            << 0x00000018U))));
                __Vfunc_aes128__DOT__next_round_key__2__n0 
                    = (__Vfunc_aes128__DOT__next_round_key__2__w0 
                       ^ __Vfunc_aes128__DOT__next_round_key__2__t);
                __Vfunc_aes128__DOT__next_round_key__2__n1 
                    = (__Vfunc_aes128__DOT__next_round_key__2__w1 
                       ^ __Vfunc_aes128__DOT__next_round_key__2__n0);
                __Vfunc_aes128__DOT__next_round_key__2__n2 
                    = (__Vfunc_aes128__DOT__next_round_key__2__w2 
                       ^ __Vfunc_aes128__DOT__next_round_key__2__n1);
                __Vfunc_aes128__DOT__next_round_key__2__n3 
                    = (__Vfunc_aes128__DOT__next_round_key__2__w3 
                       ^ __Vfunc_aes128__DOT__next_round_key__2__n2);
                __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__n3;
                __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__n2;
                __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[2U] 
                    = (IData)((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__2__n0)) 
                                << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__2__n1))));
                __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[3U] 
                    = (IData)(((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__2__n0)) 
                                 << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__2__n1))) 
                               >> 0x00000020U));
                __Vfunc_aes128__DOT__aes_round__1__k[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__1__k[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__1__k[2U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__1__k[3U] 
                    = __Vfunc_aes128__DOT__next_round_key__2__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__1__s[0U] 
                    = vlSelfRef.aes128__DOT__state[0U];
                __Vfunc_aes128__DOT__aes_round__1__s[1U] 
                    = vlSelfRef.aes128__DOT__state[1U];
                __Vfunc_aes128__DOT__aes_round__1__s[2U] 
                    = vlSelfRef.aes128__DOT__state[2U];
                __Vfunc_aes128__DOT__aes_round__1__s[3U] 
                    = vlSelfRef.aes128__DOT__state[3U];
                __Vfunc_aes128__DOT__shift_rows__3__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__1__s[0U];
                __Vfunc_aes128__DOT__shift_rows__3__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__1__s[1U];
                __Vfunc_aes128__DOT__shift_rows__3__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__1__s[2U];
                __Vfunc_aes128__DOT__shift_rows__3__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__1__s[3U];
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__3__b[__Vi0] = 0;
                }
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__3__o[__Vi0] = 0;
                }
                __Vfunc_aes128__DOT__shift_rows__3__b[0U] 
                    = (__Vfunc_aes128__DOT__shift_rows__3__s[3U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__3__b[1U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[3U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__3__b[2U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[3U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__3__b[3U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__s[3U]);
                __Vfunc_aes128__DOT__shift_rows__3__b[4U] 
                    = (__Vfunc_aes128__DOT__shift_rows__3__s[2U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__3__b[5U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[2U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__3__b[6U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[2U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__3__b[7U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__s[2U]);
                __Vfunc_aes128__DOT__shift_rows__3__b[8U] 
                    = (__Vfunc_aes128__DOT__shift_rows__3__s[1U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__3__b[9U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[1U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0aU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[1U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0bU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__s[1U]);
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0cU] 
                    = (__Vfunc_aes128__DOT__shift_rows__3__s[0U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0dU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[0U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0eU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__3__s[0U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__3__b[0x0fU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__s[0U]);
                __Vfunc_aes128__DOT__shift_rows__3__o[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0U];
                __Vfunc_aes128__DOT__shift_rows__3__o[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [5U];
                __Vfunc_aes128__DOT__shift_rows__3__o[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0aU];
                __Vfunc_aes128__DOT__shift_rows__3__o[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0fU];
                __Vfunc_aes128__DOT__shift_rows__3__o[4U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [4U];
                __Vfunc_aes128__DOT__shift_rows__3__o[5U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [9U];
                __Vfunc_aes128__DOT__shift_rows__3__o[6U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0eU];
                __Vfunc_aes128__DOT__shift_rows__3__o[7U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [3U];
                __Vfunc_aes128__DOT__shift_rows__3__o[8U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [8U];
                __Vfunc_aes128__DOT__shift_rows__3__o[9U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0dU];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0aU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [2U];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0bU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [7U];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0cU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0cU];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0dU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [1U];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0eU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [6U];
                __Vfunc_aes128__DOT__shift_rows__3__o[0x0fU] 
                    = __Vfunc_aes128__DOT__shift_rows__3__b
                    [0x0bU];
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[3U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[3U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__3__o
                                          [0U] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__3__o
                                             [1U] << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__3__o
                                               [2U] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[2U]) 
                       | (0xffff0000U & ((__Vfunc_aes128__DOT__shift_rows__3__o
                                          [4U] << 0x00000018U) 
                                         | (__Vfunc_aes128__DOT__shift_rows__3__o
                                            [5U] << 0x00000010U))));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[3U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[3U]) 
                       | (0x0000ffffU & ((0x0000ffffU 
                                          & __Vfunc_aes128__DOT__shift_rows__3__o
                                          [3U]) | (
                                                   (0x0000ffffU 
                                                    & (__Vfunc_aes128__DOT__shift_rows__3__o
                                                       [4U] 
                                                       >> 8U)) 
                                                   | (__Vfunc_aes128__DOT__shift_rows__3__o
                                                      [5U] 
                                                      >> 0x00000010U)))));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[1U] 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[1U]) 
                       | (__Vfunc_aes128__DOT__shift_rows__3__o
                          [8U] << 0x00000018U));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[2U]) 
                       | (0x00ffffffU & ((0x00ffff00U 
                                          & (__Vfunc_aes128__DOT__shift_rows__3__o
                                             [6U] << 8U)) 
                                         | ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__shift_rows__3__o
                                             [7U]) 
                                            | (__Vfunc_aes128__DOT__shift_rows__3__o
                                               [8U] 
                                               >> 8U)))));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[1U] 
                    = ((0xff000000U & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[1U]) 
                       | ((__Vfunc_aes128__DOT__shift_rows__3__o
                           [9U] << 0x00000010U) | (
                                                   (__Vfunc_aes128__DOT__shift_rows__3__o
                                                    [0x0aU] 
                                                    << 8U) 
                                                   | __Vfunc_aes128__DOT__shift_rows__3__o
                                                   [0x0bU])));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[0U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[0U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__3__o
                                          [0x0cU] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__3__o
                                             [0x0dU] 
                                             << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__3__o
                                               [0x0eU] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[0U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[0U]) 
                       | __Vfunc_aes128__DOT__shift_rows__3__o
                       [0x0fU]);
                __Vfunc_aes128__DOT__aes_round__1__t[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__1__t[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__1__t[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__1__t[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__3__Vfuncout[3U];
                __Vfunc_aes128__DOT__sub_bytes__4__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__1__t[0U];
                __Vfunc_aes128__DOT__sub_bytes__4__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__1__t[1U];
                __Vfunc_aes128__DOT__sub_bytes__4__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__1__t[2U];
                __Vfunc_aes128__DOT__sub_bytes__4__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__1__t[3U];
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[3U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[3U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__4__s[3U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__4__s[3U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[3U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[3U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__4__s[3U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__4__s[3U])]));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[2U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__4__s[2U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__4__s[2U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[2U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__4__s[2U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__4__s[2U])]));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[1U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[1U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__4__s[1U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__4__s[1U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[1U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[1U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__4__s[1U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__4__s[1U])]));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[0U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[0U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__4__s[0U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__4__s[0U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[0U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[0U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__4__s[0U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__4__s[0U])]));
                __Vfunc_aes128__DOT__aes_round__1__t[0U] 
                    = __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__1__t[1U] 
                    = __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__1__t[2U] 
                    = __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__1__t[3U] 
                    = __Vfunc_aes128__DOT__sub_bytes__4__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__1__Vfuncout[0U] 
                    = (__Vfunc_aes128__DOT__aes_round__1__t[0U] 
                       ^ __Vfunc_aes128__DOT__aes_round__1__k[0U]);
                __Vfunc_aes128__DOT__aes_round__1__Vfuncout[1U] 
                    = (__Vfunc_aes128__DOT__aes_round__1__t[1U] 
                       ^ __Vfunc_aes128__DOT__aes_round__1__k[1U]);
                __Vfunc_aes128__DOT__aes_round__1__Vfuncout[2U] 
                    = (__Vfunc_aes128__DOT__aes_round__1__t[2U] 
                       ^ __Vfunc_aes128__DOT__aes_round__1__k[2U]);
                __Vfunc_aes128__DOT__aes_round__1__Vfuncout[3U] 
                    = (__Vfunc_aes128__DOT__aes_round__1__t[3U] 
                       ^ __Vfunc_aes128__DOT__aes_round__1__k[3U]);
                __Vdly__aes128__DOT__state[0U] = __Vfunc_aes128__DOT__aes_round__1__Vfuncout[0U];
                __Vdly__aes128__DOT__state[1U] = __Vfunc_aes128__DOT__aes_round__1__Vfuncout[1U];
                __Vdly__aes128__DOT__state[2U] = __Vfunc_aes128__DOT__aes_round__1__Vfuncout[2U];
                __Vdly__aes128__DOT__state[3U] = __Vfunc_aes128__DOT__aes_round__1__Vfuncout[3U];
                __Vfunc_aes128__DOT__next_round_key__19__r 
                    = vlSelfRef.aes128__DOT__round;
                __Vfunc_aes128__DOT__next_round_key__19__k[0U] 
                    = vlSelfRef.aes128__DOT__round_key[0U];
                __Vfunc_aes128__DOT__next_round_key__19__k[1U] 
                    = vlSelfRef.aes128__DOT__round_key[1U];
                __Vfunc_aes128__DOT__next_round_key__19__k[2U] 
                    = vlSelfRef.aes128__DOT__round_key[2U];
                __Vfunc_aes128__DOT__next_round_key__19__k[3U] 
                    = vlSelfRef.aes128__DOT__round_key[3U];
                __Vfunc_aes128__DOT__next_round_key__19__w0 
                    = __Vfunc_aes128__DOT__next_round_key__19__k[3U];
                __Vfunc_aes128__DOT__next_round_key__19__w1 
                    = __Vfunc_aes128__DOT__next_round_key__19__k[2U];
                __Vfunc_aes128__DOT__next_round_key__19__w2 
                    = __Vfunc_aes128__DOT__next_round_key__19__k[1U];
                __Vfunc_aes128__DOT__next_round_key__19__w3 
                    = __Vfunc_aes128__DOT__next_round_key__19__k[0U];
                __Vfunc_aes128__DOT__next_round_key__19__t 
                    = (((vlSelfRef.aes128__DOT__SBOX
                         [(0x000000ffU & (__Vfunc_aes128__DOT__next_round_key__19__w3 
                                          >> 0x10U))] 
                         << 0x00000018U) | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__next_round_key__19__w3 
                                                 >> 8U))] 
                                            << 0x00000010U)) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & __Vfunc_aes128__DOT__next_round_key__19__w3)] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(__Vfunc_aes128__DOT__next_round_key__19__w3 
                            >> 0x18U)]));
                __Vfunc_aes128__DOT__next_round_key__19__t 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__next_round_key__19__t) 
                       | (0xff000000U & ((0xff000000U 
                                          & __Vfunc_aes128__DOT__next_round_key__19__t) 
                                         ^ (((9U >= 
                                              (0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__19__r))
                                              ? vlSelfRef.aes128__DOT__RCON
                                             [(0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__19__r)]
                                              : 0U) 
                                            << 0x00000018U))));
                __Vfunc_aes128__DOT__next_round_key__19__n0 
                    = (__Vfunc_aes128__DOT__next_round_key__19__w0 
                       ^ __Vfunc_aes128__DOT__next_round_key__19__t);
                __Vfunc_aes128__DOT__next_round_key__19__n1 
                    = (__Vfunc_aes128__DOT__next_round_key__19__w1 
                       ^ __Vfunc_aes128__DOT__next_round_key__19__n0);
                __Vfunc_aes128__DOT__next_round_key__19__n2 
                    = (__Vfunc_aes128__DOT__next_round_key__19__w2 
                       ^ __Vfunc_aes128__DOT__next_round_key__19__n1);
                __Vfunc_aes128__DOT__next_round_key__19__n3 
                    = (__Vfunc_aes128__DOT__next_round_key__19__w3 
                       ^ __Vfunc_aes128__DOT__next_round_key__19__n2);
                __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__n3;
                __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__n2;
                __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[2U] 
                    = (IData)((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__19__n0)) 
                                << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__19__n1))));
                __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[3U] 
                    = (IData)(((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__19__n0)) 
                                 << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__19__n1))) 
                               >> 0x00000020U));
                __Vfunc_aes128__DOT__aes_round__18__k[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__18__k[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__18__k[2U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__18__k[3U] 
                    = __Vfunc_aes128__DOT__next_round_key__19__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__18__s[0U] 
                    = vlSelfRef.aes128__DOT__state[0U];
                __Vfunc_aes128__DOT__aes_round__18__s[1U] 
                    = vlSelfRef.aes128__DOT__state[1U];
                __Vfunc_aes128__DOT__aes_round__18__s[2U] 
                    = vlSelfRef.aes128__DOT__state[2U];
                __Vfunc_aes128__DOT__aes_round__18__s[3U] 
                    = vlSelfRef.aes128__DOT__state[3U];
                __Vfunc_aes128__DOT__shift_rows__20__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__18__s[0U];
                __Vfunc_aes128__DOT__shift_rows__20__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__18__s[1U];
                __Vfunc_aes128__DOT__shift_rows__20__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__18__s[2U];
                __Vfunc_aes128__DOT__shift_rows__20__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__18__s[3U];
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__20__b[__Vi0] = 0;
                }
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__20__o[__Vi0] = 0;
                }
                __Vfunc_aes128__DOT__shift_rows__20__b[0U] 
                    = (__Vfunc_aes128__DOT__shift_rows__20__s[3U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__20__b[1U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[3U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__20__b[2U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[3U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__20__b[3U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__s[3U]);
                __Vfunc_aes128__DOT__shift_rows__20__b[4U] 
                    = (__Vfunc_aes128__DOT__shift_rows__20__s[2U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__20__b[5U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[2U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__20__b[6U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[2U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__20__b[7U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__s[2U]);
                __Vfunc_aes128__DOT__shift_rows__20__b[8U] 
                    = (__Vfunc_aes128__DOT__shift_rows__20__s[1U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__20__b[9U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[1U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0aU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[1U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0bU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__s[1U]);
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0cU] 
                    = (__Vfunc_aes128__DOT__shift_rows__20__s[0U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0dU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[0U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0eU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__20__s[0U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__20__b[0x0fU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__s[0U]);
                __Vfunc_aes128__DOT__shift_rows__20__o[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0U];
                __Vfunc_aes128__DOT__shift_rows__20__o[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [5U];
                __Vfunc_aes128__DOT__shift_rows__20__o[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0aU];
                __Vfunc_aes128__DOT__shift_rows__20__o[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0fU];
                __Vfunc_aes128__DOT__shift_rows__20__o[4U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [4U];
                __Vfunc_aes128__DOT__shift_rows__20__o[5U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [9U];
                __Vfunc_aes128__DOT__shift_rows__20__o[6U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0eU];
                __Vfunc_aes128__DOT__shift_rows__20__o[7U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [3U];
                __Vfunc_aes128__DOT__shift_rows__20__o[8U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [8U];
                __Vfunc_aes128__DOT__shift_rows__20__o[9U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0dU];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0aU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [2U];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0bU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [7U];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0cU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0cU];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0dU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [1U];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0eU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [6U];
                __Vfunc_aes128__DOT__shift_rows__20__o[0x0fU] 
                    = __Vfunc_aes128__DOT__shift_rows__20__b
                    [0x0bU];
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[3U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[3U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__20__o
                                          [0U] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__20__o
                                             [1U] << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__20__o
                                               [2U] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[2U]) 
                       | (0xffff0000U & ((__Vfunc_aes128__DOT__shift_rows__20__o
                                          [4U] << 0x00000018U) 
                                         | (__Vfunc_aes128__DOT__shift_rows__20__o
                                            [5U] << 0x00000010U))));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[3U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[3U]) 
                       | (0x0000ffffU & ((0x0000ffffU 
                                          & __Vfunc_aes128__DOT__shift_rows__20__o
                                          [3U]) | (
                                                   (0x0000ffffU 
                                                    & (__Vfunc_aes128__DOT__shift_rows__20__o
                                                       [4U] 
                                                       >> 8U)) 
                                                   | (__Vfunc_aes128__DOT__shift_rows__20__o
                                                      [5U] 
                                                      >> 0x00000010U)))));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[1U] 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[1U]) 
                       | (__Vfunc_aes128__DOT__shift_rows__20__o
                          [8U] << 0x00000018U));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[2U]) 
                       | (0x00ffffffU & ((0x00ffff00U 
                                          & (__Vfunc_aes128__DOT__shift_rows__20__o
                                             [6U] << 8U)) 
                                         | ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__shift_rows__20__o
                                             [7U]) 
                                            | (__Vfunc_aes128__DOT__shift_rows__20__o
                                               [8U] 
                                               >> 8U)))));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[1U] 
                    = ((0xff000000U & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[1U]) 
                       | ((__Vfunc_aes128__DOT__shift_rows__20__o
                           [9U] << 0x00000010U) | (
                                                   (__Vfunc_aes128__DOT__shift_rows__20__o
                                                    [0x0aU] 
                                                    << 8U) 
                                                   | __Vfunc_aes128__DOT__shift_rows__20__o
                                                   [0x0bU])));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[0U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[0U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__20__o
                                          [0x0cU] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__20__o
                                             [0x0dU] 
                                             << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__20__o
                                               [0x0eU] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[0U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[0U]) 
                       | __Vfunc_aes128__DOT__shift_rows__20__o
                       [0x0fU]);
                __Vfunc_aes128__DOT__aes_round__18__t[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__18__t[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__18__t[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__18__t[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__20__Vfuncout[3U];
                __Vfunc_aes128__DOT__sub_bytes__21__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__18__t[0U];
                __Vfunc_aes128__DOT__sub_bytes__21__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__18__t[1U];
                __Vfunc_aes128__DOT__sub_bytes__21__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__18__t[2U];
                __Vfunc_aes128__DOT__sub_bytes__21__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__18__t[3U];
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[3U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[3U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__21__s[3U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__21__s[3U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[3U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[3U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__21__s[3U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__21__s[3U])]));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[2U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__21__s[2U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__21__s[2U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[2U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__21__s[2U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__21__s[2U])]));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[1U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[1U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__21__s[1U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__21__s[1U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[1U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[1U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__21__s[1U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__21__s[1U])]));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[0U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[0U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__21__s[0U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__21__s[0U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[0U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[0U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__21__s[0U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__21__s[0U])]));
                __Vfunc_aes128__DOT__aes_round__18__t[0U] 
                    = __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__18__t[1U] 
                    = __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__18__t[2U] 
                    = __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__18__t[3U] 
                    = __Vfunc_aes128__DOT__sub_bytes__21__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__18__Vfuncout[0U] 
                    = (__Vfunc_aes128__DOT__aes_round__18__t[0U] 
                       ^ __Vfunc_aes128__DOT__aes_round__18__k[0U]);
                __Vfunc_aes128__DOT__aes_round__18__Vfuncout[1U] 
                    = (__Vfunc_aes128__DOT__aes_round__18__t[1U] 
                       ^ __Vfunc_aes128__DOT__aes_round__18__k[1U]);
                __Vfunc_aes128__DOT__aes_round__18__Vfuncout[2U] 
                    = (__Vfunc_aes128__DOT__aes_round__18__t[2U] 
                       ^ __Vfunc_aes128__DOT__aes_round__18__k[2U]);
                __Vfunc_aes128__DOT__aes_round__18__Vfuncout[3U] 
                    = (__Vfunc_aes128__DOT__aes_round__18__t[3U] 
                       ^ __Vfunc_aes128__DOT__aes_round__18__k[3U]);
                vlSelfRef.aes128__DOT__ciphertext[0U] 
                    = __Vfunc_aes128__DOT__aes_round__18__Vfuncout[0U];
                vlSelfRef.aes128__DOT__ciphertext[1U] 
                    = __Vfunc_aes128__DOT__aes_round__18__Vfuncout[1U];
                vlSelfRef.aes128__DOT__ciphertext[2U] 
                    = __Vfunc_aes128__DOT__aes_round__18__Vfuncout[2U];
                vlSelfRef.aes128__DOT__ciphertext[3U] 
                    = __Vfunc_aes128__DOT__aes_round__18__Vfuncout[3U];
            } else {
                __Vfunc_aes128__DOT__next_round_key__36__r 
                    = vlSelfRef.aes128__DOT__round;
                __Vfunc_aes128__DOT__next_round_key__36__k[0U] 
                    = vlSelfRef.aes128__DOT__round_key[0U];
                __Vfunc_aes128__DOT__next_round_key__36__k[1U] 
                    = vlSelfRef.aes128__DOT__round_key[1U];
                __Vfunc_aes128__DOT__next_round_key__36__k[2U] 
                    = vlSelfRef.aes128__DOT__round_key[2U];
                __Vfunc_aes128__DOT__next_round_key__36__k[3U] 
                    = vlSelfRef.aes128__DOT__round_key[3U];
                __Vfunc_aes128__DOT__next_round_key__36__w0 
                    = __Vfunc_aes128__DOT__next_round_key__36__k[3U];
                __Vfunc_aes128__DOT__next_round_key__36__w1 
                    = __Vfunc_aes128__DOT__next_round_key__36__k[2U];
                __Vfunc_aes128__DOT__next_round_key__36__w2 
                    = __Vfunc_aes128__DOT__next_round_key__36__k[1U];
                __Vfunc_aes128__DOT__next_round_key__36__w3 
                    = __Vfunc_aes128__DOT__next_round_key__36__k[0U];
                __Vfunc_aes128__DOT__next_round_key__36__t 
                    = (((vlSelfRef.aes128__DOT__SBOX
                         [(0x000000ffU & (__Vfunc_aes128__DOT__next_round_key__36__w3 
                                          >> 0x10U))] 
                         << 0x00000018U) | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__next_round_key__36__w3 
                                                 >> 8U))] 
                                            << 0x00000010U)) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & __Vfunc_aes128__DOT__next_round_key__36__w3)] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(__Vfunc_aes128__DOT__next_round_key__36__w3 
                            >> 0x18U)]));
                __Vfunc_aes128__DOT__next_round_key__36__t 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__next_round_key__36__t) 
                       | (0xff000000U & ((0xff000000U 
                                          & __Vfunc_aes128__DOT__next_round_key__36__t) 
                                         ^ (((9U >= 
                                              (0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__36__r))
                                              ? vlSelfRef.aes128__DOT__RCON
                                             [(0x0000000fU 
                                               & __Vfunc_aes128__DOT__next_round_key__36__r)]
                                              : 0U) 
                                            << 0x00000018U))));
                __Vfunc_aes128__DOT__next_round_key__36__n0 
                    = (__Vfunc_aes128__DOT__next_round_key__36__w0 
                       ^ __Vfunc_aes128__DOT__next_round_key__36__t);
                __Vfunc_aes128__DOT__next_round_key__36__n1 
                    = (__Vfunc_aes128__DOT__next_round_key__36__w1 
                       ^ __Vfunc_aes128__DOT__next_round_key__36__n0);
                __Vfunc_aes128__DOT__next_round_key__36__n2 
                    = (__Vfunc_aes128__DOT__next_round_key__36__w2 
                       ^ __Vfunc_aes128__DOT__next_round_key__36__n1);
                __Vfunc_aes128__DOT__next_round_key__36__n3 
                    = (__Vfunc_aes128__DOT__next_round_key__36__w3 
                       ^ __Vfunc_aes128__DOT__next_round_key__36__n2);
                __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__n3;
                __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__n2;
                __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[2U] 
                    = (IData)((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__36__n0)) 
                                << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__36__n1))));
                __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[3U] 
                    = (IData)(((((QData)((IData)(__Vfunc_aes128__DOT__next_round_key__36__n0)) 
                                 << 0x00000020U) | (QData)((IData)(__Vfunc_aes128__DOT__next_round_key__36__n1))) 
                               >> 0x00000020U));
                __Vfunc_aes128__DOT__aes_round__35__k[0U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__35__k[1U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__35__k[2U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__35__k[3U] 
                    = __Vfunc_aes128__DOT__next_round_key__36__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__35__s[0U] 
                    = vlSelfRef.aes128__DOT__state[0U];
                __Vfunc_aes128__DOT__aes_round__35__s[1U] 
                    = vlSelfRef.aes128__DOT__state[1U];
                __Vfunc_aes128__DOT__aes_round__35__s[2U] 
                    = vlSelfRef.aes128__DOT__state[2U];
                __Vfunc_aes128__DOT__aes_round__35__s[3U] 
                    = vlSelfRef.aes128__DOT__state[3U];
                __Vfunc_aes128__DOT__shift_rows__37__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__35__s[0U];
                __Vfunc_aes128__DOT__shift_rows__37__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__35__s[1U];
                __Vfunc_aes128__DOT__shift_rows__37__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__35__s[2U];
                __Vfunc_aes128__DOT__shift_rows__37__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__35__s[3U];
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__37__b[__Vi0] = 0;
                }
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__shift_rows__37__o[__Vi0] = 0;
                }
                __Vfunc_aes128__DOT__shift_rows__37__b[0U] 
                    = (__Vfunc_aes128__DOT__shift_rows__37__s[3U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__37__b[1U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[3U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__37__b[2U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[3U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__37__b[3U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__s[3U]);
                __Vfunc_aes128__DOT__shift_rows__37__b[4U] 
                    = (__Vfunc_aes128__DOT__shift_rows__37__s[2U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__37__b[5U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[2U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__37__b[6U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[2U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__37__b[7U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__s[2U]);
                __Vfunc_aes128__DOT__shift_rows__37__b[8U] 
                    = (__Vfunc_aes128__DOT__shift_rows__37__s[1U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__37__b[9U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[1U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0aU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[1U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0bU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__s[1U]);
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0cU] 
                    = (__Vfunc_aes128__DOT__shift_rows__37__s[0U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0dU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[0U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0eU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__shift_rows__37__s[0U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__shift_rows__37__b[0x0fU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__s[0U]);
                __Vfunc_aes128__DOT__shift_rows__37__o[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0U];
                __Vfunc_aes128__DOT__shift_rows__37__o[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [5U];
                __Vfunc_aes128__DOT__shift_rows__37__o[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0aU];
                __Vfunc_aes128__DOT__shift_rows__37__o[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0fU];
                __Vfunc_aes128__DOT__shift_rows__37__o[4U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [4U];
                __Vfunc_aes128__DOT__shift_rows__37__o[5U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [9U];
                __Vfunc_aes128__DOT__shift_rows__37__o[6U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0eU];
                __Vfunc_aes128__DOT__shift_rows__37__o[7U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [3U];
                __Vfunc_aes128__DOT__shift_rows__37__o[8U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [8U];
                __Vfunc_aes128__DOT__shift_rows__37__o[9U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0dU];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0aU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [2U];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0bU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [7U];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0cU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0cU];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0dU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [1U];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0eU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [6U];
                __Vfunc_aes128__DOT__shift_rows__37__o[0x0fU] 
                    = __Vfunc_aes128__DOT__shift_rows__37__b
                    [0x0bU];
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[3U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[3U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__37__o
                                          [0U] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__37__o
                                             [1U] << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__37__o
                                               [2U] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[2U]) 
                       | (0xffff0000U & ((__Vfunc_aes128__DOT__shift_rows__37__o
                                          [4U] << 0x00000018U) 
                                         | (__Vfunc_aes128__DOT__shift_rows__37__o
                                            [5U] << 0x00000010U))));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[3U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[3U]) 
                       | (0x0000ffffU & ((0x0000ffffU 
                                          & __Vfunc_aes128__DOT__shift_rows__37__o
                                          [3U]) | (
                                                   (0x0000ffffU 
                                                    & (__Vfunc_aes128__DOT__shift_rows__37__o
                                                       [4U] 
                                                       >> 8U)) 
                                                   | (__Vfunc_aes128__DOT__shift_rows__37__o
                                                      [5U] 
                                                      >> 0x00000010U)))));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[1U] 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[1U]) 
                       | (__Vfunc_aes128__DOT__shift_rows__37__o
                          [8U] << 0x00000018U));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[2U]) 
                       | (0x00ffffffU & ((0x00ffff00U 
                                          & (__Vfunc_aes128__DOT__shift_rows__37__o
                                             [6U] << 8U)) 
                                         | ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__shift_rows__37__o
                                             [7U]) 
                                            | (__Vfunc_aes128__DOT__shift_rows__37__o
                                               [8U] 
                                               >> 8U)))));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[1U] 
                    = ((0xff000000U & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[1U]) 
                       | ((__Vfunc_aes128__DOT__shift_rows__37__o
                           [9U] << 0x00000010U) | (
                                                   (__Vfunc_aes128__DOT__shift_rows__37__o
                                                    [0x0aU] 
                                                    << 8U) 
                                                   | __Vfunc_aes128__DOT__shift_rows__37__o
                                                   [0x0bU])));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[0U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[0U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__shift_rows__37__o
                                          [0x0cU] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__shift_rows__37__o
                                             [0x0dU] 
                                             << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__shift_rows__37__o
                                               [0x0eU] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[0U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[0U]) 
                       | __Vfunc_aes128__DOT__shift_rows__37__o
                       [0x0fU]);
                __Vfunc_aes128__DOT__aes_round__35__t[0U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__35__t[1U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__35__t[2U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__35__t[3U] 
                    = __Vfunc_aes128__DOT__shift_rows__37__Vfuncout[3U];
                __Vfunc_aes128__DOT__sub_bytes__38__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[0U];
                __Vfunc_aes128__DOT__sub_bytes__38__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[1U];
                __Vfunc_aes128__DOT__sub_bytes__38__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[2U];
                __Vfunc_aes128__DOT__sub_bytes__38__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[3U];
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[3U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[3U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__38__s[3U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__38__s[3U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[3U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[3U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__38__s[3U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__38__s[3U])]));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[2U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__38__s[2U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__38__s[2U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[2U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__38__s[2U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__38__s[2U])]));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[1U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[1U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__38__s[1U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__38__s[1U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[1U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[1U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__38__s[1U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__38__s[1U])]));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[0U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[0U]) 
                       | (0xffff0000U & ((vlSelfRef.aes128__DOT__SBOX
                                          [(__Vfunc_aes128__DOT__sub_bytes__38__s[0U] 
                                            >> 0x00000018U)] 
                                          << 0x00000018U) 
                                         | (vlSelfRef.aes128__DOT__SBOX
                                            [(0x000000ffU 
                                              & (__Vfunc_aes128__DOT__sub_bytes__38__s[0U] 
                                                 >> 0x00000010U))] 
                                            << 0x00000010U))));
                __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[0U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[0U]) 
                       | ((vlSelfRef.aes128__DOT__SBOX
                           [(0x000000ffU & (__Vfunc_aes128__DOT__sub_bytes__38__s[0U] 
                                            >> 8U))] 
                           << 8U) | vlSelfRef.aes128__DOT__SBOX
                          [(0x000000ffU & __Vfunc_aes128__DOT__sub_bytes__38__s[0U])]));
                __Vfunc_aes128__DOT__aes_round__35__t[0U] 
                    = __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__35__t[1U] 
                    = __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__35__t[2U] 
                    = __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__35__t[3U] 
                    = __Vfunc_aes128__DOT__sub_bytes__38__Vfuncout[3U];
                __Vfunc_aes128__DOT__mix_columns__39__s[0U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[0U];
                __Vfunc_aes128__DOT__mix_columns__39__s[1U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[1U];
                __Vfunc_aes128__DOT__mix_columns__39__s[2U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[2U];
                __Vfunc_aes128__DOT__mix_columns__39__s[3U] 
                    = __Vfunc_aes128__DOT__aes_round__35__t[3U];
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__mix_columns__39__b[__Vi0] = 0;
                }
                for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
                    __Vfunc_aes128__DOT__mix_columns__39__o[__Vi0] = 0;
                }
                __Vfunc_aes128__DOT__mix_columns__39__b[0U] 
                    = (__Vfunc_aes128__DOT__mix_columns__39__s[3U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__mix_columns__39__b[1U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[3U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__mix_columns__39__b[2U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[3U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__mix_columns__39__b[3U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__s[3U]);
                __Vfunc_aes128__DOT__mix_columns__39__b[4U] 
                    = (__Vfunc_aes128__DOT__mix_columns__39__s[2U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__mix_columns__39__b[5U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[2U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__mix_columns__39__b[6U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[2U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__mix_columns__39__b[7U] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__s[2U]);
                __Vfunc_aes128__DOT__mix_columns__39__b[8U] 
                    = (__Vfunc_aes128__DOT__mix_columns__39__s[1U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__mix_columns__39__b[9U] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[1U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0aU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[1U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0bU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__s[1U]);
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0cU] 
                    = (__Vfunc_aes128__DOT__mix_columns__39__s[0U] 
                       >> 0x00000018U);
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0dU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[0U] 
                                      >> 0x00000010U));
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0eU] 
                    = (0x000000ffU & (__Vfunc_aes128__DOT__mix_columns__39__s[0U] 
                                      >> 8U));
                __Vfunc_aes128__DOT__mix_columns__39__b[0x0fU] 
                    = (0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__s[0U]);
                __Vfunc_aes128__DOT__mix_columns__39__o[0U] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm2__40__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0U];
                                    __Vfunc_aes128__DOT__gm2__40__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__40__Vfuncout)) 
                         ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm3__41__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [1U];
                                    __Vfunc_aes128__DOT__gm3__41__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__42__a 
                                                    = __Vfunc_aes128__DOT__gm3__41__a;
                                                __Vfunc_aes128__DOT__gm2__42__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__42__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__41__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__41__Vfuncout))) 
                        ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [2U]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [3U]);
                __Vfunc_aes128__DOT__mix_columns__39__o[1U] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [0U] ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm2__43__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [1U];
                                    __Vfunc_aes128__DOT__gm2__43__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__43__Vfuncout))) 
                        ^ ([&]() {
                                __Vfunc_aes128__DOT__gm3__44__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [2U];
                                __Vfunc_aes128__DOT__gm3__44__Vfuncout 
                                    = (([&]() {
                                            __Vfunc_aes128__DOT__gm2__45__a 
                                                = __Vfunc_aes128__DOT__gm3__44__a;
                                            __Vfunc_aes128__DOT__gm2__45__Vfuncout 
                                                = (
                                                   (0x000000feU 
                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                       << 1U)) 
                                                   ^ 
                                                   (0x1bU 
                                                    & (- (IData)(
                                                                 (1U 
                                                                  & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                                     >> 7U))))));
                                        }(), (IData)(__Vfunc_aes128__DOT__gm2__45__Vfuncout)) 
                                       ^ (IData)(__Vfunc_aes128__DOT__gm3__44__a));
                            }(), (IData)(__Vfunc_aes128__DOT__gm3__44__Vfuncout))) 
                       ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [3U]);
                __Vfunc_aes128__DOT__mix_columns__39__o[2U] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [0U] ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [1U]) ^ ([&]() {
                                __Vfunc_aes128__DOT__gm2__46__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [2U];
                                __Vfunc_aes128__DOT__gm2__46__Vfuncout 
                                    = ((0x000000feU 
                                        & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                           << 1U)) 
                                       ^ (0x1bU & (- (IData)(
                                                             (1U 
                                                              & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                                                 >> 7U))))));
                            }(), (IData)(__Vfunc_aes128__DOT__gm2__46__Vfuncout))) 
                       ^ ([&]() {
                            __Vfunc_aes128__DOT__gm3__47__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [3U];
                            __Vfunc_aes128__DOT__gm3__47__Vfuncout 
                                = (([&]() {
                                        __Vfunc_aes128__DOT__gm2__48__a 
                                            = __Vfunc_aes128__DOT__gm3__47__a;
                                        __Vfunc_aes128__DOT__gm2__48__Vfuncout 
                                            = ((0x000000feU 
                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                   << 1U)) 
                                               ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                                   >> 7U))))));
                                    }(), (IData)(__Vfunc_aes128__DOT__gm2__48__Vfuncout)) 
                                   ^ (IData)(__Vfunc_aes128__DOT__gm3__47__a));
                        }(), (IData)(__Vfunc_aes128__DOT__gm3__47__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[3U] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm3__49__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0U];
                                    __Vfunc_aes128__DOT__gm3__49__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__50__a 
                                                    = __Vfunc_aes128__DOT__gm3__49__a;
                                                __Vfunc_aes128__DOT__gm2__50__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__50__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__49__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__49__Vfuncout)) 
                         ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [1U]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [2U]) ^ ([&]() {
                            __Vfunc_aes128__DOT__gm2__51__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [3U];
                            __Vfunc_aes128__DOT__gm2__51__Vfuncout 
                                = ((0x000000feU & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                             >> 7U))))));
                        }(), (IData)(__Vfunc_aes128__DOT__gm2__51__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[4U] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm2__40__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [4U];
                                    __Vfunc_aes128__DOT__gm2__40__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__40__Vfuncout)) 
                         ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm3__41__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [5U];
                                    __Vfunc_aes128__DOT__gm3__41__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__42__a 
                                                    = __Vfunc_aes128__DOT__gm3__41__a;
                                                __Vfunc_aes128__DOT__gm2__42__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__42__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__41__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__41__Vfuncout))) 
                        ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [6U]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [7U]);
                __Vfunc_aes128__DOT__mix_columns__39__o[5U] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [4U] ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm2__43__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [5U];
                                    __Vfunc_aes128__DOT__gm2__43__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__43__Vfuncout))) 
                        ^ ([&]() {
                                __Vfunc_aes128__DOT__gm3__44__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [6U];
                                __Vfunc_aes128__DOT__gm3__44__Vfuncout 
                                    = (([&]() {
                                            __Vfunc_aes128__DOT__gm2__45__a 
                                                = __Vfunc_aes128__DOT__gm3__44__a;
                                            __Vfunc_aes128__DOT__gm2__45__Vfuncout 
                                                = (
                                                   (0x000000feU 
                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                       << 1U)) 
                                                   ^ 
                                                   (0x1bU 
                                                    & (- (IData)(
                                                                 (1U 
                                                                  & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                                     >> 7U))))));
                                        }(), (IData)(__Vfunc_aes128__DOT__gm2__45__Vfuncout)) 
                                       ^ (IData)(__Vfunc_aes128__DOT__gm3__44__a));
                            }(), (IData)(__Vfunc_aes128__DOT__gm3__44__Vfuncout))) 
                       ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [7U]);
                __Vfunc_aes128__DOT__mix_columns__39__o[6U] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [4U] ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [5U]) ^ ([&]() {
                                __Vfunc_aes128__DOT__gm2__46__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [6U];
                                __Vfunc_aes128__DOT__gm2__46__Vfuncout 
                                    = ((0x000000feU 
                                        & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                           << 1U)) 
                                       ^ (0x1bU & (- (IData)(
                                                             (1U 
                                                              & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                                                 >> 7U))))));
                            }(), (IData)(__Vfunc_aes128__DOT__gm2__46__Vfuncout))) 
                       ^ ([&]() {
                            __Vfunc_aes128__DOT__gm3__47__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [7U];
                            __Vfunc_aes128__DOT__gm3__47__Vfuncout 
                                = (([&]() {
                                        __Vfunc_aes128__DOT__gm2__48__a 
                                            = __Vfunc_aes128__DOT__gm3__47__a;
                                        __Vfunc_aes128__DOT__gm2__48__Vfuncout 
                                            = ((0x000000feU 
                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                   << 1U)) 
                                               ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                                   >> 7U))))));
                                    }(), (IData)(__Vfunc_aes128__DOT__gm2__48__Vfuncout)) 
                                   ^ (IData)(__Vfunc_aes128__DOT__gm3__47__a));
                        }(), (IData)(__Vfunc_aes128__DOT__gm3__47__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[7U] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm3__49__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [4U];
                                    __Vfunc_aes128__DOT__gm3__49__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__50__a 
                                                    = __Vfunc_aes128__DOT__gm3__49__a;
                                                __Vfunc_aes128__DOT__gm2__50__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__50__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__49__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__49__Vfuncout)) 
                         ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [5U]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [6U]) ^ ([&]() {
                            __Vfunc_aes128__DOT__gm2__51__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [7U];
                            __Vfunc_aes128__DOT__gm2__51__Vfuncout 
                                = ((0x000000feU & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                             >> 7U))))));
                        }(), (IData)(__Vfunc_aes128__DOT__gm2__51__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[8U] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm2__40__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [8U];
                                    __Vfunc_aes128__DOT__gm2__40__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__40__Vfuncout)) 
                         ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm3__41__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [9U];
                                    __Vfunc_aes128__DOT__gm3__41__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__42__a 
                                                    = __Vfunc_aes128__DOT__gm3__41__a;
                                                __Vfunc_aes128__DOT__gm2__42__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__42__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__41__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__41__Vfuncout))) 
                        ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [0x0aU]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [0x0bU]);
                __Vfunc_aes128__DOT__mix_columns__39__o[9U] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [8U] ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm2__43__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [9U];
                                    __Vfunc_aes128__DOT__gm2__43__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__43__Vfuncout))) 
                        ^ ([&]() {
                                __Vfunc_aes128__DOT__gm3__44__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [0x0aU];
                                __Vfunc_aes128__DOT__gm3__44__Vfuncout 
                                    = (([&]() {
                                            __Vfunc_aes128__DOT__gm2__45__a 
                                                = __Vfunc_aes128__DOT__gm3__44__a;
                                            __Vfunc_aes128__DOT__gm2__45__Vfuncout 
                                                = (
                                                   (0x000000feU 
                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                       << 1U)) 
                                                   ^ 
                                                   (0x1bU 
                                                    & (- (IData)(
                                                                 (1U 
                                                                  & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                                     >> 7U))))));
                                        }(), (IData)(__Vfunc_aes128__DOT__gm2__45__Vfuncout)) 
                                       ^ (IData)(__Vfunc_aes128__DOT__gm3__44__a));
                            }(), (IData)(__Vfunc_aes128__DOT__gm3__44__Vfuncout))) 
                       ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [0x0bU]);
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0aU] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [8U] ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [9U]) ^ ([&]() {
                                __Vfunc_aes128__DOT__gm2__46__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [0x0aU];
                                __Vfunc_aes128__DOT__gm2__46__Vfuncout 
                                    = ((0x000000feU 
                                        & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                           << 1U)) 
                                       ^ (0x1bU & (- (IData)(
                                                             (1U 
                                                              & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                                                 >> 7U))))));
                            }(), (IData)(__Vfunc_aes128__DOT__gm2__46__Vfuncout))) 
                       ^ ([&]() {
                            __Vfunc_aes128__DOT__gm3__47__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [0x0bU];
                            __Vfunc_aes128__DOT__gm3__47__Vfuncout 
                                = (([&]() {
                                        __Vfunc_aes128__DOT__gm2__48__a 
                                            = __Vfunc_aes128__DOT__gm3__47__a;
                                        __Vfunc_aes128__DOT__gm2__48__Vfuncout 
                                            = ((0x000000feU 
                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                   << 1U)) 
                                               ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                                   >> 7U))))));
                                    }(), (IData)(__Vfunc_aes128__DOT__gm2__48__Vfuncout)) 
                                   ^ (IData)(__Vfunc_aes128__DOT__gm3__47__a));
                        }(), (IData)(__Vfunc_aes128__DOT__gm3__47__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0bU] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm3__49__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [8U];
                                    __Vfunc_aes128__DOT__gm3__49__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__50__a 
                                                    = __Vfunc_aes128__DOT__gm3__49__a;
                                                __Vfunc_aes128__DOT__gm2__50__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__50__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__49__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__49__Vfuncout)) 
                         ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [9U]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [0x0aU]) ^ ([&]() {
                            __Vfunc_aes128__DOT__gm2__51__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [0x0bU];
                            __Vfunc_aes128__DOT__gm2__51__Vfuncout 
                                = ((0x000000feU & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                             >> 7U))))));
                        }(), (IData)(__Vfunc_aes128__DOT__gm2__51__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0cU] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm2__40__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0x0cU];
                                    __Vfunc_aes128__DOT__gm2__40__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__40__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__40__Vfuncout)) 
                         ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm3__41__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0x0dU];
                                    __Vfunc_aes128__DOT__gm3__41__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__42__a 
                                                    = __Vfunc_aes128__DOT__gm3__41__a;
                                                __Vfunc_aes128__DOT__gm2__42__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__42__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__42__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__41__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__41__Vfuncout))) 
                        ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [0x0eU]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [0x0fU]);
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0dU] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [0x0cU] ^ ([&]() {
                                    __Vfunc_aes128__DOT__gm2__43__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0x0dU];
                                    __Vfunc_aes128__DOT__gm2__43__Vfuncout 
                                        = ((0x000000feU 
                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                               << 1U)) 
                                           ^ (0x1bU 
                                              & (- (IData)(
                                                           (1U 
                                                            & ((IData)(__Vfunc_aes128__DOT__gm2__43__a) 
                                                               >> 7U))))));
                                }(), (IData)(__Vfunc_aes128__DOT__gm2__43__Vfuncout))) 
                        ^ ([&]() {
                                __Vfunc_aes128__DOT__gm3__44__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [0x0eU];
                                __Vfunc_aes128__DOT__gm3__44__Vfuncout 
                                    = (([&]() {
                                            __Vfunc_aes128__DOT__gm2__45__a 
                                                = __Vfunc_aes128__DOT__gm3__44__a;
                                            __Vfunc_aes128__DOT__gm2__45__Vfuncout 
                                                = (
                                                   (0x000000feU 
                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                       << 1U)) 
                                                   ^ 
                                                   (0x1bU 
                                                    & (- (IData)(
                                                                 (1U 
                                                                  & ((IData)(__Vfunc_aes128__DOT__gm2__45__a) 
                                                                     >> 7U))))));
                                        }(), (IData)(__Vfunc_aes128__DOT__gm2__45__Vfuncout)) 
                                       ^ (IData)(__Vfunc_aes128__DOT__gm3__44__a));
                            }(), (IData)(__Vfunc_aes128__DOT__gm3__44__Vfuncout))) 
                       ^ __Vfunc_aes128__DOT__mix_columns__39__b
                       [0x0fU]);
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0eU] 
                    = (((__Vfunc_aes128__DOT__mix_columns__39__b
                         [0x0cU] ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [0x0dU]) ^ ([&]() {
                                __Vfunc_aes128__DOT__gm2__46__a 
                                    = __Vfunc_aes128__DOT__mix_columns__39__b
                                    [0x0eU];
                                __Vfunc_aes128__DOT__gm2__46__Vfuncout 
                                    = ((0x000000feU 
                                        & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                           << 1U)) 
                                       ^ (0x1bU & (- (IData)(
                                                             (1U 
                                                              & ((IData)(__Vfunc_aes128__DOT__gm2__46__a) 
                                                                 >> 7U))))));
                            }(), (IData)(__Vfunc_aes128__DOT__gm2__46__Vfuncout))) 
                       ^ ([&]() {
                            __Vfunc_aes128__DOT__gm3__47__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [0x0fU];
                            __Vfunc_aes128__DOT__gm3__47__Vfuncout 
                                = (([&]() {
                                        __Vfunc_aes128__DOT__gm2__48__a 
                                            = __Vfunc_aes128__DOT__gm3__47__a;
                                        __Vfunc_aes128__DOT__gm2__48__Vfuncout 
                                            = ((0x000000feU 
                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                   << 1U)) 
                                               ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(__Vfunc_aes128__DOT__gm2__48__a) 
                                                                   >> 7U))))));
                                    }(), (IData)(__Vfunc_aes128__DOT__gm2__48__Vfuncout)) 
                                   ^ (IData)(__Vfunc_aes128__DOT__gm3__47__a));
                        }(), (IData)(__Vfunc_aes128__DOT__gm3__47__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__o[0x0fU] 
                    = (((([&]() {
                                    __Vfunc_aes128__DOT__gm3__49__a 
                                        = __Vfunc_aes128__DOT__mix_columns__39__b
                                        [0x0cU];
                                    __Vfunc_aes128__DOT__gm3__49__Vfuncout 
                                        = (([&]() {
                                                __Vfunc_aes128__DOT__gm2__50__a 
                                                    = __Vfunc_aes128__DOT__gm3__49__a;
                                                __Vfunc_aes128__DOT__gm2__50__Vfuncout 
                                                    = 
                                                    ((0x000000feU 
                                                      & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                         << 1U)) 
                                                     ^ 
                                                     (0x1bU 
                                                      & (- (IData)(
                                                                   (1U 
                                                                    & ((IData)(__Vfunc_aes128__DOT__gm2__50__a) 
                                                                       >> 7U))))));
                                            }(), (IData)(__Vfunc_aes128__DOT__gm2__50__Vfuncout)) 
                                           ^ (IData)(__Vfunc_aes128__DOT__gm3__49__a));
                                }(), (IData)(__Vfunc_aes128__DOT__gm3__49__Vfuncout)) 
                         ^ __Vfunc_aes128__DOT__mix_columns__39__b
                         [0x0dU]) ^ __Vfunc_aes128__DOT__mix_columns__39__b
                        [0x0eU]) ^ ([&]() {
                            __Vfunc_aes128__DOT__gm2__51__a 
                                = __Vfunc_aes128__DOT__mix_columns__39__b
                                [0x0fU];
                            __Vfunc_aes128__DOT__gm2__51__Vfuncout 
                                = ((0x000000feU & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(__Vfunc_aes128__DOT__gm2__51__a) 
                                                             >> 7U))))));
                        }(), (IData)(__Vfunc_aes128__DOT__gm2__51__Vfuncout)));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[3U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[3U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__mix_columns__39__o
                                          [0U] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__mix_columns__39__o
                                             [1U] << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__mix_columns__39__o
                                               [2U] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[2U] 
                    = ((0x0000ffffU & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[2U]) 
                       | (0xffff0000U & ((__Vfunc_aes128__DOT__mix_columns__39__o
                                          [4U] << 0x00000018U) 
                                         | (__Vfunc_aes128__DOT__mix_columns__39__o
                                            [5U] << 0x00000010U))));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[3U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[3U]) 
                       | (0x0000ffffU & ((0x0000ffffU 
                                          & __Vfunc_aes128__DOT__mix_columns__39__o
                                          [3U]) | (
                                                   (0x0000ffffU 
                                                    & (__Vfunc_aes128__DOT__mix_columns__39__o
                                                       [4U] 
                                                       >> 8U)) 
                                                   | (__Vfunc_aes128__DOT__mix_columns__39__o
                                                      [5U] 
                                                      >> 0x00000010U)))));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[1U] 
                    = ((0x00ffffffU & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[1U]) 
                       | (__Vfunc_aes128__DOT__mix_columns__39__o
                          [8U] << 0x00000018U));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[2U] 
                    = ((0xffff0000U & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[2U]) 
                       | (0x00ffffffU & ((0x00ffff00U 
                                          & (__Vfunc_aes128__DOT__mix_columns__39__o
                                             [6U] << 8U)) 
                                         | ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__mix_columns__39__o
                                             [7U]) 
                                            | (__Vfunc_aes128__DOT__mix_columns__39__o
                                               [8U] 
                                               >> 8U)))));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[1U] 
                    = ((0xff000000U & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[1U]) 
                       | ((__Vfunc_aes128__DOT__mix_columns__39__o
                           [9U] << 0x00000010U) | (
                                                   (__Vfunc_aes128__DOT__mix_columns__39__o
                                                    [0x0aU] 
                                                    << 8U) 
                                                   | __Vfunc_aes128__DOT__mix_columns__39__o
                                                   [0x0bU])));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[0U] 
                    = ((0x000000ffU & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[0U]) 
                       | (0xffffff00U & ((__Vfunc_aes128__DOT__mix_columns__39__o
                                          [0x0cU] << 0x00000018U) 
                                         | ((__Vfunc_aes128__DOT__mix_columns__39__o
                                             [0x0dU] 
                                             << 0x00000010U) 
                                            | (__Vfunc_aes128__DOT__mix_columns__39__o
                                               [0x0eU] 
                                               << 8U)))));
                __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[0U] 
                    = ((0xffffff00U & __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[0U]) 
                       | __Vfunc_aes128__DOT__mix_columns__39__o
                       [0x0fU]);
                __Vfunc_aes128__DOT__aes_round__35__t[0U] 
                    = __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[0U];
                __Vfunc_aes128__DOT__aes_round__35__t[1U] 
                    = __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[1U];
                __Vfunc_aes128__DOT__aes_round__35__t[2U] 
                    = __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[2U];
                __Vfunc_aes128__DOT__aes_round__35__t[3U] 
                    = __Vfunc_aes128__DOT__mix_columns__39__Vfuncout[3U];
                __Vfunc_aes128__DOT__aes_round__35__Vfuncout[0U] 
                    = (__Vfunc_aes128__DOT__aes_round__35__t[0U] 
                       ^ __Vfunc_aes128__DOT__aes_round__35__k[0U]);
                __Vfunc_aes128__DOT__aes_round__35__Vfuncout[1U] 
                    = (__Vfunc_aes128__DOT__aes_round__35__t[1U] 
                       ^ __Vfunc_aes128__DOT__aes_round__35__k[1U]);
                __Vfunc_aes128__DOT__aes_round__35__Vfuncout[2U] 
                    = (__Vfunc_aes128__DOT__aes_round__35__t[2U] 
                       ^ __Vfunc_aes128__DOT__aes_round__35__k[2U]);
                __Vfunc_aes128__DOT__aes_round__35__Vfuncout[3U] 
                    = (__Vfunc_aes128__DOT__aes_round__35__t[3U] 
                       ^ __Vfunc_aes128__DOT__aes_round__35__k[3U]);
                __Vdly__aes128__DOT__state[0U] = __Vfunc_aes128__DOT__aes_round__35__Vfuncout[0U];
                __Vdly__aes128__DOT__state[1U] = __Vfunc_aes128__DOT__aes_round__35__Vfuncout[1U];
                __Vdly__aes128__DOT__state[2U] = __Vfunc_aes128__DOT__aes_round__35__Vfuncout[2U];
                __Vdly__aes128__DOT__state[3U] = __Vfunc_aes128__DOT__aes_round__35__Vfuncout[3U];
                __Vdly__aes128__DOT__round = (0x0000000fU 
                                              & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.aes128__DOT__round)));
            }
        }
    } else {
        __Vdly__aes128__DOT__state[0U] = 0U;
        __Vdly__aes128__DOT__state[1U] = 0U;
        __Vdly__aes128__DOT__state[2U] = 0U;
        __Vdly__aes128__DOT__state[3U] = 0U;
        __Vdly__aes128__DOT__round_key[0U] = 0U;
        __Vdly__aes128__DOT__round_key[1U] = 0U;
        __Vdly__aes128__DOT__round_key[2U] = 0U;
        __Vdly__aes128__DOT__round_key[3U] = 0U;
        __Vdly__aes128__DOT__round = 0U;
        __Vdly__aes128__DOT__busy = 0U;
        vlSelfRef.aes128__DOT__done = 0U;
        vlSelfRef.aes128__DOT__ciphertext[0U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[1U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[2U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[3U] = 0U;
    }
    vlSelfRef.aes128__DOT__state[0U] = __Vdly__aes128__DOT__state[0U];
    vlSelfRef.aes128__DOT__state[1U] = __Vdly__aes128__DOT__state[1U];
    vlSelfRef.aes128__DOT__state[2U] = __Vdly__aes128__DOT__state[2U];
    vlSelfRef.aes128__DOT__state[3U] = __Vdly__aes128__DOT__state[3U];
    vlSelfRef.aes128__DOT__round_key[0U] = __Vdly__aes128__DOT__round_key[0U];
    vlSelfRef.aes128__DOT__round_key[1U] = __Vdly__aes128__DOT__round_key[1U];
    vlSelfRef.aes128__DOT__round_key[2U] = __Vdly__aes128__DOT__round_key[2U];
    vlSelfRef.aes128__DOT__round_key[3U] = __Vdly__aes128__DOT__round_key[3U];
    vlSelfRef.aes128__DOT__round = __Vdly__aes128__DOT__round;
    vlSelfRef.aes128__DOT__busy = __Vdly__aes128__DOT__busy;
    vlSelfRef.done = vlSelfRef.aes128__DOT__done;
    vlSelfRef.ciphertext[0U] = vlSelfRef.aes128__DOT__ciphertext[0U];
    vlSelfRef.ciphertext[1U] = vlSelfRef.aes128__DOT__ciphertext[1U];
    vlSelfRef.ciphertext[2U] = vlSelfRef.aes128__DOT__ciphertext[2U];
    vlSelfRef.ciphertext[3U] = vlSelfRef.aes128__DOT__ciphertext[3U];
}

void Vtop___024root___eval_nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vtop___024root___nba_sequent__TOP__0(vlSelf);
    }
}

void Vtop___024root___trigger_orInto__act(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_orInto__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtop___024root___eval_phase__act(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__act\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vtop___024root___eval_triggers__act(vlSelf);
    Vtop___024root___trigger_orInto__act(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vtop___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vtop___024root___eval_phase__nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vtop___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vtop___024root___eval_nba(vlSelf);
        Vtop___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

void Vtop___024root___eval(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/aes128_benchmark_corrupted/rtl_verification/candidates/iteration_02/aes128.sv", 1, "", "Input combinational region did not converge after 100 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
    } while (Vtop___024root___eval_phase__ico(vlSelf));
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/aes128_benchmark_corrupted/rtl_verification/candidates/iteration_02/aes128.sv", 1, "", "NBA region did not converge after 100 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00000064U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/workspace/generated/designs/aes128_benchmark_corrupted/rtl_verification/candidates/iteration_02/aes128.sv", 1, "", "Active region did not converge after 100 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
        } while (Vtop___024root___eval_phase__act(vlSelf));
    } while (Vtop___024root___eval_phase__nba(vlSelf));
}

#ifdef VL_DEBUG
void Vtop___024root___eval_debug_assertions(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_debug_assertions\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst_n & 0xfeU)))) {
        Verilated::overWidthError("rst_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.start & 0xfeU)))) {
        Verilated::overWidthError("start");
    }
}
#endif  // VL_DEBUG
