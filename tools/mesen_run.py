"""Run Mesen test runner and extract SHOT lines into PNG files."""
import subprocess, sys, os, binascii
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(script, rom, outdir, timeout=600):
    os.makedirs(outdir, exist_ok=True)
    p = subprocess.run([os.path.join(ROOT, 'Mesen.exe'), '--testrunner', script, rom], capture_output=True, timeout=timeout, cwd=ROOT)
    log = []
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if line.startswith('SHOT '):
            _, tag, hx = line.split(' ', 2)
            open(os.path.join(outdir, 'shot_%s.png' % tag), 'wb').write(binascii.unhexlify(hx.strip()))
        elif 'Uninitialized' not in line:
            log.append(line)
    return p.returncode, log
if __name__ == '__main__':
    rc, log = run(sys.argv[1], sys.argv[2], sys.argv[3])
    print('rc', rc); print('\n'.join(log[-40:]))
