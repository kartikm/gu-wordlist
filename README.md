gu-wordlist
===========

Gujarati wordlist which is base of aspell-gu dictionary.

gu-wordlist.txt: Gujarati words collection from various sources.

wikipedia-wordlist.txt: Words dumped from Gujarati wikipedia <http://dumps.wikimedia.org/backup-index.html>

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

An automated GitHub Action workflow (`.github/workflows/update-wikipedia.yml`) is also configured to run periodically on the 1st of every month or manually via workflow dispatch.

LICENSE
=======

gu-wordlist.txt: GPL-2+

wikipedia-wordlist.txt: Wikipedia license at the time of writing.
