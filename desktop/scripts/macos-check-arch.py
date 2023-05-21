#!/usr/bin/env python3

import os, subprocess, sys

def main(argv):
    if len(argv) != 2:
        print("Usage: check-arch.py PATH_TO_APP", file = sys.stderr)
        sys.exit(-1)
    universal = []
    silicon = []
    intel = []
    for d in os.walk(argv[1]):
        ap = os.path.join(os.path.abspath('.'),d[0])
        for f in os.listdir(ap):
            fl = os.path.join(ap,f)
            if os.path.isfile(fl):
                a = subprocess.run(['file',fl], stdout = subprocess.PIPE)
                b = a.stdout.decode('utf-8')
                if 'binary' in b or 'executable' in b or 'library' in b:
                    arm64, x86 = False, False
                    if 'arm64' in b:
                        arm64 = True
                    if 'x86_64' in b:
                        x86 = True
                    if arm64 and x86:
                        universal += [fl]
                    elif arm64:
                        silicon += [fl]
                    elif x86:
                        intel += [fl]
    with open('macos-check-arch.log', 'w') as fout:
        fout.write('-*- Universal -*-\n')
        for p in universal:
            fout.write(p+'\n')
        fout.write('\n-*- Silicon -*-\n')
        for p in silicon:
            fout.write(p+'\n')
        fout.write('\n-*- Intel -*-\n')
        for p in intel:
            fout.write(p+'\n')

if __name__ == '__main__':
    main(sys.argv)
