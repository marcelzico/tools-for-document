#!/usr/bin/env python3
"""
DOCX to Markdown Converter (v3 - Separated Output & Global Assets)
Converts Word documents to Markdown with proper formatting, tables, and formulas.
Outputs to a completely separate directory, reproducing the original folder structure.
Uses a global _assets folder and SHA-256 hashing to prevent duplicate images.
"""

import os
import sys
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import mammoth

try:
    import docxlatex
    HAS_DOCLATEX = True
except ImportError:
    HAS_DOCLATEX = False
    print("Warning: docxlatex not installed. Equations will not be extracted.")


class DocxToMarkdownConverter:
    """Convert DOCX files to Markdown with global image deduplication."""
    
    def __init__(self, input_dir: str, output_dir: str = None):
        self.input_dir = Path(input_dir).resolve()
        
        # If no output directory is specified, create a separate sibling folder
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            self.output_dir = self.input_dir.parent / f"{self.input_dir.name}_converted"
            
        # Global assets folder to prevent duplicate images across documents
        self.global_images_dir = self.output_dir / "_assets" / "images"
        self.global_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Maps image hash (SHA256) to the absolute Path of the saved image
        self.image_hash_map: Dict[str, Path] = {}
        
        self.stats = {
            'files_converted': 0,
            'images_extracted': 0,
            'duplicate_images_skipped': 0,
            'errors': 0,
            'formulas_extracted': 0
        }
        
        # Custom style map for better heading/list conversion
        self.style_map = """
        p[style-name='Heading 1'] => h1:fresh
        p[style-name='Heading 2'] => h2:fresh
        p[style-name='Heading 3'] => h3:fresh
        p[style-name='Heading 4'] => h4:fresh
        p[style-name='Heading 5'] => h5:fresh
        p[style-name='Heading 6'] => h6:fresh
        p[style-name^='Heading'] => h6:fresh
        p[style-name='Title'] => h1:fresh
        p[style-name='Subtitle'] => h2:fresh
        """

    def extract_formulas(self, docx_path: Path) -> Tuple[str, List[str]]:
        """Extract text and formulas from DOCX using docxlatex."""
        if not HAS_DOCLATEX:
            return "", []
        
        try:
            doc = docxlatex.Document(str(docx_path))
            text = doc.get_text()
            equations = doc.equations
            self.stats['formulas_extracted'] += len(equations)
            return text, equations
        except Exception as e:
            print(f"   Warning: Could not extract formulas: {e}")
            return "", []


    def convert_to_markdown(self, docx_path: Path) -> str:
        """Convert DOCX to HTML using mammoth, then to Markdown using markdownify for perfect table support."""
        
        def convert_image(image):
            """Custom image handler that hashes and deduplicates images globally."""
            with image.open() as image_bytes:
                img_data = image_bytes.read()
                
            img_hash = hashlib.sha256(img_data).hexdigest()
            
            if img_hash in self.image_hash_map:
                saved_abs_path = self.image_hash_map[img_hash]
                self.stats['duplicate_images_skipped'] += 1
            else:
                ext = ".png"
                if "jpeg" in image.content_type or "jpg" in image.content_type:
                    ext = ".jpg"
                elif "gif" in image.content_type:
                    ext = ".gif"
                elif "bmp" in image.content_type:
                    ext = ".bmp"
                elif "webp" in image.content_type:
                    ext = ".webp"
                    
                saved_filename = f"{img_hash[:16]}{ext}"
                saved_abs_path = self.global_images_dir / saved_filename
                
                with open(saved_abs_path, 'wb') as f:
                    f.write(img_data)
                    
                self.image_hash_map[img_hash] = saved_abs_path
                self.stats['images_extracted'] += 1
                print(f"  ✓ Extracted new image: {saved_filename}")
            
            rel_path = os.path.relpath(saved_abs_path, self.current_md_path.parent).replace('\\', '/')
            
            return {
                "src": rel_path,
                "alt": image.alt_text or ""
            }
        
        with open(docx_path, "rb") as docx_file:
            # STEP 1: Convert DOCX to HTML (Mammoth handles tables perfectly in HTML)
            result = mammoth.convert_to_html(
                docx_file,
                style_map=self.style_map,
                convert_image=mammoth.images.img_element(convert_image)
            )
            
            for message in result.messages:
                if message.type == "warning":
                    print(f"  ⚠ Warning: {message.message}")
            
            html_content = result.value
            
            # STEP 2: Convert HTML to Markdown (markdownify handles tables perfectly)
            import markdownify
            markdown = markdownify.markdownify(
                html_content, 
                heading_style="ATX",  # Uses # for headings
                bullets='-'           # Uses - for bullet points
            )
            
            # Clean up unnecessary character escapes (like \+ or \-)
            markdown = markdown.replace(r'\+', '+').replace(r'\-', '-')
            
            return markdown

    def post_process_markdown(self, markdown: str, formulas: List[str]) -> str:
        """Post-process Markdown to add formulas and improve formatting."""
        if formulas:
            markdown += "\n\n---\n\n## Mathematical Formulas\n\n"
            for i, formula in enumerate(formulas, 1):
                markdown += f"{i}. ${formula}$\n"
        
        # Clean up multiple blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        return markdown

    def convert_file(self, docx_path: Path) -> bool:
        """Convert a single DOCX file to Markdown."""
        print(f"\nConverting: {docx_path}")
        
        try:
            rel_path = docx_path.relative_to(self.input_dir)
            md_path = self.output_dir / rel_path.with_suffix('.md')
            md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set current md_path for relative path calculation in image callback
            self.current_md_path = md_path
            
            # Extract formulas
            _, formulas = self.extract_formulas(docx_path)
            
            # Convert to markdown (this will also extract and deduplicate images)
            markdown = self.convert_to_markdown(docx_path)
            
            # Post-process
            markdown = self.post_process_markdown(markdown, formulas)
            
            # Add metadata header
            metadata = f"""---
source: {docx_path.name}
converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
formulas: {len(formulas)}
---

"""
            markdown = metadata + markdown
            
            # Write markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  ✓ Saved: {md_path}")
            self.stats['files_converted'] += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error converting {docx_path.name}: {e}")
            self.stats['errors'] += 1
            return False

    def convert_all(self, pattern: str = "**/*.docx"):
        """Convert all DOCX files in the input directory recursively."""
        print(f"Input directory:  {self.input_dir}")
        print(f"Output directory: {self.output_dir} (Completely separated)")
        print(f"Global Images:    {self.global_images_dir}")
        print("-" * 60)
        
        docx_files = list(self.input_dir.glob(pattern))
        
        if not docx_files:
            print("No DOCX files found!")
            return
        
        print(f"Found {len(docx_files)} DOCX file(s)\n")
        
        for docx_file in docx_files:
            # Check if the target markdown file already exists in the output folder
            rel_path = docx_file.relative_to(self.input_dir)
            md_equiv = self.output_dir / rel_path.with_suffix('.md')
            
            if md_equiv.exists():
                print(f"\nSkipping (already converted): {docx_file}")
                continue
            
            self.convert_file(docx_file)
        
        self.print_statistics()

    def print_statistics(self):
        """Print conversion statistics."""
        print("\n" + "=" * 60)
        print("Conversion Statistics:")
        print("=" * 60)
        print(f"Files converted:         {self.stats['files_converted']}")
        print(f"Unique images extracted: {self.stats['images_extracted']}")
        print(f"Duplicate images saved:  {self.stats['duplicate_images_skipped']} (Skipped to save space!)")
        print(f"Formulas extracted:      {self.stats['formulas_extracted']}")
        print(f"Errors:                  {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert DOCX files to Markdown with global image deduplication and separated output.")
    parser.add_argument("input_dir", help="Input directory containing DOCX files")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: {input_folder}_converted)", default=None)
    parser.add_argument("--pattern", help="Glob pattern to match files", default="**/*.docx")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Invalid input directory: {input_path}")
        sys.exit(1)
    
    converter = DocxToMarkdownConverter(input_dir=args.input_dir, output_dir=args.output_dir)
    converter.convert_all(pattern=args.pattern)


if __name__ == "__main__":
    main()