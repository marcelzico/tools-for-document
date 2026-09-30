import os
import sys
import argparse
from pathlib import Path
import csv
import re

def clean_filename(name):
    """Nettoyer le nom de fichier/dossier pour éviter les problèmes."""
    # Supprimer les espaces en début et fin
    name = name.strip()
    # Remplacer les caractères problématiques
    name = name.replace('/', '-').replace('\\', '-')
    # Supprimer les espaces multiples
    name = re.sub(r'\s+', ' ', name)
    return name

def generate_templates(source_path, output_path=None):
    source_dir = Path(source_path).resolve()
    
    if not source_dir.exists():
        print(f"Error: The folder '{source_dir}' does not exist.")
        sys.exit(1)
    
    if not source_dir.is_dir():
        print(f"Error: '{source_dir}' is not a directory.")
        sys.exit(1)
    
    # Si output_path n'est pas fourni, créer un dossier à côté avec suffixe _qa-cl
    if output_path is None:
        output_dir = source_dir.parent / f"{source_dir.name}_qa-cl"
    else:
        output_dir = Path(output_path).resolve()
    
    print(f"Scanning source folder: {source_dir}")
    print(f"Output directory: {output_dir}\n")

    # Parcourir récursivement tous les fichiers
    file_count = 0
    error_count = 0
    
    for lesson_file in source_dir.rglob('*'):
        if lesson_file.is_file() and lesson_file.suffix.lower() in ['.docx', '.pdf', '.txt', '.md']:
            try:
                # Obtenir le chemin relatif par rapport au dossier source
                rel_path = lesson_file.relative_to(source_dir)
                chapter_name = lesson_file.stem
                
                # Nettoyer les noms pour éviter les problèmes
                cleaned_chapter_name = clean_filename(chapter_name)
                cleaned_parent_parts = [clean_filename(part) for part in rel_path.parent.parts]
                
                # Reproduire la structure des dossiers dans la sortie
                chapter_out_dir = output_dir / Path(*cleaned_parent_parts) / cleaned_chapter_name
                chapter_out_dir.mkdir(parents=True, exist_ok=True)
                
                # 1. Create the CSV template
                csv_file = chapter_out_dir / f"qa-{cleaned_chapter_name}.csv"
                if not csv_file.exists():
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                        writer.writerow(["question", "answer", "explanation"])
                    print(f"  ✓ Created: {csv_file.relative_to(output_dir)}")
                
                # 2. Create the TXT template
                txt_file = chapter_out_dir / f"clinical_case-{cleaned_chapter_name}.txt"
                if not txt_file.exists():
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(f"# CAS CLINIQUES : {cleaned_chapter_name.upper()}\n\n")
                        f.write(f"Chapitre: {cleaned_chapter_name}\n")
                        f.write(f"Chemin source: {rel_path}\n")
                        f.write("-" * 50 + "\n\n")
                    print(f"  ✓ Created: {txt_file.relative_to(output_dir)}")
                
                file_count += 1
                
            except Exception as e:
                print(f"  ✗ Error processing {lesson_file.name}: {e}")
                error_count += 1
    
    if file_count == 0:
        print(f"No lesson files found in {source_dir}")
    else:
        print(f"\nProcessed {file_count} lesson file(s)")
        if error_count > 0:
            print(f"Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate empty exercise template files (CSV and TXT) for medical revision.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "C:\\path\\to\\5ème année"
  %(prog)s "C:\\path\\to\\5ème année\\Chirurgie pédiatrique"
  %(prog)s "C:\\path\\to\\5ème année" -o "C:\\path\\to\\custom_output"
        """
    )
    
    parser.add_argument("source_path", help="Path to the source folder (can be any level)")
    parser.add_argument("-o", "--output", required=False, help="Path to the output directory (default: creates '{source_folder}_qa-cl' next to the source)")
    
    args = parser.parse_args()
    
    generate_templates(args.source_path, args.output)
    print("\nDone! Your folder structure is ready for copy-pasting.")