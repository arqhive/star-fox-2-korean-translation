"""Run Mesen from a savestate with a Lua input snippet; collect SHOT/DECOMP/STATE output.

  python tools/state_run.py rom state.mss input.lua outdir [frames] [shot_every]
input.lua body can use: frame, press(tbl)  (called once per polled frame)
"""
import sys, os, subprocess, binascii
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = r'''
local hex = "%(hex)s"
local st = (hex:gsub("..", function(cc) return string.char(tonumber(cc, 16)) end))
local frame=0
local loaded=false
local saveReq=nil
local seen={}
local function rw(a) return emu.read(a, emu.memType.gsuWorkRam) | (emu.read(a+1, emu.memType.gsuWorkRam)<<8) end
local function hexs(s) return (s:gsub(".", function(c) return string.format("%%02x", string.byte(c)) end)) end
emu.addMemoryCallback(function(addr, value)
  local key=string.format("%%02X:%%04X", rw(0x6A)&0xff, rw(0x68))
  if not seen[key] then seen[key]=true; print(string.format("F%%d DECOMP %%s", frame, key)) end
end, emu.callbackType.exec, 0x01D9FF, 0x01D9FF, emu.cpuType.gsu, emu.memType.gsuMemory)
emu.addMemoryCallback(function(addr, value)
  if not loaded then loaded=true; emu.loadSavestate(st) end
  if saveReq then print("STATE "..saveReq.." "..hexs(emu.createSavestate())); saveReq=nil end
end, emu.callbackType.exec, 0x000000, 0xFFFFFF, emu.cpuType.snes, emu.memType.snesMemory)
local function press(t) emu.setInput(t, 0) end
local function shot(tag) print("SHOT "..tag.." "..hexs(emu.takeScreenshot())) end
local function savestate(tag) saveReq=tag end
emu.addEventCallback(function()
  if not loaded then return end
  frame=frame+1
%(body)s
  if frame %% %(every)d == 0 then shot(string.format("%%05d", frame)) end
  if frame >= %(frames)d then emu.stop(0) end
end, emu.eventType.inputPolled)
'''
def run(rom, state, body, outdir, frames=1200, every=60):
    os.makedirs(outdir, exist_ok=True)
    lua = TEMPLATE % {'hex': open(state, 'rb').read().hex(), 'body': body, 'frames': frames, 'every': every}
    lp = os.path.join(outdir, '_run.lua'); open(lp, 'w').write(lua)
    p = subprocess.run([os.path.join(ROOT, 'Mesen.exe'), '--testrunner', lp, rom], capture_output=True, timeout=1800, cwd=ROOT)
    log = []
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if line.startswith('SHOT '):
            _, tag, hx = line.split(' ', 2)
            open(os.path.join(outdir, 'shot_%s.png' % tag), 'wb').write(binascii.unhexlify(hx))
        elif line.startswith('STATE '):
            _, tag, hx = line.split(' ', 2)
            open(os.path.join(outdir, '%s.mss' % tag), 'wb').write(binascii.unhexlify(hx))
            log.append('saved state ' + tag)
        elif 'Uninitialized' not in line:
            log.append(line)
    return log
def grid(outdir, cols=6, scale=0.5):
    from PIL import Image; import glob
    fs = sorted(glob.glob(os.path.join(outdir, 'shot_*.png')))
    w, h = int(256 * scale), int(224 * scale)
    c = Image.new('RGB', (cols * w, ((len(fs) + cols - 1) // cols) * h))
    for i, f in enumerate(fs):
        c.paste(Image.open(f).resize((w, h)), ((i % cols) * w, (i // cols) * h))
    c.save(os.path.join(outdir, 'grid.png'))
    return len(fs)
if __name__ == '__main__':
    rom, state, body_file, outdir = sys.argv[1:5]
    frames = int(sys.argv[5]) if len(sys.argv) > 5 else 1200
    every = int(sys.argv[6]) if len(sys.argv) > 6 else 60
    for l in run(rom, state, open(body_file).read(), outdir, frames, every): print(l)
    print('shots', grid(outdir))
