"""PyUVM sequencer for the parameterized adder DUT.

This sequencer is a thin ``uvm_sequencer`` subclass that arbitrates
among sequences producing ``AdderTransaction`` items.  It contains no
additional logic beyond what ``uvm_sequencer`` provides out of the box.

The sequencer is instantiated once inside the adder agent (see later
stages) and sits between the running sequence and the driver.
"""

from pyuvm import uvm_sequencer
from adder_transaction import AdderTransaction


class AdderSequencer(uvm_sequencer):
    """Sequencer that forwards ``AdderTransaction`` items to the driver.

    Parameters
    ----------
    name : str
        Instance name (default ``"adder_sequencer"``).
    parent : uvm_component
        Parent component, typically the agent.
    """

    def __init__(self, name="adder_sequencer", parent=None):
        super().__init__(name, parent)
