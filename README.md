# news-image-20261119 entry

A self-contained Python program (standard library only) that draws one
1024x1024 PNG summing up the world news of Thursday 19 November 2026, and
writes it to /output/entry.png.

The front page is rendered entirely by code: a bitmap font, panel
illustrations drawn from primitives (the summit flags of the US, China
and Russia, the scales of justice, an IPO chart, a cyclone spiral, the
Voyager probe, a recalled envoy's letter), two mini stories and a news
ticker. All news content lives in one NEWS structure at the top of
main.py, taken from real reporting of the day (Reuters, Le Monde, NASA,
AP and others; sources are listed in the build notes). The program needs
no network and runs deterministically — two runs produce byte-identical
output.

License: MIT (see LICENSE).
