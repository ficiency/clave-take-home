"""
Normalization functions for item names and categories.
Uses pre-compiled regex patterns from config for O(1) matching efficiency.
"""

from .config import (
    TYPO_PATTERNS, ABBREV_PATTERNS, CATEGORY_FIXES, LOWERCASE_WORDS,
    EMOJI_RE, SPACES_RE, AMPERSAND_RE, HYPHEN_RE, PCS_RE, NUM_LETTERS_RE, PIECE_RE
)


def normalize_item_name(name: str) -> str:
    """
    Normalizes item name: fixes typos, expands abbreviations, standardizes formatting.
    Uses pre-compiled patterns for O(1) regex matching.
    """
    if not name:
        return ""
    
    name = str(name).strip()
    
    # Fix typos using pre-compiled patterns
    for pattern, replacement in TYPO_PATTERNS:
        name = pattern.sub(replacement, name)
    
    # Normalize symbols
    name = AMPERSAND_RE.sub(' and ', name)
    name = HYPHEN_RE.sub(' ', name)
    
    # Expand abbreviations using pre-compiled patterns
    for pattern, replacement in ABBREV_PATTERNS:
        name = pattern.sub(replacement, name)
    
    # Normalize "12pcs" -> "12pc"
    name = PCS_RE.sub(r'\1pc', name)
    name = SPACES_RE.sub(' ', name)
    
    # Capitalize words with special handling
    words = name.split()
    result = []
    for i, word in enumerate(words):
        if word.isupper() and len(word) > 1:
            result.append(word)  # Keep acronyms (BBQ)
        elif match := NUM_LETTERS_RE.match(word):
            result.append(match[1] + match[2].lower())  # "12PC" -> "12pc"
        elif word.lower() in LOWERCASE_WORDS and i > 0:
            result.append(word.lower())  # Lowercase conjunctions (not first word)
        else:
            result.append(word.capitalize())
    
    name = ' '.join(result)
    
    # Specific known corrections
    if name.startswith("Fries ") or name == "Fries":
        name = name.replace("Fries", "French Fries", 1)
    
    if "Coke" in name and "Coca Cola" not in name:
        name = name.replace("Coke", "Coca Cola")
        if name.startswith("Large "):
            name = name.replace("Large ", "", 1) + " Large"
    
    if "Hashbrowns" in name:
        name = name.replace("Hashbrowns", "Hash Browns")
    
    return name.strip()


def normalize_category_name(cat: str) -> str:
    """
    Normalizes category: removes emojis, fixes typos, standardizes case.
    Uses pre-compiled emoji pattern for O(1) matching.
    """
    if not cat:
        return "Unknown"
    
    cat = EMOJI_RE.sub('', str(cat).strip())
    cat = SPACES_RE.sub(' ', cat).strip()
    return CATEGORY_FIXES.get(cat, cat)


def square_variation_suffix(var_name: str, item_name: str) -> str:
    """
    Returns suffix for Square variations (Double, piece count, Large fries).
    Uses pre-compiled pattern for O(1) piece count matching.
    """
    if not var_name or var_name == "Regular":
        return ""
    if var_name == "Double" and any(x in item_name for x in ("Burger", "Espresso")):
        return " Double"
    if match := PIECE_RE.search(var_name):
        return f" {match.group(1)}pc"
    if var_name == "Large" and "Fries" in item_name:
        return " Large"
    return ""

