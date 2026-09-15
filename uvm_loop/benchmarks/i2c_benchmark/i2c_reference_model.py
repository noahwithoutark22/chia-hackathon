"""Reference model for the I2C benchmark.

The model describes the intended transaction-level behavior independently
of the candidate RTL implementation.
"""

from dataclasses import dataclass, field


@dataclass
class I2CReferenceModel:
    supported_slave: int = 0x50
    memory: dict[int, int] = field(default_factory=dict)

    def reset(self) -> None:
        self.memory.clear()

    def transact(
        self,
        rw: int,
        slave_addr: int,
        reg_addr: int,
        write_data: int = 0,
    ) -> dict:
        """Execute one abstract I2C transaction.

        rw=0 performs a one-byte write.
        rw=1 performs a one-byte read.
        """
        if not 0 <= slave_addr <= 0x7F:
            raise ValueError("slave_addr must be 7-bit")
        if not 0 <= reg_addr <= 0xFF:
            raise ValueError("reg_addr must be 8-bit")
        if not 0 <= write_data <= 0xFF:
            raise ValueError("write_data must be 8-bit")
        if rw not in (0, 1):
            raise ValueError("rw must be 0 or 1")

        if slave_addr != self.supported_slave:
            return {
                "done": 1,
                "busy_after": 0,
                "ack_error": 1,
                "read_data": 0,
            }

        if rw == 0:
            self.memory[reg_addr] = write_data
            return {
                "done": 1,
                "busy_after": 0,
                "ack_error": 0,
                "read_data": 0,
            }

        return {
            "done": 1,
            "busy_after": 0,
            "ack_error": 0,
            "read_data": self.memory.get(reg_addr, 0),
        }
