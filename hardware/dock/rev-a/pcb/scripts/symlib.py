"""Tiny KiCad .kicad_sym reader: get a symbol block (with extends resolved) and its pins."""
import re
L='/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/'
def sexp_block(s,start):
    d=0;i=start
    while True:
        c=s[i]
        if c=='"':
            i+=1
            while s[i]!='"':
                if s[i]=='\\': i+=1
                i+=1
        elif c=='(': d+=1
        elif c==')':
            d-=1
            if d==0: return s[start:i+1]
        i+=1
_cache={}
def libtext(lib):
    if lib not in _cache: _cache[lib]=open(L+lib+'.kicad_sym').read()
    return _cache[lib]
def get(lib,name,path=None):
    s=open(path).read() if path else libtext(lib)
    m=re.search(r'\n\t\(symbol "%s"\n'%re.escape(name),s)
    blk=sexp_block(s,m.start()+2)
    e=re.search(r'\(extends "([^"]+)"\)',blk)
    if e:
        base=get(lib,e.group(1),path)
        # take base body, rename, override properties from derived
        b=base.replace(f'(symbol "{e.group(1)}"',f'(symbol "{name}"',1)
        b=re.sub(r'\(symbol "%s_(\d+_\d+)"'%re.escape(e.group(1)),lambda mm:f'(symbol "{name}_{mm.group(1)}"',b)
        def props(t):
            out={}
            for pm in re.finditer(r'\n(\t+)\(property "([^"]+)"',t):
                st=pm.start()+1+len(pm.group(1)); out[pm.group(2)]=(st,sexp_block(t,st))
            return out
        dp=props(blk)
        for k,(st,pb) in dp.items():
            bp=props(b)
            if k in bp:
                bst,bb=bp[k]; b=b[:bst]+pb+b[bst+len(bb):]
            else:
                i=b.index('(property'); b=b[:i]+pb+'\n\t\t'+b[i:]
        return b
    return blk
def pins(blk):
    out=[]
    for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length ([-\d.]+)\)[\s\S]*?\(name "([^"]*)"[\s\S]*?\(number "([^"]*)"',blk):
        t,g,x,y,a,l,n,num=m.groups()
        out.append(dict(type=t,x=float(x),y=float(y),a=float(a),name=n,num=num))
    return out
if __name__=='__main__':
    import sys
    for spec in sys.argv[1:]:
        lib,name=spec.split(':'); b=get(lib,name)
        print('==',spec,' '.join(f"{p['num']}:{p['name']}:{p['type']}" for p in pins(b)))
