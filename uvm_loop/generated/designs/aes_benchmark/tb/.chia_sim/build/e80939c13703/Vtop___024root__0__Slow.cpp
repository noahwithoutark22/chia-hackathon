// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

VL_ATTR_COLD void Vtop___024root___eval_static(Vtop___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_static\n"); );
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__clk__0 
        = vlSelfRef.aes128__DOT__clk;
    vlSelfRef.__Vtrigprevexpr___TOP__aes128__DOT__rst_n__0 
        = vlSelfRef.aes128__DOT__rst_n;
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
            VL_FATAL_MT("/workspace/generated/designs/aes_benchmark/rtl_verification/accepted/aes128.sv", 13, "", "Settle region did not converge after 100 tries");
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
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge aes128.clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(negedge aes128.rst_n)\n");
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
    VL_SCOPED_RAND_RESET_W(128, vlSelf->key, __VscopeHash, 14066609003741847747ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->plaintext, __VscopeHash, 15306753485699558102ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->ciphertext, __VscopeHash, 5156948722554576173ull);
    vlSelf->busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6386567572483775230ull);
    vlSelf->done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10296494685231209730ull);
    vlSelf->aes128__DOT__clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14544860489790919967ull);
    vlSelf->aes128__DOT__rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5368040182413869784ull);
    vlSelf->aes128__DOT__start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9164625767454374564ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__key, __VscopeHash, 10482088784381507549ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__plaintext, __VscopeHash, 12199150672749767971ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__ciphertext, __VscopeHash, 17475667321111049765ull);
    vlSelf->aes128__DOT__busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17670995702114245922ull);
    vlSelf->aes128__DOT__done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10264609018133761590ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__state_reg, __VscopeHash, 3053697348767337149ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__round_key, __VscopeHash, 16061596745193678768ull);
    vlSelf->aes128__DOT__round = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 2439001684704844499ull);
    vlSelf->aes128__DOT__state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 13340969635794758130ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__rk_next, __VscopeHash, 15244687416086475645ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__sb_next, __VscopeHash, 15716621936024578243ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__sr_next, __VscopeHash, 17809712802459973778ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__mc_next, __VscopeHash, 4824945416314176545ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->aes128__DOT__state_next, __VscopeHash, 6483374738932410688ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__2__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14491213766730728181ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__2__a = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8256122388241694532ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__3__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8406531357323404805ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__3__a = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5736898573509202665ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__4__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16898221733902716721ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__4__a = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5272685393634827475ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__5__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14763149846761411652ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__5__a = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 6936950873808372694ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__sub_bytes__6__y, __VscopeHash, 9264579218545655816ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__7__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 11328138234546298608ull);
    vlSelf->__Vfunc_aes128__DOT__sbox__7__a = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10798827981345760255ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__shift_rows__8__y, __VscopeHash, 17632048163419041600ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->__Vfunc_aes128__DOT__mix_columns__9__y, __VscopeHash, 4458951099714502511ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__10__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5268519252148885661ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__10__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8542890044340788206ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__11__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 2888374430768905939ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__11__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14393216256103668335ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__12__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 3748269734866596945ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__12__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16484566949394729320ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__13__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 133720045416992989ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__13__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 197734281660140578ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__14__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 9485836994791181512ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__14__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14551607387081145088ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__15__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1941997861999114462ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__15__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14945218500774261094ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__16__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12292126555757921367ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__16__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1096678536158726726ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__17__Vfuncout = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 12583041513419715614ull);
    vlSelf->__Vfunc_aes128__DOT__xtime__17__x = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 7761557967429325265ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__aes128__DOT__clk__0 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17826933779502392162ull);
    vlSelf->__Vtrigprevexpr___TOP__aes128__DOT__rst_n__0 = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 434344195693693649ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
