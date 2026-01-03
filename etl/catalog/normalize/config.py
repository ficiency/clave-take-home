"""Constants and pre-compiled patterns for normalization."""

import re

# Typo corrections (word boundaries applied during matching)
NAME_TYPOS = {
    "Griled": "Grilled", "Chiken": "Chicken", "Sandwhich": "Sandwich",
    "expresso": "Espresso", "coffe": "Coffee", "churos": "Churros", "Coffe": "Coffee",
}

# Abbreviation expansions
ABBREVIATIONS = {
    "Lg": "Large", "lg": "Large", "sm": "Small",
    "reg": "Regular", "dbl": "Double", "dbl shot": "Double Shot",
}

# Category mappings
CATEGORY_FIXES = {"ENTREES": "Entrees", "Appitizers": "Appetizers"}

# Words that stay lowercase (except at start)
LOWERCASE_WORDS = {"and", "of", "the", "a", "an", "in", "on", "at", "to", "for"}

# Pre-compiled patterns (O(1) matching vs O(n) compilation per call)
EMOJI_RE = re.compile(r'[🍔🍟🌅🍰🥤🍕🌮🍗]+\s*')
SPACES_RE = re.compile(r'\s+')
AMPERSAND_RE = re.compile(r'\s*&\s*')
HYPHEN_RE = re.compile(r'\s*-\s*')
PCS_RE = re.compile(r'(\d+)pcs\b', re.IGNORECASE)
NUM_LETTERS_RE = re.compile(r'^(\d+)([a-z]+)$', re.IGNORECASE)
PIECE_RE = re.compile(r'(\d+)\s*piece')

# Pre-compile typo and abbreviation patterns (longest first to avoid partial matches)
TYPO_PATTERNS = [(re.compile(r'\b' + re.escape(k) + r'\b'), v) 
                 for k, v in sorted(NAME_TYPOS.items(), key=lambda x: -len(x[0]))]
ABBREV_PATTERNS = [(re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE), v)
                   for k, v in sorted(ABBREVIATIONS.items(), key=lambda x: -len(x[0]))]

