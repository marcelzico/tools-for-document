import os
from pathlib import Path

# ===== CONFIGURATION – EDIT THESE PATHS =====
SOURCE_DIR = r"C:\Users\ZICO\Desktop\medzone-documents\original\5ème année\Anglais"   # Folder containing your PDFs, DOCX, PPTX etc.
DEST_DIR   = r"C:\Users\ZICO\Desktop\tesing-file" # Where the new folders & text files will be created
# If you want the folders to be created in the same place as the original files, set DEST_DIR = SOURCE_DIR
# =============================================

# Extensions to process – add or remove as needed
SUPPORTED_EXTS = {'.pdf', '.docx', '.pptx', '.doc', '.ppt', '.txt'}

# The six text file prefixes
PREFIXES = ['mcq', 'qa', 'resume', 'card', 'terminology', 'clinical_case']

def create_folder_and_text_files(file_path: Path, dest_root: Path):
    """
    Given a file path, create a folder named after the file (without extension)
    inside dest_root, and create the six text files inside it.
    """
    # Get the base name without extension
    base_name = file_path.stem   # e.g. "anatomy" from "anatomy.pdf"

    # Target folder path
    target_folder = dest_root / base_name

    # Create the target folder if it doesn't exist
    try:
        target_folder.mkdir(parents=True, exist_ok=False)  # exist_ok=False so we know if it already existed
        print(f"Created folder: {target_folder}")
    except FileExistsError:
        print(f"Folder already exists (skipping creation): {target_folder}")
        # If you prefer to overwrite or merge, you can change the logic here

    # Create the six text files inside the target folder
    for prefix in PREFIXES:
        text_file = target_folder / f"{prefix}-{base_name}.txt"
        if not text_file.exists():
            # Create an empty file
            text_file.touch()
            print(f"  Created: {text_file.name}")
        else:
            print(f"  File already exists: {text_file.name}")

def main():
    source = Path(SOURCE_DIR)
    dest   = Path(DEST_DIR)

    if not source.is_dir():
        print(f"Error: Source directory '{source}' does not exist.")
        return

    # Create destination directory if it doesn't exist
    dest.mkdir(parents=True, exist_ok=True)

    # Iterate over all items in source directory
    for item in source.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS:
            print(f"\nProcessing: {item.name}")
            create_folder_and_text_files(item, dest)
        else:
            # Skip directories and unsupported file types
            continue

    print("\nDone.")

if __name__ == "__main__":
    main()