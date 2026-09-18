// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vtop__pch.h"
#include "Vtop.h"
#include "Vtop___024root.h"

// FUNCTIONS
Vtop__Syms::~Vtop__Syms()
{

    // Tear down scope hierarchy
    __Vhier.remove(0, &__Vscope_hamming_encoder);

}

Vtop__Syms::Vtop__Syms(VerilatedContext* contextp, const char* namep, Vtop* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(124);
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
    __Vscope_TOP.configure(this, name(), "TOP", "TOP", "<null>", 0, VerilatedScope::SCOPE_OTHER);
    __Vscope_hamming_encoder.configure(this, name(), "hamming_encoder", "hamming_encoder", "hamming_encoder", -9, VerilatedScope::SCOPE_MODULE);

    // Set up scope hierarchy
    __Vhier.add(0, &__Vscope_hamming_encoder);

    // Setup export functions
    for (int __Vfinal = 0; __Vfinal < 2; ++__Vfinal) {
        __Vscope_TOP.varInsert(__Vfinal,"codeword", &(TOP.codeword), false, VLVT_WDATA,VLVD_OUT|VLVF_PUB_RW,0,1 ,71,0);
        __Vscope_TOP.varInsert(__Vfinal,"data_in", &(TOP.data_in), false, VLVT_UINT64,VLVD_IN|VLVF_PUB_RW,0,1 ,63,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"codeword", &(TOP.hamming_encoder__DOT__codeword), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,71,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"data_idx", &(TOP.hamming_encoder__DOT__data_idx), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,5,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"data_in", &(TOP.hamming_encoder__DOT__data_in), false, VLVT_UINT64,VLVD_NODIR|VLVF_PUB_RW,0,1 ,63,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"hamming_bits", &(TOP.hamming_encoder__DOT__hamming_bits), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,71,1);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"overall_parity", &(TOP.hamming_encoder__DOT__overall_parity), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p1", &(TOP.hamming_encoder__DOT__p1), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p16", &(TOP.hamming_encoder__DOT__p16), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p2", &(TOP.hamming_encoder__DOT__p2), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p32", &(TOP.hamming_encoder__DOT__p32), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p4", &(TOP.hamming_encoder__DOT__p4), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p64", &(TOP.hamming_encoder__DOT__p64), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"p8", &(TOP.hamming_encoder__DOT__p8), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"pos", &(TOP.hamming_encoder__DOT__pos), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
    }
}
