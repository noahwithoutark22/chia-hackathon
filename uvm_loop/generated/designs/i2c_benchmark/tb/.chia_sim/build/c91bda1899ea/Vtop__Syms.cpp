// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vtop__pch.h"
#include "Vtop.h"
#include "Vtop___024root.h"

// FUNCTIONS
Vtop__Syms::~Vtop__Syms()
{

    // Tear down scope hierarchy
    __Vhier.remove(0, &__Vscope_i2c_master);

}

Vtop__Syms::Vtop__Syms(VerilatedContext* contextp, const char* namep, Vtop* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(258);
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    // Setup scopes
    __Vscope_TOP.configure(this, name(), "TOP", "TOP", "<null>", 0, VerilatedScope::SCOPE_OTHER);
    __Vscope_i2c_master.configure(this, name(), "i2c_master", "i2c_master", "i2c_master", -9, VerilatedScope::SCOPE_MODULE);

    // Set up scope hierarchy
    __Vhier.add(0, &__Vscope_i2c_master);

    // Setup export functions
    for (int __Vfinal = 0; __Vfinal < 2; ++__Vfinal) {
        __Vscope_TOP.varInsert(__Vfinal,"ack_error", &(TOP.ack_error), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"busy", &(TOP.busy), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"clk", &(TOP.clk), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"done", &(TOP.done), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"read_data", &(TOP.read_data), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_TOP.varInsert(__Vfinal,"reg_addr", &(TOP.reg_addr), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_TOP.varInsert(__Vfinal,"rst_n", &(TOP.rst_n), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"rw", &(TOP.rw), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"scl", &(TOP.scl), false, VLVT_UINT8,VLVD_INOUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"sda", &(TOP.sda), false, VLVT_UINT8,VLVD_INOUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"slave_addr", &(TOP.slave_addr), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_TOP.varInsert(__Vfinal,"start", &(TOP.start), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"write_data", &(TOP.write_data), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"ack_error", &(TOP.i2c_master__DOT__ack_error), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"active_addr", &(TOP.i2c_master__DOT__active_addr), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"active_reg", &(TOP.i2c_master__DOT__active_reg), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"active_rw", &(TOP.i2c_master__DOT__active_rw), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"busy", &(TOP.i2c_master__DOT__busy), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"clk", &(TOP.i2c_master__DOT__clk), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"done", &(TOP.i2c_master__DOT__done), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"memory", &(TOP.i2c_master__DOT__memory), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,1,1 ,0,255 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"pending_data", &(TOP.i2c_master__DOT__pending_data), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"read_data", &(TOP.i2c_master__DOT__read_data), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"reg_addr", &(TOP.i2c_master__DOT__reg_addr), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rst_n", &(TOP.i2c_master__DOT__rst_n), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rw", &(TOP.i2c_master__DOT__rw), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"scl", &(TOP.i2c_master__DOT__scl), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"scl_oe", &(TOP.i2c_master__DOT__scl_oe), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"sda", &(TOP.i2c_master__DOT__sda), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"sda_oe", &(TOP.i2c_master__DOT__sda_oe), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"slave_addr", &(TOP.i2c_master__DOT__slave_addr), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"start", &(TOP.i2c_master__DOT__start), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"state", &(TOP.i2c_master__DOT__state), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,2,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"write_data", &(TOP.i2c_master__DOT__write_data), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
    }
}
