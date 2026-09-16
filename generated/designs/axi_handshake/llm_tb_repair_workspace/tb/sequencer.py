"""UVM sequencer for the axi_handshake DUT.

Parameterised with AxiHandshakeTxn so that every sequence that starts
on this sequencer produces the correct transaction type.
"""

from pyuvm import uvm_sequencer

from transaction import AxiHandshakeTxn


class AxiHandshakeSequencer(uvm_sequencer):
    """Sequencer that feeds AxiHandshakeTxn items to the driver."""

    def __init__(self, name, parent):
        super().__init__(name, parent)
