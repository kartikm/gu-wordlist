# Minimal Hunspell emulator for SFX-only .aff files (no PFX/compounding).
import sys, re, unicodedata
def expand(w, flags, rules, words, depth):
    for f in flags:
        for strip, add, cond, cont in rules.get(f, []):
            if cond and not cond.search(w): continue
            if strip and not w.endswith(strip): continue
            nw = (w[:-len(strip)] if strip else w) + add
            words.add(nw)
            if cont and depth == 0: expand(nw, cont, rules, words, 1)

def load(aff, dic):
    rules = {}
    for line in open(aff, encoding='utf-8'):
        p = line.split()
        if len(p) >= 5 and p[0] == 'SFX':
            strip = '' if p[2] == '0' else p[2]
            add, _, cont = ('' if p[3] == '0' else p[3]).partition('/')
            if p[3].startswith('0/'): add, cont = '', p[3][2:]
            cond = p[4]
            rules.setdefault(p[1], []).append((strip, add, re.compile('(' + cond + ')$') if cond != '.' else None, cont))
    words = set()
    lines = open(dic, encoding='utf-8').read().splitlines()[1:]
    for l in lines:
        if not l.strip(): continue
        w, _, flags = l.partition('/')
        words.add(w)
        expand(w, flags.strip(), rules, words, 0)
    return words
if __name__ == '__main__':
    aff, dic, txt = sys.argv[1:4]
    words = load(aff, dic)
    text = open(txt, encoding='utf-8').read()
    toks = re.findall(r'[઀-૿]+', text)
    bad = []
    for t in toks:
        if re.fullmatch(r'[૦-૯]+', t): continue
        if t not in words and t not in bad: bad.append(t)
    print(len(set(toks)), 'unique tokens;', len(bad), 'unknown')
    print('\n'.join(bad))
