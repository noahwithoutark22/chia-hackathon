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
    __Vhier.remove(&__Vscope_hamming_encoder, &__Vscope_hamming_encoder__build_and_encode);

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
    __Vscope_hamming_encoder__build_and_encode.configure(this, name(), "hamming_encoder.build_and_encode", "build_and_encode", "<null>", -9, VerilatedScope::SCOPE_OTHER);

    // Set up scope hierarchy
    __Vhier.add(0, &__Vscope_hamming_encoder);
    __Vhier.add(&__Vscope_hamming_encoder, &__Vscope_hamming_encoder__build_and_encode);

    // Setup export functions
    for (int __Vfinal = 0; __Vfinal < 2; ++__Vfinal) {
        __Vscope_TOP.varInsert(__Vfinal,"code_out", &(TOP.code_out), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_TOP.varInsert(__Vfinal,"data_in", &(TOP.data_in), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,3,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"BASE_WIDTH", const_cast<void*>(static_cast<const void*>(&(TOP.hamming_encoder__DOT__BASE_WIDTH))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"CODE_WIDTH", const_cast<void*>(static_cast<const void*>(&(TOP.hamming_encoder__DOT__CODE_WIDTH))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"DATA_WIDTH", const_cast<void*>(static_cast<const void*>(&(TOP.hamming_encoder__DOT__DATA_WIDTH))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"PARITY_BITS", const_cast<void*>(static_cast<const void*>(&(TOP.hamming_encoder__DOT__PARITY_BITS))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"SECDED", const_cast<void*>(static_cast<const void*>(&(TOP.hamming_encoder__DOT__SECDED))), true, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"code_out", &(TOP.hamming_encoder__DOT__code_out), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"data_in", &(TOP.hamming_encoder__DOT__data_in), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,3,0);
        __Vscope_hamming_encoder.varInsert(__Vfinal,"ham", &(TOP.hamming_encoder__DOT__ham), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,1);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"data_idx", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__data_idx), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"overall_par", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__overall_par), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"p", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__p), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"par", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__par), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"parity_pos", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__parity_pos), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_hamming_encoder__build_and_encode.varInsert(__Vfinal,"pos", &(TOP.hamming_encoder__DOT__build_and_encode__DOT__pos), false, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
    }
}
