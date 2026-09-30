import sys
import argparse
from pathlib import Path
from docx import Document
from utils import get_heading_level

def shift_up_headings(folder_path: str):
    in_folder = Path(folder_path).resolve()
    if not in_folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        sys.exit(1)

    out_folder = in_folder.parent / "shifted_up"
    out_folder.mkdir(exist_ok=True)

    docx_files = [f for f in in_folder.rglob("*.docx") if not f.name.startswith("~$")]

    if not docx_files:
        print("No .docx files found in the directory or its subfolders.")
        return

    failed_files = []

    for docx_file in docx_files:
        rel_path = docx_file.relative_to(in_folder)
        out_file = out_folder / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Processing (Shift Up): {rel_path}")
        try:
            doc = Document(docx_file)
            
            for para in doc.paragraphs:
                level = get_heading_level(para.style.name)
                if 1 <= level <= 8:
                    para.style = doc.styles[f'Heading {level + 1}']
                    
            doc.save(out_file)
        except Exception as e:
            print(f"  [ERROR] Skipped corrupted file: {e}")
            failed_files.append(rel_path)
            continue
            
    print(f"\nSuccessfully processed {len(docx_files) - len(failed_files)} files. Saved to: {out_folder}")
    if failed_files:
        print(f"\n[WARNING] {len(failed_files)} files failed (corrupted/missing images) and were skipped:")
        for f in failed_files:
            print(f"  - {f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively shift heading levels UP.")
    parser.add_argument("folder", type=str, help="Path to the root folder containing the docx files.")
    args = parser.parse_args()
    shift_up_headings(args.folder)

    