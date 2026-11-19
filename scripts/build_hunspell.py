#!/usr/bin/env python3
"""Build gu_IN.aff / gu_IN.dic from kartikm/gu-wordlist.

Usage:
    python3 scripts/build_hunspell.py [--no-wiki] gu-wordlist.txt wikipedia-frequency.tsv .

wikipedia-frequency.tsv (word<TAB>count) is produced by
scripts/count_wiki_frequencies.py from a Gujarati Wikipedia dump.

* Every correct word of gu-wordlist.txt stays accepted (checked at the end).
  Mechanically generated wrong forms (case marker on the -ું / singular -ો
  form, missing anusvara) are dropped unless Wikipedia uses them 5+ times.
* Paradigm flags (see gu_IN.aff): verbs (V, W) from every infinitive; nouns
  get the full paradigm with plurals (N, O, U) only when Wikipedia attests an
  inflected form; every other noun-like word gets case markers only (K).
* Wikipedia words are added when seen 3+ times, are the most frequent of their
  spelling variants, and no variant is already accepted. This keeps common
  misspellings such as સક્રીય, બ્રિટીશ, નિમણૂંક flagged. --no-wiki skips this.
* Explicit inflected forms that the flags regenerate are removed.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))

CONS = 'કખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલળવશષસહ'
VOWEL_END = 'ાિીુૂૃે'          # vowel signs after which plural is -ઓ
CASE = ['નો', 'ની', 'નું', 'ના', 'નાં', 'ને', 'થી', 'માં', 'માંથી', 'માંનો', 'માંની', 'માંનું', 'માંના', 'નેય', 'માંય']
C_ = f'[{CONS}]'
V_ = f'[{VOWEL_END}]'

def sfx(flag, rows, cross='Y'):
    out = [f'SFX {flag} {cross} {len(rows)}']
    out += [f'SFX {flag} {s or "0"} {a} {c}' for s, a, c in rows]
    return out

AFF = []
AFF += ['SET UTF-8',
        'TRY ાર્ંવનકુીતોમિસલેયદપગડટજબણચઅળશહધૂભખથષફઆછઠઘઉઝઈઓૃઇઢએૈઊૉઞૅૌઍઃઋઑઔઐઙ઼ઁ',
        '', 'REP 18']
for a, b in [('િ', 'ી'), ('ુ', 'ૂ'), ('ો', 'ૌ'), ('શ', 'ષ'), ('સ', 'શ'), ('ન', 'ણ'),
             ('ૃ', 'ૄ'), ('ર્', 'ૃ'), ('ળ', 'લ')]:
    AFF += [f'REP {a} {b}', f'REP {b} {a}']
AFF += ['',
        '# ---- Nouns ---------------------------------------------------------',
        '# C = case markers / ergative, applied to stems and (via /C) plurals',]
AFF += sfx('C', [('', m, '.') for m in CASE] + [('', 'એ', '.')])
AFF += ['', '# N = noun ending in consonant or vowel sign (ઘર, પુત્ર, પિતા, ક્રાંતિકારી)',
        '#     case markers, ergative/locative -એ/-ે, plural -ો/-ઓ (+ case on plural)']
rows = [('', m, '.') for m in CASE]
rows += [('', 'ે', C_), ('', 'એ', V_), ('', 'ો/C', C_), ('', 'ઓ/C', V_)]
AFF += sfx('N', rows)
AFF += ['', '# K = any other noun-like word (names, loanwords): case markers and -એ/-ે only, no plural']
rows = [('', m, f'[{CONS}ાિીુૂૃો]') for m in CASE] + [('', 'ે', C_), ('', 'એ', '[ાિીુૂો]')]
AFF += sfx('K', rows)
AFF += ['', '# O = masculine -ો nouns/adjectives (રસ્તો, છોકરો, પુરાવો): oblique -ા, plural -ાઓ, locative -ે']
rows = [('ો', 'ા', 'ો'), ('ો', 'ે', 'ો'), ('ો', 'ાએ', 'ો'), ('ો', 'ાઓ/C', 'ો')]
rows += [('ો', 'ા' + m, 'ો') for m in CASE]
AFF += sfx('O', rows)
AFF += ['', '# U = neuter -ું nouns/adjectives (અથાણું, છોકરું): -ા, plural -ાં, locative -ે']
rows = [('ું', 'ા', 'ું'), ('ું', 'ાં', 'ું'), ('ું', 'ે', 'ું'), ('ું', 'ાએ', 'ું'), ('ું', 'ાંઓ/C', 'ું')]
rows += [('ું', 'ા' + m, 'ું') for m in CASE]
AFF += sfx('U', rows)

# ---- Verbs ----
VCONS = ['ું', 'ે', 'ો', 'ીએ', 'ત', 'જે', 'જો',                       # present / imperative
         '્યો', '્યા', '્યું', '્યાં', 'ી', 'ીને', 'ીનેય',             # past, conjunctive
         'ીશ', 'ીશું', 'શે', 'શો',                                    # future
         'તો', 'તી', 'તું', 'તા', 'તાં',                              # present participle
         'ેલ', 'ેલો', 'ેલી', 'ેલું', 'ેલા', 'ેલાં', 'ેલાઓ',           # perfect participle
         'વું', 'વો', 'વી', 'વા', 'વાં', 'વાનો', 'વાની', 'વાનું', 'વાના', 'વાનાં',
         'વાને', 'વાથી', 'વામાં', 'વાય', 'વાયો', 'વાયા', 'વાયું', 'વાઈ', 'વાશે',   # infinitive, passive
         'નાર', 'નારો', 'નારી', 'નારું', 'નારા', 'નારાઓ', 'નારાં',  # agentive
         'ાય', 'ાયો', 'ાયા', 'ાયું', 'ાયેલ', 'ાયેલો', 'ાયેલી', 'ાયેલું', 'ાયેલા', 'ાઈ', 'ાશે', 'ાતો', 'ાતી', 'ાતું', 'ાતા']
VAA = ['ઉં', 'ય', 'ઓ', 'ઈએ', 'ત', 'જે', 'જો',
       'યો', 'યા', 'યું', 'યાં', 'ઈ', 'ઈને',
       'ઈશ', 'ઈશું', 'શે', 'શો',
       'તો', 'તી', 'તું', 'તા', 'તાં',
       'યેલ', 'યેલો', 'યેલી', 'યેલું', 'યેલા', 'યેલાં',
       'વું', 'વો', 'વી', 'વા', 'વાં', 'વાનો', 'વાની', 'વાનું', 'વાના', 'વાનાં', 'વાને', 'વાથી', 'વામાં', 'વાય',
       'નાર', 'નારો', 'નારી', 'નારું', 'નારા', 'નારાઓ']
AFF += ['', '# ---- Verbs (root = infinitive minus -વું) ---------------------------',
        '# V = consonant-final root (કર, બનાવ, પડ, ઉતર): કરે, કર્યો, કરી, કરશે, કરતો, કરેલું, કરવાનું, કરાય...']
AFF += sfx('V', [('', s, C_) for s in VCONS])
AFF += ['', '# W = -ા root (જોડા, ગભરા, શરમા): જોડાય, જોડાયો, જોડાઈ, જોડાશે, જોડાયેલું...']
AFF += sfx('W', [('', s, 'ા') for s in VAA])
AFF_TEXT = '\n'.join(AFF) + '\n'

IRREGULAR_ROOTS = {'જ', 'થ', 'હ', 'લ', 'દ', 'ખા', 'પા', 'ના', 'ગા'}  # જવું, થવું, હોવું ... handled by explicit forms


WITH_WIKI = True
WIKI_MIN_FREQ = 3        # a Wikipedia-only word must occur at least this often
ATTEST_MIN_FREQ = 2      # an inflected form counts as evidence from this frequency
KEEP_JUNK_FREQ = 5       # a suspicious base form survives if Wikipedia really uses it
VALID = re.compile('[અ-ઔક-હળ][઀-૿]*[^્ઃ]')

# Sign sequences that cannot occur in correctly encoded Gujarati: two vowel
# signs in a row (કાર્યાેત્તર), a sign after a virama (ટે્રઇન, વચ્ચ્ે), a vowel
# sign after anusvara (આવતંું), a virama after a vowel sign, a doubled anusvara.
# Mostly left over from converting old non-Unicode fonts.
_M, _V, _A = '\u0ABE-\u0ACC\u0AE2\u0AE3', '\u0ACD', '\u0A81-\u0A83'
MALFORMED = re.compile(f'[{_M}][{_M}]|{_V}[{_M}{_A}{_V}]|[{_A}][{_M}{_V}]|[{_M}]{_V}|\u0A82\u0A82')
MALFORMED_OK = {'રૂા'}   # standard abbreviation of રૂપિયા


def malformed(w):
    return w not in MALFORMED_OK and bool(MALFORMED.search(w))


STRICT = [('ઈ', 'ઇ'), ('ઊ', 'ઉ'), ('ી', 'િ'), ('ૂ', 'ુ'), ('ં', ''), ('ઁ', ''),
          ('્રૃ', 'ૃ'), ('ૌ', 'ો'), ('ૈ', 'ે')]
LOOSE = [('ર્', ''), ('ષ', 'શ'), ('ણ', 'ન'), ('ળ', 'લ'), ('્', '')]


def norm(w, loose=False):
    """Collapse common Gujarati spelling confusions. STRICT pairs (long/short
    vowels, anusvara) almost never separate two real words; LOOSE ones (repha,
    virama, ષ/શ, ણ/ન, ળ/લ) sometimes do (લોર્ડ/લોડ), so they only decide
    between two spellings by frequency."""
    for a, b in STRICT + (LOOSE if loose else []):
        w = w.replace(a, b)
    return w


def split_case(w):
    for m in sorted(CASE, key=len, reverse=True):
        if w.endswith(m) and len(w) > len(m) + 1:
            return w[:-len(m)], m
    return None, None


# Words that do not change form before a case marker, so e.g. આસોના, નેવુંની
# are correct, and real words that merely end in -નુ.
INVARIANT = {'આસો', 'સલોકો'}
NOT_MISSING_ANUSVARA = {'છન્નુ', 'સૂનુ', 'કાનુ', 'સોનુ'}


def junk_reason(w, known, freq):
    """Mechanically generated wrong forms found in gu-wordlist.txt."""
    st, m = split_case(w)
    if st and freq.get(w, 0) < KEEP_JUNK_FREQ and st not in INVARIANT:
        if st.endswith('ું') and not (st.endswith('ાણું') or st == 'નેવું'):   # numerals 90-99 are invariant
            return 'case on -ું form'                          # કરવુંના, અથાણુંનો -> કરવાના, અથાણાનો
        obl = st[:-1] + 'ા'
        if (st.endswith('ો') and st in known and st[:-1] not in known
                and (obl in known or any(obl + c in known for c in CASE))):
            return 'case on -ો form'                           # આખોમાં -> આખામાં (but પુત્રોના is a plural)
    if (w.endswith('નુ') and w not in NOT_MISSING_ANUSVARA and w[:-2] + 'નું' in known
            and (freq.get(w[:-2] + 'નું', 0) > freq.get(w, 0)
                 or freq.get(w, 0) == freq.get(w[:-2] + 'નું', 0) == 0)):
        return 'missing anusvara'                              # ઘરનુ -> ઘરનું, but ભાનુ, તનુ stay
    return None


def noun_attested(w, seen):
    if w[-1] not in CONS and w[-1] not in VOWEL_END:
        return False
    pl = w + ('ો' if w[-1] in CONS else 'ઓ')
    erg = w + ('ે' if w[-1] in CONS else 'એ')
    return (any(w + m in seen for m in CASE) or pl in seen or erg in seen
            or any(pl + m in seen for m in CASE))


def takes_case(w, accepted):
    """K flag: noun-like entry that is not itself already an inflected form."""
    if len(w) < 2:
        return False
    if w[-1] == 'ો':                 # વીડિયો, રેડિયો take markers directly; રસ્તો (-> રસ્તા) does not
        if w[:-1] + 'ા' in accepted:
            return False
    elif w[-1] not in CONS and w[-1] not in 'ાિીુૂૃ':
        return False
    st, _ = split_case(w)
    return not (st and st in accepted)


def expand(aff, out_dir, entries):
    from hspell import load
    tmp = os.path.join(out_dir, '_tmp.dic')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(f'{len(entries)}\n' + ''.join(f'{w}/{fl}\n' if fl else f'{w}\n' for w, fl in entries.items()))
    words = load(aff, tmp)
    os.remove(tmp)
    return words


def main(base_path, freq_path, out_dir):
    from hspell import load
    rej_path = os.path.join(os.path.dirname(os.path.abspath(base_path)), 'rejected-words.txt')
    rejected = set()
    if os.path.exists(rej_path):
        rejected = {l.strip() for l in open(rej_path, encoding='utf-8')
                    if l.strip() and not l.startswith('#')}
    freq = {}
    for l in open(freq_path, encoding='utf-8'):
        w, _, n = l.rstrip('\n').partition('\t')
        freq[w] = int(n or 0)
    raw = [l.strip() for l in open(base_path, encoding='utf-8') if l.strip() and l.strip() not in rejected]
    raw_set = set(raw)
    junk = {w: r for w in raw if (r := junk_reason(w, raw_set, freq))}
    base = [w for w in raw if w not in junk]
    base_set = set(base)
    seen = base_set | {w for w, n in freq.items() if n >= ATTEST_MIN_FREQ}
    flags = {}

    def add(stem, f):
        flags.setdefault(stem, set()).add(f)

    for w in base:                                   # verbs from infinitives
        if w.endswith('વું') and len(w) > 3:
            r = w[:-3]
            if r in IRREGULAR_ROOTS:
                continue
            if r[-1] in CONS:
                add(r, 'V')
            elif r.endswith('ા'):
                add(r, 'W')
    for w in base:                                   # nouns with attested inflection
        if w.endswith('ો') and len(w) > 2:
            st = w[:-1] + 'ા'
            if any(st + m in seen for m in CASE) or st + 'ઓ' in seen:
                add(w, 'O')
        elif w.endswith('ું') and len(w) > 3:
            st = w[:-2] + 'ા'
            if any(st + m in seen for m in CASE) or w[:-2] + 'ાં' in seen:
                add(w, 'U')
        elif noun_attested(w, seen):
            add(w, 'N')

    os.makedirs(out_dir, exist_ok=True)
    aff = os.path.join(out_dir, 'gu_IN.aff')
    open(aff, 'w', encoding='utf-8').write(AFF_TEXT)
    generated = expand(aff, out_dir, {s: ''.join(sorted(f)) for s, f in flags.items()})
    accepted = generated | base_set

    # Wikipedia words: keep a word only if it is the most frequent spelling among
    # its spelling variants and no variant is already accepted.
    wiki_added = []
    if WITH_WIKI:
        acc_norm = {norm(w) for w in accepted}
        cand = [w for w, n in freq.items() if n >= WIKI_MIN_FREQ and w not in accepted
                and VALID.fullmatch(w) and len(w) <= 25 and not malformed(w) and w not in rejected
                and not junk_reason(w, accepted, freq)]
        cand = [w for w in cand if norm(w) not in acc_norm]
        # most frequent spelling per loose key, counting accepted words too
        top = {}
        for w in list(accepted & freq.keys()) + cand:
            k = norm(w, loose=True)
            top[k] = max(top.get(k, 0), freq.get(w, 0))
        best = {}
        for w in cand:
            k = norm(w, loose=True)
            if freq[w] < top[k]:
                continue
            k1 = norm(w)
            if k1 not in best or freq[w] > freq[best[k1]]:
                best[k1] = w
        wiki_added = sorted(best.values())
        print(f'wikipedia candidates {len(cand)}, added {len(wiki_added)}')

    # Entries: flagged stems, unflagged base words, Wikipedia words. Every noun-like
    # entry without a noun paradigm gets K (case markers only, no plural).
    entries = {s: set(f) for s, f in flags.items()}
    for w in base + wiki_added:
        if w not in entries and w not in generated:
            entries[w] = set()
    for w in wiki_added:
        if w in entries and noun_attested(w, seen):
            entries[w].add('N')
    all_words = accepted | set(wiki_added)
    for w, f in entries.items():
        if not f & {'N', 'O', 'U'} and takes_case(w, all_words):
            f.add('K')
    final_entries = {w: ''.join(sorted(f)) for w, f in entries.items()}
    gen_all = expand(aff, out_dir, {w: f for w, f in final_entries.items() if f})
    # drop explicit entries that the flags now generate
    final_entries = {w: f for w, f in final_entries.items() if f or w not in gen_all}

    order = [w for w in base if w in final_entries]
    order += sorted(set(final_entries) - set(order))
    dic = os.path.join(out_dir, 'gu_IN.dic')
    with open(dic, 'w', encoding='utf-8') as f:
        f.write(f'{len(order)}\n')
        for w in order:
            f.write(f'{w}/{final_entries[w]}\n' if final_entries[w] else f'{w}\n')

    final = load(aff, dic)
    lost = [w for w in base if w not in final]
    still_junk = [w for w in junk if w in final]
    by = {}
    for r in junk.values():
        by[r] = by.get(r, 0) + 1
    cnt = lambda c: sum(c in f for f in final_entries.values())
    print(f'entries {len(order)}; N {cnt("N")} O {cnt("O")} U {cnt("U")} V {cnt("V")} W {cnt("W")} K {cnt("K")}')
    print(f'junk removed from gu-wordlist: {len(junk)} {by}; still accepted via rules: {len(still_junk)}')
    print(f'lost from base: {len(lost)}')
    bad_enc = [w for w in base if malformed(w)]
    if bad_enc:
        print(f'warning: {len(bad_enc)} gu-wordlist.txt entries look wrongly encoded, e.g. {" ".join(bad_enc[:10])}')
    return final


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--no-wiki' in args:
        WITH_WIKI = False
        args.remove('--no-wiki')
    main(*args[:3])
