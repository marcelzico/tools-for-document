import sys
import argparse
import shutil
from pathlib import Path

def capitalize_filename(name: str) -> str:
    """
    Sentence case: only the first letter of the entire filename is uppercase.
    Example: "TRAUMATISME DE LA VESSIE" -> "Traumatisme de la vessie"
    """
    if not name:
        return name
    return name.capitalize()

def copy_with_capitalized_names(source_folder: str, dry_run: bool = False):
    """
    Creates a new folder with the same structure as the source, but with
    sentence-case filenames. The new folder will be named: source_folder_name_capitalized
    """
    source_path = Path(source_folder).resolve()
    
    if not source_path.is_dir():
        print(f"Error: {source_folder} is not a valid directory.")
        sys.exit(1)
    
    dest_path = source_path.parent / f"{source_path.name}_capitalized"
    
    print(f"Source folder: {source_path}")
    print(f"Destination folder: {dest_path}")
    
    if dry_run:
        print("[DRY RUN MODE - No files will be copied]\n")
    else:
        print("\n")
        dest_path.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    skipped_count = 0
    error_count = 0
    
    for item_path in source_path.rglob("*"):
        rel_path = item_path.relative_to(source_path)
        
        if item_path.is_dir():
            dest_item_path = dest_path / rel_path
            if not dry_run:
                dest_item_path.mkdir(parents=True, exist_ok=True)
            print(f"  📁 Created folder: {rel_path}")
            continue
        
        if item_path.name.startswith("~$"):
            print(f"  ⚠ SKIPPED (temp file): {item_path.name}")
            skipped_count += 1
            continue
        
        original_name = item_path.stem
        extension = item_path.suffix
        capitalized_name = capitalize_filename(original_name)
        
        dest_item_path = dest_path / rel_path.parent / f"{capitalized_name}{extension}"
        
        try:
            if dry_run:
                print(f"  [WOULD COPY]: {item_path.name} -> {capitalized_name}{extension}")
            else:
                shutil.copy2(item_path, dest_item_path)
                print(f"  ✓ Copied: {item_path.name} -> {capitalized_name}{extension}")
            copied_count += 1
        except Exception as e:
            print(f"  ⚠ ERROR copying {item_path.name}: {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files copied: {copied_count}")
    print(f"  Files skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")
    
    if not dry_run and copied_count > 0:
        print(f"\n✓ New folder created: {dest_path}")
        print(f"You can now verify the contents and delete the original folder if satisfied.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a new folder with sentence-case filenames while preserving folder structure."
    )
    parser.add_argument(
        "folder", 
        type=str, 
        help="Path to the source folder"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be done without actually copying files"
    )
    
    args = parser.parse_args()
    copy_with_capitalized_names(args.folder, dry_run=args.dry_run)