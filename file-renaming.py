import sys
import argparse
import shutil
from pathlib import Path

def rename_files_and_folders(source_folder: str, dry_run: bool = False):
    """
    Creates a new folder with _change suffix (only the root folder).
    Renames files:
    - qa-*.csv -> flashcard-*.csv
    - clinical_case-*.txt -> summary-*.txt
    
    All subfolder structure remains exactly the same.
    """
    source_path = Path(source_folder).resolve()
    
    if not source_path.is_dir():
        print(f"Error: {source_folder} is not a valid directory.")
        sys.exit(1)
    
    # Only the root folder gets _change
    dest_path = source_path.parent / f"{source_path.name}_change"
    
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
    
    # Iterate through all items
    for item_path in source_path.rglob("*"):
        # Get relative path from source
        rel_path = item_path.relative_to(source_path)
        
        # Destination path keeps the same folder structure
        dest_item_path = dest_path / rel_path
        
        if item_path.is_dir():
            # Create folder with same name
            try:
                if not dry_run:
                    dest_item_path.mkdir(parents=True, exist_ok=True)
                print(f"  📁 {rel_path}")
            except Exception as e:
                print(f"  ⚠ ERROR creating folder {rel_path}: {e}")
                error_count += 1
        else:
            # Handle file renaming
            original_name = item_path.name
            
            # Check if file matches the patterns
            if original_name.startswith("qa-"):
                new_name = "flashcard-" + original_name[3:]
            elif original_name.startswith("clinical_case-"):
                new_name = "summary-" + original_name[14:]
            else:
                # No change needed
                new_name = original_name
            
            new_item_path = dest_item_path.parent / new_name
            
            try:
                if dry_run:
                    if new_name != original_name:
                        print(f"  ✓ {original_name} -> {new_name}")
                    else:
                        print(f"  📄 {original_name} (no change)")
                else:
                    shutil.copy2(item_path, new_item_path)
                    if new_name != original_name:
                        print(f"  ✓ {original_name} -> {new_name}")
                    else:
                        print(f"  📄 {original_name} (no change)")
                copied_count += 1
            except Exception as e:
                print(f"  ⚠ ERROR copying {original_name}: {e}")
                error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files copied: {copied_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")
    
    if not dry_run and copied_count > 0:
        print(f"\n✓ New folder created: {dest_path}")
        print(f"You can now verify the contents and delete the original folder if satisfied.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rename files (qa- -> flashcard-, clinical_case- -> summary-) in a new folder with _change suffix."
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
    rename_files_and_folders(args.folder, dry_run=args.dry_run)