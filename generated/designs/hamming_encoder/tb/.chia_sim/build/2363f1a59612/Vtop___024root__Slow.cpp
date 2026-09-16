// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"

// Parameter definitions for Vtop___024root
constexpr CData/*0:0*/ Vtop___024root::hamming_encoder__DOT__SECDED;
constexpr IData/*31:0*/ Vtop___024root::hamming_encoder__DOT__DATA_WIDTH;
constexpr IData/*31:0*/ Vtop___024root::hamming_encoder__DOT__PARITY_BITS;
constexpr IData/*31:0*/ Vtop___024root::hamming_encoder__DOT__BASE_WIDTH;
constexpr IData/*31:0*/ Vtop___024root::hamming_encoder__DOT__CODE_WIDTH;


void Vtop___024root___ctor_var_reset(Vtop___024root* vlSelf);

Vtop___024root::Vtop___024root(Vtop__Syms* symsp, const char* v__name)
    : VerilatedModule{v__name}
    , vlSymsp{symsp}
 {
    // Reset structure values
    Vtop___024root___ctor_var_reset(this);
}

void Vtop___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vtop___024root::~Vtop___024root() {
}
