gu-wordlist
===========

Gujarati wordlist which is base of aspell-gu dictionary.

gu-wordlist.txt: Gujarati words collection from various sources.

gu_IN.aff, gu_IN.dic: Hunspell dictionary generated from gu-wordlist.txt and wikipedia-frequency.tsv by scripts/build_hunspell.py (see below).

wikipedia-wordlist.txt: Words dumped from Gujarati wikipedia <http://dumps.wikimedia.org/backup-index.html>

wikipedia-frequency.tsv: How often each word occurs in Gujarati Wikipedia (word, TAB, count; words seen at least twice).

Updating Wikipedia Wordlist
===========================

To update `wikipedia-wordlist.txt` from the latest Wikimedia dump:

```bash
python3 scripts/update_wikipedia_wordlist.py
```

This will automatically download the latest Gujarati Wikipedia database dump, filter out typos and single-occurrence noise (minimum frequency >= 3), deduplicate, and sort entries using standard Gujarati alphabetical collation.

Options:
- `--file <path>`: Use an existing local `.xml.bz2` dump file instead of downloading.
- `--min-freq <n>`: Set minimum frequency threshold (default: 3).
- `--output <path>`: Specify output file (default: `wikipedia-wordlist.txt`).
- `--base-wordlist <path>`: Base dictionary to preserve verified words (default: `gu-wordlist.txt`).
- `--dry-run`: View extraction statistics without modifying files.

An automated GitHub Action workflow (`.github/workflows/update-wikipedia.yml`) is also configured to run periodically on the 1st of every month or manually via workflow dispatch. It updates `wikipedia-wordlist.txt` and `wikipedia-frequency.tsv` and rebuilds `gu_IN.aff` / `gu_IN.dic`.

Building the Hunspell dictionary
================================

`gu_IN.aff` and `gu_IN.dic` are generated files. Do not edit them by hand; change
`gu-wordlist.txt` (or the script) and rebuild:

```bash
python3 scripts/build_hunspell.py gu-wordlist.txt wikipedia-frequency.tsv .
```

To refresh the frequencies from a new dump first:

```bash
python3 scripts/count_wiki_frequencies.py guwiki-latest-pages-articles-multistream.xml.bz2 > wikipedia-frequency.tsv
```

Gujarati attaches case markers and plural endings to the word, so the
dictionary uses Hunspell affix rules instead of listing every form:

| Flag | Applies to | Generates |
|------|------------|-----------|
| `N` | nouns with attested inflections (ઘર, પુત્ર, પિતા) | case markers (નો, ની, નું, ના, નાં, ને, થી, માં, માંથી, ...), -એ/-ે (ઘરે, પિતાએ), plural -ો/-ઓ, and case markers on the plural (પુત્રોને, સજાઓમાં) |
| `O` | -ો nouns/adjectives (રસ્તો, પુરાવો) | -ા, -ે, -ાએ, plural -ાઓ, case markers on -ા (રસ્તાના, રસ્તે, પુરાવાઓના) |
| `U` | -ું nouns/adjectives (અથાણું, કરવું) | -ા, -ાં, -ે, case markers on -ા (અથાણાનો, કરવામાં) |
| `V` | consonant-final verb roots (કર, બનાવ, પડ) | present, past, future, participles, infinitive, passive (કરે, કર્યો, કરશે, કરતો, કરેલું, કરવાનું, કરાય) |
| `W` | -ા verb roots (જોડા, ગભરા) | જોડાય, જોડાયો, જોડાઈ, જોડાશે, જોડાયેલું, ... |
| `K` | every other noun-like word, including names and loanwords | case markers and -એ/-ે only, no plural (ખુદીરામને, વીડિયોનો) |
| `C` | (continuation) plurals | case markers on plurals |

The script also:

- drops mechanically generated wrong forms from the wordlist (case marker on
  the -ું or singular -ો form such as કરવુંના, missing anusvara such as ઘરનુ)
  unless Wikipedia uses them 5 or more times;
- adds words seen 3+ times on Wikipedia (names, loanwords) only when they are
  the most frequent spelling among their spelling variants (ી/િ, ૂ/ુ, ઈ/ઇ,
  anusvara, repha, ષ/શ, ણ/ન) and no variant is already in the wordlist, so
  common misspellings like સક્રીય, બ્રિટીશ, નિમણૂંક stay flagged.
  Use `--no-wiki` to build from gu-wordlist.txt alone;
- checks that every correct word of gu-wordlist.txt is still accepted.

`scripts/hspell.py` is a small Python reader for these affix rules that the
build uses; to test with real Hunspell:

```bash
echo "પુત્રોને સક્રીય" | hunspell -d ./gu_IN -l
```

LICENSE
=======

gu-wordlist.txt: GPL-2+

gu_IN.aff, gu_IN.dic: GPL-2+. gu_IN.dic also contains words selected from Gujarati Wikipedia (use `--no-wiki` for a build from gu-wordlist.txt only).

wikipedia-wordlist.txt, wikipedia-frequency.tsv: Wikipedia license at the time of writing.
