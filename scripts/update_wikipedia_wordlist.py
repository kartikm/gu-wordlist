#!/usr/bin/env python3
"""
update_wikipedia_wordlist.py

Periodically fetches the latest Gujarati Wikipedia database dump,
filters noise/typos, applies frequency thresholds, and updates wikipedia-wordlist.txt.

Usage:
    python3 scripts/update_wikipedia_wordlist.py
    python3 scripts/update_wikipedia_wordlist.py --file /path/to/guwiki-latest-pages-articles-multistream.xml.bz2
    python3 scripts/update_wikipedia_wordlist.py --min-freq 3 --output wikipedia-wordlist.txt
"""

import argparse
import bz2
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

WIKIPEDIA_DUMP_URL = (
    "https://dumps.wikimedia.org/guwiki/latest/"
    "guwiki-latest-pages-articles-multistream.xml.bz2"
)

# Gujarati Unicode collation weights
GUJARATI_ORDER = (
    "અઆઇઈઉઊઋઌઍએઐઑઓઔ"
    "કખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલળવશષસહ"
    "઼ઽાિીુૂૃૄૅેૈૉોૌ્"
    "ંઁઃ"
)
CHAR_WEIGHTS = {char: idx + 1 for idx, char in enumerate(GUJARATI_ORDER)}


def gujarati_sort_key(word):
    """Generates a tuple sort key based on standard Gujarati alphabetical order."""
    return tuple(CHAR_WEIGHTS.get(c, 1000 + ord(c)) for c in word)


def download_dump(url, destination_path):
    """Downloads the Wikimedia dump with progress reporting."""
    print(f"Downloading latest dump from:\n  {url}")
    print(f"Destination: {destination_path}")

    def progress_callback(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded / total_size * 100
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(
                f"\r  -> Progress: {percent:5.1f}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)"
            )
        else:
            sys.stdout.write(f"\r  -> Downloaded: {downloaded / (1024 * 1024):.1f} MB")
        sys.stdout.flush()

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, destination_path, reporthook=progress_callback)
    print("\nDownload complete.")


# Compile regex patterns for fast token filtering
GUJARATI_TOKEN_RE = re.compile(r"[\u0A80-\u0AFF]+")
DIGIT_RE = re.compile(r"[\u0AE6-\u0AEF0-9]")
DOUBLE_MATRA_RE = re.compile(r"[\u0ABE-\u0ACC]{2}")
ROGUE_VIRAMA_RE = re.compile(r"\u0ACD{2,}")
INVALID_START_RE = re.compile(r"^[\u0ABE-\u0ACD\u0A82\u0A83]")
INVALID_END_RE = re.compile(r"\u0ACD$")

VALID_SINGLE_LETTERS = set("અઆઇઈઉઊઋઍએઐઑઓઔ")


def is_valid_gujarati_word(token):
    """
    Validates that a token is a legitimate Gujarati word:
    - Contains only Gujarati characters.
    - No digits (English or Gujarati citation years/tags).
    - No double vowel signs (matras).
    - Does not start with dependent vowel signs or end in raw virama.
    - Has length >= 2 or is a standalone valid vowel.
    """
    if len(token) < 2:
        return token in VALID_SINGLE_LETTERS

    if DIGIT_RE.search(token):
        return False

    if DOUBLE_MATRA_RE.search(token):
        return False

    if ROGUE_VIRAMA_RE.search(token):
        return False

    if INVALID_START_RE.search(token):
        return False

    if INVALID_END_RE.search(token):
        return False

    return True


def extract_words_from_stream(bz2_path):
    """
    Reads the compressed XML dump line by line to minimize memory usage,
    extracting tokens from page text.
    """
    print(f"Processing dump file: {bz2_path}")
    word_counts = Counter()
    total_articles = 0
    in_text = False
    text_buffer = []

    with bz2.open(bz2_path, mode="rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "<text" in line:
                in_text = True
                text_buffer = [line]
                if "</text>" in line:
                    in_text = False
                    total_articles += 1
                    content = "".join(text_buffer)
                    for match in GUJARATI_TOKEN_RE.finditer(content):
                        token = match.group()
                        if is_valid_gujarati_word(token):
                            word_counts[token] += 1
                    text_buffer = []
                    if total_articles % 5000 == 0:
                        sys.stdout.write(
                            f"\r  -> Processed {total_articles:,} pages | {len(word_counts):,} unique candidates..."
                        )
                        sys.stdout.flush()
            elif in_text:
                text_buffer.append(line)
                if "</text>" in line:
                    in_text = False
                    total_articles += 1
                    content = "".join(text_buffer)
                    for match in GUJARATI_TOKEN_RE.finditer(content):
                        token = match.group()
                        if is_valid_gujarati_word(token):
                            word_counts[token] += 1
                    text_buffer = []
                    if total_articles % 5000 == 0:
                        sys.stdout.write(
                            f"\r  -> Processed {total_articles:,} pages | {len(word_counts):,} unique candidates..."
                        )
                        sys.stdout.flush()

    print(f"\nCompleted extraction: {total_articles:,} pages scanned.")
    print(f"Total raw candidate vocabulary: {len(word_counts):,} words.")
    return word_counts


def filter_and_collate_wordlist(word_counts, base_wordlist_path=None, min_freq=3):
    """
    Applies the minimum frequency threshold, merges with base dictionary
    to ensure verified terms are not omitted, and sorts the words.
    """
    base_words = set()
    if base_wordlist_path and Path(base_wordlist_path).is_file():
        print(f"Loading verified base vocabulary from: {base_wordlist_path}")
        with open(base_wordlist_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    base_words.add(w)
        print(f"Loaded {len(base_words):,} base words.")

    final_words = set()

    for word, count in word_counts.items():
        if count >= min_freq or word in base_words:
            final_words.add(word)

    print(
        f"Filtered vocabulary (min_freq >= {min_freq} or in base list): {len(final_words):,} words."
    )

    print("Sorting words using Gujarati alphabetical order...")
    sorted_words = sorted(final_words, key=gujarati_sort_key)
    return sorted_words


def main():
    parser = argparse.ArgumentParser(
        description="Extract and update Gujarati Wikipedia wordlist from Wikimedia dumps."
    )
    parser.add_argument(
        "--file",
        dest="dump_file",
        type=Path,
        default=None,
        help="Path to an existing .xml.bz2 dump file. If omitted, downloads latest dump.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("wikipedia-wordlist.txt"),
        help="Path to output wordlist file (default: wikipedia-wordlist.txt).",
    )
    parser.add_argument(
        "--base-wordlist",
        type=Path,
        default=Path("gu-wordlist.txt"),
        help="Path to base wordlist to retain verified terms (default: gu-wordlist.txt).",
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=3,
        help="Minimum frequency threshold across Wikipedia articles (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run extraction and filtering without writing to output file.",
    )

    args = parser.parse_args()

    # Determine dump file location
    dump_path = args.dump_file
    if dump_path is None or not dump_path.is_file():
        default_local = Path("guwiki-latest-pages-articles-multistream.xml.bz2")
        if default_local.is_file():
            dump_path = default_local
            print(f"Using existing local dump file: {dump_path}")
        else:
            dump_path = Path("downloads") / "guwiki-latest-pages-articles-multistream.xml.bz2"
            download_dump(WIKIPEDIA_DUMP_URL, dump_path)

    word_counts = extract_words_from_stream(dump_path)
    sorted_words = filter_and_collate_wordlist(
        word_counts, base_wordlist_path=args.base_wordlist, min_freq=args.min_freq
    )

    if args.dry_run:
        print("Dry run requested. No files were modified.")
        return

    output_path = args.output
    print(f"Writing {len(sorted_words):,} words to {output_path}...")
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        for word in sorted_words:
            f.write(f"{word}\n")

    print("Success! wikipedia-wordlist.txt updated.")


if __name__ == "__main__":
    main()
