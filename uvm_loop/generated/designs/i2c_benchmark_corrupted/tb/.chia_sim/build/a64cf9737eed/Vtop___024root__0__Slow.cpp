// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

VL_ATTR_COLD void Vtop___024root___eval_static(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_static\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__i2c_master__DOT__clk__0 
        = vlSelfRef.i2c_master__DOT__clk;
}

VL_ATTR_COLD void Vtop___024root___eval_initial__TOP(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_initial(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vtop___024root___eval_initial__TOP(vlSelf);
}

VL_ATTR_COLD void Vtop___024root___eval_initial__TOP(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial__TOP\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.i2c_master__DOT__sda_out = 0U;
    vlSelfRef.i2c_master__DOT__scl_out = 0U;
}

VL_ATTR_COLD void Vtop___024root___eval_final(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_final\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_settle(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_settle\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VstlIterCount;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00000064U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
            VL_FATAL_MT("/workspace/generated/designs/i2c_benchmark_corrupted/rtl_verification/candidates/iteration_01/i2c_master.sv", 1, "", "Settle region did not converge after 100 tries");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
    } while (Vtop___024root___eval_phase__stl(vlSelf));
}

VL_ATTR_COLD void Vtop___024root___eval_triggers__stl(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_triggers__stl\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered
                                      [0U]) | (IData)((IData)(vlSelfRef.__VstlFirstIteration)));
    vlSelfRef.__VstlFirstIteration = 0U;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtop___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
}

VL_ATTR_COLD bool Vtop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vtop___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___trigger_anySet__stl\n"); );
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

void Vtop___024root___ico_sequent__TOP__0(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_stl(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_stl\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        Vtop___024root___ico_sequent__TOP__0(vlSelf);
    }
}

VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__stl\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vtop___024root___eval_triggers__stl(vlSelf);
    __VstlExecute = Vtop___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vtop___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vtop___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vtop___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vtop___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge i2c_master.clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtop___024root___ctor_var_reset(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ctor_var_reset\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->name());
    vlSelf->clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1638864771569018232ull);
    vlSelf->start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9867861323841650631ull);
    vlSelf->slave_addr = VL_SCOPED_RAND_RESET_I(7, __VscopeHash, 9024215834569103971ull);
    vlSelf->rw = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8121497556497431088ull);
    vlSelf->tx_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14770307426006424685ull);
    vlSelf->sda_in = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10842241167456196672ull);
    vlSelf->scl_in = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17166283181084171217ull);
    vlSelf->sda_out = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13382750783056966018ull);
    vlSelf->sda_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13809046488170418561ull);
    vlSelf->scl_out = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7359435583922376207ull);
    vlSelf->scl_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7513410202475038261ull);
    vlSelf->rx_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 15001017414173623810ull);
    vlSelf->done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10296494685231209730ull);
    vlSelf->busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6386567572483775230ull);
    vlSelf->ack_error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8774941393143077774ull);
    vlSelf->i2c_master__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1804842597454346349ull);
    vlSelf->i2c_master__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2656899490836843068ull);
    vlSelf->i2c_master__DOT__start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 450355577921815430ull);
    vlSelf->i2c_master__DOT__slave_addr = VL_SCOPED_RAND_RESET_I(7, __VscopeHash, 3645770442778113261ull);
    vlSelf->i2c_master__DOT__rw = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8096738480053663076ull);
    vlSelf->i2c_master__DOT__tx_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12310352623613702830ull);
    vlSelf->i2c_master__DOT__sda_in = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12078945903665035379ull);
    vlSelf->i2c_master__DOT__scl_in = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3472690577435174282ull);
    vlSelf->i2c_master__DOT__sda_out = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9549272820662917488ull);
    vlSelf->i2c_master__DOT__sda_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3487202470202450044ull);
    vlSelf->i2c_master__DOT__scl_out = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14900068471008851567ull);
    vlSelf->i2c_master__DOT__scl_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3832351885203811576ull);
    vlSelf->i2c_master__DOT__rx_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 4224047504189470748ull);
    vlSelf->i2c_master__DOT__done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2192303045415082219ull);
    vlSelf->i2c_master__DOT__busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17917605544934380768ull);
    vlSelf->i2c_master__DOT__ack_error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15055085522582919785ull);
    vlSelf->i2c_master__DOT__state = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 2669848436360764816ull);
    vlSelf->i2c_master__DOT__div_cnt = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 4541379835609835073ull);
    vlSelf->i2c_master__DOT__bit_cnt = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 1313445759222190348ull);
    vlSelf->i2c_master__DOT__shift_reg = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16236699903037281477ull);
    vlSelf->i2c_master__DOT__rx_shift = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 7988107045496819694ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__i2c_master__DOT__clk__0 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7112288327582634539ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
