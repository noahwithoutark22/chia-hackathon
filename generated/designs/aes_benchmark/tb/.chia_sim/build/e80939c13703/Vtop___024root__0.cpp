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
    // Locals
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__0__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__0__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__next_round_key__0__k;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__next_round_key__0__k);
    CData/*3:0*/ __Vfunc_aes128__DOT__next_round_key__0__r;
    __Vfunc_aes128__DOT__next_round_key__0__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w0;
    __Vfunc_aes128__DOT__next_round_key__0__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w1;
    __Vfunc_aes128__DOT__next_round_key__0__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w2;
    __Vfunc_aes128__DOT__next_round_key__0__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w3;
    __Vfunc_aes128__DOT__next_round_key__0__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n0;
    __Vfunc_aes128__DOT__next_round_key__0__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n1;
    __Vfunc_aes128__DOT__next_round_key__0__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n2;
    __Vfunc_aes128__DOT__next_round_key__0__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n3;
    __Vfunc_aes128__DOT__next_round_key__0__n3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__Vfuncout;
    __Vfunc_aes128__DOT__next_word__1__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__prev;
    __Vfunc_aes128__DOT__next_word__1__prev = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__word0;
    __Vfunc_aes128__DOT__next_word__1__word0 = 0;
    CData/*3:0*/ __Vfunc_aes128__DOT__next_word__1__r;
    __Vfunc_aes128__DOT__next_word__1__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__t;
    __Vfunc_aes128__DOT__next_word__1__t = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__next_word__1__rc;
    __Vfunc_aes128__DOT__next_word__1__rc = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__6__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__6__x);
    IData/*31:0*/ __Vfunc_aes128__DOT__sub_bytes__6__i;
    __Vfunc_aes128__DOT__sub_bytes__6__i = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__8__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__8__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__8__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__8__x);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__9__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__9__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__9__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__9__x);
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a0;
    __Vfunc_aes128__DOT__mix_columns__9__a0 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a1;
    __Vfunc_aes128__DOT__mix_columns__9__a1 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a2;
    __Vfunc_aes128__DOT__mix_columns__9__a2 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a3;
    __Vfunc_aes128__DOT__mix_columns__9__a3 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b0;
    __Vfunc_aes128__DOT__mix_columns__9__b0 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b1;
    __Vfunc_aes128__DOT__mix_columns__9__b1 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b2;
    __Vfunc_aes128__DOT__mix_columns__9__b2 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b3;
    __Vfunc_aes128__DOT__mix_columns__9__b3 = 0;
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
    vlSelfRef.ciphertext[0U] = vlSelfRef.aes128__DOT__ciphertext[0U];
    vlSelfRef.ciphertext[1U] = vlSelfRef.aes128__DOT__ciphertext[1U];
    vlSelfRef.ciphertext[2U] = vlSelfRef.aes128__DOT__ciphertext[2U];
    vlSelfRef.ciphertext[3U] = vlSelfRef.aes128__DOT__ciphertext[3U];
    vlSelfRef.busy = vlSelfRef.aes128__DOT__busy;
    vlSelfRef.done = vlSelfRef.aes128__DOT__done;
    __Vfunc_aes128__DOT__next_round_key__0__r = (0x0000000fU 
                                                 & ((IData)(1U) 
                                                    + (IData)(vlSelfRef.aes128__DOT__round)));
    __Vfunc_aes128__DOT__next_round_key__0__k[0U] = 
        vlSelfRef.aes128__DOT__round_key[0U];
    __Vfunc_aes128__DOT__next_round_key__0__k[1U] = 
        vlSelfRef.aes128__DOT__round_key[1U];
    __Vfunc_aes128__DOT__next_round_key__0__k[2U] = 
        vlSelfRef.aes128__DOT__round_key[2U];
    __Vfunc_aes128__DOT__next_round_key__0__k[3U] = 
        vlSelfRef.aes128__DOT__round_key[3U];
    __Vfunc_aes128__DOT__next_round_key__0__w0 = __Vfunc_aes128__DOT__next_round_key__0__k[3U];
    __Vfunc_aes128__DOT__next_round_key__0__w1 = __Vfunc_aes128__DOT__next_round_key__0__k[2U];
    __Vfunc_aes128__DOT__next_round_key__0__w2 = __Vfunc_aes128__DOT__next_round_key__0__k[1U];
    __Vfunc_aes128__DOT__next_round_key__0__w3 = __Vfunc_aes128__DOT__next_round_key__0__k[0U];
    __Vfunc_aes128__DOT__next_word__1__r = __Vfunc_aes128__DOT__next_round_key__0__r;
    __Vfunc_aes128__DOT__next_word__1__word0 = __Vfunc_aes128__DOT__next_round_key__0__w0;
    __Vfunc_aes128__DOT__next_word__1__prev = __Vfunc_aes128__DOT__next_round_key__0__w3;
    __Vfunc_aes128__DOT__next_word__1__rc = ((8U & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                              ? ((4U 
                                                  & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                  ? 0U
                                                  : 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0U
                                                    : 0x36U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x1bU
                                                    : 0x80U)))
                                              : ((4U 
                                                  & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                  ? 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x40U
                                                    : 0x20U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x10U
                                                    : 8U))
                                                  : 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 4U
                                                    : 2U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 1U
                                                    : 0U))));
    __Vfunc_aes128__DOT__next_word__1__t = ((([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a 
                        = (0x000000ffU & (__Vfunc_aes128__DOT__next_word__1__prev 
                                          >> 0x10U));
                    vlSelfRef.__Vfunc_aes128__DOT__sbox__2__Vfuncout 
                        = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                            ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x16U
                                                     : 0xbbU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x54U
                                                     : 0xb0U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0fU
                                                     : 0x2dU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x99U
                                                     : 0x41U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x68U
                                                     : 0x42U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe6U
                                                     : 0xbfU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0dU
                                                     : 0x89U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa1U
                                                     : 0x8cU))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdfU
                                                     : 0x28U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x55U
                                                     : 0xceU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe9U
                                                     : 0x87U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1eU
                                                     : 0x9bU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x94U
                                                     : 0x8eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd9U
                                                     : 0x69U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x11U
                                                     : 0x98U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf8U
                                                     : 0xe1U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9eU
                                                     : 0x1dU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc1U
                                                     : 0x86U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb9U
                                                     : 0x57U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x35U
                                                     : 0x61U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0eU
                                                     : 0xf6U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 3U
                                                     : 0x48U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x66U
                                                     : 0xb5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3eU
                                                     : 0x70U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x8aU
                                                     : 0x8bU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xbdU
                                                     : 0x4bU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1fU
                                                     : 0x74U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xddU
                                                     : 0xe8U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc6U
                                                     : 0xb4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa6U
                                                     : 0x1cU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2eU
                                                     : 0x25U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x78U
                                                     : 0xbaU))))))
                                : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 8U
                                                     : 0xaeU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7aU
                                                     : 0x65U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xeaU
                                                     : 0xf4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x56U
                                                     : 0x6cU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa9U
                                                     : 0x4eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd5U
                                                     : 0x8dU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6dU
                                                     : 0x37U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc8U
                                                     : 0xe7U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x79U
                                                     : 0xe4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x95U
                                                     : 0x91U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x62U
                                                     : 0xacU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd3U
                                                     : 0xc2U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5cU
                                                     : 0x24U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 6U
                                                     : 0x49U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0aU
                                                     : 0x3aU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x32U
                                                     : 0xe0U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdbU
                                                     : 0x0bU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5eU
                                                     : 0xdeU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x14U
                                                     : 0xb8U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xeeU
                                                     : 0x46U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x88U
                                                     : 0x90U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2aU
                                                     : 0x22U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdcU
                                                     : 0x4fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x81U
                                                     : 0x60U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x73U
                                                     : 0x19U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5dU
                                                     : 0x64U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3dU
                                                     : 0x7eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa7U
                                                     : 0xc4U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x17U
                                                     : 0x44U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x97U
                                                     : 0x5fU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xecU
                                                     : 0x13U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0cU
                                                     : 0xcdU)))))))
                            : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd2U
                                                     : 0xf3U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xffU
                                                     : 0x10U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x21U
                                                     : 0xdaU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb6U
                                                     : 0xbcU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf5U
                                                     : 0x38U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9dU
                                                     : 0x92U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x8fU
                                                     : 0x40U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa3U
                                                     : 0x51U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa8U
                                                     : 0x9fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3cU
                                                     : 0x50U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7fU
                                                     : 2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf9U
                                                     : 0x45U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x85U
                                                     : 0x33U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x4dU
                                                     : 0x43U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfbU
                                                     : 0xaaU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xefU
                                                     : 0xd0U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xcfU
                                                     : 0x58U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x4cU
                                                     : 0x4aU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x39U
                                                     : 0xbeU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xcbU
                                                     : 0x6aU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5bU
                                                     : 0xb1U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfcU
                                                     : 0x20U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xedU
                                                     : 0U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd1U
                                                     : 0x53U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x84U
                                                     : 0x2fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe3U
                                                     : 0x29U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb3U
                                                     : 0xd6U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3bU
                                                     : 0x52U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa0U
                                                     : 0x5aU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6eU
                                                     : 0x1bU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1aU
                                                     : 0x2cU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x83U
                                                     : 9U))))))
                                : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x75U
                                                     : 0xb2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x27U
                                                     : 0xebU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe2U
                                                     : 0x80U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x12U
                                                     : 7U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9aU
                                                     : 5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x96U
                                                     : 0x18U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc3U
                                                     : 0x23U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc7U
                                                     : 4U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x15U
                                                     : 0x31U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd8U
                                                     : 0x71U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf1U
                                                     : 0xe5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa5U
                                                     : 0x34U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xccU
                                                     : 0xf7U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3fU
                                                     : 0x36U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x26U
                                                     : 0x93U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfdU
                                                     : 0xb7U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc0U
                                                     : 0x72U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa4U
                                                     : 0x9cU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xafU
                                                     : 0xa2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd4U
                                                     : 0xadU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf0U
                                                     : 0x47U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x59U
                                                     : 0xfaU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7dU
                                                     : 0xc9U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x82U
                                                     : 0xcaU))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x76U
                                                     : 0xabU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd7U
                                                     : 0xfeU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2bU
                                                     : 0x67U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 1U
                                                     : 0x30U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc5U
                                                     : 0x6fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6bU
                                                     : 0xf2U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7bU
                                                     : 0x77U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7cU
                                                     : 0x63U))))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__Vfuncout)) 
                                             << 0x00000018U) 
                                            | ((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a 
                            = (0x000000ffU & (__Vfunc_aes128__DOT__next_word__1__prev 
                                              >> 8U));
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__3__Vfuncout 
                            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x16U
                                                      : 0xbbU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x54U
                                                      : 0xb0U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0fU
                                                      : 0x2dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x99U
                                                      : 0x41U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x68U
                                                      : 0x42U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe6U
                                                      : 0xbfU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0dU
                                                      : 0x89U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa1U
                                                      : 0x8cU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdfU
                                                      : 0x28U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x55U
                                                      : 0xceU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe9U
                                                      : 0x87U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1eU
                                                      : 0x9bU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x94U
                                                      : 0x8eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd9U
                                                      : 0x69U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x11U
                                                      : 0x98U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf8U
                                                      : 0xe1U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9eU
                                                      : 0x1dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc1U
                                                      : 0x86U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb9U
                                                      : 0x57U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x35U
                                                      : 0x61U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0eU
                                                      : 0xf6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 3U
                                                      : 0x48U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x66U
                                                      : 0xb5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3eU
                                                      : 0x70U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x8aU
                                                      : 0x8bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xbdU
                                                      : 0x4bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1fU
                                                      : 0x74U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xddU
                                                      : 0xe8U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc6U
                                                      : 0xb4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa6U
                                                      : 0x1cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2eU
                                                      : 0x25U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x78U
                                                      : 0xbaU))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 8U
                                                      : 0xaeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7aU
                                                      : 0x65U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xeaU
                                                      : 0xf4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x56U
                                                      : 0x6cU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa9U
                                                      : 0x4eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd5U
                                                      : 0x8dU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6dU
                                                      : 0x37U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc8U
                                                      : 0xe7U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x79U
                                                      : 0xe4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x95U
                                                      : 0x91U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x62U
                                                      : 0xacU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd3U
                                                      : 0xc2U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5cU
                                                      : 0x24U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 6U
                                                      : 0x49U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0aU
                                                      : 0x3aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x32U
                                                      : 0xe0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdbU
                                                      : 0x0bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5eU
                                                      : 0xdeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x14U
                                                      : 0xb8U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xeeU
                                                      : 0x46U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x88U
                                                      : 0x90U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2aU
                                                      : 0x22U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdcU
                                                      : 0x4fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x81U
                                                      : 0x60U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x73U
                                                      : 0x19U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5dU
                                                      : 0x64U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3dU
                                                      : 0x7eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa7U
                                                      : 0xc4U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x17U
                                                      : 0x44U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x97U
                                                      : 0x5fU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xecU
                                                      : 0x13U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0cU
                                                      : 0xcdU)))))))
                                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd2U
                                                      : 0xf3U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xffU
                                                      : 0x10U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x21U
                                                      : 0xdaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb6U
                                                      : 0xbcU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf5U
                                                      : 0x38U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9dU
                                                      : 0x92U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x8fU
                                                      : 0x40U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa3U
                                                      : 0x51U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa8U
                                                      : 0x9fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3cU
                                                      : 0x50U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7fU
                                                      : 2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf9U
                                                      : 0x45U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x85U
                                                      : 0x33U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x4dU
                                                      : 0x43U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfbU
                                                      : 0xaaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xefU
                                                      : 0xd0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xcfU
                                                      : 0x58U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x4cU
                                                      : 0x4aU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x39U
                                                      : 0xbeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xcbU
                                                      : 0x6aU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5bU
                                                      : 0xb1U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfcU
                                                      : 0x20U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xedU
                                                      : 0U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd1U
                                                      : 0x53U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x84U
                                                      : 0x2fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe3U
                                                      : 0x29U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb3U
                                                      : 0xd6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3bU
                                                      : 0x52U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa0U
                                                      : 0x5aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6eU
                                                      : 0x1bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1aU
                                                      : 0x2cU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x83U
                                                      : 9U))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x75U
                                                      : 0xb2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x27U
                                                      : 0xebU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe2U
                                                      : 0x80U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x12U
                                                      : 7U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9aU
                                                      : 5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x96U
                                                      : 0x18U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc3U
                                                      : 0x23U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc7U
                                                      : 4U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x15U
                                                      : 0x31U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd8U
                                                      : 0x71U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf1U
                                                      : 0xe5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa5U
                                                      : 0x34U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xccU
                                                      : 0xf7U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3fU
                                                      : 0x36U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x26U
                                                      : 0x93U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfdU
                                                      : 0xb7U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc0U
                                                      : 0x72U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa4U
                                                      : 0x9cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xafU
                                                      : 0xa2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd4U
                                                      : 0xadU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf0U
                                                      : 0x47U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x59U
                                                      : 0xfaU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7dU
                                                      : 0xc9U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x82U
                                                      : 0xcaU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x76U
                                                      : 0xabU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd7U
                                                      : 0xfeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2bU
                                                      : 0x67U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 1U
                                                      : 0x30U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc5U
                                                      : 0x6fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6bU
                                                      : 0xf2U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7bU
                                                      : 0x77U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7cU
                                                      : 0x63U))))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__Vfuncout)) 
                                                << 0x00000010U) 
                                               | ((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a 
                                = (0x000000ffU & __Vfunc_aes128__DOT__next_word__1__prev);
                            vlSelfRef.__Vfunc_aes128__DOT__sbox__4__Vfuncout 
                                = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                    ? ((0x00000040U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                        ? ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x16U
                                                       : 0xbbU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x54U
                                                       : 0xb0U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0fU
                                                       : 0x2dU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x99U
                                                       : 0x41U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x68U
                                                       : 0x42U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe6U
                                                       : 0xbfU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0dU
                                                       : 0x89U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa1U
                                                       : 0x8cU))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdfU
                                                       : 0x28U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x55U
                                                       : 0xceU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe9U
                                                       : 0x87U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1eU
                                                       : 0x9bU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x94U
                                                       : 0x8eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd9U
                                                       : 0x69U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x11U
                                                       : 0x98U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf8U
                                                       : 0xe1U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9eU
                                                       : 0x1dU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc1U
                                                       : 0x86U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb9U
                                                       : 0x57U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x35U
                                                       : 0x61U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0eU
                                                       : 0xf6U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 3U
                                                       : 0x48U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x66U
                                                       : 0xb5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3eU
                                                       : 0x70U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x8aU
                                                       : 0x8bU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xbdU
                                                       : 0x4bU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1fU
                                                       : 0x74U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xddU
                                                       : 0xe8U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc6U
                                                       : 0xb4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa6U
                                                       : 0x1cU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2eU
                                                       : 0x25U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x78U
                                                       : 0xbaU))))))
                                        : ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 8U
                                                       : 0xaeU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7aU
                                                       : 0x65U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xeaU
                                                       : 0xf4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x56U
                                                       : 0x6cU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa9U
                                                       : 0x4eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd5U
                                                       : 0x8dU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6dU
                                                       : 0x37U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc8U
                                                       : 0xe7U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x79U
                                                       : 0xe4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x95U
                                                       : 0x91U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x62U
                                                       : 0xacU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd3U
                                                       : 0xc2U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5cU
                                                       : 0x24U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 6U
                                                       : 0x49U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0aU
                                                       : 0x3aU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x32U
                                                       : 0xe0U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdbU
                                                       : 0x0bU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5eU
                                                       : 0xdeU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x14U
                                                       : 0xb8U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xeeU
                                                       : 0x46U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x88U
                                                       : 0x90U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2aU
                                                       : 0x22U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdcU
                                                       : 0x4fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x81U
                                                       : 0x60U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x73U
                                                       : 0x19U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5dU
                                                       : 0x64U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3dU
                                                       : 0x7eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa7U
                                                       : 0xc4U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x17U
                                                       : 0x44U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x97U
                                                       : 0x5fU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xecU
                                                       : 0x13U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0cU
                                                       : 0xcdU)))))))
                                    : ((0x00000040U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                        ? ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd2U
                                                       : 0xf3U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xffU
                                                       : 0x10U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x21U
                                                       : 0xdaU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb6U
                                                       : 0xbcU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf5U
                                                       : 0x38U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9dU
                                                       : 0x92U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x8fU
                                                       : 0x40U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa3U
                                                       : 0x51U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa8U
                                                       : 0x9fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3cU
                                                       : 0x50U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7fU
                                                       : 2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf9U
                                                       : 0x45U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x85U
                                                       : 0x33U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x4dU
                                                       : 0x43U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfbU
                                                       : 0xaaU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xefU
                                                       : 0xd0U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xcfU
                                                       : 0x58U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x4cU
                                                       : 0x4aU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x39U
                                                       : 0xbeU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xcbU
                                                       : 0x6aU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5bU
                                                       : 0xb1U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfcU
                                                       : 0x20U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xedU
                                                       : 0U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd1U
                                                       : 0x53U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x84U
                                                       : 0x2fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe3U
                                                       : 0x29U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb3U
                                                       : 0xd6U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3bU
                                                       : 0x52U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa0U
                                                       : 0x5aU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6eU
                                                       : 0x1bU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1aU
                                                       : 0x2cU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x83U
                                                       : 9U))))))
                                        : ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x75U
                                                       : 0xb2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x27U
                                                       : 0xebU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe2U
                                                       : 0x80U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x12U
                                                       : 7U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9aU
                                                       : 5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x96U
                                                       : 0x18U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc3U
                                                       : 0x23U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc7U
                                                       : 4U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x15U
                                                       : 0x31U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd8U
                                                       : 0x71U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf1U
                                                       : 0xe5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa5U
                                                       : 0x34U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xccU
                                                       : 0xf7U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3fU
                                                       : 0x36U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x26U
                                                       : 0x93U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfdU
                                                       : 0xb7U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc0U
                                                       : 0x72U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa4U
                                                       : 0x9cU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xafU
                                                       : 0xa2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd4U
                                                       : 0xadU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf0U
                                                       : 0x47U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x59U
                                                       : 0xfaU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7dU
                                                       : 0xc9U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x82U
                                                       : 0xcaU))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x76U
                                                       : 0xabU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd7U
                                                       : 0xfeU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2bU
                                                       : 0x67U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 1U
                                                       : 0x30U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc5U
                                                       : 0x6fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6bU
                                                       : 0xf2U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7bU
                                                       : 0x77U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7cU
                                                       : 0x63U))))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__Vfuncout)) 
                                                   << 8U) 
                                                  | ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a 
                            = (__Vfunc_aes128__DOT__next_word__1__prev 
                               >> 0x18U);
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__5__Vfuncout 
                            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x16U
                                                      : 0xbbU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x54U
                                                      : 0xb0U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0fU
                                                      : 0x2dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x99U
                                                      : 0x41U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x68U
                                                      : 0x42U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe6U
                                                      : 0xbfU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0dU
                                                      : 0x89U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa1U
                                                      : 0x8cU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdfU
                                                      : 0x28U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x55U
                                                      : 0xceU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe9U
                                                      : 0x87U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1eU
                                                      : 0x9bU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x94U
                                                      : 0x8eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd9U
                                                      : 0x69U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x11U
                                                      : 0x98U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf8U
                                                      : 0xe1U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9eU
                                                      : 0x1dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc1U
                                                      : 0x86U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb9U
                                                      : 0x57U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x35U
                                                      : 0x61U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0eU
                                                      : 0xf6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 3U
                                                      : 0x48U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x66U
                                                      : 0xb5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3eU
                                                      : 0x70U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x8aU
                                                      : 0x8bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xbdU
                                                      : 0x4bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1fU
                                                      : 0x74U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xddU
                                                      : 0xe8U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc6U
                                                      : 0xb4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa6U
                                                      : 0x1cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2eU
                                                      : 0x25U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x78U
                                                      : 0xbaU))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 8U
                                                      : 0xaeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7aU
                                                      : 0x65U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xeaU
                                                      : 0xf4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x56U
                                                      : 0x6cU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa9U
                                                      : 0x4eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd5U
                                                      : 0x8dU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6dU
                                                      : 0x37U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc8U
                                                      : 0xe7U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x79U
                                                      : 0xe4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x95U
                                                      : 0x91U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x62U
                                                      : 0xacU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd3U
                                                      : 0xc2U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5cU
                                                      : 0x24U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 6U
                                                      : 0x49U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0aU
                                                      : 0x3aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x32U
                                                      : 0xe0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdbU
                                                      : 0x0bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5eU
                                                      : 0xdeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x14U
                                                      : 0xb8U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xeeU
                                                      : 0x46U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x88U
                                                      : 0x90U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2aU
                                                      : 0x22U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdcU
                                                      : 0x4fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x81U
                                                      : 0x60U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x73U
                                                      : 0x19U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5dU
                                                      : 0x64U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3dU
                                                      : 0x7eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa7U
                                                      : 0xc4U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x17U
                                                      : 0x44U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x97U
                                                      : 0x5fU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xecU
                                                      : 0x13U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0cU
                                                      : 0xcdU)))))))
                                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd2U
                                                      : 0xf3U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xffU
                                                      : 0x10U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x21U
                                                      : 0xdaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb6U
                                                      : 0xbcU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf5U
                                                      : 0x38U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9dU
                                                      : 0x92U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x8fU
                                                      : 0x40U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa3U
                                                      : 0x51U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa8U
                                                      : 0x9fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3cU
                                                      : 0x50U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7fU
                                                      : 2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf9U
                                                      : 0x45U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x85U
                                                      : 0x33U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x4dU
                                                      : 0x43U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfbU
                                                      : 0xaaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xefU
                                                      : 0xd0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xcfU
                                                      : 0x58U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x4cU
                                                      : 0x4aU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x39U
                                                      : 0xbeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xcbU
                                                      : 0x6aU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5bU
                                                      : 0xb1U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfcU
                                                      : 0x20U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xedU
                                                      : 0U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd1U
                                                      : 0x53U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x84U
                                                      : 0x2fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe3U
                                                      : 0x29U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb3U
                                                      : 0xd6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3bU
                                                      : 0x52U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa0U
                                                      : 0x5aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6eU
                                                      : 0x1bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1aU
                                                      : 0x2cU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x83U
                                                      : 9U))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x75U
                                                      : 0xb2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x27U
                                                      : 0xebU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe2U
                                                      : 0x80U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x12U
                                                      : 7U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9aU
                                                      : 5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x96U
                                                      : 0x18U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc3U
                                                      : 0x23U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc7U
                                                      : 4U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x15U
                                                      : 0x31U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd8U
                                                      : 0x71U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf1U
                                                      : 0xe5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa5U
                                                      : 0x34U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xccU
                                                      : 0xf7U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3fU
                                                      : 0x36U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x26U
                                                      : 0x93U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfdU
                                                      : 0xb7U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc0U
                                                      : 0x72U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa4U
                                                      : 0x9cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xafU
                                                      : 0xa2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd4U
                                                      : 0xadU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf0U
                                                      : 0x47U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x59U
                                                      : 0xfaU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7dU
                                                      : 0xc9U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x82U
                                                      : 0xcaU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x76U
                                                      : 0xabU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd7U
                                                      : 0xfeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2bU
                                                      : 0x67U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 1U
                                                      : 0x30U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc5U
                                                      : 0x6fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6bU
                                                      : 0xf2U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7bU
                                                      : 0x77U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7cU
                                                      : 0x63U))))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__Vfuncout)))));
    __Vfunc_aes128__DOT__next_word__1__t = ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__next_word__1__t) 
                                            | (0xff000000U 
                                               & ((0xff000000U 
                                                   & __Vfunc_aes128__DOT__next_word__1__t) 
                                                  ^ 
                                                  ((IData)(__Vfunc_aes128__DOT__next_word__1__rc) 
                                                   << 0x00000018U))));
    __Vfunc_aes128__DOT__next_word__1__Vfuncout = (__Vfunc_aes128__DOT__next_word__1__word0 
                                                   ^ __Vfunc_aes128__DOT__next_word__1__t);
    __Vfunc_aes128__DOT__next_round_key__0__n0 = __Vfunc_aes128__DOT__next_word__1__Vfuncout;
    __Vfunc_aes128__DOT__next_round_key__0__n1 = (__Vfunc_aes128__DOT__next_round_key__0__w1 
                                                  ^ __Vfunc_aes128__DOT__next_round_key__0__n0);
    __Vfunc_aes128__DOT__next_round_key__0__n2 = (__Vfunc_aes128__DOT__next_round_key__0__w2 
                                                  ^ __Vfunc_aes128__DOT__next_round_key__0__n1);
    __Vfunc_aes128__DOT__next_round_key__0__n3 = (__Vfunc_aes128__DOT__next_round_key__0__w3 
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
    vlSelfRef.aes128__DOT__rk_next[0U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[0U];
    vlSelfRef.aes128__DOT__rk_next[1U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[1U];
    vlSelfRef.aes128__DOT__rk_next[2U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[2U];
    vlSelfRef.aes128__DOT__rk_next[3U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[3U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[0U] = vlSelfRef.aes128__DOT__state_reg[0U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[1U] = vlSelfRef.aes128__DOT__state_reg[1U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[2U] = vlSelfRef.aes128__DOT__state_reg[2U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[3U] = vlSelfRef.aes128__DOT__state_reg[3U];
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->name());
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__sub_bytes__6__y, __VscopeHash, 9264579218545655816ull);
    __Vfunc_aes128__DOT__sub_bytes__6__i = 0U;
    while (VL_GTS_III(32, 0x00000010U, __Vfunc_aes128__DOT__sub_bytes__6__i)) {
        vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a = 
            (0x000000ffU & (((0U == (0x0000001fU & 
                                     (((IData)(0x7fU) 
                                       - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                      - (IData)(7U))))
                              ? 0U : (__Vfunc_aes128__DOT__sub_bytes__6__x[
                                      (((IData)(7U) 
                                        + (0x0000007fU 
                                           & (((IData)(0x7fU) 
                                               - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                              - (IData)(7U)))) 
                                       >> 5U)] << ((IData)(0x00000020U) 
                                                   - 
                                                   (0x0000001fU 
                                                    & (((IData)(0x7fU) 
                                                        - 
                                                        VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                       - (IData)(7U)))))) 
                            | (__Vfunc_aes128__DOT__sub_bytes__6__x[
                               (3U & ((((IData)(0x7fU) 
                                        - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                       - (IData)(7U)) 
                                      >> 5U))] >> (0x0000001fU 
                                                   & (((IData)(0x7fU) 
                                                       - 
                                                       VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                      - (IData)(7U))))));
        vlSelfRef.__Vfunc_aes128__DOT__sbox__7__Vfuncout 
            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                    ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x16U
                                            : 0xbbU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x54U
                                            : 0xb0U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0fU
                                            : 0x2dU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x99U
                                            : 0x41U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x68U
                                            : 0x42U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe6U
                                            : 0xbfU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0dU
                                            : 0x89U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa1U
                                            : 0x8cU))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdfU
                                            : 0x28U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x55U
                                            : 0xceU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe9U
                                            : 0x87U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1eU
                                            : 0x9bU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x94U
                                            : 0x8eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd9U
                                            : 0x69U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x11U
                                            : 0x98U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf8U
                                            : 0xe1U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9eU
                                            : 0x1dU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc1U
                                            : 0x86U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb9U
                                            : 0x57U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x35U
                                            : 0x61U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0eU
                                            : 0xf6U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 3U : 0x48U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x66U
                                            : 0xb5U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3eU
                                            : 0x70U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x8aU
                                            : 0x8bU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xbdU
                                            : 0x4bU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1fU
                                            : 0x74U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xddU
                                            : 0xe8U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc6U
                                            : 0xb4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa6U
                                            : 0x1cU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2eU
                                            : 0x25U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x78U
                                            : 0xbaU))))))
                    : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 8U : 0xaeU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7aU
                                            : 0x65U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xeaU
                                            : 0xf4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x56U
                                            : 0x6cU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa9U
                                            : 0x4eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd5U
                                            : 0x8dU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6dU
                                            : 0x37U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc8U
                                            : 0xe7U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x79U
                                            : 0xe4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x95U
                                            : 0x91U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x62U
                                            : 0xacU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd3U
                                            : 0xc2U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5cU
                                            : 0x24U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 6U : 0x49U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0aU
                                            : 0x3aU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x32U
                                            : 0xe0U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdbU
                                            : 0x0bU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5eU
                                            : 0xdeU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x14U
                                            : 0xb8U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xeeU
                                            : 0x46U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x88U
                                            : 0x90U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2aU
                                            : 0x22U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdcU
                                            : 0x4fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x81U
                                            : 0x60U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x73U
                                            : 0x19U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5dU
                                            : 0x64U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3dU
                                            : 0x7eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa7U
                                            : 0xc4U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x17U
                                            : 0x44U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x97U
                                            : 0x5fU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xecU
                                            : 0x13U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0cU
                                            : 0xcdU)))))))
                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                    ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd2U
                                            : 0xf3U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xffU
                                            : 0x10U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x21U
                                            : 0xdaU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb6U
                                            : 0xbcU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf5U
                                            : 0x38U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9dU
                                            : 0x92U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x8fU
                                            : 0x40U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa3U
                                            : 0x51U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa8U
                                            : 0x9fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3cU
                                            : 0x50U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7fU
                                            : 2U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0xf9U : 0x45U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x85U
                                            : 0x33U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x4dU
                                            : 0x43U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfbU
                                            : 0xaaU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xefU
                                            : 0xd0U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xcfU
                                            : 0x58U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x4cU
                                            : 0x4aU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x39U
                                            : 0xbeU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xcbU
                                            : 0x6aU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5bU
                                            : 0xb1U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfcU
                                            : 0x20U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xedU
                                            : 0U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0xd1U : 0x53U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x84U
                                            : 0x2fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe3U
                                            : 0x29U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb3U
                                            : 0xd6U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3bU
                                            : 0x52U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa0U
                                            : 0x5aU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6eU
                                            : 0x1bU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1aU
                                            : 0x2cU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x83U
                                            : 9U))))))
                    : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x75U
                                            : 0xb2U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x27U
                                            : 0xebU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe2U
                                            : 0x80U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x12U
                                            : 7U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9aU
                                            : 5U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0x96U : 0x18U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc3U
                                            : 0x23U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc7U
                                            : 4U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x15U
                                            : 0x31U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd8U
                                            : 0x71U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf1U
                                            : 0xe5U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa5U
                                            : 0x34U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xccU
                                            : 0xf7U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3fU
                                            : 0x36U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x26U
                                            : 0x93U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfdU
                                            : 0xb7U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc0U
                                            : 0x72U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa4U
                                            : 0x9cU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xafU
                                            : 0xa2U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd4U
                                            : 0xadU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf0U
                                            : 0x47U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x59U
                                            : 0xfaU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7dU
                                            : 0xc9U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x82U
                                            : 0xcaU))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x76U
                                            : 0xabU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd7U
                                            : 0xfeU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2bU
                                            : 0x67U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 1U : 0x30U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc5U
                                            : 0x6fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6bU
                                            : 0xf2U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7bU
                                            : 0x77U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7cU
                                            : 0x63U))))))));
        VL_ASSIGNSEL_WI(128, 8, (0x0000007fU & (((IData)(0x7fU) 
                                                 - 
                                                 VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                - (IData)(7U))), vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y, vlSelfRef.__Vfunc_aes128__DOT__sbox__7__Vfuncout);
        __Vfunc_aes128__DOT__sub_bytes__6__i = ((IData)(1U) 
                                                + __Vfunc_aes128__DOT__sub_bytes__6__i);
    }
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[0U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[1U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[2U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[3U];
    vlSelfRef.aes128__DOT__sb_next[0U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[0U];
    vlSelfRef.aes128__DOT__sb_next[1U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[1U];
    vlSelfRef.aes128__DOT__sb_next[2U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[2U];
    vlSelfRef.aes128__DOT__sb_next[3U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[3U];
    __Vfunc_aes128__DOT__shift_rows__8__x[0U] = vlSelfRef.aes128__DOT__sb_next[0U];
    __Vfunc_aes128__DOT__shift_rows__8__x[1U] = vlSelfRef.aes128__DOT__sb_next[1U];
    __Vfunc_aes128__DOT__shift_rows__8__x[2U] = vlSelfRef.aes128__DOT__sb_next[2U];
    __Vfunc_aes128__DOT__shift_rows__8__x[3U] = vlSelfRef.aes128__DOT__sb_next[3U];
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__shift_rows__8__y, __VscopeHash, 17632048163419041600ull);
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U];
    vlSelfRef.aes128__DOT__sr_next[0U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[0U];
    vlSelfRef.aes128__DOT__sr_next[1U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[1U];
    vlSelfRef.aes128__DOT__sr_next[2U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[2U];
    vlSelfRef.aes128__DOT__sr_next[3U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[3U];
    __Vfunc_aes128__DOT__mix_columns__9__x[0U] = vlSelfRef.aes128__DOT__sr_next[0U];
    __Vfunc_aes128__DOT__mix_columns__9__x[1U] = vlSelfRef.aes128__DOT__sr_next[1U];
    __Vfunc_aes128__DOT__mix_columns__9__x[2U] = vlSelfRef.aes128__DOT__sr_next[2U];
    __Vfunc_aes128__DOT__mix_columns__9__x[3U] = vlSelfRef.aes128__DOT__sr_next[3U];
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__mix_columns__9__y, __VscopeHash, 4458951099714502511ull);
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[3U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[3U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[2U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[2U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[1U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[1U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[0U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[0U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[0U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[1U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[2U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[3U];
    vlSelfRef.aes128__DOT__mc_next[0U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[0U];
    vlSelfRef.aes128__DOT__mc_next[1U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[1U];
    vlSelfRef.aes128__DOT__mc_next[2U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[2U];
    vlSelfRef.aes128__DOT__mc_next[3U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[3U];
    if ((0x0aU == (IData)(vlSelfRef.aes128__DOT__round))) {
        vlSelfRef.aes128__DOT__state_next[0U] = (vlSelfRef.aes128__DOT__sr_next[0U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[0U]);
        vlSelfRef.aes128__DOT__state_next[1U] = (vlSelfRef.aes128__DOT__sr_next[1U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[1U]);
        vlSelfRef.aes128__DOT__state_next[2U] = (vlSelfRef.aes128__DOT__sr_next[2U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[2U]);
        vlSelfRef.aes128__DOT__state_next[3U] = (vlSelfRef.aes128__DOT__sr_next[3U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[3U]);
    } else {
        vlSelfRef.aes128__DOT__state_next[0U] = (vlSelfRef.aes128__DOT__mc_next[0U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[0U]);
        vlSelfRef.aes128__DOT__state_next[1U] = (vlSelfRef.aes128__DOT__mc_next[1U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[1U]);
        vlSelfRef.aes128__DOT__state_next[2U] = (vlSelfRef.aes128__DOT__mc_next[2U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[2U]);
        vlSelfRef.aes128__DOT__state_next[3U] = (vlSelfRef.aes128__DOT__mc_next[3U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[3U]);
    }
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
                                                    ((((~ (IData)(vlSelfRef.aes128__DOT__rst_n)) 
                                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__rst_n__0)) 
                                                      << 1U) 
                                                     | ((IData)(vlSelfRef.aes128__DOT__clk) 
                                                        & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__clk__0))))));
    vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__clk__0 
        = vlSelfRef.aes128__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__rst_n__0 
        = vlSelfRef.aes128__DOT__rst_n;
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
    CData/*3:0*/ __Vfunc_aes128__DOT__next_round_key__0__r;
    __Vfunc_aes128__DOT__next_round_key__0__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w0;
    __Vfunc_aes128__DOT__next_round_key__0__w0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w1;
    __Vfunc_aes128__DOT__next_round_key__0__w1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w2;
    __Vfunc_aes128__DOT__next_round_key__0__w2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__w3;
    __Vfunc_aes128__DOT__next_round_key__0__w3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n0;
    __Vfunc_aes128__DOT__next_round_key__0__n0 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n1;
    __Vfunc_aes128__DOT__next_round_key__0__n1 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n2;
    __Vfunc_aes128__DOT__next_round_key__0__n2 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_round_key__0__n3;
    __Vfunc_aes128__DOT__next_round_key__0__n3 = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__Vfuncout;
    __Vfunc_aes128__DOT__next_word__1__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__prev;
    __Vfunc_aes128__DOT__next_word__1__prev = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__word0;
    __Vfunc_aes128__DOT__next_word__1__word0 = 0;
    CData/*3:0*/ __Vfunc_aes128__DOT__next_word__1__r;
    __Vfunc_aes128__DOT__next_word__1__r = 0;
    IData/*31:0*/ __Vfunc_aes128__DOT__next_word__1__t;
    __Vfunc_aes128__DOT__next_word__1__t = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__next_word__1__rc;
    __Vfunc_aes128__DOT__next_word__1__rc = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__sub_bytes__6__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__sub_bytes__6__x);
    IData/*31:0*/ __Vfunc_aes128__DOT__sub_bytes__6__i;
    __Vfunc_aes128__DOT__sub_bytes__6__i = 0;
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__8__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__8__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__shift_rows__8__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__shift_rows__8__x);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__9__Vfuncout;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__9__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_aes128__DOT__mix_columns__9__x;
    VL_ZERO_W(128, __Vfunc_aes128__DOT__mix_columns__9__x);
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a0;
    __Vfunc_aes128__DOT__mix_columns__9__a0 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a1;
    __Vfunc_aes128__DOT__mix_columns__9__a1 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a2;
    __Vfunc_aes128__DOT__mix_columns__9__a2 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__a3;
    __Vfunc_aes128__DOT__mix_columns__9__a3 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b0;
    __Vfunc_aes128__DOT__mix_columns__9__b0 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b1;
    __Vfunc_aes128__DOT__mix_columns__9__b1 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b2;
    __Vfunc_aes128__DOT__mix_columns__9__b2 = 0;
    CData/*7:0*/ __Vfunc_aes128__DOT__mix_columns__9__b3;
    __Vfunc_aes128__DOT__mix_columns__9__b3 = 0;
    VlWide<4>/*127:0*/ __Vdly__aes128__DOT__state_reg;
    VL_ZERO_W(128, __Vdly__aes128__DOT__state_reg);
    CData/*3:0*/ __Vdly__aes128__DOT__round;
    __Vdly__aes128__DOT__round = 0;
    CData/*1:0*/ __Vdly__aes128__DOT__state;
    __Vdly__aes128__DOT__state = 0;
    // Body
    __Vdly__aes128__DOT__state = vlSelfRef.aes128__DOT__state;
    __Vdly__aes128__DOT__state_reg[0U] = vlSelfRef.aes128__DOT__state_reg[0U];
    __Vdly__aes128__DOT__state_reg[1U] = vlSelfRef.aes128__DOT__state_reg[1U];
    __Vdly__aes128__DOT__state_reg[2U] = vlSelfRef.aes128__DOT__state_reg[2U];
    __Vdly__aes128__DOT__state_reg[3U] = vlSelfRef.aes128__DOT__state_reg[3U];
    __Vdly__aes128__DOT__round = vlSelfRef.aes128__DOT__round;
    if (vlSelfRef.aes128__DOT__rst_n) {
        vlSelfRef.aes128__DOT__done = 0U;
        if ((0U == (IData)(vlSelfRef.aes128__DOT__state))) {
            vlSelfRef.aes128__DOT__busy = 0U;
            if (vlSelfRef.aes128__DOT__start) {
                __Vdly__aes128__DOT__state_reg[0U] 
                    = (vlSelfRef.aes128__DOT__plaintext[0U] 
                       ^ vlSelfRef.aes128__DOT__key[0U]);
                __Vdly__aes128__DOT__state_reg[1U] 
                    = (vlSelfRef.aes128__DOT__plaintext[1U] 
                       ^ vlSelfRef.aes128__DOT__key[1U]);
                __Vdly__aes128__DOT__state_reg[2U] 
                    = (vlSelfRef.aes128__DOT__plaintext[2U] 
                       ^ vlSelfRef.aes128__DOT__key[2U]);
                __Vdly__aes128__DOT__state_reg[3U] 
                    = (vlSelfRef.aes128__DOT__plaintext[3U] 
                       ^ vlSelfRef.aes128__DOT__key[3U]);
                vlSelfRef.aes128__DOT__round_key[0U] 
                    = vlSelfRef.aes128__DOT__key[0U];
                vlSelfRef.aes128__DOT__round_key[1U] 
                    = vlSelfRef.aes128__DOT__key[1U];
                vlSelfRef.aes128__DOT__round_key[2U] 
                    = vlSelfRef.aes128__DOT__key[2U];
                vlSelfRef.aes128__DOT__round_key[3U] 
                    = vlSelfRef.aes128__DOT__key[3U];
                __Vdly__aes128__DOT__round = 0U;
                vlSelfRef.aes128__DOT__busy = 1U;
                __Vdly__aes128__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelfRef.aes128__DOT__state))) {
            __Vdly__aes128__DOT__round = (0x0000000fU 
                                          & ((IData)(1U) 
                                             + (IData)(vlSelfRef.aes128__DOT__round)));
            vlSelfRef.aes128__DOT__round_key[0U] = 
                vlSelfRef.aes128__DOT__rk_next[0U];
            vlSelfRef.aes128__DOT__round_key[1U] = 
                vlSelfRef.aes128__DOT__rk_next[1U];
            vlSelfRef.aes128__DOT__round_key[2U] = 
                vlSelfRef.aes128__DOT__rk_next[2U];
            vlSelfRef.aes128__DOT__round_key[3U] = 
                vlSelfRef.aes128__DOT__rk_next[3U];
            __Vdly__aes128__DOT__state_reg[0U] = vlSelfRef.aes128__DOT__state_next[0U];
            __Vdly__aes128__DOT__state_reg[1U] = vlSelfRef.aes128__DOT__state_next[1U];
            __Vdly__aes128__DOT__state_reg[2U] = vlSelfRef.aes128__DOT__state_next[2U];
            __Vdly__aes128__DOT__state_reg[3U] = vlSelfRef.aes128__DOT__state_next[3U];
            if ((9U == (IData)(vlSelfRef.aes128__DOT__round))) {
                __Vdly__aes128__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelfRef.aes128__DOT__state))) {
            vlSelfRef.aes128__DOT__ciphertext[0U] = 
                vlSelfRef.aes128__DOT__state_reg[0U];
            vlSelfRef.aes128__DOT__ciphertext[1U] = 
                vlSelfRef.aes128__DOT__state_reg[1U];
            vlSelfRef.aes128__DOT__ciphertext[2U] = 
                vlSelfRef.aes128__DOT__state_reg[2U];
            vlSelfRef.aes128__DOT__ciphertext[3U] = 
                vlSelfRef.aes128__DOT__state_reg[3U];
            vlSelfRef.aes128__DOT__busy = 0U;
            vlSelfRef.aes128__DOT__done = 1U;
            __Vdly__aes128__DOT__state = 0U;
        } else {
            __Vdly__aes128__DOT__state = 0U;
        }
    } else {
        __Vdly__aes128__DOT__state_reg[0U] = 0U;
        __Vdly__aes128__DOT__state_reg[1U] = 0U;
        __Vdly__aes128__DOT__state_reg[2U] = 0U;
        __Vdly__aes128__DOT__state_reg[3U] = 0U;
        vlSelfRef.aes128__DOT__round_key[0U] = 0U;
        vlSelfRef.aes128__DOT__round_key[1U] = 0U;
        vlSelfRef.aes128__DOT__round_key[2U] = 0U;
        vlSelfRef.aes128__DOT__round_key[3U] = 0U;
        __Vdly__aes128__DOT__round = 0U;
        vlSelfRef.aes128__DOT__ciphertext[0U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[1U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[2U] = 0U;
        vlSelfRef.aes128__DOT__ciphertext[3U] = 0U;
        vlSelfRef.aes128__DOT__busy = 0U;
        vlSelfRef.aes128__DOT__done = 0U;
        __Vdly__aes128__DOT__state = 0U;
    }
    vlSelfRef.aes128__DOT__state = __Vdly__aes128__DOT__state;
    vlSelfRef.aes128__DOT__state_reg[0U] = __Vdly__aes128__DOT__state_reg[0U];
    vlSelfRef.aes128__DOT__state_reg[1U] = __Vdly__aes128__DOT__state_reg[1U];
    vlSelfRef.aes128__DOT__state_reg[2U] = __Vdly__aes128__DOT__state_reg[2U];
    vlSelfRef.aes128__DOT__state_reg[3U] = __Vdly__aes128__DOT__state_reg[3U];
    vlSelfRef.aes128__DOT__round = __Vdly__aes128__DOT__round;
    vlSelfRef.done = vlSelfRef.aes128__DOT__done;
    vlSelfRef.busy = vlSelfRef.aes128__DOT__busy;
    vlSelfRef.ciphertext[0U] = vlSelfRef.aes128__DOT__ciphertext[0U];
    vlSelfRef.ciphertext[1U] = vlSelfRef.aes128__DOT__ciphertext[1U];
    vlSelfRef.ciphertext[2U] = vlSelfRef.aes128__DOT__ciphertext[2U];
    vlSelfRef.ciphertext[3U] = vlSelfRef.aes128__DOT__ciphertext[3U];
    __Vfunc_aes128__DOT__next_round_key__0__r = (0x0000000fU 
                                                 & ((IData)(1U) 
                                                    + (IData)(vlSelfRef.aes128__DOT__round)));
    __Vfunc_aes128__DOT__next_round_key__0__k[0U] = 
        vlSelfRef.aes128__DOT__round_key[0U];
    __Vfunc_aes128__DOT__next_round_key__0__k[1U] = 
        vlSelfRef.aes128__DOT__round_key[1U];
    __Vfunc_aes128__DOT__next_round_key__0__k[2U] = 
        vlSelfRef.aes128__DOT__round_key[2U];
    __Vfunc_aes128__DOT__next_round_key__0__k[3U] = 
        vlSelfRef.aes128__DOT__round_key[3U];
    __Vfunc_aes128__DOT__next_round_key__0__w0 = __Vfunc_aes128__DOT__next_round_key__0__k[3U];
    __Vfunc_aes128__DOT__next_round_key__0__w1 = __Vfunc_aes128__DOT__next_round_key__0__k[2U];
    __Vfunc_aes128__DOT__next_round_key__0__w2 = __Vfunc_aes128__DOT__next_round_key__0__k[1U];
    __Vfunc_aes128__DOT__next_round_key__0__w3 = __Vfunc_aes128__DOT__next_round_key__0__k[0U];
    __Vfunc_aes128__DOT__next_word__1__r = __Vfunc_aes128__DOT__next_round_key__0__r;
    __Vfunc_aes128__DOT__next_word__1__word0 = __Vfunc_aes128__DOT__next_round_key__0__w0;
    __Vfunc_aes128__DOT__next_word__1__prev = __Vfunc_aes128__DOT__next_round_key__0__w3;
    __Vfunc_aes128__DOT__next_word__1__rc = ((8U & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                              ? ((4U 
                                                  & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                  ? 0U
                                                  : 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0U
                                                    : 0x36U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x1bU
                                                    : 0x80U)))
                                              : ((4U 
                                                  & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                  ? 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x40U
                                                    : 0x20U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 0x10U
                                                    : 8U))
                                                  : 
                                                 ((2U 
                                                   & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                   ? 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 4U
                                                    : 2U)
                                                   : 
                                                  ((1U 
                                                    & (IData)(__Vfunc_aes128__DOT__next_word__1__r))
                                                    ? 1U
                                                    : 0U))));
    __Vfunc_aes128__DOT__next_word__1__t = ((([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a 
                        = (0x000000ffU & (__Vfunc_aes128__DOT__next_word__1__prev 
                                          >> 0x10U));
                    vlSelfRef.__Vfunc_aes128__DOT__sbox__2__Vfuncout 
                        = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                            ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x16U
                                                     : 0xbbU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x54U
                                                     : 0xb0U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0fU
                                                     : 0x2dU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x99U
                                                     : 0x41U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x68U
                                                     : 0x42U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe6U
                                                     : 0xbfU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0dU
                                                     : 0x89U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa1U
                                                     : 0x8cU))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdfU
                                                     : 0x28U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x55U
                                                     : 0xceU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe9U
                                                     : 0x87U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1eU
                                                     : 0x9bU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x94U
                                                     : 0x8eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd9U
                                                     : 0x69U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x11U
                                                     : 0x98U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf8U
                                                     : 0xe1U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9eU
                                                     : 0x1dU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc1U
                                                     : 0x86U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb9U
                                                     : 0x57U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x35U
                                                     : 0x61U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0eU
                                                     : 0xf6U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 3U
                                                     : 0x48U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x66U
                                                     : 0xb5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3eU
                                                     : 0x70U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x8aU
                                                     : 0x8bU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xbdU
                                                     : 0x4bU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1fU
                                                     : 0x74U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xddU
                                                     : 0xe8U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc6U
                                                     : 0xb4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa6U
                                                     : 0x1cU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2eU
                                                     : 0x25U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x78U
                                                     : 0xbaU))))))
                                : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 8U
                                                     : 0xaeU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7aU
                                                     : 0x65U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xeaU
                                                     : 0xf4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x56U
                                                     : 0x6cU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa9U
                                                     : 0x4eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd5U
                                                     : 0x8dU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6dU
                                                     : 0x37U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc8U
                                                     : 0xe7U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x79U
                                                     : 0xe4U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x95U
                                                     : 0x91U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x62U
                                                     : 0xacU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd3U
                                                     : 0xc2U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5cU
                                                     : 0x24U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 6U
                                                     : 0x49U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0aU
                                                     : 0x3aU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x32U
                                                     : 0xe0U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdbU
                                                     : 0x0bU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5eU
                                                     : 0xdeU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x14U
                                                     : 0xb8U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xeeU
                                                     : 0x46U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x88U
                                                     : 0x90U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2aU
                                                     : 0x22U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xdcU
                                                     : 0x4fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x81U
                                                     : 0x60U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x73U
                                                     : 0x19U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5dU
                                                     : 0x64U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3dU
                                                     : 0x7eU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa7U
                                                     : 0xc4U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x17U
                                                     : 0x44U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x97U
                                                     : 0x5fU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xecU
                                                     : 0x13U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x0cU
                                                     : 0xcdU)))))))
                            : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd2U
                                                     : 0xf3U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xffU
                                                     : 0x10U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x21U
                                                     : 0xdaU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb6U
                                                     : 0xbcU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf5U
                                                     : 0x38U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9dU
                                                     : 0x92U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x8fU
                                                     : 0x40U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa3U
                                                     : 0x51U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa8U
                                                     : 0x9fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3cU
                                                     : 0x50U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7fU
                                                     : 2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf9U
                                                     : 0x45U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x85U
                                                     : 0x33U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x4dU
                                                     : 0x43U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfbU
                                                     : 0xaaU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xefU
                                                     : 0xd0U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xcfU
                                                     : 0x58U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x4cU
                                                     : 0x4aU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x39U
                                                     : 0xbeU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xcbU
                                                     : 0x6aU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x5bU
                                                     : 0xb1U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfcU
                                                     : 0x20U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xedU
                                                     : 0U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd1U
                                                     : 0x53U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x84U
                                                     : 0x2fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe3U
                                                     : 0x29U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xb3U
                                                     : 0xd6U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3bU
                                                     : 0x52U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa0U
                                                     : 0x5aU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6eU
                                                     : 0x1bU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x1aU
                                                     : 0x2cU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x83U
                                                     : 9U))))))
                                : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                    ? ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x75U
                                                     : 0xb2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x27U
                                                     : 0xebU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xe2U
                                                     : 0x80U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x12U
                                                     : 7U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x9aU
                                                     : 5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x96U
                                                     : 0x18U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc3U
                                                     : 0x23U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc7U
                                                     : 4U))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x15U
                                                     : 0x31U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd8U
                                                     : 0x71U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf1U
                                                     : 0xe5U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa5U
                                                     : 0x34U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xccU
                                                     : 0xf7U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x3fU
                                                     : 0x36U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x26U
                                                     : 0x93U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xfdU
                                                     : 0xb7U)))))
                                    : ((0x00000010U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                        ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc0U
                                                     : 0x72U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xa4U
                                                     : 0x9cU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xafU
                                                     : 0xa2U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd4U
                                                     : 0xadU)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xf0U
                                                     : 0x47U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x59U
                                                     : 0xfaU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7dU
                                                     : 0xc9U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x82U
                                                     : 0xcaU))))
                                        : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                            ? ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x76U
                                                     : 0xabU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xd7U
                                                     : 0xfeU))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x2bU
                                                     : 0x67U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 1U
                                                     : 0x30U)))
                                            : ((4U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                ? (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0xc5U
                                                     : 0x6fU)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x6bU
                                                     : 0xf2U))
                                                : (
                                                   (2U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                    ? 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7bU
                                                     : 0x77U)
                                                    : 
                                                   ((1U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__a))
                                                     ? 0x7cU
                                                     : 0x63U))))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__2__Vfuncout)) 
                                             << 0x00000018U) 
                                            | ((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a 
                            = (0x000000ffU & (__Vfunc_aes128__DOT__next_word__1__prev 
                                              >> 8U));
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__3__Vfuncout 
                            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x16U
                                                      : 0xbbU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x54U
                                                      : 0xb0U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0fU
                                                      : 0x2dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x99U
                                                      : 0x41U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x68U
                                                      : 0x42U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe6U
                                                      : 0xbfU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0dU
                                                      : 0x89U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa1U
                                                      : 0x8cU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdfU
                                                      : 0x28U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x55U
                                                      : 0xceU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe9U
                                                      : 0x87U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1eU
                                                      : 0x9bU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x94U
                                                      : 0x8eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd9U
                                                      : 0x69U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x11U
                                                      : 0x98U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf8U
                                                      : 0xe1U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9eU
                                                      : 0x1dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc1U
                                                      : 0x86U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb9U
                                                      : 0x57U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x35U
                                                      : 0x61U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0eU
                                                      : 0xf6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 3U
                                                      : 0x48U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x66U
                                                      : 0xb5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3eU
                                                      : 0x70U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x8aU
                                                      : 0x8bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xbdU
                                                      : 0x4bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1fU
                                                      : 0x74U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xddU
                                                      : 0xe8U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc6U
                                                      : 0xb4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa6U
                                                      : 0x1cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2eU
                                                      : 0x25U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x78U
                                                      : 0xbaU))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 8U
                                                      : 0xaeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7aU
                                                      : 0x65U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xeaU
                                                      : 0xf4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x56U
                                                      : 0x6cU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa9U
                                                      : 0x4eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd5U
                                                      : 0x8dU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6dU
                                                      : 0x37U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc8U
                                                      : 0xe7U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x79U
                                                      : 0xe4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x95U
                                                      : 0x91U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x62U
                                                      : 0xacU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd3U
                                                      : 0xc2U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5cU
                                                      : 0x24U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 6U
                                                      : 0x49U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0aU
                                                      : 0x3aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x32U
                                                      : 0xe0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdbU
                                                      : 0x0bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5eU
                                                      : 0xdeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x14U
                                                      : 0xb8U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xeeU
                                                      : 0x46U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x88U
                                                      : 0x90U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2aU
                                                      : 0x22U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xdcU
                                                      : 0x4fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x81U
                                                      : 0x60U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x73U
                                                      : 0x19U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5dU
                                                      : 0x64U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3dU
                                                      : 0x7eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa7U
                                                      : 0xc4U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x17U
                                                      : 0x44U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x97U
                                                      : 0x5fU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xecU
                                                      : 0x13U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x0cU
                                                      : 0xcdU)))))))
                                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd2U
                                                      : 0xf3U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xffU
                                                      : 0x10U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x21U
                                                      : 0xdaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb6U
                                                      : 0xbcU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf5U
                                                      : 0x38U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9dU
                                                      : 0x92U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x8fU
                                                      : 0x40U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa3U
                                                      : 0x51U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa8U
                                                      : 0x9fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3cU
                                                      : 0x50U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7fU
                                                      : 2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf9U
                                                      : 0x45U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x85U
                                                      : 0x33U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x4dU
                                                      : 0x43U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfbU
                                                      : 0xaaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xefU
                                                      : 0xd0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xcfU
                                                      : 0x58U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x4cU
                                                      : 0x4aU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x39U
                                                      : 0xbeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xcbU
                                                      : 0x6aU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x5bU
                                                      : 0xb1U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfcU
                                                      : 0x20U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xedU
                                                      : 0U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd1U
                                                      : 0x53U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x84U
                                                      : 0x2fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe3U
                                                      : 0x29U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xb3U
                                                      : 0xd6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3bU
                                                      : 0x52U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa0U
                                                      : 0x5aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6eU
                                                      : 0x1bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x1aU
                                                      : 0x2cU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x83U
                                                      : 9U))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x75U
                                                      : 0xb2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x27U
                                                      : 0xebU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xe2U
                                                      : 0x80U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x12U
                                                      : 7U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x9aU
                                                      : 5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x96U
                                                      : 0x18U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc3U
                                                      : 0x23U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc7U
                                                      : 4U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x15U
                                                      : 0x31U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd8U
                                                      : 0x71U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf1U
                                                      : 0xe5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa5U
                                                      : 0x34U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xccU
                                                      : 0xf7U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x3fU
                                                      : 0x36U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x26U
                                                      : 0x93U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xfdU
                                                      : 0xb7U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc0U
                                                      : 0x72U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xa4U
                                                      : 0x9cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xafU
                                                      : 0xa2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd4U
                                                      : 0xadU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xf0U
                                                      : 0x47U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x59U
                                                      : 0xfaU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7dU
                                                      : 0xc9U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x82U
                                                      : 0xcaU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x76U
                                                      : 0xabU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xd7U
                                                      : 0xfeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x2bU
                                                      : 0x67U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 1U
                                                      : 0x30U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0xc5U
                                                      : 0x6fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x6bU
                                                      : 0xf2U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7bU
                                                      : 0x77U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__a))
                                                      ? 0x7cU
                                                      : 0x63U))))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__3__Vfuncout)) 
                                                << 0x00000010U) 
                                               | ((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a 
                                = (0x000000ffU & __Vfunc_aes128__DOT__next_word__1__prev);
                            vlSelfRef.__Vfunc_aes128__DOT__sbox__4__Vfuncout 
                                = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                    ? ((0x00000040U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                        ? ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x16U
                                                       : 0xbbU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x54U
                                                       : 0xb0U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0fU
                                                       : 0x2dU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x99U
                                                       : 0x41U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x68U
                                                       : 0x42U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe6U
                                                       : 0xbfU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0dU
                                                       : 0x89U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa1U
                                                       : 0x8cU))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdfU
                                                       : 0x28U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x55U
                                                       : 0xceU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe9U
                                                       : 0x87U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1eU
                                                       : 0x9bU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x94U
                                                       : 0x8eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd9U
                                                       : 0x69U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x11U
                                                       : 0x98U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf8U
                                                       : 0xe1U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9eU
                                                       : 0x1dU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc1U
                                                       : 0x86U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb9U
                                                       : 0x57U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x35U
                                                       : 0x61U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0eU
                                                       : 0xf6U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 3U
                                                       : 0x48U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x66U
                                                       : 0xb5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3eU
                                                       : 0x70U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x8aU
                                                       : 0x8bU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xbdU
                                                       : 0x4bU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1fU
                                                       : 0x74U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xddU
                                                       : 0xe8U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc6U
                                                       : 0xb4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa6U
                                                       : 0x1cU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2eU
                                                       : 0x25U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x78U
                                                       : 0xbaU))))))
                                        : ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 8U
                                                       : 0xaeU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7aU
                                                       : 0x65U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xeaU
                                                       : 0xf4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x56U
                                                       : 0x6cU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa9U
                                                       : 0x4eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd5U
                                                       : 0x8dU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6dU
                                                       : 0x37U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc8U
                                                       : 0xe7U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x79U
                                                       : 0xe4U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x95U
                                                       : 0x91U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x62U
                                                       : 0xacU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd3U
                                                       : 0xc2U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5cU
                                                       : 0x24U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 6U
                                                       : 0x49U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0aU
                                                       : 0x3aU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x32U
                                                       : 0xe0U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdbU
                                                       : 0x0bU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5eU
                                                       : 0xdeU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x14U
                                                       : 0xb8U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xeeU
                                                       : 0x46U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x88U
                                                       : 0x90U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2aU
                                                       : 0x22U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xdcU
                                                       : 0x4fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x81U
                                                       : 0x60U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x73U
                                                       : 0x19U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5dU
                                                       : 0x64U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3dU
                                                       : 0x7eU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa7U
                                                       : 0xc4U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x17U
                                                       : 0x44U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x97U
                                                       : 0x5fU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xecU
                                                       : 0x13U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x0cU
                                                       : 0xcdU)))))))
                                    : ((0x00000040U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                        ? ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd2U
                                                       : 0xf3U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xffU
                                                       : 0x10U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x21U
                                                       : 0xdaU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb6U
                                                       : 0xbcU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf5U
                                                       : 0x38U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9dU
                                                       : 0x92U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x8fU
                                                       : 0x40U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa3U
                                                       : 0x51U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa8U
                                                       : 0x9fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3cU
                                                       : 0x50U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7fU
                                                       : 2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf9U
                                                       : 0x45U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x85U
                                                       : 0x33U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x4dU
                                                       : 0x43U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfbU
                                                       : 0xaaU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xefU
                                                       : 0xd0U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xcfU
                                                       : 0x58U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x4cU
                                                       : 0x4aU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x39U
                                                       : 0xbeU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xcbU
                                                       : 0x6aU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x5bU
                                                       : 0xb1U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfcU
                                                       : 0x20U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xedU
                                                       : 0U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd1U
                                                       : 0x53U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x84U
                                                       : 0x2fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe3U
                                                       : 0x29U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xb3U
                                                       : 0xd6U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3bU
                                                       : 0x52U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa0U
                                                       : 0x5aU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6eU
                                                       : 0x1bU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x1aU
                                                       : 0x2cU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x83U
                                                       : 9U))))))
                                        : ((0x00000020U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                            ? ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x75U
                                                       : 0xb2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x27U
                                                       : 0xebU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xe2U
                                                       : 0x80U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x12U
                                                       : 7U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x9aU
                                                       : 5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x96U
                                                       : 0x18U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc3U
                                                       : 0x23U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc7U
                                                       : 4U))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x15U
                                                       : 0x31U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd8U
                                                       : 0x71U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf1U
                                                       : 0xe5U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa5U
                                                       : 0x34U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xccU
                                                       : 0xf7U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x3fU
                                                       : 0x36U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x26U
                                                       : 0x93U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xfdU
                                                       : 0xb7U)))))
                                            : ((0x00000010U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                ? (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc0U
                                                       : 0x72U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xa4U
                                                       : 0x9cU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xafU
                                                       : 0xa2U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd4U
                                                       : 0xadU)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xf0U
                                                       : 0x47U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x59U
                                                       : 0xfaU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7dU
                                                       : 0xc9U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x82U
                                                       : 0xcaU))))
                                                : (
                                                   (8U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                    ? 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x76U
                                                       : 0xabU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xd7U
                                                       : 0xfeU))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x2bU
                                                       : 0x67U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 1U
                                                       : 0x30U)))
                                                    : 
                                                   ((4U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                     ? 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0xc5U
                                                       : 0x6fU)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x6bU
                                                       : 0xf2U))
                                                     : 
                                                    ((2U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                      ? 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7bU
                                                       : 0x77U)
                                                      : 
                                                     ((1U 
                                                       & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__a))
                                                       ? 0x7cU
                                                       : 0x63U))))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__4__Vfuncout)) 
                                                   << 8U) 
                                                  | ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a 
                            = (__Vfunc_aes128__DOT__next_word__1__prev 
                               >> 0x18U);
                        vlSelfRef.__Vfunc_aes128__DOT__sbox__5__Vfuncout 
                            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x16U
                                                      : 0xbbU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x54U
                                                      : 0xb0U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0fU
                                                      : 0x2dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x99U
                                                      : 0x41U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x68U
                                                      : 0x42U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe6U
                                                      : 0xbfU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0dU
                                                      : 0x89U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa1U
                                                      : 0x8cU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdfU
                                                      : 0x28U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x55U
                                                      : 0xceU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe9U
                                                      : 0x87U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1eU
                                                      : 0x9bU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x94U
                                                      : 0x8eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd9U
                                                      : 0x69U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x11U
                                                      : 0x98U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf8U
                                                      : 0xe1U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9eU
                                                      : 0x1dU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc1U
                                                      : 0x86U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb9U
                                                      : 0x57U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x35U
                                                      : 0x61U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0eU
                                                      : 0xf6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 3U
                                                      : 0x48U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x66U
                                                      : 0xb5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3eU
                                                      : 0x70U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x8aU
                                                      : 0x8bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xbdU
                                                      : 0x4bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1fU
                                                      : 0x74U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xddU
                                                      : 0xe8U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc6U
                                                      : 0xb4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa6U
                                                      : 0x1cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2eU
                                                      : 0x25U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x78U
                                                      : 0xbaU))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 8U
                                                      : 0xaeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7aU
                                                      : 0x65U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xeaU
                                                      : 0xf4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x56U
                                                      : 0x6cU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa9U
                                                      : 0x4eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd5U
                                                      : 0x8dU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6dU
                                                      : 0x37U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc8U
                                                      : 0xe7U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x79U
                                                      : 0xe4U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x95U
                                                      : 0x91U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x62U
                                                      : 0xacU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd3U
                                                      : 0xc2U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5cU
                                                      : 0x24U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 6U
                                                      : 0x49U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0aU
                                                      : 0x3aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x32U
                                                      : 0xe0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdbU
                                                      : 0x0bU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5eU
                                                      : 0xdeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x14U
                                                      : 0xb8U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xeeU
                                                      : 0x46U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x88U
                                                      : 0x90U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2aU
                                                      : 0x22U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xdcU
                                                      : 0x4fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x81U
                                                      : 0x60U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x73U
                                                      : 0x19U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5dU
                                                      : 0x64U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3dU
                                                      : 0x7eU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa7U
                                                      : 0xc4U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x17U
                                                      : 0x44U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x97U
                                                      : 0x5fU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xecU
                                                      : 0x13U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x0cU
                                                      : 0xcdU)))))))
                                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                    ? ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd2U
                                                      : 0xf3U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xffU
                                                      : 0x10U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x21U
                                                      : 0xdaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb6U
                                                      : 0xbcU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf5U
                                                      : 0x38U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9dU
                                                      : 0x92U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x8fU
                                                      : 0x40U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa3U
                                                      : 0x51U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa8U
                                                      : 0x9fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3cU
                                                      : 0x50U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7fU
                                                      : 2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf9U
                                                      : 0x45U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x85U
                                                      : 0x33U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x4dU
                                                      : 0x43U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfbU
                                                      : 0xaaU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xefU
                                                      : 0xd0U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xcfU
                                                      : 0x58U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x4cU
                                                      : 0x4aU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x39U
                                                      : 0xbeU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xcbU
                                                      : 0x6aU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x5bU
                                                      : 0xb1U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfcU
                                                      : 0x20U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xedU
                                                      : 0U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd1U
                                                      : 0x53U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x84U
                                                      : 0x2fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe3U
                                                      : 0x29U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xb3U
                                                      : 0xd6U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3bU
                                                      : 0x52U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa0U
                                                      : 0x5aU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6eU
                                                      : 0x1bU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x1aU
                                                      : 0x2cU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x83U
                                                      : 9U))))))
                                    : ((0x00000020U 
                                        & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                        ? ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x75U
                                                      : 0xb2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x27U
                                                      : 0xebU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xe2U
                                                      : 0x80U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x12U
                                                      : 7U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x9aU
                                                      : 5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x96U
                                                      : 0x18U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc3U
                                                      : 0x23U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc7U
                                                      : 4U))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x15U
                                                      : 0x31U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd8U
                                                      : 0x71U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf1U
                                                      : 0xe5U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa5U
                                                      : 0x34U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xccU
                                                      : 0xf7U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x3fU
                                                      : 0x36U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x26U
                                                      : 0x93U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xfdU
                                                      : 0xb7U)))))
                                        : ((0x00000010U 
                                            & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                            ? ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc0U
                                                      : 0x72U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xa4U
                                                      : 0x9cU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xafU
                                                      : 0xa2U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd4U
                                                      : 0xadU)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xf0U
                                                      : 0x47U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x59U
                                                      : 0xfaU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7dU
                                                      : 0xc9U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x82U
                                                      : 0xcaU))))
                                            : ((8U 
                                                & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                ? (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x76U
                                                      : 0xabU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xd7U
                                                      : 0xfeU))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x2bU
                                                      : 0x67U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 1U
                                                      : 0x30U)))
                                                : (
                                                   (4U 
                                                    & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                    ? 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0xc5U
                                                      : 0x6fU)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x6bU
                                                      : 0xf2U))
                                                    : 
                                                   ((2U 
                                                     & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                     ? 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7bU
                                                      : 0x77U)
                                                     : 
                                                    ((1U 
                                                      & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__a))
                                                      ? 0x7cU
                                                      : 0x63U))))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__5__Vfuncout)))));
    __Vfunc_aes128__DOT__next_word__1__t = ((0x00ffffffU 
                                             & __Vfunc_aes128__DOT__next_word__1__t) 
                                            | (0xff000000U 
                                               & ((0xff000000U 
                                                   & __Vfunc_aes128__DOT__next_word__1__t) 
                                                  ^ 
                                                  ((IData)(__Vfunc_aes128__DOT__next_word__1__rc) 
                                                   << 0x00000018U))));
    __Vfunc_aes128__DOT__next_word__1__Vfuncout = (__Vfunc_aes128__DOT__next_word__1__word0 
                                                   ^ __Vfunc_aes128__DOT__next_word__1__t);
    __Vfunc_aes128__DOT__next_round_key__0__n0 = __Vfunc_aes128__DOT__next_word__1__Vfuncout;
    __Vfunc_aes128__DOT__next_round_key__0__n1 = (__Vfunc_aes128__DOT__next_round_key__0__w1 
                                                  ^ __Vfunc_aes128__DOT__next_round_key__0__n0);
    __Vfunc_aes128__DOT__next_round_key__0__n2 = (__Vfunc_aes128__DOT__next_round_key__0__w2 
                                                  ^ __Vfunc_aes128__DOT__next_round_key__0__n1);
    __Vfunc_aes128__DOT__next_round_key__0__n3 = (__Vfunc_aes128__DOT__next_round_key__0__w3 
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
    vlSelfRef.aes128__DOT__rk_next[0U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[0U];
    vlSelfRef.aes128__DOT__rk_next[1U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[1U];
    vlSelfRef.aes128__DOT__rk_next[2U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[2U];
    vlSelfRef.aes128__DOT__rk_next[3U] = __Vfunc_aes128__DOT__next_round_key__0__Vfuncout[3U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[0U] = vlSelfRef.aes128__DOT__state_reg[0U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[1U] = vlSelfRef.aes128__DOT__state_reg[1U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[2U] = vlSelfRef.aes128__DOT__state_reg[2U];
    __Vfunc_aes128__DOT__sub_bytes__6__x[3U] = vlSelfRef.aes128__DOT__state_reg[3U];
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->name());
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__sub_bytes__6__y, __VscopeHash, 9264579218545655816ull);
    __Vfunc_aes128__DOT__sub_bytes__6__i = 0U;
    while (VL_GTS_III(32, 0x00000010U, __Vfunc_aes128__DOT__sub_bytes__6__i)) {
        vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a = 
            (0x000000ffU & (((0U == (0x0000001fU & 
                                     (((IData)(0x7fU) 
                                       - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                      - (IData)(7U))))
                              ? 0U : (__Vfunc_aes128__DOT__sub_bytes__6__x[
                                      (((IData)(7U) 
                                        + (0x0000007fU 
                                           & (((IData)(0x7fU) 
                                               - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                              - (IData)(7U)))) 
                                       >> 5U)] << ((IData)(0x00000020U) 
                                                   - 
                                                   (0x0000001fU 
                                                    & (((IData)(0x7fU) 
                                                        - 
                                                        VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                       - (IData)(7U)))))) 
                            | (__Vfunc_aes128__DOT__sub_bytes__6__x[
                               (3U & ((((IData)(0x7fU) 
                                        - VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                       - (IData)(7U)) 
                                      >> 5U))] >> (0x0000001fU 
                                                   & (((IData)(0x7fU) 
                                                       - 
                                                       VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                      - (IData)(7U))))));
        vlSelfRef.__Vfunc_aes128__DOT__sbox__7__Vfuncout 
            = ((0x00000080U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                ? ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                    ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x16U
                                            : 0xbbU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x54U
                                            : 0xb0U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0fU
                                            : 0x2dU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x99U
                                            : 0x41U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x68U
                                            : 0x42U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe6U
                                            : 0xbfU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0dU
                                            : 0x89U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa1U
                                            : 0x8cU))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdfU
                                            : 0x28U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x55U
                                            : 0xceU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe9U
                                            : 0x87U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1eU
                                            : 0x9bU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x94U
                                            : 0x8eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd9U
                                            : 0x69U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x11U
                                            : 0x98U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf8U
                                            : 0xe1U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9eU
                                            : 0x1dU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc1U
                                            : 0x86U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb9U
                                            : 0x57U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x35U
                                            : 0x61U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0eU
                                            : 0xf6U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 3U : 0x48U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x66U
                                            : 0xb5U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3eU
                                            : 0x70U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x8aU
                                            : 0x8bU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xbdU
                                            : 0x4bU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1fU
                                            : 0x74U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xddU
                                            : 0xe8U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc6U
                                            : 0xb4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa6U
                                            : 0x1cU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2eU
                                            : 0x25U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x78U
                                            : 0xbaU))))))
                    : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 8U : 0xaeU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7aU
                                            : 0x65U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xeaU
                                            : 0xf4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x56U
                                            : 0x6cU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa9U
                                            : 0x4eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd5U
                                            : 0x8dU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6dU
                                            : 0x37U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc8U
                                            : 0xe7U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x79U
                                            : 0xe4U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x95U
                                            : 0x91U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x62U
                                            : 0xacU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd3U
                                            : 0xc2U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5cU
                                            : 0x24U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 6U : 0x49U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0aU
                                            : 0x3aU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x32U
                                            : 0xe0U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdbU
                                            : 0x0bU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5eU
                                            : 0xdeU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x14U
                                            : 0xb8U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xeeU
                                            : 0x46U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x88U
                                            : 0x90U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2aU
                                            : 0x22U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xdcU
                                            : 0x4fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x81U
                                            : 0x60U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x73U
                                            : 0x19U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5dU
                                            : 0x64U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3dU
                                            : 0x7eU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa7U
                                            : 0xc4U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x17U
                                            : 0x44U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x97U
                                            : 0x5fU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xecU
                                            : 0x13U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x0cU
                                            : 0xcdU)))))))
                : ((0x00000040U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                    ? ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd2U
                                            : 0xf3U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xffU
                                            : 0x10U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x21U
                                            : 0xdaU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb6U
                                            : 0xbcU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf5U
                                            : 0x38U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9dU
                                            : 0x92U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x8fU
                                            : 0x40U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa3U
                                            : 0x51U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa8U
                                            : 0x9fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3cU
                                            : 0x50U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7fU
                                            : 2U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0xf9U : 0x45U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x85U
                                            : 0x33U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x4dU
                                            : 0x43U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfbU
                                            : 0xaaU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xefU
                                            : 0xd0U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xcfU
                                            : 0x58U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x4cU
                                            : 0x4aU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x39U
                                            : 0xbeU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xcbU
                                            : 0x6aU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x5bU
                                            : 0xb1U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfcU
                                            : 0x20U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xedU
                                            : 0U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0xd1U : 0x53U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x84U
                                            : 0x2fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe3U
                                            : 0x29U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xb3U
                                            : 0xd6U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3bU
                                            : 0x52U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa0U
                                            : 0x5aU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6eU
                                            : 0x1bU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x1aU
                                            : 0x2cU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x83U
                                            : 9U))))))
                    : ((0x00000020U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                        ? ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x75U
                                            : 0xb2U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x27U
                                            : 0xebU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xe2U
                                            : 0x80U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x12U
                                            : 7U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x9aU
                                            : 5U) : 
                                       ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                         ? 0x96U : 0x18U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc3U
                                            : 0x23U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc7U
                                            : 4U))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x15U
                                            : 0x31U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd8U
                                            : 0x71U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf1U
                                            : 0xe5U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa5U
                                            : 0x34U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xccU
                                            : 0xf7U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x3fU
                                            : 0x36U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x26U
                                            : 0x93U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xfdU
                                            : 0xb7U)))))
                        : ((0x00000010U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                            ? ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc0U
                                            : 0x72U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xa4U
                                            : 0x9cU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xafU
                                            : 0xa2U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd4U
                                            : 0xadU)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xf0U
                                            : 0x47U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x59U
                                            : 0xfaU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7dU
                                            : 0xc9U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x82U
                                            : 0xcaU))))
                            : ((8U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                ? ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x76U
                                            : 0xabU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xd7U
                                            : 0xfeU))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x2bU
                                            : 0x67U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 1U : 0x30U)))
                                : ((4U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                    ? ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0xc5U
                                            : 0x6fU)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x6bU
                                            : 0xf2U))
                                    : ((2U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                        ? ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7bU
                                            : 0x77U)
                                        : ((1U & (IData)(vlSelfRef.__Vfunc_aes128__DOT__sbox__7__a))
                                            ? 0x7cU
                                            : 0x63U))))))));
        VL_ASSIGNSEL_WI(128, 8, (0x0000007fU & (((IData)(0x7fU) 
                                                 - 
                                                 VL_SHIFTL_III(7,32,32, __Vfunc_aes128__DOT__sub_bytes__6__i, 3U)) 
                                                - (IData)(7U))), vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y, vlSelfRef.__Vfunc_aes128__DOT__sbox__7__Vfuncout);
        __Vfunc_aes128__DOT__sub_bytes__6__i = ((IData)(1U) 
                                                + __Vfunc_aes128__DOT__sub_bytes__6__i);
    }
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[0U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[1U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[2U];
    __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__sub_bytes__6__y[3U];
    vlSelfRef.aes128__DOT__sb_next[0U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[0U];
    vlSelfRef.aes128__DOT__sb_next[1U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[1U];
    vlSelfRef.aes128__DOT__sb_next[2U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[2U];
    vlSelfRef.aes128__DOT__sb_next[3U] = __Vfunc_aes128__DOT__sub_bytes__6__Vfuncout[3U];
    __Vfunc_aes128__DOT__shift_rows__8__x[0U] = vlSelfRef.aes128__DOT__sb_next[0U];
    __Vfunc_aes128__DOT__shift_rows__8__x[1U] = vlSelfRef.aes128__DOT__sb_next[1U];
    __Vfunc_aes128__DOT__shift_rows__8__x[2U] = vlSelfRef.aes128__DOT__sb_next[2U];
    __Vfunc_aes128__DOT__shift_rows__8__x[3U] = vlSelfRef.aes128__DOT__sb_next[3U];
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__shift_rows__8__y, __VscopeHash, 17632048163419041600ull);
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0x00ffffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0xff000000U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xff00ffffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x00ff0000U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xffff00ffU & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x0000ff00U & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[0U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[3U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[2U]));
    vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U] 
        = ((0xffffff00U & vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U]) 
           | (0x000000ffU & __Vfunc_aes128__DOT__shift_rows__8__x[1U]));
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[0U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[1U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[2U];
    __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__shift_rows__8__y[3U];
    vlSelfRef.aes128__DOT__sr_next[0U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[0U];
    vlSelfRef.aes128__DOT__sr_next[1U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[1U];
    vlSelfRef.aes128__DOT__sr_next[2U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[2U];
    vlSelfRef.aes128__DOT__sr_next[3U] = __Vfunc_aes128__DOT__shift_rows__8__Vfuncout[3U];
    __Vfunc_aes128__DOT__mix_columns__9__x[0U] = vlSelfRef.aes128__DOT__sr_next[0U];
    __Vfunc_aes128__DOT__mix_columns__9__x[1U] = vlSelfRef.aes128__DOT__sr_next[1U];
    __Vfunc_aes128__DOT__mix_columns__9__x[2U] = vlSelfRef.aes128__DOT__sr_next[2U];
    __Vfunc_aes128__DOT__mix_columns__9__x[3U] = vlSelfRef.aes128__DOT__sr_next[3U];
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__mix_columns__9__y, __VscopeHash, 4458951099714502511ull);
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[3U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[3U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[3U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[2U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[2U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[2U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[1U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[1U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[1U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__a0 = (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                               >> 0x00000018U);
    __Vfunc_aes128__DOT__mix_columns__9__a1 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                                  >> 0x00000010U));
    __Vfunc_aes128__DOT__mix_columns__9__a2 = (0x000000ffU 
                                               & (__Vfunc_aes128__DOT__mix_columns__9__x[0U] 
                                                  >> 8U));
    __Vfunc_aes128__DOT__mix_columns__9__a3 = (0x000000ffU 
                                               & __Vfunc_aes128__DOT__mix_columns__9__x[0U]);
    __Vfunc_aes128__DOT__mix_columns__9__b0 = (((([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a0;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__10__Vfuncout)) 
                                                 ^ 
                                                 (([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a1;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__11__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1))) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b1 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ 
                                                 ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a1;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__12__Vfuncout))) 
                                                ^ (
                                                   ([&]() {
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x 
                            = __Vfunc_aes128__DOT__mix_columns__9__a2;
                        vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout 
                            = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                               << 1U)) 
                               ^ (0x1bU & (- (IData)(
                                                     (1U 
                                                      & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__x) 
                                                         >> 7U))))));
                    }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__13__Vfuncout)) 
                                                   ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2))) 
                                               ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3));
    __Vfunc_aes128__DOT__mix_columns__9__b2 = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__a0) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ ([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a2;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__14__Vfuncout))) 
                                               ^ (([&]() {
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x 
                        = __Vfunc_aes128__DOT__mix_columns__9__a3;
                    vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout 
                        = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                           << 1U)) 
                           ^ (0x1bU & (- (IData)((1U 
                                                  & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__x) 
                                                     >> 7U))))));
                }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__15__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a3)));
    __Vfunc_aes128__DOT__mix_columns__9__b3 = ((((([&]() {
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x 
                                = __Vfunc_aes128__DOT__mix_columns__9__a0;
                            vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout 
                                = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                   << 1U)) 
                                   ^ (0x1bU & (- (IData)(
                                                         (1U 
                                                          & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__x) 
                                                             >> 7U))))));
                        }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__16__Vfuncout)) 
                                                  ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a0)) 
                                                 ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a1)) 
                                                ^ (IData)(__Vfunc_aes128__DOT__mix_columns__9__a2)) 
                                               ^ ([&]() {
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x 
                    = __Vfunc_aes128__DOT__mix_columns__9__a3;
                vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout 
                    = ((0x000000feU & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                       << 1U)) ^ (0x1bU 
                                                  & (- (IData)(
                                                               (1U 
                                                                & ((IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__x) 
                                                                   >> 7U))))));
            }(), (IData)(vlSelfRef.__Vfunc_aes128__DOT__xtime__17__Vfuncout)));
    vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[0U] 
        = ((((IData)(__Vfunc_aes128__DOT__mix_columns__9__b0) 
             << 0x00000018U) | ((IData)(__Vfunc_aes128__DOT__mix_columns__9__b1) 
                                << 0x00000010U)) | 
           (((IData)(__Vfunc_aes128__DOT__mix_columns__9__b2) 
             << 8U) | (IData)(__Vfunc_aes128__DOT__mix_columns__9__b3)));
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[0U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[0U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[1U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[1U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[2U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[2U];
    __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[3U] 
        = vlSelfRef.__Vfunc_aes128__DOT__mix_columns__9__y[3U];
    vlSelfRef.aes128__DOT__mc_next[0U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[0U];
    vlSelfRef.aes128__DOT__mc_next[1U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[1U];
    vlSelfRef.aes128__DOT__mc_next[2U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[2U];
    vlSelfRef.aes128__DOT__mc_next[3U] = __Vfunc_aes128__DOT__mix_columns__9__Vfuncout[3U];
    if ((0x0aU == (IData)(vlSelfRef.aes128__DOT__round))) {
        vlSelfRef.aes128__DOT__state_next[0U] = (vlSelfRef.aes128__DOT__sr_next[0U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[0U]);
        vlSelfRef.aes128__DOT__state_next[1U] = (vlSelfRef.aes128__DOT__sr_next[1U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[1U]);
        vlSelfRef.aes128__DOT__state_next[2U] = (vlSelfRef.aes128__DOT__sr_next[2U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[2U]);
        vlSelfRef.aes128__DOT__state_next[3U] = (vlSelfRef.aes128__DOT__sr_next[3U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[3U]);
    } else {
        vlSelfRef.aes128__DOT__state_next[0U] = (vlSelfRef.aes128__DOT__mc_next[0U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[0U]);
        vlSelfRef.aes128__DOT__state_next[1U] = (vlSelfRef.aes128__DOT__mc_next[1U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[1U]);
        vlSelfRef.aes128__DOT__state_next[2U] = (vlSelfRef.aes128__DOT__mc_next[2U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[2U]);
        vlSelfRef.aes128__DOT__state_next[3U] = (vlSelfRef.aes128__DOT__mc_next[3U] 
                                                 ^ 
                                                 vlSelfRef.aes128__DOT__rk_next[3U]);
    }
}
