import re

def get_heading_level(style_name: str) -> int:
    """
    Extracts the heading level from a style name.
    Handles 'Heading 1', 'Heading1', 'Titre 1', case-insensitive.
    Returns 0 if not a heading.
    """
    if not style_name:
        return 0
    
    style_lower = style_name.lower().strip()
    
    # Check English: "heading 1", "heading1"
    match = re.search(r'heading\s*(\d+)', style_lower)
    if match:
        return int(match.group(1))
        
    # Check French: "titre 1", "titre1" (common in medical docs)
    match_fr = re.search(r'titre\s*(\d+)', style_lower)
    if match_fr:
        return int(match_fr.group(1))
        
    return 0

def sanitize_filename(name: str) -> str:
    """Removes invalid characters for filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip('. ')
    return name if name else "Untitled_Chapter"
