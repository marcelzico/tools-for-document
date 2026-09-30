#!/usr/bin/env python3
"""
PDF to TXT Converter
Converts PDF documents to plain text files.
Outputs to a completely separate directory, reproducing the original folder structure.
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Please run: pip install PyMuPDF")
    sys.exit(1)


class PdfToTxtConverter:
    """Convert PDF files to TXT with separated output."""
    
    def __init__(self, input_dir: str, output_dir: str = None):
        self.input_dir = Path(input_dir).resolve()
        
        # If no output directory is specified, create a separate sibling folder
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            # Added '_txt' to avoid overwriting the DOCX converted folder if they share a parent
            self.output_dir = self.input_dir.parent / f"{self.input_dir.name}_converted_txt"
            
        self.stats = {
            'files_converted': 0,
            'errors': 0,
            'pages_processed': 0
        }

    def convert_file(self, pdf_path: Path) -> bool:
        """Convert a single PDF file to TXT."""
        print(f"\nConverting: {pdf_path}")
        
        try:
            # Calculate output paths
            rel_path = pdf_path.relative_to(self.input_dir)
            txt_path = self.output_dir / rel_path.with_suffix('.txt')
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open PDF and extract text
            doc = fitz.open(pdf_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text as plain text
                text = page.get_text("text")
                
                # Add a page separator for better readability
                text_content.append(f"\n--- Page {page_num + 1} ---\n{text}")
                self.stats['pages_processed'] += 1
                
            doc.close()
            
            # Write to TXT file
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_content))
            
            print(f"  ✓ Saved: {txt_path}")
            self.stats['files_converted'] += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error converting {pdf_path.name}: {e}")
            self.stats['errors'] += 1
            return False

    def convert_all(self, pattern: str = "**/*.pdf"):
        """Convert all PDF files in the input directory recursively."""
        print(f"Input directory:  {self.input_dir}")
        print(f"Output directory: {self.output_dir} (Completely separated)")
        print("-" * 60)
        
        pdf_files = list(self.input_dir.glob(pattern))
        
        if not pdf_files:
            print("No PDF files found!")
            return
        
        print(f"Found {len(pdf_files)} PDF file(s)\n")
        
        for pdf_file in pdf_files:
            # Check if the target txt file already exists in the output folder
            rel_path = pdf_file.relative_to(self.input_dir)
            txt_equiv = self.output_dir / rel_path.with_suffix('.txt')
            
            if txt_equiv.exists():
                print(f"\nSkipping (already converted): {pdf_file}")
                continue
            
            self.convert_file(pdf_file)
        
        self.print_statistics()

    def print_statistics(self):
        """Print conversion statistics."""
        print("\n" + "=" * 60)
        print("Conversion Statistics:")
        print("=" * 60)
        print(f"Files converted: {self.stats['files_converted']}")
        print(f"Pages processed: {self.stats['pages_processed']}")
        print(f"Errors:          {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Convert PDF files to TXT with separated output.")
    parser.add_argument("input_dir", help="Input directory containing PDF files")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: {input_folder}_converted_txt)", default=None)
    parser.add_argument("--pattern", help="Glob pattern to match files", default="**/*.pdf")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Invalid input directory: {input_path}")
        sys.exit(1)
    
    converter = PdfToTxtConverter(input_dir=args.input_dir, output_dir=args.output_dir)
    converter.convert_all(pattern=args.pattern)


if __name__ == "__main__":
    main()