import sys
import argparse
import shutil
from pathlib import Path

def merge_folders(source_folders: list, output_folder: str = None, dry_run: bool = False):
    """
    Merges multiple folders into one, eliminating duplicates.
    Folders with the same relative path are merged together.
    Files with the same name in the same relative path are kept only once.
    
    Args:
        source_folders: List of folder paths to merge
        output_folder: Name of the output folder (default: "merged_output")
        dry_run: If True, only shows what would be done without copying
    """
    # Validate all source folders
    source_paths = []
    for folder in source_folders:
        path = Path(folder).resolve()
        if not path.is_dir():
            print(f"Error: {folder} is not a valid directory.")
            sys.exit(1)
        source_paths.append(path)
    
    # Determine output folder
    if output_folder is None:
        output_folder = "merged_output"
    
    # Use the parent of the first source folder as the base
    output_path = source_paths[0].parent / output_folder
    
    print(f"Merging {len(source_paths)} folder(s):")
    for i, path in enumerate(source_paths, 1):
        print(f"  {i}. {path}")
    print(f"\nOutput folder: {output_path}")
    
    if dry_run:
        print("[DRY RUN MODE - No files will be copied]\n")
    else:
        print("\n")
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Track what we've already copied to avoid duplicates
    copied_files = set()
    copied_count = 0
    duplicate_count = 0
    error_count = 0
    
    # Process each source folder
    for source_idx, source_path in enumerate(source_paths, 1):
        print(f"\n{'='*60}")
        print(f"Processing source {source_idx}/{len(source_paths)}: {source_path.name}")
        print(f"{'='*60}\n")
        
        for item_path in source_path.rglob("*"):
            # Get relative path from source root
            rel_path = item_path.relative_to(source_path)
            
            # Destination path in output folder
            dest_item_path = output_path / rel_path
            
            if item_path.is_dir():
                # Create directory if it doesn't exist
                try:
                    if not dry_run:
                        dest_item_path.mkdir(parents=True, exist_ok=True)
                    print(f"  📁 {rel_path}")
                except Exception as e:
                    print(f"  ⚠ ERROR creating folder {rel_path}: {e}")
                    error_count += 1
            else:
                # Check if this file has already been copied
                file_key = str(rel_path)
                
                if file_key in copied_files:
                    # Duplicate found
                    print(f"  ⚠ DUPLICATE SKIPPED: {rel_path}")
                    duplicate_count += 1
                    continue
                
                # Copy the file
                try:
                    if dry_run:
                        print(f"  ✓ {rel_path}")
                    else:
                        dest_item_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item_path, dest_item_path)
                        print(f"  ✓ {rel_path}")
                    
                    copied_files.add(file_key)
                    copied_count += 1
                except Exception as e:
                    print(f"  ⚠ ERROR copying {rel_path}: {e}")
                    error_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"MERGE SUMMARY:")
    print(f"{'='*60}")
    print(f"  Source folders processed: {len(source_paths)}")
    print(f"  Files copied: {copied_count}")
    print(f"  Duplicates skipped: {duplicate_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")
    
    if not dry_run and copied_count > 0:
        print(f"\n✓ Merged folder created: {output_path}")
        print(f"Total unique files: {len(copied_files)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge multiple folders into one, eliminating duplicates while preserving folder structure."
    )
    parser.add_argument(
        "folders", 
        type=str, 
        nargs="+",
        help="Paths to the folders to merge (2 or more)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="merged_output",
        help="Name of the output folder (default: merged_output)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be done without actually copying files"
    )
    
    args = parser.parse_args()
    
    if len(args.folders) < 2:
        print("Error: Please provide at least 2 folders to merge.")
        sys.exit(1)
    
    merge_folders(args.folders, output_folder=args.output, dry_run=args.dry_run)