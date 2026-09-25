// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vtop__pch.h"
#include "Vtop.h"
#include "Vtop___024root.h"

// FUNCTIONS
Vtop__Syms::~Vtop__Syms()
{

    // Tear down scope hierarchy
    __Vhier.remove(0, &__Vscope_aes128);

}

Vtop__Syms::Vtop__Syms(VerilatedContext* contextp, const char* namep, Vtop* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(2110);
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
    __Vscope_TOP.configure(this, name(), "TOP", "TOP", "<null>", 0, VerilatedScope::SCOPE_OTHER);
    __Vscope_aes128.configure(this, name(), "aes128", "aes128", "aes128", -9, VerilatedScope::SCOPE_MODULE);

    // Set up scope hierarchy
    __Vhier.add(0, &__Vscope_aes128);

    // Setup export functions
    for (int __Vfinal = 0; __Vfinal < 2; ++__Vfinal) {
        __Vscope_TOP.varInsert(__Vfinal,"ciphertext", &(TOP.ciphertext), false, VLVT_WDATA,VLVD_OUT|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_TOP.varInsert(__Vfinal,"clk", &(TOP.clk), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"done", &(TOP.done), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"key", &(TOP.key), false, VLVT_WDATA,VLVD_IN|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_TOP.varInsert(__Vfinal,"plaintext", &(TOP.plaintext), false, VLVT_WDATA,VLVD_IN|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_TOP.varInsert(__Vfinal,"rst_n", &(TOP.rst_n), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"start", &(TOP.start), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"RCON", const_cast<void*>(static_cast<const void*>(&(TOP.aes128__DOT__RCON))), true, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,1,1 ,1,10 ,7,0);
        __Vscope_aes128.varInsert(__Vfinal,"SBOX", const_cast<void*>(static_cast<const void*>(&(TOP.aes128__DOT__SBOX))), true, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,1,1 ,0,255 ,7,0);
        __Vscope_aes128.varInsert(__Vfinal,"busy", &(TOP.aes128__DOT__busy), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"ciphertext", &(TOP.aes128__DOT__ciphertext), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_aes128.varInsert(__Vfinal,"clk", &(TOP.aes128__DOT__clk), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"done", &(TOP.aes128__DOT__done), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"key", &(TOP.aes128__DOT__key), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_aes128.varInsert(__Vfinal,"plaintext", &(TOP.aes128__DOT__plaintext), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_aes128.varInsert(__Vfinal,"round", &(TOP.aes128__DOT__round), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,3,0);
        __Vscope_aes128.varInsert(__Vfinal,"round_key", &(TOP.aes128__DOT__round_key), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,127,0);
        __Vscope_aes128.varInsert(__Vfinal,"rst_n", &(TOP.aes128__DOT__rst_n), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"start", &(TOP.aes128__DOT__start), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_aes128.varInsert(__Vfinal,"state", &(TOP.aes128__DOT__state), false, VLVT_WDATA,VLVD_NODIR|VLVF_PUB_RW,0,1 ,127,0);
    }
}
