"""
rename_exercices_folders.py

Renames exercise folders to exactly match the chapter .docx filenames
from the reference folder (splitted/ or shifted_down/).

Uses fuzzy matching to handle:
- Case differences (Chapitre vs chapitre)
- Accents (é vs e)
- Hyphens, underscores, apostrophes, spaces
- Minor wording differences

Usage:
    1. Set DRY_RUN = True (default) and run to preview changes
    2. Review the output carefully
    3. Set DRY_RUN = False and run again to apply renames
"""

import os
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

# ==========================================
# CONFIGURATION - EDIT THESE PATHS
# ==========================================
BULK_ROOT = Path(r"C:\Users\ZICO\Desktop\backup-medzone-documents\medzone-documents")

# The reference folder that contains the .docx chapter files
# Use 'splitted' or 'shifted_down' - whichever has the canonical names
REFERENCE_SUBDIR = 'splitted'

# The folder containing exercise folders that need to be renamed
EXERCICES_SUBDIR = 'exercices'

# Set to True to preview changes WITHOUT actually renaming (SAFETY FIRST!)
# Set to False only after you've reviewed the dry run output
DRY_RUN = False
# ==========================================


def aggressive_normalize(text):
    """
    Very aggressive normalization for fuzzy matching:
    - Remove accents
    - Lowercase
    - Remove ALL non-alphanumeric characters (hyphens, underscores, 
      apostrophes, spaces, colons, etc.)
    - Collapse multiple spaces
    
    Examples:
        "Chapitre 1: Introduction" -> "chapitre1introduction"
        "Chapitre-1-Introduction" -> "chapitre1introduction"
        "Chapitre_1_Introduction" -> "chapitre1introduction"
        "L'Introduction" -> "lintroduction"
        "Chapitre 1ère" -> "chapitre1ere"
    """
    if not text:
        return ''
    
    # Normalize unicode (NFKD decomposes characters)
    nfkd = unicodedata.normalize('NFKD', text)
    
    # Remove combining characters (accents)
    without_accents = ''.join(c for c in nfkd if not unicodedata.combining(c))
    
    # Lowercase
    lowered = without_accents.lower()
    
    # Handle special ligatures
    lowered = lowered.replace('œ', 'oe').replace('æ', 'ae')
    
    # Remove ALL non-alphanumeric characters (keeps only letters and digits)
    # This handles hyphens, underscores, apostrophes, spaces, colons, etc.
    cleaned = re.sub(r'[^a-z0-9]', '', lowered)
    
    return cleaned


def find_best_match(target_name, candidates):
    """
    Find the best matching candidate for a target name using aggressive normalization.
    Returns (matched_candidate, original_candidate_path) or (None, None) if no match.
    """
    norm_target = aggressive_normalize(target_name)
    if not norm_target:
        return None, None
    
    # First pass: exact normalized match
    for candidate in candidates:
        if aggressive_normalize(candidate.name) == norm_target:
            return candidate.name, candidate
    
    # Second pass: check if one contains the other (for partial matches)
    # Only use this if the normalized strings are very similar
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        norm_candidate = aggressive_normalize(candidate.name)
        if not norm_candidate:
            continue
        
        # Check containment
        if norm_target in norm_candidate or norm_candidate in norm_target:
            # Score based on length ratio (closer to 1.0 = better match)
            shorter = min(len(norm_target), len(norm_candidate))
            longer = max(len(norm_target), len(norm_candidate))
            score = shorter / longer if longer > 0 else 0
            
            if score > best_score and score >= 0.7:  # At least 70% similarity
                best_score = score
                best_match = (candidate.name, candidate)
    
    return best_match if best_match else (None, None)


def process_level(reference_root, exercices_root, level_ref_folder, stats, renames_log):
    """Process all unites within a level."""
    level_name = level_ref_folder.name
    
    # Find matching level folder in exercices
    exercice_level_folders = [d for d in exercices_root.iterdir() if d.is_dir()] if exercices_root.exists() else []
    
    matched_level_name, matched_level_path = find_best_match(level_name, exercice_level_folders)
    
    if not matched_level_path:
        stats['no_match_levels'].append(level_name)
        print(f"  ⚠️  No matching level folder found for '{level_name}'")
        return
    
    # Rename level folder if names differ
    if matched_level_name != level_name:
        new_level_path = exercices_root / level_name
        renames_log.append({
            'type': 'level',
            'old': str(matched_level_path),
            'new': str(new_level_path),
        })
        if not DRY_RUN:
            matched_level_path.rename(new_level_path)
            matched_level_path = new_level_path
        stats['renamed_levels'] += 1
        print(f"  📁 Level: '{matched_level_name}' → '{level_name}'")
    else:
        matched_level_path = exercices_root / level_name
    
    # Process unites within this level
    for unite_ref_folder in level_ref_folder.iterdir():
        if not unite_ref_folder.is_dir():
            continue
        process_unite(matched_level_path, unite_ref_folder, stats, renames_log)


def process_unite(exercice_level_folder, unite_ref_folder, stats, renames_log):
    """Process all chapters within a unite."""
    unite_name = unite_ref_folder.name
    
    # Find matching unite folder in exercices
    exercice_unite_folders = [d for d in exercice_level_folder.iterdir() if d.is_dir()] if exercice_level_folder.exists() else []
    
    matched_unite_name, matched_unite_path = find_best_match(unite_name, exercice_unite_folders)
    
    if not matched_unite_path:
        stats['no_match_unites'].append(f"{exercice_level_folder.name}/{unite_name}")
        print(f"    ⚠️  No matching unite folder found for '{unite_name}'")
        return
    
    # Rename unite folder if names differ
    if matched_unite_name != unite_name:
        new_unite_path = exercice_level_folder / unite_name
        renames_log.append({
            'type': 'unite',
            'old': str(matched_unite_path),
            'new': str(new_unite_path),
        })
        if not DRY_RUN:
            matched_unite_path.rename(new_unite_path)
            matched_unite_path = new_unite_path
        stats['renamed_unites'] += 1
        print(f"    📂 Unite: '{matched_unite_name}' → '{unite_name}'")
    else:
        matched_unite_path = exercice_level_folder / unite_name
    
    # Now process chapters: match .docx files to exercise folders
    # Get all .docx files from reference (these are the source of truth)
    docx_files = [f for f in unite_ref_folder.iterdir() 
                  if f.is_file() and f.suffix.lower() == '.docx']
    
    # Get all exercise folders (these need to be renamed)
    exercice_chapter_folders = [d for d in matched_unite_path.iterdir() if d.is_dir()]
    
    print(f"      📖 Processing {len(docx_files)} chapters in '{unite_name}'...")
    
    # Track which exercise folders have been matched (to avoid double-matching)
    used_exercise_folders = set()
    
    for docx_file in docx_files:
        # The canonical chapter name is the filename without extension
        canonical_name = docx_file.stem
        
        # Find matching exercise folder
        available_folders = [f for f in exercice_chapter_folders 
                            if f.name not in used_exercise_folders]
        
        matched_folder_name, matched_folder_path = find_best_match(canonical_name, available_folders)
        
        if not matched_folder_path:
            stats['no_match_chapters'].append(f"{unite_name}/{canonical_name}")
            print(f"        ⚠️  No exercise folder found for '{canonical_name}'")
            continue
        
        # Check if rename is needed
        if matched_folder_name != canonical_name:
            new_folder_path = matched_unite_path / canonical_name
            
            # Safety check: don't overwrite existing folders
            if new_folder_path.exists() and new_folder_path != matched_folder_path:
                stats['conflicts'].append(f"{matched_folder_path} → {new_folder_path} (target exists!)")
                print(f"        ❌ CONFLICT: Cannot rename '{matched_folder_name}' → '{canonical_name}' (target exists)")
                continue
            
            renames_log.append({
                'type': 'chapter',
                'old': str(matched_folder_path),
                'new': str(new_folder_path),
                'docx_source': docx_file.name,
            })
            
            if not DRY_RUN:
                matched_folder_path.rename(new_folder_path)
            
            stats['renamed_chapters'] += 1
            print(f"        ✅ '{matched_folder_name}' → '{canonical_name}' (from {docx_file.name})")
        else:
            stats['already_correct'] += 1
        
        used_exercise_folders.add(matched_folder_name)
    
    # Report unmatched exercise folders (orphans)
    remaining = [f for f in exercice_chapter_folders if f.name not in used_exercise_folders]
    if remaining:
        for orphan in remaining:
            stats['orphan_exercise_folders'].append(str(orphan))
            print(f"        🗂️  Orphan exercise folder (no matching .docx): '{orphan.name}'")


def main():
    reference_root = BULK_ROOT / REFERENCE_SUBDIR
    exercices_root = BULK_ROOT / EXERCICES_SUBDIR
    
    print("=" * 70)
    print("EXERCISE FOLDER RENAMER")
    print("=" * 70)
    print(f"Reference folder (source of truth): {reference_root}")
    print(f"Exercices folder (to be renamed):   {exercices_root}")
    print(f"Mode: {'🔍 DRY RUN (no changes will be made)' if DRY_RUN else '🔥 LIVE RUN (folders WILL be renamed)'}")
    print("=" * 70)
    
    if not reference_root.exists():
        print(f"❌ Reference folder does not exist: {reference_root}")
        return
    
    if not exercices_root.exists():
        print(f"❌ Exercices folder does not exist: {exercices_root}")
        return
    
    stats = {
        'renamed_levels': 0,
        'renamed_unites': 0,
        'renamed_chapters': 0,
        'already_correct': 0,
        'no_match_levels': [],
        'no_match_unites': [],
        'no_match_chapters': [],
        'conflicts': [],
        'orphan_exercise_folders': [],
    }
    renames_log = []
    
    # Process each level
    level_folders = [d for d in reference_root.iterdir() if d.is_dir()]
    print(f"\nFound {len(level_folders)} levels to process.\n")
    
    for level_folder in level_folders:
        print(f"📚 Level: {level_folder.name}")
        process_level(reference_root, exercices_root, level_folder, stats, renames_log)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Levels renamed:        {stats['renamed_levels']}")
    print(f"Unites renamed:        {stats['renamed_unites']}")
    print(f"Chapters renamed:      {stats['renamed_chapters']}")
    print(f"Already correct:       {stats['already_correct']}")
    print(f"No match (levels):     {len(stats['no_match_levels'])}")
    print(f"No match (unites):     {len(stats['no_match_unites'])}")
    print(f"No match (chapters):   {len(stats['no_match_chapters'])}")
    print(f"Conflicts:             {len(stats['conflicts'])}")
    print(f"Orphan exercise dirs:  {len(stats['orphan_exercise_folders'])}")
    
    if stats['no_match_levels']:
        print("\n⚠️  Levels with no match in exercices:")
        for l in stats['no_match_levels']:
            print(f"   - {l}")
    
    if stats['no_match_unites']:
        print("\n⚠️  Unites with no match in exercices:")
        for u in stats['no_match_unites']:
            print(f"   - {u}")
    
    if stats['no_match_chapters']:
        print("\n⚠️  Chapters with no matching exercise folder:")
        for c in stats['no_match_chapters']:
            print(f"   - {c}")
    
    if stats['conflicts']:
        print("\n❌ Conflicts (could not rename due to existing target):")
        for c in stats['conflicts']:
            print(f"   - {c}")
    
    if stats['orphan_exercise_folders']:
        print("\n🗂️  Orphan exercise folders (no matching .docx):")
        for o in stats['orphan_exercise_folders']:
            print(f"   - {o}")
    
    if renames_log:
        print(f"\n📝 {'Planned' if DRY_RUN else 'Executed'} renames ({len(renames_log)}):")
        for entry in renames_log[:20]:  # Show first 20
            print(f"   [{entry['type']}] {entry['old']}")
            print(f"      → {entry['new']}")
        if len(renames_log) > 20:
            print(f"   ... and {len(renames_log) - 20} more")
    
    print("\n" + "=" * 70)
    if DRY_RUN:
        print("✅ DRY RUN COMPLETE. No changes were made.")
        print("   Review the output above. If everything looks correct,")
        print("   set DRY_RUN = False and run the script again.")
    else:
        print("🎉 LIVE RUN COMPLETE. All renames have been applied.")
    print("=" * 70)


if __name__ == "__main__":
    main()