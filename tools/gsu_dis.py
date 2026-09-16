import sys
def dis(d, base, start, count, fileoff):
    pc=start; alt=0; out=[]
    def rd(o): return d[fileoff+(o-base)]
    n=0
    while n<count:
        a=pc; op=rd(pc); pc+=1; s=None
        hi=op>>4; lo=op&15
        if op==0: s='STOP'
        elif op==1: s='NOP'
        elif op==2: s='CACHE'
        elif op==3: s='LSR'
        elif op==4: s='ROL'
        elif 5<=op<=0xF:
            e=rd(pc); pc+=1; e=e-256 if e>127 else e
            s='%s $%04X'%(['BRA','BGE','BLT','BNE','BEQ','BPL','BMI','BCC','BCS','BVC','BVS'][op-5],(pc+e)&0xffff)
        elif hi==1: s='TO R%d'%lo
        elif hi==2: s='WITH R%d'%lo
        elif hi==3:
            if lo<12: s=('STB' if alt&1 else 'STW')+' (R%d)'%lo
            elif lo==12: s='LOOP'
            elif lo==13: s='ALT1'; alt=1
            elif lo==14: s='ALT2'; alt=2
            else: s='ALT3'; alt=3
            if lo in (13,14,15): out.append('%04X %02X    %s'%(a,op,s)); n+=1; continue
        elif hi==4:
            if lo<12: s=('LDB' if alt&1 else 'LDW')+' (R%d)'%lo
            elif lo==12: s='RPIX' if alt&1 else 'PLOT'
            elif lo==13: s='SWAP'
            elif lo==14: s='CMODE' if alt&1 else 'COLOR'
            else: s='NOT'
        elif hi==5: s=['ADD R','ADC R','ADD #','ADC #'][alt]+str(lo)
        elif hi==6: s=['SUB R','SBC R','SUB #','CMP R'][alt]+str(lo)
        elif hi==7: s='MERGE' if lo==0 else ['AND R','BIC R','AND #','BIC #'][alt]+str(lo)
        elif hi==8: s=['MULT R','UMULT R','MULT #','UMULT #'][alt]+str(lo)
        elif hi==9:
            if lo==0: s='SBK'
            elif 1<=lo<=4: s='LINK #%d'%lo
            elif lo==5: s='SEX'
            elif lo==6: s='DIV2' if alt&1 else 'ASR'
            elif lo==7: s='ROR'
            elif 8<=lo<=13: s=('LJMP R%d' if alt&1 else 'JMP R%d')%lo
            elif lo==14: s='LOB'
            else: s='LMULT' if alt&1 else 'FMULT'
        elif hi==0xA:
            b=rd(pc); pc+=1
            if alt==0: s='IBT R%d,#$%02X'%(lo,b)
            elif alt==1: s='LMS R%d,($%03X)'%(lo,b*2)
            else: s='SMS R%d,($%03X)'%(lo,b*2)
        elif hi==0xB: s='FROM R%d'%lo
        elif hi==0xC: s='HIB' if lo==0 else ['OR R','XOR R','OR #','XOR #'][alt]+str(lo)
        elif hi==0xD:
            if lo<15: s='INC R%d'%lo
            else: s=['GETC','GETC','RAMB','ROMB'][alt]
        elif hi==0xE:
            if lo<15: s='DEC R%d'%lo
            else: s=['GETB','GETBH','GETBL','GETBS'][alt]
        elif hi==0xF:
            w=rd(pc)|rd(pc+1)<<8; pc+=2
            if alt==0: s='IWT R%d,#$%04X'%(lo,w)
            elif alt==1: s='LM R%d,($%04X)'%(lo,w)
            else: s='SM R%d,($%04X)'%(lo,w)
        alt=0
        out.append('%04X %-8s %s'%(a,' '.join('%02X'%rd(x) for x in range(a,pc)),s)); n+=1
    return out
def fold(lines):
    out=[];i=0
    while i<len(lines):
        l=lines[i]
        m=re.match(r'(\w{4}) (.{8}) WITH R(\d+)$',l)
        if m and i+1<len(lines):
            n=re.match(r'(\w{4}) (.{8}) (TO|FROM) R(\d+)$',lines[i+1])
            if n:
                if n.group(3)=='TO': out.append('%s %s MOVE R%s,R%s'%(m.group(1),'%-8s'%'2x',n.group(4),m.group(3)))
                else: out.append('%s %s MOVES R%s,R%s'%(m.group(1),'%-8s'%'2x',m.group(3),n.group(4)))
                i+=2; continue
        out.append(l); i+=1
    return out
import re
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    bank=int(sys.argv[2],16); addr=int(sys.argv[3],16); cnt=int(sys.argv[4])
    fo=bank*0x10000+0 if False else (bank&0x3f)*0x8000
    print('\n'.join(dis(d,0x8000,addr,cnt,(bank&0x3f)*0x8000)))
