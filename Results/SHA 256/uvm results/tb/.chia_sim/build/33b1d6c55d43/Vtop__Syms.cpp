// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vtop__pch.h"
#include "Vtop.h"
#include "Vtop___024root.h"

// FUNCTIONS
Vtop__Syms::~Vtop__Syms()
{

    // Tear down scope hierarchy
    __Vhier.remove(0, &__Vscope_sha256);

}

Vtop__Syms::Vtop__Syms(VerilatedContext* contextp, const char* namep, Vtop* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(628);
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
    __Vscope_TOP.configure(this, name(), "TOP", "TOP", "<null>", 0, VerilatedScope::SCOPE_OTHER);
    __Vscope_sha256.configure(this, name(), "sha256", "sha256", "sha256", -9, VerilatedScope::SCOPE_MODULE);

    // Set up scope hierarchy
    __Vhier.add(0, &__Vscope_sha256);

    // Setup export functions
    for (int __Vfinal = 0; __Vfinal < 2; ++__Vfinal) {
        __Vscope_TOP.varInsert(__Vfinal,"block", &(TOP.block), false, VLVT_WDATA,VLVD_IN|VLVF_PUB_RW,0,1 ,511,0);
        __Vscope_TOP.varInsert(__Vfinal,"clk", &(TOP.clk), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"digest", &(TOP.digest), false, VLVT_WDATA,VLVD_OUT|VLVF_PUB_RW,0,1 ,255,0);
        __Vscope_TOP.varInsert(__Vfinal,"done", &(TOP.done), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"rst_n", &(TOP.rst_n), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"start", &(TOP.start), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"H0", &(TOP.sha256__DOT__H0), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H1", &(TOP.sha256__DOT__H1), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H2", &(TOP.sha256__DOT__H2), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H3", &(TOP.sha256__DOT__H3), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H4", &(TOP.sha256__DOT__H4), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H5", &(TOP.sha256__DOT__H5), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H6", &(TOP.sha256__DOT__H6), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"H7", &(TOP.sha256__DOT__H7), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"K", const_cast<void*>(static_cast<const void*>(&(TOP.sha256__DOT__K))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,1,1 ,0,63 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"W", &(TOP.sha256__DOT__W), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,1,1 ,0,63 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"a", &(TOP.sha256__DOT__a), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"b", &(TOP.sha256__DOT__b), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"block", &(TOP.sha256__DOT__block), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,511,0);
        __Vscope_sha256.varInsert(__Vfinal,"busy", &(TOP.sha256__DOT__busy), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"c", &(TOP.sha256__DOT__c), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"clk", &(TOP.sha256__DOT__clk), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"d", &(TOP.sha256__DOT__d), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"digest", &(TOP.sha256__DOT__digest), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,255,0);
        __Vscope_sha256.varInsert(__Vfinal,"done", &(TOP.sha256__DOT__done), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"e", &(TOP.sha256__DOT__e), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"f", &(TOP.sha256__DOT__f), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"g", &(TOP.sha256__DOT__g), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"h", &(TOP.sha256__DOT__h), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"i", &(TOP.sha256__DOT__i), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"message_word", &(TOP.sha256__DOT__message_word), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"na", &(TOP.sha256__DOT__na), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"nb", &(TOP.sha256__DOT__nb), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"nc", &(TOP.sha256__DOT__nc), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"nd", &(TOP.sha256__DOT__nd), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"ne", &(TOP.sha256__DOT__ne), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"next_t1", &(TOP.sha256__DOT__next_t1), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"next_t2", &(TOP.sha256__DOT__next_t2), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"next_w", &(TOP.sha256__DOT__next_w), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"nf", &(TOP.sha256__DOT__nf), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"ng", &(TOP.sha256__DOT__ng), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"nh", &(TOP.sha256__DOT__nh), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"round", &(TOP.sha256__DOT__round), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_sha256.varInsert(__Vfinal,"rst_n", &(TOP.sha256__DOT__rst_n), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"start", &(TOP.sha256__DOT__start), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_sha256.varInsert(__Vfinal,"t1", &(TOP.sha256__DOT__t1), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
        __Vscope_sha256.varInsert(__Vfinal,"t2", &(TOP.sha256__DOT__t2), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW,0,1 ,31,0);
    }
}
