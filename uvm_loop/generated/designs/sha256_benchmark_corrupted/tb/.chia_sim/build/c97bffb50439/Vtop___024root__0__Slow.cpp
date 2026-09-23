// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

VL_ATTR_COLD void Vtop___024root___eval_static(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_static\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__clk__0 
        = vlSelfRef.sha256__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__sha256__DOT__rst_n__0 
        = vlSelfRef.sha256__DOT__rst_n;
}

VL_ATTR_COLD void Vtop___024root___eval_initial(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
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
            VL_FATAL_MT("/workspace/generated/designs/sha256_benchmark_corrupted/rtl_verification/candidates/iteration_03/sha256.sv", 1, "", "Settle region did not converge after 100 tries");
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
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge sha256.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(negedge sha256.rst_n)\n");
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
    VL_SCOPED_RAND_RESET_W(512, vlSelf->block, __VscopeHash, 12356766002385227290ull);
    vlSelf->done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10296494685231209730ull);
    VL_SCOPED_RAND_RESET_W(256, vlSelf->digest, __VscopeHash, 154021876994649933ull);
    vlSelf->sha256__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10145646241421977445ull);
    vlSelf->sha256__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2271943918967602312ull);
    vlSelf->sha256__DOT__start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16195435477028113397ull);
    VL_SCOPED_RAND_RESET_W(512, vlSelf->sha256__DOT__block, __VscopeHash, 15629307290678387662ull);
    vlSelf->sha256__DOT__done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16315074416253384118ull);
    VL_SCOPED_RAND_RESET_W(256, vlSelf->sha256__DOT__digest, __VscopeHash, 9551124613075190411ull);
    for (int __Vi0 = 0; __Vi0 < 64; ++__Vi0) {
        vlSelf->sha256__DOT__W[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6822303704496111371ull);
    }
    vlSelf->sha256__DOT__H0 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5270258164664775480ull);
    vlSelf->sha256__DOT__H1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17914782488850571985ull);
    vlSelf->sha256__DOT__H2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5196014180990395987ull);
    vlSelf->sha256__DOT__H3 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18143115553528233010ull);
    vlSelf->sha256__DOT__H4 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 974922989236245547ull);
    vlSelf->sha256__DOT__H5 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5148171249901108292ull);
    vlSelf->sha256__DOT__H6 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14964189572052704199ull);
    vlSelf->sha256__DOT__H7 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17317911033035671760ull);
    vlSelf->sha256__DOT__a = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8385919444450084569ull);
    vlSelf->sha256__DOT__b = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15238666963767747598ull);
    vlSelf->sha256__DOT__c = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15531344538825877955ull);
    vlSelf->sha256__DOT__d = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6192365099780477916ull);
    vlSelf->sha256__DOT__e = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10736447175304787866ull);
    vlSelf->sha256__DOT__f = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 279958944569754207ull);
    vlSelf->sha256__DOT__g = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8647062395073242456ull);
    vlSelf->sha256__DOT__h = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7316398374213429943ull);
    vlSelf->sha256__DOT__t1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10312711179960646446ull);
    vlSelf->sha256__DOT__t2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16874028569701681907ull);
    vlSelf->sha256__DOT__round = VL_SCOPED_RAND_RESET_I(7, __VscopeHash, 12617960770635731168ull);
    vlSelf->sha256__DOT__busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5641424913318151093ull);
    vlSelf->sha256__DOT__message_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 310573963335216871ull);
    vlSelf->sha256__DOT__i = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10218202892360294028ull);
    vlSelf->sha256__DOT__next_w = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15271400865840327817ull);
    vlSelf->sha256__DOT__next_t1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11120465126059706638ull);
    vlSelf->sha256__DOT__next_t2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7981981233092839024ull);
    vlSelf->sha256__DOT__na = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15566553390500090128ull);
    vlSelf->sha256__DOT__nb = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4520370289939722710ull);
    vlSelf->sha256__DOT__nc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9718995296860092778ull);
    vlSelf->sha256__DOT__nd = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17517373365682163586ull);
    vlSelf->sha256__DOT__ne = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3238258583840502203ull);
    vlSelf->sha256__DOT__nf = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16317742023299736202ull);
    vlSelf->sha256__DOT__ng = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10066745417753723361ull);
    vlSelf->sha256__DOT__nh = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7858485150252544399ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__sha256__DOT__clk__0 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6636350722880159342ull);
    vlSelf->__Vtrigprevexpr___TOP__sha256__DOT__rst_n__0 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 741336985680219949ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
