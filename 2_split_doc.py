import sys
import argparse
import shutil
import re
from pathlib import Path
from docx import Document
from utils import sanitize_filename

def get_heading_level_robust(para) -> int:
    """
    The most powerful way to detect heading levels in python-docx.
    1. Checks style name (handles 'Heading 1', 'Heading1', 'Titre 1', etc.)
    2. Falls back to XML <w:outlineLvl> which is the absolute source of truth in Word.
    """
    # 1. Style Name Check
    style_name = para.style.name if para.style else ""
    if style_name:
        match = re.search(r'(?:heading|titre)\s*(\d+)', style_name.lower())
        if match:
            return int(match.group(1))
    
    # 2. XML Outline Level Check (0-indexed: 0 = Heading 1, 1 = Heading 2)
    pPr = para._element.pPr
    if pPr is not None and pPr.outlineLvl is not None:
        return int(pPr.outlineLvl.val) + 1
        
    return 0

def deduplicate_heading(text):
    """
    Fixes the bug where the heading text is repeated 3 times in the document's XML.
    It detects if the first word appears 3 times and truncates the string to the first occurrence.
    """
    if not text:
        return text
    
    text = text.strip()
    if not text:
        return text
        
    # Find the first word
    first_word = text.split()[0]
    if len(first_word) < 2:
        return text
        
    # Find the second and third occurrences of the first word
    idx1 = text.find(first_word, 1)
    if idx1 == -1:
        return text
        
    idx2 = text.find(first_word, idx1 + 1)
    if idx2 == -1:
        return text
        
    # If we found 3 occurrences, it's duplicated.
    # The first repetition ends at `idx1`.
    return text[:idx1].strip()

def split_by_heading_1(folder_path: str):
    in_folder = Path(folder_path).resolve()
    if not in_folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory.")
        sys.exit(1)

    out_folder = in_folder.parent / "splitted"
    out_folder.mkdir(exist_ok=True)

    docx_files = [f for f in in_folder.rglob("*.docx") if not f.name.startswith("~$")]

    if not docx_files:
        print("No .docx files found.")
        return

    success_count = 0
    error_count = 0

    for docx_file in docx_files:
        rel_path = docx_file.relative_to(in_folder)
        out_dir = out_folder / rel_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nProcessing (Split): {rel_path}")

        try:
            doc = Document(docx_file)
        except Exception as e:
            print(f"  ⚠ SKIPPED (corrupted file): {e}")
            error_count += 1
            continue

        try:
            body_elements = list(doc.element.body)
            
            # Store tuples of (xml_index, paragraph_object)
            h1_data = [] 
            
            # Find all Heading 1s using the robust method
            for para in doc.paragraphs:
                if get_heading_level_robust(para) == 1:
                    try:
                        idx = body_elements.index(para._element)
                        h1_data.append((idx, para))
                    except ValueError:
                        pass # Paragraph might be in a header, footer, or textbox

            # Extract just the indices for the chapter splitting logic
            h1_indices = [item[0] for item in h1_data]
            print(f"  -> Found {len(h1_indices)} Heading 1(s).")

            # EXCEPTION: If 1 or 0 Heading 1, just copy the file
            if len(h1_indices) <= 1:
                print(f"  -> 1 or 0 Heading 1 found. Copying as-is.")
                shutil.copy2(docx_file, out_dir / docx_file.name)
                success_count += 1
                continue

            # Determine start/end XML indices for each chapter
            chapters = []
            for i in range(len(h1_indices)):
                start = h1_indices[i] if i > 0 else 0
                end = h1_indices[i+1] if i + 1 < len(h1_indices) else len(body_elements)
                chapters.append((start, end))

            used_names = {}
            
            for i, (start, end) in enumerate(chapters):
                if i == 0 and h1_indices[0] > 0:
                    heading_text = "00_Preamble"
                else:
                    # Use python-docx's built-in para.text
                    para = h1_data[i][1]
                    heading_text = para.text.strip()
                    
                    # NEW: Deduplicate the heading text if it's repeated 3 times
                    heading_text = deduplicate_heading(heading_text)
                    
                    if not heading_text:
                        heading_text = f"Chapter_{i+1}"

                safe_name = sanitize_filename(heading_text)
                
                if safe_name in used_names:
                    used_names[safe_name] += 1
                    safe_name = f"{safe_name}_{used_names[safe_name]}"
                else:
                    used_names[safe_name] = 0

                out_path = out_dir / f"{safe_name}.docx"
                
                # 1. Copy original to preserve ALL formatting, headers, footers, and images
                shutil.copy2(docx_file, out_path)
                
                # 2. Open copy and delete XML elements outside the current chapter's range
                new_doc = Document(out_path)
                new_body_elements = list(new_doc.element.body)
                
                to_remove = [elem for idx, elem in enumerate(new_body_elements) if idx < start or idx >= end]
                for elem in to_remove:
                    new_doc.element.body.remove(elem)
                    
                new_doc.save(out_path)
                print(f"  -> Created: {safe_name}.docx")

            success_count += 1
        except Exception as e:
            print(f"  ⚠ SKIPPED (error during processing): {e}")
            error_count += 1

    print(f"\nDone. {success_count} succeeded, {error_count} skipped.")
    print(f"Saved to: {out_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively split docx files by Heading 1.")
    parser.add_argument("folder", type=str, help="Path to the 'shifted_up' folder.")
    args = parser.parse_args()
    split_by_heading_1(args.folder)