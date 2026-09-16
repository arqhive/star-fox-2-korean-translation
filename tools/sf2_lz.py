"""Star Fox 2 GSU LZ decompression via the ROM's own routine ($01:D9FF)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gsu_emu import GSU

def decompress(rom, bank, end_addr, dst=0x3B50):
    cpu = GSU(rom)
    cpu.ram[0x6A] = bank; cpu.ram[0x6B] = 0
    cpu.ram[0x68] = end_addr & 0xFF; cpu.ram[0x69] = end_addr >> 8
    cpu.ram[0x2C] = dst & 0xFF; cpu.ram[0x2D] = dst >> 8
    cpu.ram[0xA2] = 0; cpu.ram[0xA3] = 0
    cpu.r[10] = 0x04F0
    cpu.call(0x01, 0xD9FF)
    size = int.from_bytes(cpu.ram[0x60:0x62], 'little') - dst
    start = int.from_bytes(cpu.ram[0x68:0x6A], 'little')
    return bytes(cpu.ram[dst:dst + size]), start, cpu.steps

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    b = int(sys.argv[2], 16); a = int(sys.argv[3], 16)
    data, start, steps = decompress(rom, b, a)
    print('size %X start %02X:%04X steps %d' % (len(data), b, start, steps))
    if len(sys.argv) > 4: open(sys.argv[4], 'wb').write(data)
