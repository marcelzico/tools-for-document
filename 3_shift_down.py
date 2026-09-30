import sys
import argparse
from pathlib import Path
from docx import Document
from utils import get_heading_level

def shift_down_headings(folder_path: str):
    in_folder = Path(folder_path).resolve()
    if not in_folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        sys.exit(1)

    out_folder = in_folder.parent / "shifted_down"
    out_folder.mkdir(exist_ok=True)

    docx_files = [f for f in in_folder.rglob("*.docx") if not f.name.startswith("~$")]

    if not docx_files:
        print("No .docx files found.")
        return

    success_count = 0
    error_count = 0

    for docx_file in docx_files:
        rel_path = docx_file.relative_to(in_folder)
        out_file = out_folder / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Processing (Shift Down): {rel_path}")

        try:
            doc = Document(docx_file)
        except Exception as e:
            print(f"  ⚠ SKIPPED (corrupted file): {e}")
            error_count += 1
            continue

        try:
            for para in doc.paragraphs:
                level = get_heading_level(para.style.name)
                if 2 <= level <= 9:
                    para.style = doc.styles[f'Heading {level - 1}']
                    
            doc.save(out_file)
            success_count += 1
        except Exception as e:
            print(f"  ⚠ SKIPPED (error during processing): {e}")
            error_count += 1
        
    print(f"\nDone. {success_count} succeeded, {error_count} skipped.")
    print(f"Saved to: {out_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively shift heading levels DOWN.")
    parser.add_argument("folder", type=str, help="Path to the 'splitted' folder.")
    args = parser.parse_args()
    shift_down_headings(args.folder)

    