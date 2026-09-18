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
    vlSelfRef.hamming_encoder__DOT__data_in = vlSelfRef.data_in;
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] = 0U;
    vlSelfRef.hamming_encoder__DOT__hamming_bits[1U] = 0U;
    vlSelfRef.hamming_encoder__DOT__hamming_bits[2U] = 0U;
    vlSelfRef.hamming_encoder__DOT__data_idx = 0U;
    vlSelfRef.hamming_encoder__DOT__pos = 1U;
    while (VL_GTES_III(32, 0x00000047U, vlSelfRef.hamming_encoder__DOT__pos)) {
        if ((1U & (~ (([&]() {
                                vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p 
                                    = vlSelfRef.hamming_encoder__DOT__pos;
                                vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__Vfuncout 
                                    = (((((((1U == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p) 
                                            | (2U == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p)) 
                                           | (4U == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p)) 
                                          | (8U == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p)) 
                                         | (0x00000010U 
                                            == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p)) 
                                        | (0x00000020U 
                                           == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p)) 
                                       | (0x00000040U 
                                          == vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__p));
                            }(), (IData)(vlSelfRef.__Vfunc_hamming_encoder__DOT__is_parity_position__0__Vfuncout)) 
                      | (3U == vlSelfRef.hamming_encoder__DOT__pos))))) {
            vlSelfRef.hamming_encoder__DOT____Vlvbound_h3db7eb6d__0 
                = (1U & (IData)((vlSelfRef.hamming_encoder__DOT__data_in 
                                 >> (0x0000003fU & 
                                     ((IData)(1U) + vlSelfRef.hamming_encoder__DOT__data_idx)))));
            if (VL_LIKELY(((0x46U >= (0x0000007fU & 
                                      (vlSelfRef.hamming_encoder__DOT__pos 
                                       - (IData)(1U))))))) {
                vlSelfRef.hamming_encoder__DOT__hamming_bits[(3U 
                                                              & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                                  - (IData)(1U)) 
                                                                 >> 5U))] 
                    = (((~ ((IData)(1U) << (0x0000001fU 
                                            & (vlSelfRef.hamming_encoder__DOT__pos 
                                               - (IData)(1U))))) 
                        & vlSelfRef.hamming_encoder__DOT__hamming_bits[
                        (3U & ((vlSelfRef.hamming_encoder__DOT__pos 
                                - (IData)(1U)) >> 5U))]) 
                       | ((IData)(vlSelfRef.hamming_encoder__DOT____Vlvbound_h3db7eb6d__0) 
                          << (0x0000001fU & (vlSelfRef.hamming_encoder__DOT__pos 
                                             - (IData)(1U)))));
            }
            vlSelfRef.hamming_encoder__DOT__data_idx 
                = ((IData)(1U) + vlSelfRef.hamming_encoder__DOT__data_idx);
        }
        vlSelfRef.hamming_encoder__DOT__pos = ((IData)(1U) 
                                               + vlSelfRef.hamming_encoder__DOT__pos);
    }
    vlSelfRef.hamming_encoder__DOT__p1 = 0U;
    vlSelfRef.hamming_encoder__DOT__p2 = 0U;
    vlSelfRef.hamming_encoder__DOT__p4 = 0U;
    vlSelfRef.hamming_encoder__DOT__p8 = 0U;
    vlSelfRef.hamming_encoder__DOT__p16 = 0U;
    vlSelfRef.hamming_encoder__DOT__p32 = 0U;
    vlSelfRef.hamming_encoder__DOT__p64 = 0U;
    vlSelfRef.hamming_encoder__DOT__pos = 1U;
    while (VL_GTES_III(32, 0x00000047U, vlSelfRef.hamming_encoder__DOT__pos)) {
        if ((0U != (2U & vlSelfRef.hamming_encoder__DOT__pos))) {
            vlSelfRef.hamming_encoder__DOT__p1 = ((IData)(vlSelfRef.hamming_encoder__DOT__p1) 
                                                  ^ 
                                                  ((0x46U 
                                                    >= 
                                                    (0x0000007fU 
                                                     & (vlSelfRef.hamming_encoder__DOT__pos 
                                                        - (IData)(1U)))) 
                                                   && (1U 
                                                       & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                          (3U 
                                                           & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)) 
                                                              >> 5U))] 
                                                          >> 
                                                          (0x0000001fU 
                                                           & (vlSelfRef.hamming_encoder__DOT__pos 
                                                              - (IData)(1U)))))));
        }
        if ((0U != (4U & vlSelfRef.hamming_encoder__DOT__pos))) {
            vlSelfRef.hamming_encoder__DOT__p2 = ((IData)(vlSelfRef.hamming_encoder__DOT__p2) 
                                                  ^ 
                                                  ((0x46U 
                                                    >= 
                                                    (0x0000007fU 
                                                     & (vlSelfRef.hamming_encoder__DOT__pos 
                                                        - (IData)(1U)))) 
                                                   && (1U 
                                                       & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                          (3U 
                                                           & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)) 
                                                              >> 5U))] 
                                                          >> 
                                                          (0x0000001fU 
                                                           & (vlSelfRef.hamming_encoder__DOT__pos 
                                                              - (IData)(1U)))))));
            vlSelfRef.hamming_encoder__DOT__p4 = ((IData)(vlSelfRef.hamming_encoder__DOT__p4) 
                                                  ^ 
                                                  ((0x46U 
                                                    >= 
                                                    (0x0000007fU 
                                                     & (vlSelfRef.hamming_encoder__DOT__pos 
                                                        - (IData)(1U)))) 
                                                   && (1U 
                                                       & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                          (3U 
                                                           & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)) 
                                                              >> 5U))] 
                                                          >> 
                                                          (0x0000001fU 
                                                           & (vlSelfRef.hamming_encoder__DOT__pos 
                                                              - (IData)(1U)))))));
        }
        if ((0U != (0x00000010U & vlSelfRef.hamming_encoder__DOT__pos))) {
            vlSelfRef.hamming_encoder__DOT__p8 = ((IData)(vlSelfRef.hamming_encoder__DOT__p8) 
                                                  ^ 
                                                  ((0x46U 
                                                    >= 
                                                    (0x0000007fU 
                                                     & (vlSelfRef.hamming_encoder__DOT__pos 
                                                        - (IData)(1U)))) 
                                                   && (1U 
                                                       & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                          (3U 
                                                           & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)) 
                                                              >> 5U))] 
                                                          >> 
                                                          (0x0000001fU 
                                                           & (vlSelfRef.hamming_encoder__DOT__pos 
                                                              - (IData)(1U)))))));
            vlSelfRef.hamming_encoder__DOT__p16 = ((IData)(vlSelfRef.hamming_encoder__DOT__p16) 
                                                   ^ 
                                                   ((0x46U 
                                                     >= 
                                                     (0x0000007fU 
                                                      & (vlSelfRef.hamming_encoder__DOT__pos 
                                                         - (IData)(1U)))) 
                                                    && (1U 
                                                        & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                           (3U 
                                                            & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                                - (IData)(1U)) 
                                                               >> 5U))] 
                                                           >> 
                                                           (0x0000001fU 
                                                            & (vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)))))));
        }
        if ((0U != (0x00000020U & vlSelfRef.hamming_encoder__DOT__pos))) {
            vlSelfRef.hamming_encoder__DOT__p32 = ((IData)(vlSelfRef.hamming_encoder__DOT__p32) 
                                                   ^ 
                                                   ((0x46U 
                                                     >= 
                                                     (0x0000007fU 
                                                      & (vlSelfRef.hamming_encoder__DOT__pos 
                                                         - (IData)(1U)))) 
                                                    && (1U 
                                                        & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                           (3U 
                                                            & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                                - (IData)(1U)) 
                                                               >> 5U))] 
                                                           >> 
                                                           (0x0000001fU 
                                                            & (vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)))))));
        }
        if ((0U != (0x00000040U & vlSelfRef.hamming_encoder__DOT__pos))) {
            vlSelfRef.hamming_encoder__DOT__p64 = ((IData)(vlSelfRef.hamming_encoder__DOT__p64) 
                                                   ^ 
                                                   ((0x46U 
                                                     >= 
                                                     (0x0000007fU 
                                                      & (vlSelfRef.hamming_encoder__DOT__pos 
                                                         - (IData)(1U)))) 
                                                    && (1U 
                                                        & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                                                           (3U 
                                                            & ((vlSelfRef.hamming_encoder__DOT__pos 
                                                                - (IData)(1U)) 
                                                               >> 5U))] 
                                                           >> 
                                                           (0x0000001fU 
                                                            & (vlSelfRef.hamming_encoder__DOT__pos 
                                                               - (IData)(1U)))))));
        }
        vlSelfRef.hamming_encoder__DOT__pos = ((IData)(1U) 
                                               + vlSelfRef.hamming_encoder__DOT__pos);
    }
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] 
        = ((0xfffffffcU & vlSelfRef.hamming_encoder__DOT__hamming_bits[0U]) 
           | (((IData)(vlSelfRef.hamming_encoder__DOT__p2) 
               << 1U) | (IData)(vlSelfRef.hamming_encoder__DOT__p1)));
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] 
        = ((0xfffffff7U & vlSelfRef.hamming_encoder__DOT__hamming_bits[0U]) 
           | ((IData)(vlSelfRef.hamming_encoder__DOT__p4) 
              << 3U));
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] 
        = ((0xffffff7fU & vlSelfRef.hamming_encoder__DOT__hamming_bits[0U]) 
           | ((IData)(vlSelfRef.hamming_encoder__DOT__p8) 
              << 7U));
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] 
        = ((0xffff7fffU & vlSelfRef.hamming_encoder__DOT__hamming_bits[0U]) 
           | (0x00008000U & ((~ (IData)(vlSelfRef.hamming_encoder__DOT__p16)) 
                             << 0x0000000fU)));
    vlSelfRef.hamming_encoder__DOT__hamming_bits[0U] 
        = ((0x7fffffffU & vlSelfRef.hamming_encoder__DOT__hamming_bits[0U]) 
           | ((IData)(vlSelfRef.hamming_encoder__DOT__p16) 
              << 0x0000001fU));
    vlSelfRef.hamming_encoder__DOT__hamming_bits[1U] 
        = ((0x7fffffffU & vlSelfRef.hamming_encoder__DOT__hamming_bits[1U]) 
           | ((IData)(vlSelfRef.hamming_encoder__DOT__p64) 
              << 0x0000001fU));
    vlSelfRef.hamming_encoder__DOT__pos = 1U;
    while (VL_GTES_III(32, 0x00000047U, vlSelfRef.hamming_encoder__DOT__pos)) {
        vlSelfRef.hamming_encoder__DOT____Vlvbound_h39fd7bc0__0 
            = ((0x46U >= (0x0000007fU & (vlSelfRef.hamming_encoder__DOT__pos 
                                         - (IData)(1U)))) 
               && (1U & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                         (3U & ((vlSelfRef.hamming_encoder__DOT__pos 
                                 - (IData)(1U)) >> 5U))] 
                         >> (0x0000001fU & (vlSelfRef.hamming_encoder__DOT__pos 
                                            - (IData)(1U))))));
        if (VL_LIKELY(((0x47U >= ((0x0000000aU == vlSelfRef.hamming_encoder__DOT__pos)
                                   ? 0x0000000bU : 
                                  (0x0000007fU & vlSelfRef.hamming_encoder__DOT__pos)))))) {
            vlSelfRef.hamming_encoder__DOT__codeword[(
                                                      ((0x0000000aU 
                                                        == vlSelfRef.hamming_encoder__DOT__pos)
                                                        ? 0x0000000bU
                                                        : 
                                                       (0x0000007fU 
                                                        & vlSelfRef.hamming_encoder__DOT__pos)) 
                                                      >> 5U)] 
                = (((~ ((IData)(1U) << ((0x0000000aU 
                                         == vlSelfRef.hamming_encoder__DOT__pos)
                                         ? 0x0000000bU
                                         : (0x0000001fU 
                                            & vlSelfRef.hamming_encoder__DOT__pos)))) 
                    & vlSelfRef.hamming_encoder__DOT__codeword[
                    (((0x0000000aU == vlSelfRef.hamming_encoder__DOT__pos)
                       ? 0x0000000bU : (0x0000007fU 
                                        & vlSelfRef.hamming_encoder__DOT__pos)) 
                     >> 5U)]) | ((IData)(vlSelfRef.hamming_encoder__DOT____Vlvbound_h39fd7bc0__0) 
                                 << ((0x0000000aU == vlSelfRef.hamming_encoder__DOT__pos)
                                      ? 0x0000000bU
                                      : (0x0000001fU 
                                         & vlSelfRef.hamming_encoder__DOT__pos))));
        }
        vlSelfRef.hamming_encoder__DOT__pos = ((IData)(1U) 
                                               + vlSelfRef.hamming_encoder__DOT__pos);
    }
    vlSelfRef.hamming_encoder__DOT__overall_parity = 0U;
    vlSelfRef.hamming_encoder__DOT__pos = 1U;
    while (VL_GTES_III(32, 0x00000046U, vlSelfRef.hamming_encoder__DOT__pos)) {
        vlSelfRef.hamming_encoder__DOT__overall_parity 
            = ((IData)(vlSelfRef.hamming_encoder__DOT__overall_parity) 
               ^ ((0x46U >= (0x0000007fU & (vlSelfRef.hamming_encoder__DOT__pos 
                                            - (IData)(1U)))) 
                  && (1U & (vlSelfRef.hamming_encoder__DOT__hamming_bits[
                            (3U & ((vlSelfRef.hamming_encoder__DOT__pos 
                                    - (IData)(1U)) 
                                   >> 5U))] >> (0x0000001fU 
                                                & (vlSelfRef.hamming_encoder__DOT__pos 
                                                   - (IData)(1U)))))));
        vlSelfRef.hamming_encoder__DOT__pos = ((IData)(1U) 
                                               + vlSelfRef.hamming_encoder__DOT__pos);
    }
    vlSelfRef.hamming_encoder__DOT__codeword[0U] = 
        ((0xfffffffeU & vlSelfRef.hamming_encoder__DOT__codeword[0U]) 
         | (1U & (~ (IData)(vlSelfRef.hamming_encoder__DOT__overall_parity))));
    vlSelfRef.codeword[0U] = vlSelfRef.hamming_encoder__DOT__codeword[0U];
    vlSelfRef.codeword[1U] = vlSelfRef.hamming_encoder__DOT__codeword[1U];
    vlSelfRef.codeword[2U] = vlSelfRef.hamming_encoder__DOT__codeword[2U];
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

void Vtop___024root___eval(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/hamming_encoder_corrupted/rtl_verification/accepted/hamming_encoder.sv", 1, "", "Input combinational region did not converge after 100 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
    } while (Vtop___024root___eval_phase__ico(vlSelf));
}

#ifdef VL_DEBUG
void Vtop___024root___eval_debug_assertions(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_debug_assertions\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}
#endif  // VL_DEBUG
