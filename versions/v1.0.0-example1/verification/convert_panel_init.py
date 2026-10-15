"""Convert the supplied 3-byte-header COE records to the Anlogic demo ROM.

Run from any directory. No register values are invented or changed.
The matching controller uses opcodes 1=long, 2=short+param,
3=short without param, 4=32-bit cycle delay, 5=end, at 10 MHz.
"""
from pathlib import Path
import re
import json

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / 'user_source/ip_source/w8_d1024_rom'

def convert(text):
    tokens = text.split('memory_initialization_vector=', 1)[1].split(';', 1)[0].split()
    data = [int(t, 16) for t in tokens]
    rom, packets = [], []
    pos = 0
    while pos < len(data):
        dt, delay, size = data[pos:pos+3]
        payload = data[pos+3:pos+3+size]
        assert len(payload) == size
        if dt == 0x15:
            assert size == 2
            rom += [2] + payload
        elif dt == 0x39:
            assert 0 < size < 256
            rom += [1, size] + payload
        elif dt == 0x05:
            assert size == 1
            rom += [3] + payload
        else:
            raise ValueError(f'Unsupported packet {dt:#x}')
        if delay:
            rom += [4] + list((delay * 10000).to_bytes(4, 'big'))
        packets.append((dt, payload, delay))
        pos += 3 + size
    assert pos == len(data) and len(rom) < 1024
    return rom + [5], packets

def decode(rom):
    """Independent round-trip check of the controller's instruction encoding."""
    packets = []
    pos = 0
    while rom[pos] != 5:
        op = rom[pos]
        if op == 1:
            n = rom[pos+1]
            packets.append((0x39, rom[pos+2:pos+2+n], 0))
            pos += 2+n
        elif op in (2, 3):
            n = 2 if op == 2 else 1
            packets.append((0x15 if op == 2 else 0x05, rom[pos+1:pos+1+n], 0))
            pos += 1+n
        elif op == 4:
            dt, payload, delay = packets.pop()
            cycles = int.from_bytes(bytes(rom[pos+1:pos+5]), 'big')
            assert delay == 0 and cycles % 10000 == 0
            packets.append((dt, payload, cycles // 10000))
            pos += 5
        else:
            raise ValueError(f'Unsupported opcode {op}')
    return packets

if __name__ == '__main__':
    rom, packets = convert((ROM/'7inch_init_sequence.coe').read_text())
    assert decode(rom) == packets
    active = [int(s, 2) for s in (ROM/'config_data_panel7.mif.dat').read_text().split()]
    assert active == rom + [0]*(1024-len(rom))
    sleep = [i for i,p in enumerate(packets) if p[:2] == (0x05,[0x11])]
    display = [i for i,p in enumerate(packets) if p[:2] == (0x05,[0x29])]
    assert len(sleep) == len(display) == 1 and sleep[0] < display[0]
    assert packets[sleep[0]][2] == 120 and packets[display[0]][2] == 32
    print(f'PASS: {len(packets)} exact COE packets, {len(rom)} ROM bytes, all parameters and delays preserved.')
