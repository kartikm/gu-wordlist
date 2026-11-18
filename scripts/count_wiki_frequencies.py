#!/usr/bin/env python3
"""Count Gujarati word frequencies in a Wikipedia dump.

Usage:
    python3 scripts/count_wiki_frequencies.py guwiki-latest-pages-articles-multistream.xml.bz2 > wikipedia-frequency.tsv

Writes "word<TAB>count", most frequent first. Words seen fewer than
--min-freq times (default 2) are left out; build_hunspell.py never uses them.
"""
import argparse
import bz2
import collections
import re
import sys

TOKEN = re.compile(r'[ઁ-ૣૹ-૿‌‍]+')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dump')
    ap.add_argument('--min-freq', type=int, default=2)
    args = ap.parse_args()
    counts = collections.Counter()
    with bz2.open(args.dump, 'rt', encoding='utf-8') as f:
        in_text = False
        for line in f:
            if '<text' in line:
                in_text = True
            if in_text:
                for t in TOKEN.findall(line):
                    t = t.replace('‍', '').replace('‌', '')
                    if t:
                        counts[t] += 1
            if '</text>' in line:
                in_text = False
    for w, n in counts.most_common():
        if n < args.min_freq:
            break
        sys.stdout.write(f'{w}\t{n}\n')


if __name__ == '__main__':
    main()
