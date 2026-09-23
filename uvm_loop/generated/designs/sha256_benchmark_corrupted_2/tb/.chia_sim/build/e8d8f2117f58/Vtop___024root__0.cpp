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
    vlSelfRef.sha256__DOT__clk = vlSelfRef.clk;
    vlSelfRef.sha256__DOT__rst_n = vlSelfRef.rst_n;
    vlSelfRef.sha256__DOT__start = vlSelfRef.start;
    vlSelfRef.sha256__DOT__block[0U] = vlSelfRef.block[0U];
    vlSelfRef.sha256__DOT__block[1U] = vlSelfRef.block[1U];
    vlSelfRef.sha256__DOT__block[2U] = vlSelfRef.block[2U];
    vlSelfRef.sha256__DOT__block[3U] = vlSelfRef.block[3U];
    vlSelfRef.sha256__DOT__block[4U] = vlSelfRef.block[4U];
    vlSelfRef.sha256__DOT__block[5U] = vlSelfRef.block[5U];
    vlSelfRef.sha256__DOT__block[6U] = vlSelfRef.block[6U];
    vlSelfRef.sha256__DOT__block[7U] = vlSelfRef.block[7U];
    vlSelfRef.sha256__DOT__block[8U] = vlSelfRef.block[8U];
    vlSelfRef.sha256__DOT__block[9U] = vlSelfRef.block[9U];
    vlSelfRef.sha256__DOT__block[0x0000000aU] = vlSelfRef.block[0x0000000aU];
    vlSelfRef.sha256__DOT__block[0x0000000bU] = vlSelfRef.block[0x0000000bU];
    vlSelfRef.sha256__DOT__block[0x0000000cU] = vlSelfRef.block[0x0000000cU];
    vlSelfRef.sha256__DOT__block[0x0000000dU] = vlSelfRef.block[0x0000000dU];
    vlSelfRef.sha256__DOT__block[0x0000000eU] = vlSelfRef.block[0x0000000eU];
    vlSelfRef.sha256__DOT__block[0x0000000fU] = vlSelfRef.block[0x0000000fU];
    vlSelfRef.done = vlSelfRef.sha256__DOT__done;
    vlSelfRef.digest[0U] = vlSelfRef.sha256__DOT__digest[0U];
    vlSelfRef.digest[1U] = vlSelfRef.sha256__DOT__digest[1U];
    vlSelfRef.digest[2U] = vlSelfRef.sha256__DOT__digest[2U];
    vlSelfRef.digest[3U] = vlSelfRef.sha256__DOT__digest[3U];
    vlSelfRef.digest[4U] = vlSelfRef.sha256__DOT__digest[4U];
    vlSelfRef.digest[5U] = vlSelfRef.sha256__DOT__digest[5U];
    vlSelfRef.digest[6U] = vlSelfRef.sha256__DOT__digest[6U];
    vlSelfRef.digest[7U] = vlSelfRef.sha256__DOT__digest[7U];
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
                                                    ((((~ (IData)(vlSelfRef.sha256__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__rst_n__0)) 
                                                      << 1U) 
                                                     | ((IData)(vlSelfRef.sha256__DOT__clk) 
                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__clk__0 
        = vlSelfRef.sha256__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__rst_n__0 
        = vlSelfRef.sha256__DOT__rst_n;
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

extern const VlWide<8>/*255:0*/ Vtop__ConstPool__CONST_h9e67c271_0;

void Vtop___024root___nba_sequent__TOP__0(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___nba_sequent__TOP__0\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vfunc_sha256__DOT__SmallSigma1__0__Vfuncout;
    __Vfunc_sha256__DOT__SmallSigma1__0__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__SmallSigma1__0__x;
    __Vfunc_sha256__DOT__SmallSigma1__0__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__1__Vfuncout;
    __Vfunc_sha256__DOT__rotr__1__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__1__x;
    __Vfunc_sha256__DOT__rotr__1__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__2__Vfuncout;
    __Vfunc_sha256__DOT__rotr__2__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__2__x;
    __Vfunc_sha256__DOT__rotr__2__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__SmallSigma0__3__Vfuncout;
    __Vfunc_sha256__DOT__SmallSigma0__3__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__SmallSigma0__3__x;
    __Vfunc_sha256__DOT__SmallSigma0__3__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__4__Vfuncout;
    __Vfunc_sha256__DOT__rotr__4__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__4__x;
    __Vfunc_sha256__DOT__rotr__4__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__5__Vfuncout;
    __Vfunc_sha256__DOT__rotr__5__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__5__x;
    __Vfunc_sha256__DOT__rotr__5__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__BigSigma1__6__Vfuncout;
    __Vfunc_sha256__DOT__BigSigma1__6__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__BigSigma1__6__x;
    __Vfunc_sha256__DOT__BigSigma1__6__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__7__Vfuncout;
    __Vfunc_sha256__DOT__rotr__7__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__7__x;
    __Vfunc_sha256__DOT__rotr__7__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__8__Vfuncout;
    __Vfunc_sha256__DOT__rotr__8__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__8__x;
    __Vfunc_sha256__DOT__rotr__8__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__9__Vfuncout;
    __Vfunc_sha256__DOT__rotr__9__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__9__x;
    __Vfunc_sha256__DOT__rotr__9__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Ch__10__Vfuncout;
    __Vfunc_sha256__DOT__Ch__10__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Ch__10__x;
    __Vfunc_sha256__DOT__Ch__10__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Ch__10__y;
    __Vfunc_sha256__DOT__Ch__10__y = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Ch__10__z;
    __Vfunc_sha256__DOT__Ch__10__z = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__BigSigma0__11__Vfuncout;
    __Vfunc_sha256__DOT__BigSigma0__11__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__BigSigma0__11__x;
    __Vfunc_sha256__DOT__BigSigma0__11__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__12__Vfuncout;
    __Vfunc_sha256__DOT__rotr__12__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__12__x;
    __Vfunc_sha256__DOT__rotr__12__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__13__Vfuncout;
    __Vfunc_sha256__DOT__rotr__13__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__13__x;
    __Vfunc_sha256__DOT__rotr__13__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__14__Vfuncout;
    __Vfunc_sha256__DOT__rotr__14__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__rotr__14__x;
    __Vfunc_sha256__DOT__rotr__14__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Maj__15__Vfuncout;
    __Vfunc_sha256__DOT__Maj__15__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Maj__15__x;
    __Vfunc_sha256__DOT__Maj__15__x = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Maj__15__y;
    __Vfunc_sha256__DOT__Maj__15__y = 0;
    IData/*31:0*/ __Vfunc_sha256__DOT__Maj__15__z;
    __Vfunc_sha256__DOT__Maj__15__z = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__a;
    __Vdly__sha256__DOT__a = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__b;
    __Vdly__sha256__DOT__b = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__c;
    __Vdly__sha256__DOT__c = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__d;
    __Vdly__sha256__DOT__d = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__e;
    __Vdly__sha256__DOT__e = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__f;
    __Vdly__sha256__DOT__f = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__g;
    __Vdly__sha256__DOT__g = 0;
    IData/*31:0*/ __Vdly__sha256__DOT__h;
    __Vdly__sha256__DOT__h = 0;
    CData/*6:0*/ __Vdly__sha256__DOT__round;
    __Vdly__sha256__DOT__round = 0;
    CData/*0:0*/ __Vdly__sha256__DOT__busy;
    __Vdly__sha256__DOT__busy = 0;
    IData/*31:0*/ __VdlyVal__sha256__DOT__W__v0;
    __VdlyVal__sha256__DOT__W__v0 = 0;
    CData/*5:0*/ __VdlyDim0__sha256__DOT__W__v0;
    __VdlyDim0__sha256__DOT__W__v0 = 0;
    IData/*31:0*/ __VdlyVal__sha256__DOT__W__v1;
    __VdlyVal__sha256__DOT__W__v1 = 0;
    CData/*5:0*/ __VdlyDim0__sha256__DOT__W__v1;
    __VdlyDim0__sha256__DOT__W__v1 = 0;
    CData/*5:0*/ __VdlyDim0__sha256__DOT__W__v2;
    __VdlyDim0__sha256__DOT__W__v2 = 0;
    // Body
    __Vdly__sha256__DOT__a = vlSelfRef.sha256__DOT__a;
    __Vdly__sha256__DOT__b = vlSelfRef.sha256__DOT__b;
    __Vdly__sha256__DOT__c = vlSelfRef.sha256__DOT__c;
    __Vdly__sha256__DOT__d = vlSelfRef.sha256__DOT__d;
    __Vdly__sha256__DOT__e = vlSelfRef.sha256__DOT__e;
    __Vdly__sha256__DOT__f = vlSelfRef.sha256__DOT__f;
    __Vdly__sha256__DOT__g = vlSelfRef.sha256__DOT__g;
    __Vdly__sha256__DOT__h = vlSelfRef.sha256__DOT__h;
    __Vdly__sha256__DOT__round = vlSelfRef.sha256__DOT__round;
    __Vdly__sha256__DOT__busy = vlSelfRef.sha256__DOT__busy;
    if (vlSelfRef.sha256__DOT__rst_n) {
        vlSelfRef.sha256__DOT__done = 1U;
        if (((IData)(vlSelfRef.sha256__DOT__start) 
             & (~ (IData)(vlSelfRef.sha256__DOT__busy)))) {
            vlSelfRef.sha256__DOT__i = 0U;
            while (VL_GTS_III(32, 0x00000010U, vlSelfRef.sha256__DOT__i)) {
                vlSelfRef.sha256__DOT__message_word 
                    = (((0U == (0x0000001fU & (((IData)(0x01ffU) 
                                                - VL_SHIFTL_III(9,32,32, vlSelfRef.sha256__DOT__i, 5U)) 
                                               - (IData)(0x001fU))))
                         ? 0U : (vlSelfRef.sha256__DOT__block[
                                 (((IData)(0x0000001fU) 
                                   + (0x000001ffU & 
                                      (((IData)(0x01ffU) 
                                        - VL_SHIFTL_III(9,32,32, vlSelfRef.sha256__DOT__i, 5U)) 
                                       - (IData)(0x001fU)))) 
                                  >> 5U)] << ((IData)(0x00000020U) 
                                              - (0x0000001fU 
                                                 & (((IData)(0x01ffU) 
                                                     - 
                                                     VL_SHIFTL_III(9,32,32, vlSelfRef.sha256__DOT__i, 5U)) 
                                                    - (IData)(0x001fU)))))) 
                       | (vlSelfRef.sha256__DOT__block[
                          (0x0000000fU & ((((IData)(0x01ffU) 
                                            - VL_SHIFTL_III(9,32,32, vlSelfRef.sha256__DOT__i, 5U)) 
                                           - (IData)(0x001fU)) 
                                          >> 5U))] 
                          >> (0x0000001fU & (((IData)(0x01ffU) 
                                              - VL_SHIFTL_III(9,32,32, vlSelfRef.sha256__DOT__i, 5U)) 
                                             - (IData)(0x001fU)))));
                __VdlyVal__sha256__DOT__W__v0 = vlSelfRef.sha256__DOT__message_word;
                __VdlyDim0__sha256__DOT__W__v0 = (0x0000003fU 
                                                  & vlSelfRef.sha256__DOT__i);
                vlSelfRef.__VdlyCommitQueuesha256__DOT__W.enqueue(__VdlyVal__sha256__DOT__W__v0, (IData)(__VdlyDim0__sha256__DOT__W__v0));
                vlSelfRef.sha256__DOT__i = ((IData)(1U) 
                                            + vlSelfRef.sha256__DOT__i);
            }
            vlSelfRef.sha256__DOT__H0 = 0x6a09e667U;
            vlSelfRef.sha256__DOT__H1 = 0xbb67ae85U;
            vlSelfRef.sha256__DOT__H2 = 0x3c6ef372U;
            vlSelfRef.sha256__DOT__H3 = 0xa54ff53aU;
            vlSelfRef.sha256__DOT__H4 = 0x510e527fU;
            vlSelfRef.sha256__DOT__H5 = 0x9b05688cU;
            vlSelfRef.sha256__DOT__H6 = 0x1f83d9abU;
            vlSelfRef.sha256__DOT__H7 = 0x5be0cd19U;
            __Vdly__sha256__DOT__a = 0x6a09e667U;
            __Vdly__sha256__DOT__b = 0xbb67ae85U;
            __Vdly__sha256__DOT__c = 0x3c6ef372U;
            __Vdly__sha256__DOT__d = 0xa54ff53aU;
            __Vdly__sha256__DOT__e = 0x510e527fU;
            __Vdly__sha256__DOT__f = 0x9b05688cU;
            __Vdly__sha256__DOT__g = 0x1f83d9abU;
            __Vdly__sha256__DOT__h = 0x5be0cd19U;
            __Vdly__sha256__DOT__round = 0U;
            __Vdly__sha256__DOT__busy = 1U;
        } else if (vlSelfRef.sha256__DOT__busy) {
            vlSelfRef.sha256__DOT__next_w = ((0x10U 
                                              > (IData)(vlSelfRef.sha256__DOT__round))
                                              ? vlSelfRef.sha256__DOT__W
                                             [(0x0000003fU 
                                               & (IData)(vlSelfRef.sha256__DOT__round))]
                                              : (((
                                                   ([&]() {
                                    __Vfunc_sha256__DOT__SmallSigma1__0__x 
                                        = vlSelfRef.sha256__DOT__W
                                        [(0x0000003fU 
                                          & ((IData)(vlSelfRef.sha256__DOT__round) 
                                             - (IData)(2U)))];
                                    __Vfunc_sha256__DOT__SmallSigma1__0__Vfuncout 
                                        = ((([&]() {
                                                    __Vfunc_sha256__DOT__rotr__1__x 
                                                        = __Vfunc_sha256__DOT__SmallSigma1__0__x;
                                                    __Vfunc_sha256__DOT__rotr__1__Vfuncout 
                                                        = 
                                                        (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__1__x, 0x00000011U) 
                                                         | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__1__x, 0x0000000fU));
                                                }(), __Vfunc_sha256__DOT__rotr__1__Vfuncout) 
                                            ^ ([&]() {
                                                    __Vfunc_sha256__DOT__rotr__2__x 
                                                        = __Vfunc_sha256__DOT__SmallSigma1__0__x;
                                                    __Vfunc_sha256__DOT__rotr__2__Vfuncout 
                                                        = 
                                                        (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__2__x, 0x00000013U) 
                                                         | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__2__x, 0x0000000dU));
                                                }(), __Vfunc_sha256__DOT__rotr__2__Vfuncout)) 
                                           ^ VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__SmallSigma1__0__x, 0x0000000aU));
                                }(), __Vfunc_sha256__DOT__SmallSigma1__0__Vfuncout) 
                                                   + 
                                                   vlSelfRef.sha256__DOT__W
                                                   [
                                                   (0x0000003fU 
                                                    & ((IData)(vlSelfRef.sha256__DOT__round) 
                                                       - (IData)(7U)))]) 
                                                  + 
                                                  ([&]() {
                                __Vfunc_sha256__DOT__SmallSigma0__3__x 
                                    = vlSelfRef.sha256__DOT__W
                                    [(0x0000003fU & 
                                      ((IData)(vlSelfRef.sha256__DOT__round) 
                                       - (IData)(0x0fU)))];
                                __Vfunc_sha256__DOT__SmallSigma0__3__Vfuncout 
                                    = ((([&]() {
                                                __Vfunc_sha256__DOT__rotr__4__x 
                                                    = __Vfunc_sha256__DOT__SmallSigma0__3__x;
                                                __Vfunc_sha256__DOT__rotr__4__Vfuncout 
                                                    = 
                                                    (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__4__x, 7U) 
                                                     | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__4__x, 0x00000019U));
                                            }(), __Vfunc_sha256__DOT__rotr__4__Vfuncout) 
                                        ^ ([&]() {
                                                __Vfunc_sha256__DOT__rotr__5__x 
                                                    = __Vfunc_sha256__DOT__SmallSigma0__3__x;
                                                __Vfunc_sha256__DOT__rotr__5__Vfuncout 
                                                    = 
                                                    (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__5__x, 0x00000012U) 
                                                     | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__5__x, 0x0000000eU));
                                            }(), __Vfunc_sha256__DOT__rotr__5__Vfuncout)) 
                                       ^ VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__SmallSigma0__3__x, 3U));
                            }(), __Vfunc_sha256__DOT__SmallSigma0__3__Vfuncout)) 
                                                 + 
                                                 vlSelfRef.sha256__DOT__W
                                                 [(0x0000003fU 
                                                   & ((IData)(vlSelfRef.sha256__DOT__round) 
                                                      - (IData)(0x10U)))]));
            if ((0x10U <= (IData)(vlSelfRef.sha256__DOT__round))) {
                __VdlyVal__sha256__DOT__W__v1 = vlSelfRef.sha256__DOT__next_w;
                __VdlyDim0__sha256__DOT__W__v1 = (0x0000003fU 
                                                  & (IData)(vlSelfRef.sha256__DOT__round));
                vlSelfRef.__VdlyCommitQueuesha256__DOT__W.enqueue(__VdlyVal__sha256__DOT__W__v1, (IData)(__VdlyDim0__sha256__DOT__W__v1));
            }
            vlSelfRef.sha256__DOT__next_t1 = ((((vlSelfRef.sha256__DOT__h 
                                                 + 
                                                 ([&]() {
                                    __Vfunc_sha256__DOT__BigSigma1__6__x 
                                        = vlSelfRef.sha256__DOT__e;
                                    __Vfunc_sha256__DOT__BigSigma1__6__Vfuncout 
                                        = ((([&]() {
                                                    __Vfunc_sha256__DOT__rotr__7__x 
                                                        = __Vfunc_sha256__DOT__BigSigma1__6__x;
                                                    __Vfunc_sha256__DOT__rotr__7__Vfuncout 
                                                        = 
                                                        (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__7__x, 6U) 
                                                         | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__7__x, 0x0000001aU));
                                                }(), __Vfunc_sha256__DOT__rotr__7__Vfuncout) 
                                            ^ ([&]() {
                                                    __Vfunc_sha256__DOT__rotr__8__x 
                                                        = __Vfunc_sha256__DOT__BigSigma1__6__x;
                                                    __Vfunc_sha256__DOT__rotr__8__Vfuncout 
                                                        = 
                                                        (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__8__x, 0x0000000bU) 
                                                         | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__8__x, 0x00000015U));
                                                }(), __Vfunc_sha256__DOT__rotr__8__Vfuncout)) 
                                           ^ ([&]() {
                                                __Vfunc_sha256__DOT__rotr__9__x 
                                                    = __Vfunc_sha256__DOT__BigSigma1__6__x;
                                                __Vfunc_sha256__DOT__rotr__9__Vfuncout 
                                                    = 
                                                    (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__9__x, 0x00000019U) 
                                                     | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__9__x, 7U));
                                            }(), __Vfunc_sha256__DOT__rotr__9__Vfuncout));
                                }(), __Vfunc_sha256__DOT__BigSigma1__6__Vfuncout)) 
                                                + ([&]() {
                                __Vfunc_sha256__DOT__Ch__10__z 
                                    = vlSelfRef.sha256__DOT__g;
                                __Vfunc_sha256__DOT__Ch__10__y 
                                    = vlSelfRef.sha256__DOT__f;
                                __Vfunc_sha256__DOT__Ch__10__x 
                                    = vlSelfRef.sha256__DOT__e;
                                __Vfunc_sha256__DOT__Ch__10__Vfuncout 
                                    = ((__Vfunc_sha256__DOT__Ch__10__x 
                                        & __Vfunc_sha256__DOT__Ch__10__y) 
                                       ^ ((~ __Vfunc_sha256__DOT__Ch__10__x) 
                                          & __Vfunc_sha256__DOT__Ch__10__z));
                            }(), __Vfunc_sha256__DOT__Ch__10__Vfuncout)) 
                                               + vlSelfRef.sha256__DOT__K
                                               [(0x0000003fU 
                                                 & (IData)(vlSelfRef.sha256__DOT__round))]) 
                                              + vlSelfRef.sha256__DOT__next_w);
            vlSelfRef.sha256__DOT__next_t2 = (([&]() {
                        __Vfunc_sha256__DOT__BigSigma0__11__x 
                            = vlSelfRef.sha256__DOT__a;
                        __Vfunc_sha256__DOT__BigSigma0__11__Vfuncout 
                            = ((([&]() {
                                        __Vfunc_sha256__DOT__rotr__12__x 
                                            = __Vfunc_sha256__DOT__BigSigma0__11__x;
                                        __Vfunc_sha256__DOT__rotr__12__Vfuncout 
                                            = (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__12__x, 2U) 
                                               | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__12__x, 0x0000001eU));
                                    }(), __Vfunc_sha256__DOT__rotr__12__Vfuncout) 
                                ^ ([&]() {
                                        __Vfunc_sha256__DOT__rotr__13__x 
                                            = __Vfunc_sha256__DOT__BigSigma0__11__x;
                                        __Vfunc_sha256__DOT__rotr__13__Vfuncout 
                                            = (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__13__x, 0x0000000dU) 
                                               | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__13__x, 0x00000013U));
                                    }(), __Vfunc_sha256__DOT__rotr__13__Vfuncout)) 
                               ^ ([&]() {
                                    __Vfunc_sha256__DOT__rotr__14__x 
                                        = __Vfunc_sha256__DOT__BigSigma0__11__x;
                                    __Vfunc_sha256__DOT__rotr__14__Vfuncout 
                                        = (VL_SHIFTR_III(32,32,32, __Vfunc_sha256__DOT__rotr__14__x, 0x00000016U) 
                                           | VL_SHIFTL_III(32,32,32, __Vfunc_sha256__DOT__rotr__14__x, 0x0000000aU));
                                }(), __Vfunc_sha256__DOT__rotr__14__Vfuncout));
                    }(), __Vfunc_sha256__DOT__BigSigma0__11__Vfuncout) 
                                              + ([&]() {
                        __Vfunc_sha256__DOT__Maj__15__z 
                            = vlSelfRef.sha256__DOT__c;
                        __Vfunc_sha256__DOT__Maj__15__y 
                            = vlSelfRef.sha256__DOT__b;
                        __Vfunc_sha256__DOT__Maj__15__x 
                            = vlSelfRef.sha256__DOT__a;
                        __Vfunc_sha256__DOT__Maj__15__Vfuncout 
                            = (((__Vfunc_sha256__DOT__Maj__15__x 
                                 & __Vfunc_sha256__DOT__Maj__15__y) 
                                ^ (__Vfunc_sha256__DOT__Maj__15__x 
                                   & __Vfunc_sha256__DOT__Maj__15__z)) 
                               ^ (__Vfunc_sha256__DOT__Maj__15__y 
                                  & __Vfunc_sha256__DOT__Maj__15__z));
                    }(), __Vfunc_sha256__DOT__Maj__15__Vfuncout));
            vlSelfRef.sha256__DOT__na = (vlSelfRef.sha256__DOT__next_t1 
                                         + vlSelfRef.sha256__DOT__next_t2);
            vlSelfRef.sha256__DOT__nb = vlSelfRef.sha256__DOT__a;
            vlSelfRef.sha256__DOT__nc = vlSelfRef.sha256__DOT__b;
            vlSelfRef.sha256__DOT__nd = vlSelfRef.sha256__DOT__c;
            vlSelfRef.sha256__DOT__ne = (vlSelfRef.sha256__DOT__d 
                                         + vlSelfRef.sha256__DOT__next_t1);
            vlSelfRef.sha256__DOT__nf = vlSelfRef.sha256__DOT__e;
            vlSelfRef.sha256__DOT__ng = vlSelfRef.sha256__DOT__f;
            vlSelfRef.sha256__DOT__nh = vlSelfRef.sha256__DOT__g;
            __Vdly__sha256__DOT__a = vlSelfRef.sha256__DOT__na;
            __Vdly__sha256__DOT__b = vlSelfRef.sha256__DOT__nb;
            __Vdly__sha256__DOT__c = vlSelfRef.sha256__DOT__nc;
            __Vdly__sha256__DOT__d = vlSelfRef.sha256__DOT__nd;
            __Vdly__sha256__DOT__e = vlSelfRef.sha256__DOT__ne;
            __Vdly__sha256__DOT__f = vlSelfRef.sha256__DOT__nf;
            __Vdly__sha256__DOT__g = vlSelfRef.sha256__DOT__ng;
            __Vdly__sha256__DOT__h = vlSelfRef.sha256__DOT__nh;
            if ((0x3fU == (IData)(vlSelfRef.sha256__DOT__round))) {
                vlSelfRef.sha256__DOT__digest[0U] = 
                    ((IData)(0x5be0cd19U) + vlSelfRef.sha256__DOT__nh);
                vlSelfRef.sha256__DOT__digest[1U] = (IData)(
                                                            (((QData)((IData)(
                                                                              ((IData)(0x9b05688cU) 
                                                                               + vlSelfRef.sha256__DOT__nf))) 
                                                              << 0x00000020U) 
                                                             | (QData)((IData)(
                                                                               ((IData)(0x1f83d9abU) 
                                                                                + vlSelfRef.sha256__DOT__ng)))));
                vlSelfRef.sha256__DOT__digest[2U] = (IData)(
                                                            ((((QData)((IData)(
                                                                               ((IData)(0x9b05688cU) 
                                                                                + vlSelfRef.sha256__DOT__nf))) 
                                                               << 0x00000020U) 
                                                              | (QData)((IData)(
                                                                                ((IData)(0x1f83d9abU) 
                                                                                + vlSelfRef.sha256__DOT__ng)))) 
                                                             >> 0x00000020U));
                vlSelfRef.sha256__DOT__digest[3U] = 
                    ((IData)(0x510e527fU) + vlSelfRef.sha256__DOT__ne);
                vlSelfRef.sha256__DOT__digest[4U] = (IData)(
                                                            (((QData)((IData)(
                                                                              ((IData)(0x3c6ef372U) 
                                                                               + vlSelfRef.sha256__DOT__nc))) 
                                                              << 0x00000020U) 
                                                             | (QData)((IData)(
                                                                               ((IData)(0xa54ff53aU) 
                                                                                + vlSelfRef.sha256__DOT__nd)))));
                vlSelfRef.sha256__DOT__digest[5U] = (IData)(
                                                            ((((QData)((IData)(
                                                                               ((IData)(0x3c6ef372U) 
                                                                                + vlSelfRef.sha256__DOT__nc))) 
                                                               << 0x00000020U) 
                                                              | (QData)((IData)(
                                                                                ((IData)(0xa54ff53aU) 
                                                                                + vlSelfRef.sha256__DOT__nd)))) 
                                                             >> 0x00000020U));
                vlSelfRef.sha256__DOT__digest[6U] = (IData)(
                                                            (((QData)((IData)(
                                                                              ((IData)(0x6a09e667U) 
                                                                               + vlSelfRef.sha256__DOT__na))) 
                                                              << 0x00000020U) 
                                                             | (QData)((IData)(
                                                                               ((IData)(0xbb67ae85U) 
                                                                                + vlSelfRef.sha256__DOT__nb)))));
                vlSelfRef.sha256__DOT__digest[7U] = (IData)(
                                                            ((((QData)((IData)(
                                                                               ((IData)(0x6a09e667U) 
                                                                                + vlSelfRef.sha256__DOT__na))) 
                                                               << 0x00000020U) 
                                                              | (QData)((IData)(
                                                                                ((IData)(0xbb67ae85U) 
                                                                                + vlSelfRef.sha256__DOT__nb)))) 
                                                             >> 0x00000020U));
                __Vdly__sha256__DOT__busy = 0U;
                vlSelfRef.sha256__DOT__done = 1U;
            } else {
                __Vdly__sha256__DOT__round = (0x0000007fU 
                                              & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.sha256__DOT__round)));
            }
        }
    } else {
        vlSelfRef.sha256__DOT__i = 0U;
        vlSelfRef.sha256__DOT__done = 1U;
        vlSelfRef.sha256__DOT__digest[0U] = Vtop__ConstPool__CONST_h9e67c271_0[0U];
        vlSelfRef.sha256__DOT__digest[1U] = Vtop__ConstPool__CONST_h9e67c271_0[1U];
        vlSelfRef.sha256__DOT__digest[2U] = Vtop__ConstPool__CONST_h9e67c271_0[2U];
        vlSelfRef.sha256__DOT__digest[3U] = Vtop__ConstPool__CONST_h9e67c271_0[3U];
        vlSelfRef.sha256__DOT__digest[4U] = Vtop__ConstPool__CONST_h9e67c271_0[4U];
        vlSelfRef.sha256__DOT__digest[5U] = Vtop__ConstPool__CONST_h9e67c271_0[5U];
        vlSelfRef.sha256__DOT__digest[6U] = Vtop__ConstPool__CONST_h9e67c271_0[6U];
        vlSelfRef.sha256__DOT__digest[7U] = Vtop__ConstPool__CONST_h9e67c271_0[7U];
        __Vdly__sha256__DOT__busy = 0U;
        __Vdly__sha256__DOT__round = 0U;
        vlSelfRef.sha256__DOT__H0 = 0x6a09e667U;
        vlSelfRef.sha256__DOT__H1 = 0xbb67ae85U;
        vlSelfRef.sha256__DOT__H2 = 0x3c6ef372U;
        vlSelfRef.sha256__DOT__H3 = 0xa54ff53aU;
        vlSelfRef.sha256__DOT__H4 = 0x510e527fU;
        vlSelfRef.sha256__DOT__H5 = 0x9b05688cU;
        vlSelfRef.sha256__DOT__H6 = 0x1f83d9abU;
        vlSelfRef.sha256__DOT__H7 = 0x5be0cd19U;
        __Vdly__sha256__DOT__a = 0U;
        __Vdly__sha256__DOT__b = 0U;
        __Vdly__sha256__DOT__c = 0U;
        __Vdly__sha256__DOT__d = 0U;
        __Vdly__sha256__DOT__e = 0U;
        __Vdly__sha256__DOT__f = 0U;
        __Vdly__sha256__DOT__g = 0U;
        __Vdly__sha256__DOT__h = 0U;
        while (VL_GTS_III(32, 0x00000040U, vlSelfRef.sha256__DOT__i)) {
            __VdlyDim0__sha256__DOT__W__v2 = (0x0000003fU 
                                              & vlSelfRef.sha256__DOT__i);
            vlSelfRef.__VdlyCommitQueuesha256__DOT__W.enqueue(0U, (IData)(__VdlyDim0__sha256__DOT__W__v2));
            vlSelfRef.sha256__DOT__i = ((IData)(1U) 
                                        + vlSelfRef.sha256__DOT__i);
        }
    }
    vlSelfRef.sha256__DOT__a = __Vdly__sha256__DOT__a;
    vlSelfRef.sha256__DOT__b = __Vdly__sha256__DOT__b;
    vlSelfRef.sha256__DOT__c = __Vdly__sha256__DOT__c;
    vlSelfRef.sha256__DOT__d = __Vdly__sha256__DOT__d;
    vlSelfRef.sha256__DOT__e = __Vdly__sha256__DOT__e;
    vlSelfRef.sha256__DOT__f = __Vdly__sha256__DOT__f;
    vlSelfRef.sha256__DOT__g = __Vdly__sha256__DOT__g;
    vlSelfRef.sha256__DOT__h = __Vdly__sha256__DOT__h;
    vlSelfRef.sha256__DOT__round = __Vdly__sha256__DOT__round;
    vlSelfRef.sha256__DOT__busy = __Vdly__sha256__DOT__busy;
    vlSelfRef.__VdlyCommitQueuesha256__DOT__W.commit(vlSelfRef.sha256__DOT__W);
    vlSelfRef.done = vlSelfRef.sha256__DOT__done;
    vlSelfRef.digest[0U] = vlSelfRef.sha256__DOT__digest[0U];
    vlSelfRef.digest[1U] = vlSelfRef.sha256__DOT__digest[1U];
    vlSelfRef.digest[2U] = vlSelfRef.sha256__DOT__digest[2U];
    vlSelfRef.digest[3U] = vlSelfRef.sha256__DOT__digest[3U];
    vlSelfRef.digest[4U] = vlSelfRef.sha256__DOT__digest[4U];
    vlSelfRef.digest[5U] = vlSelfRef.sha256__DOT__digest[5U];
    vlSelfRef.digest[6U] = vlSelfRef.sha256__DOT__digest[6U];
    vlSelfRef.digest[7U] = vlSelfRef.sha256__DOT__digest[7U];
}

void Vtop___024root___eval_nba(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_nba\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
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
            VL_FATAL_MT("/workspace/generated/designs/sha256_benchmark_corrupted_2/rtl_verification/accepted/sha256.sv", 1, "", "Input combinational region did not converge after 100 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
    } while (Vtop___024root___eval_phase__ico(vlSelf));
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/sha256_benchmark_corrupted_2/rtl_verification/accepted/sha256.sv", 1, "", "NBA region did not converge after 100 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00000064U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/workspace/generated/designs/sha256_benchmark_corrupted_2/rtl_verification/accepted/sha256.sv", 1, "", "Active region did not converge after 100 tries");
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
