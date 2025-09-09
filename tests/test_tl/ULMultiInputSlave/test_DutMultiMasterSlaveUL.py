import cocotb # type: ignore
from cocotb.clock import Clock # type: ignore
from cocotb.handle import SimHandleBase # type: ignore
from cocotb.triggers import ClockCycles, RisingEdge, ReadOnly, Timer, Combine # type: ignore

from cocotb_TileLink.drivers.DutMultiMasterSlaveUL import DutMultiMasterSlaveUL
from cocotb_TileLink.drivers.SimTrafficGeneratorUL import SimTrafficGeneratorUL

from cocotb_TileLink.monitors.TileLinkULMonitor import TileLinkULMonitor

CLK_PERIOD = (10, "ns")

async def setup_dut(dut: SimHandleBase) -> None:
    cocotb.start_soon(Clock(dut.clk, *CLK_PERIOD).start())
    dut.rstn.value = 0
    await ClockCycles(dut.clk, 100)
    dut.rstn.value = 1
    await ClockCycles(dut.clk, 10)


@cocotb.test() # type: ignore
async def test_MultiMasterSlave(dut: SimHandleBase) -> None:
    TLSlave = DutMultiMasterSlaveUL(dut, max_masters_count=2)

    master1 = SimTrafficGeneratorUL(name="first").register_clock(dut.clk).register_reset(dut.rstn, True)
    master1.register_slave(TLSlave.get_slave_interface(bus_name="first"))
    TLSlave.register_master(master1.get_master_interface(), bus_name="first")

    TLmonitor1 = TileLinkULMonitor(name="first").register_clock(dut.clk).register_reset(dut.rstn, True)
    TLmonitor1.register_device(master1)
    cocotb.start_soon(TLmonitor1.process())

    master2 = SimTrafficGeneratorUL(name="second").register_clock(dut.clk).register_reset(dut.rstn, True)
    master2.register_slave(TLSlave.get_slave_interface(bus_name="second"))
    TLSlave.register_master(master2.get_master_interface(), bus_name="second")

    TLmonitor2 = TileLinkULMonitor(name="second").register_clock(dut.clk).register_reset(dut.rstn, True)
    TLmonitor2.register_device(master2)
    cocotb.start_soon(TLmonitor2.process())

    cocotb.start_soon(TLSlave.process())
    cocotb.start_soon(master1.process())
    cocotb.start_soon(master2.process())

    await setup_dut(dut)

    await master1.sim_finished()
    await master2.sim_finished()
