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
        __Vscope_TOP.varInsert(__Vfinal,"rst_n", &(TOP.rst_n), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"rw", &(TOP.rw), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"rx_data", &(TOP.rx_data), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_TOP.varInsert(__Vfinal,"scl_in", &(TOP.scl_in), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"scl_oe", &(TOP.scl_oe), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"scl_out", &(TOP.scl_out), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"sda_in", &(TOP.sda_in), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"sda_oe", &(TOP.sda_oe), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"sda_out", &(TOP.sda_out), false, VLVT_UINT8,VLVD_OUT|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"slave_addr", &(TOP.slave_addr), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_TOP.varInsert(__Vfinal,"start", &(TOP.start), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,0);
        __Vscope_TOP.varInsert(__Vfinal,"tx_data", &(TOP.tx_data), false, VLVT_UINT8,VLVD_IN|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"CLK_DIV", const_cast<void*>(static_cast<const void*>(&(TOP.i2c_master__DOT__CLK_DIV))), true, VLVT_UINT32,VLVD_NODIR|VLVF_PUB_RW|VLVF_DPI_CLAY,0,1 ,31,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"ack_error", &(TOP.i2c_master__DOT__ack_error), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"bit_cnt", &(TOP.i2c_master__DOT__bit_cnt), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,3,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"busy", &(TOP.i2c_master__DOT__busy), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"clk", &(TOP.i2c_master__DOT__clk), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"div_cnt", &(TOP.i2c_master__DOT__div_cnt), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,1,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"done", &(TOP.i2c_master__DOT__done), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rst_n", &(TOP.i2c_master__DOT__rst_n), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rw", &(TOP.i2c_master__DOT__rw), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rx_data", &(TOP.i2c_master__DOT__rx_data), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"rx_shift", &(TOP.i2c_master__DOT__rx_shift), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"scl_in", &(TOP.i2c_master__DOT__scl_in), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"scl_oe", &(TOP.i2c_master__DOT__scl_oe), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"scl_out", &(TOP.i2c_master__DOT__scl_out), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"sda_in", &(TOP.i2c_master__DOT__sda_in), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"sda_oe", &(TOP.i2c_master__DOT__sda_oe), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"sda_out", &(TOP.i2c_master__DOT__sda_out), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"shift_reg", &(TOP.i2c_master__DOT__shift_reg), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"slave_addr", &(TOP.i2c_master__DOT__slave_addr), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,6,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"start", &(TOP.i2c_master__DOT__start), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"state", &(TOP.i2c_master__DOT__state), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,3,0);
        __Vscope_i2c_master.varInsert(__Vfinal,"tx_data", &(TOP.i2c_master__DOT__tx_data), false, VLVT_UINT8,VLVD_NODIR|VLVF_PUB_RW,0,1 ,7,0);
    }
}
