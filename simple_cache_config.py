from m5.objects import *
import m5

# Define a custom L1 Cache class
class L1Cache(Cache):
    def __init__(self, size='32kB', assoc=2):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = 2
        self.data_latency = 2
        self.response_latency = 2
        self.mshrs = 4
        self.tgts_per_mshr = 20

    def connectCPU(self, cpu, is_icache=True):
        if is_icache:
            self.cpu_side = cpu.icache_port
        else:
            self.cpu_side = cpu.dcache_port

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports

# Define a custom L2 Cache class
class L2Cache(Cache):
    def __init__(self, size='256kB', assoc=8):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = 20
        self.data_latency = 20
        self.response_latency = 20
        self.mshrs = 16
        self.tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

# Create the system
system = System()
system.clk_domain = SrcClockDomain(clock='1GHz', voltage_domain=VoltageDomain())
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

# Create CPU and add TLBs for virtual memory simulation
system.cpu = TimingSimpleCPU()
system.cpu.itb = X86TLB(entry_type="instruction")
system.cpu.dtb = X86TLB(entry_type="data")

# Create system buses
system.l2bus = SystemXBar()
system.membus = SystemXBar()

# Create and connect L1 caches
system.cpu.icache = L1Cache(size='32kB', assoc=2)
system.cpu.dcache = L1Cache(size='32kB', assoc=2)
system.cpu.icache.connectCPU(system.cpu, is_icache=True)
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectCPU(system.cpu, is_icache=False)
system.cpu.dcache.connectBus(system.l2bus)

# Create and connect L2 cache
system.l2cache = L2Cache(size='256kB', assoc=8)
system.l2cache.connectCPUSideBus(system.l2bus)
system.l2cache.connectMemSideBus(system.membus)

# Create simple memory
system.mem_ctrl = SimpleMemory()
system.mem_ctrl.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Setup interrupt controller properly
system.cpu.createInterruptController()

# Connect all required interrupt ports on index [0]
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_master = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_slave = system.membus.mem_side_ports

# Load your local hello binary
binary = 'hello'
system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

# Create root and run
root = Root(full_system=False, system=system)
m5.instantiate()

print("Starting simulation...")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
