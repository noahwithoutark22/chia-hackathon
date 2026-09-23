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
    vlSelfRef.i2c_master__DOT__clk = vlSelfRef.clk;
    vlSelfRef.i2c_master__DOT__rst_n = vlSelfRef.rst_n;
    vlSelfRef.i2c_master__DOT__start = vlSelfRef.start;
    vlSelfRef.i2c_master__DOT__slave_addr = vlSelfRef.slave_addr;
    vlSelfRef.i2c_master__DOT__rw = vlSelfRef.rw;
    vlSelfRef.i2c_master__DOT__tx_data = vlSelfRef.tx_data;
    vlSelfRef.i2c_master__DOT__sda_in = vlSelfRef.sda_in;
    vlSelfRef.i2c_master__DOT__scl_in = vlSelfRef.scl_in;
    vlSelfRef.sda_out = vlSelfRef.i2c_master__DOT__sda_out;
    vlSelfRef.busy = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.scl_out = vlSelfRef.i2c_master__DOT__scl_out;
    vlSelfRef.rx_data = vlSelfRef.i2c_master__DOT__rx_data;
    vlSelfRef.done = vlSelfRef.i2c_master__DOT__done;
    vlSelfRef.ack_error = vlSelfRef.i2c_master__DOT__ack_error;
    vlSelfRef.i2c_master__DOT__sda_oe = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.i2c_master__DOT__scl_oe = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.sda_oe = vlSelfRef.i2c_master__DOT__sda_oe;
    vlSelfRef.scl_oe = vlSelfRef.i2c_master__DOT__scl_oe;
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
                                                    ((IData)(vlSelfRef.i2c_master__DOT__clk) 
                                                     & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__i2c_master__DOT__clk__0)))));
    vlSelfRef.__Vtrigprevexpr___TOP__i2c_master__DOT__clk__0 
        = vlSelfRef.i2c_master__DOT__clk;
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
    CData/*3:0*/ __Vdly__i2c_master__DOT__bit_cnt;
    __Vdly__i2c_master__DOT__bit_cnt = 0;
    CData/*3:0*/ __Vdly__i2c_master__DOT__state;
    __Vdly__i2c_master__DOT__state = 0;
    CData/*1:0*/ __Vdly__i2c_master__DOT__div_cnt;
    __Vdly__i2c_master__DOT__div_cnt = 0;
    // Body
    __Vdly__i2c_master__DOT__bit_cnt = vlSelfRef.i2c_master__DOT__bit_cnt;
    __Vdly__i2c_master__DOT__state = vlSelfRef.i2c_master__DOT__state;
    __Vdly__i2c_master__DOT__div_cnt = vlSelfRef.i2c_master__DOT__div_cnt;
    if (vlSelfRef.i2c_master__DOT__rst_n) {
        vlSelfRef.i2c_master__DOT__done = 0U;
        if (((0U == (IData)(vlSelfRef.i2c_master__DOT__state)) 
             & (IData)(vlSelfRef.i2c_master__DOT__start))) {
            vlSelfRef.i2c_master__DOT__busy = 1U;
            vlSelfRef.i2c_master__DOT__shift_reg = 
                (((IData)(vlSelfRef.i2c_master__DOT__slave_addr) 
                  << 1U) | (1U & (~ (IData)(vlSelfRef.i2c_master__DOT__rw))));
            __Vdly__i2c_master__DOT__bit_cnt = 6U;
            __Vdly__i2c_master__DOT__state = 1U;
        } else if ((3U == (IData)(vlSelfRef.i2c_master__DOT__div_cnt))) {
            __Vdly__i2c_master__DOT__div_cnt = 0U;
            if ((8U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                if ((4U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    __Vdly__i2c_master__DOT__state = 0U;
                    vlSelfRef.i2c_master__DOT__busy = 0U;
                } else if ((2U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    __Vdly__i2c_master__DOT__state = 0U;
                    vlSelfRef.i2c_master__DOT__busy = 0U;
                } else if ((1U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    __Vdly__i2c_master__DOT__state = 0U;
                    vlSelfRef.i2c_master__DOT__busy = 0U;
                } else {
                    vlSelfRef.i2c_master__DOT__busy = 1U;
                    vlSelfRef.i2c_master__DOT__done = 1U;
                    __Vdly__i2c_master__DOT__state = 1U;
                }
            } else if ((4U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                        vlSelfRef.i2c_master__DOT__rx_data 
                            = (0x000000ffU & (~ (IData)(vlSelfRef.i2c_master__DOT__rx_shift)));
                        __Vdly__i2c_master__DOT__state = 5U;
                    } else {
                        vlSelfRef.i2c_master__DOT__rx_shift 
                            = (((~ ((IData)(1U) << 
                                    (7U & ((IData)(7U) 
                                           - (IData)(vlSelfRef.i2c_master__DOT__bit_cnt))))) 
                                & (IData)(vlSelfRef.i2c_master__DOT__rx_shift)) 
                               | (0x00ffU & ((IData)(vlSelfRef.i2c_master__DOT__sda_in) 
                                             << (7U 
                                                 & ((IData)(7U) 
                                                    - (IData)(vlSelfRef.i2c_master__DOT__bit_cnt))))));
                        if ((1U == (IData)(vlSelfRef.i2c_master__DOT__bit_cnt))) {
                            __Vdly__i2c_master__DOT__state = 7U;
                        } else {
                            __Vdly__i2c_master__DOT__bit_cnt 
                                = (0x0000000fU & ((IData)(vlSelfRef.i2c_master__DOT__bit_cnt) 
                                                  - (IData)(1U)));
                        }
                    }
                } else if ((1U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelfRef.i2c_master__DOT__sda_in)))) {
                        vlSelfRef.i2c_master__DOT__ack_error = 1U;
                    }
                    __Vdly__i2c_master__DOT__state = 6U;
                } else if ((0U == (IData)(vlSelfRef.i2c_master__DOT__bit_cnt))) {
                    __Vdly__i2c_master__DOT__state = 5U;
                } else {
                    __Vdly__i2c_master__DOT__bit_cnt 
                        = (0x0000000fU & ((IData)(vlSelfRef.i2c_master__DOT__bit_cnt) 
                                          - (IData)(1U)));
                }
            } else if ((2U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelfRef.i2c_master__DOT__sda_in)))) {
                        vlSelfRef.i2c_master__DOT__ack_error = 1U;
                    }
                    if (vlSelfRef.i2c_master__DOT__rw) {
                        vlSelfRef.i2c_master__DOT__shift_reg 
                            = (0x000000ffU & (~ (IData)(vlSelfRef.i2c_master__DOT__tx_data)));
                        __Vdly__i2c_master__DOT__bit_cnt = 7U;
                        __Vdly__i2c_master__DOT__state = 4U;
                    } else {
                        __Vdly__i2c_master__DOT__bit_cnt = 7U;
                        vlSelfRef.i2c_master__DOT__rx_shift = 0U;
                        __Vdly__i2c_master__DOT__state = 6U;
                    }
                } else if ((1U == (IData)(vlSelfRef.i2c_master__DOT__bit_cnt))) {
                    __Vdly__i2c_master__DOT__state = 3U;
                } else {
                    __Vdly__i2c_master__DOT__bit_cnt 
                        = (0x0000000fU & ((IData)(1U) 
                                          + (IData)(vlSelfRef.i2c_master__DOT__bit_cnt)));
                }
            } else if ((1U & (IData)(vlSelfRef.i2c_master__DOT__state))) {
                __Vdly__i2c_master__DOT__state = 2U;
            } else {
                vlSelfRef.i2c_master__DOT__busy = 0U;
                vlSelfRef.i2c_master__DOT__ack_error = 1U;
            }
        } else {
            __Vdly__i2c_master__DOT__div_cnt = (3U 
                                                & ((IData)(1U) 
                                                   + (IData)(vlSelfRef.i2c_master__DOT__div_cnt)));
        }
    } else {
        __Vdly__i2c_master__DOT__state = 0U;
        __Vdly__i2c_master__DOT__div_cnt = 0U;
        __Vdly__i2c_master__DOT__bit_cnt = 0U;
        vlSelfRef.i2c_master__DOT__shift_reg = 0U;
        vlSelfRef.i2c_master__DOT__rx_shift = 0U;
        vlSelfRef.i2c_master__DOT__rx_data = 0U;
        vlSelfRef.i2c_master__DOT__done = 0U;
        vlSelfRef.i2c_master__DOT__busy = 0U;
        vlSelfRef.i2c_master__DOT__ack_error = 0U;
    }
    vlSelfRef.i2c_master__DOT__bit_cnt = __Vdly__i2c_master__DOT__bit_cnt;
    vlSelfRef.i2c_master__DOT__state = __Vdly__i2c_master__DOT__state;
    vlSelfRef.i2c_master__DOT__div_cnt = __Vdly__i2c_master__DOT__div_cnt;
    vlSelfRef.done = vlSelfRef.i2c_master__DOT__done;
    vlSelfRef.rx_data = vlSelfRef.i2c_master__DOT__rx_data;
    vlSelfRef.ack_error = vlSelfRef.i2c_master__DOT__ack_error;
    vlSelfRef.busy = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.i2c_master__DOT__sda_oe = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.i2c_master__DOT__scl_oe = vlSelfRef.i2c_master__DOT__busy;
    vlSelfRef.sda_oe = vlSelfRef.i2c_master__DOT__sda_oe;
    vlSelfRef.scl_oe = vlSelfRef.i2c_master__DOT__scl_oe;
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
            VL_FATAL_MT("/workspace/generated/designs/i2c_benchmark_corrupted/rtl_verification/candidates/iteration_05/i2c_master.sv", 1, "", "Input combinational region did not converge after 100 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
    } while (Vtop___024root___eval_phase__ico(vlSelf));
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/i2c_benchmark_corrupted/rtl_verification/candidates/iteration_05/i2c_master.sv", 1, "", "NBA region did not converge after 100 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00000064U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vtop___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/workspace/generated/designs/i2c_benchmark_corrupted/rtl_verification/candidates/iteration_05/i2c_master.sv", 1, "", "Active region did not converge after 100 tries");
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
    if (VL_UNLIKELY(((vlSelfRef.slave_addr & 0x80U)))) {
        Verilated::overWidthError("slave_addr");
    }
    if (VL_UNLIKELY(((vlSelfRef.rw & 0xfeU)))) {
        Verilated::overWidthError("rw");
    }
    if (VL_UNLIKELY(((vlSelfRef.sda_in & 0xfeU)))) {
        Verilated::overWidthError("sda_in");
    }
    if (VL_UNLIKELY(((vlSelfRef.scl_in & 0xfeU)))) {
        Verilated::overWidthError("scl_in");
    }
}
#endif  // VL_DEBUG
