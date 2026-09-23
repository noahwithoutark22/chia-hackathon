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
    VL_OUT8(done,0,0);
    CData/*0:0*/ sha256__DOT__clk;
    CData/*0:0*/ sha256__DOT__rst_n;
    CData/*0:0*/ sha256__DOT__start;
    CData/*0:0*/ sha256__DOT__done;
    CData/*6:0*/ sha256__DOT__round;
    CData/*0:0*/ sha256__DOT__busy;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__sha256__DOT__clk__0;
    CData/*0:0*/ __Vtrigprevexpr___TOP__sha256__DOT__rst_n__0;
    VL_INW(block,511,0,16);
    VL_OUTW(digest,255,0,8);
    VlWide<16>/*511:0*/ sha256__DOT__block;
    VlWide<8>/*255:0*/ sha256__DOT__digest;
    IData/*31:0*/ sha256__DOT__H0;
    IData/*31:0*/ sha256__DOT__H1;
    IData/*31:0*/ sha256__DOT__H2;
    IData/*31:0*/ sha256__DOT__H3;
    IData/*31:0*/ sha256__DOT__H4;
    IData/*31:0*/ sha256__DOT__H5;
    IData/*31:0*/ sha256__DOT__H6;
    IData/*31:0*/ sha256__DOT__H7;
    IData/*31:0*/ sha256__DOT__a;
    IData/*31:0*/ sha256__DOT__b;
    IData/*31:0*/ sha256__DOT__c;
    IData/*31:0*/ sha256__DOT__d;
    IData/*31:0*/ sha256__DOT__e;
    IData/*31:0*/ sha256__DOT__f;
    IData/*31:0*/ sha256__DOT__g;
    IData/*31:0*/ sha256__DOT__h;
    IData/*31:0*/ sha256__DOT__t1;
    IData/*31:0*/ sha256__DOT__t2;
    IData/*31:0*/ sha256__DOT__message_word;
    IData/*31:0*/ sha256__DOT__i;
    IData/*31:0*/ sha256__DOT__next_w;
    IData/*31:0*/ sha256__DOT__next_t1;
    IData/*31:0*/ sha256__DOT__next_t2;
    IData/*31:0*/ sha256__DOT__na;
    IData/*31:0*/ sha256__DOT__nb;
    IData/*31:0*/ sha256__DOT__nc;
    IData/*31:0*/ sha256__DOT__nd;
    IData/*31:0*/ sha256__DOT__ne;
    IData/*31:0*/ sha256__DOT__nf;
    IData/*31:0*/ sha256__DOT__ng;
    IData/*31:0*/ sha256__DOT__nh;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<IData/*31:0*/, 64> sha256__DOT__W;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    VlNBACommitQueue<VlUnpacked<IData/*31:0*/, 64>, false, IData/*31:0*/, 1> __VdlyCommitQueuesha256__DOT__W;

    // INTERNAL VARIABLES
    Vtop__Syms* const vlSymsp;

    // PARAMETERS
    static constexpr VlUnpacked<IData/*31:0*/, 64> sha256__DOT__K = {{
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
        0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
        0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
        0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
        0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
        0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
        0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
        0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
        0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
        0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
        0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U
    }};

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* v__name);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
