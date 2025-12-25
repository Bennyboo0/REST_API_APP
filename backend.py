"""
Hebrew Gematria Utilities
Purpose: Correct, library-free Hebrew gematria computation
"""

import re

# --------------------------------------------------
# 1. Canonical Hebrew Gematria Map (Mispar Gadol)
# --------------------------------------------------

GEMATRIA_MAP = {
    'א': 1,  'ב': 2,  'ג': 3,  'ד': 4,  'ה': 5,
    'ו': 6,  'ז': 7,  'ח': 8,  'ט': 9,
    'י': 10,'כ': 20,'ל': 30,'מ': 40,'נ': 50,
    'ס': 60,'ע': 70,'פ': 80,'צ': 90,
    'ק': 100,'ר': 200,'ש': 300,'ת': 400,

    # Final letters (same value in standard gematria)
    'ך': 20,'ם': 40,'ן': 50,'ף': 80,'ץ': 90
}

# --------------------------------------------------
# 2. Hebrew Normalization
# --------------------------------------------------
# Removes:
# - niqqud
# - ta'amim
# - non-Hebrew characters
# --------------------------------------------------

NIQQUD_AND_TAAMIM = re.compile(r'[\u0591-\u05C7]')
NON_HEBREW = re.compile(r'[^\u05D0-\u05EA\u05DA\u05DD\u05DF\u05E3\u05E5]')

def _normalize(text: str) -> str:
    text = NIQQUD_AND_TAAMIM.sub('', text)
    return NON_HEBREW.sub('', text)

# --------------------------------------------------
# 3. Public API
# --------------------------------------------------

def get_gematria(text: str) -> int:
    """
    Compute standard Hebrew gematria (Mispar Gadol).

    Args:
        text (str): Any string containing Hebrew text.

    Returns:
        int: Gematria value.
    """
    text = _normalize(text)
    return sum(GEMATRIA_MAP.get(ch, 0) for ch in text)

# --------------------------------------------------
# 4. Optional: Debug / Breakdown Helper
# --------------------------------------------------

def gematria_breakdown(text: str) -> list[tuple[str, int]]:
    """
    Returns per-letter gematria breakdown.
    """
    text = _normalize(text)
    return [(ch, GEMATRIA_MAP[ch]) for ch in text]

# --------------------------------------------------
# 5. Manual Test
# --------------------------------------------------

if __name__ == "__main__":
    examples = [
        "בראשית",
        "בְּרֵאשִׁית",
        "וַיְהִי־אוֹר",
        "שלום עולם"
    ]

    for e in examples:
        print(e, "→", gematria_breakdown(e))