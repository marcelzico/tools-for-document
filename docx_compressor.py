import sys
import argparse
import shutil
import zipfile
import tempfile
from pathlib import Path
from PIL import Image
import io

def compress_image(image_data: bytes, max_size: tuple = (1920, 1080), quality: int = 85) -> bytes:
    """
    Compresses an image while maintaining reasonable quality.
    
    Args:
        image_data: Original image bytes
        max_size: Maximum dimensions (width, height)
        quality: JPEG quality (1-100, lower = more compression)
    
    Returns:
        Compressed image bytes
    """
    try:
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Compress to JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
    except Exception as e:
        print(f"    ⚠ Could not compress image: {e}")
        return image_data  # Return original if compression fails

def compress_docx(docx_path: Path, output_path: Path, max_size: tuple, quality: int) -> tuple:
    """
    Compresses a single .docx file by compressing its images.
    
    Returns:
        (original_size, compressed_size)
    """
    original_size = docx_path.stat().st_size
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract docx (it's a ZIP file)
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)
        
        # Find and compress all images in word/media/
        media_path = temp_path / 'word' / 'media'
        compressed_count = 0
        
        if media_path.exists():
            for img_file in media_path.iterdir():
                if img_file.is_file():
                    # Read original image
                    with open(img_file, 'rb') as f:
                        original_data = f.read()
                    
                    # Compress image
                    compressed_data = compress_image(original_data, max_size, quality)
                    
                    # Save compressed image
                    with open(img_file, 'wb') as f:
                        f.write(compressed_data)
                    
                    compressed_count += 1
        
        # Repack as docx
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
    
    compressed_size = output_path.stat().st_size
    
    return original_size, compressed_size, compressed_count

def compress_word_documents(source_folder: str, max_size: tuple = (1920, 1080), 
                            quality: int = 85, dry_run: bool = False):
    """
    Recursively compresses all .docx files in a folder by compressing their images.
    Creates a new folder with _compressed suffix.
    
    Args:
        source_folder: Path to the source folder
        max_size: Maximum image dimensions (width, height)
        quality: JPEG quality (1-100)
        dry_run: If True, only shows what would be done
    """
    source_path = Path(source_folder).resolve()
    
    if not source_path.is_dir():
        print(f"Error: {source_folder} is not a valid directory.")
        sys.exit(1)
    
    dest_path = source_path.parent / f"{source_path.name}_compressed"
    
    print(f"Source folder: {source_path}")
    print(f"Destination folder: {dest_path}")
    print(f"Compression settings: max_size={max_size}, quality={quality}")
    
    if dry_run:
        print("[DRY RUN MODE - No files will be compressed]\n")
    else:
        print("\n")
        dest_path.mkdir(parents=True, exist_ok=True)
    
    # Find all .docx files
    docx_files = [f for f in source_path.rglob("*.docx") if not f.name.startswith("~$")]
    
    if not docx_files:
        print("No .docx files found.")
        return
    
    print(f"Found {len(docx_files)} .docx file(s)\n")
    
    total_original_size = 0
    total_compressed_size = 0
    total_images_compressed = 0
    error_count = 0
    
    for docx_file in docx_files:
        rel_path = docx_file.relative_to(source_path)
        dest_docx = dest_path / rel_path
        
        try:
            if dry_run:
                print(f"  [WOULD COMPRESS]: {rel_path}")
            else:
                # Create parent directory
                dest_docx.parent.mkdir(parents=True, exist_ok=True)
                
                # Compress the document
                original_size, compressed_size, img_count = compress_docx(
                    docx_file, dest_docx, max_size, quality
                )
                
                # Calculate reduction
                reduction = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
                
                # Format sizes
                orig_mb = original_size / (1024 * 1024)
                comp_mb = compressed_size / (1024 * 1024)
                
                print(f"  ✓ {rel_path}")
                print(f"    {orig_mb:.2f} MB → {comp_mb:.2f} MB ({reduction:.1f}% reduction, {img_count} images)")
                
                total_original_size += original_size
                total_compressed_size += compressed_size
                total_images_compressed += img_count
                
        except Exception as e:
            print(f"  ⚠ ERROR compressing {rel_path}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"COMPRESSION SUMMARY:")
    print(f"{'='*60}")
    print(f"  Documents processed: {len(docx_files)}")
    print(f"  Total images compressed: {total_images_compressed}")
    
    if total_original_size > 0:
        total_reduction = ((total_original_size - total_compressed_size) / total_original_size * 100)
        print(f"  Total original size: {total_original_size / (1024 * 1024):.2f} MB")
        print(f"  Total compressed size: {total_compressed_size / (1024 * 1024):.2f} MB")
        print(f"  Overall reduction: {total_reduction:.1f}%")
    
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")
    
    if not dry_run and total_images_compressed > 0:
        print(f"\n✓ Compressed folder created: {dest_path}")
        print(f"You can now verify the contents and delete the original folder if satisfied.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compress Word documents by compressing their images."
    )
    parser.add_argument(
        "folder", 
        type=str, 
        help="Path to the source folder"
    )
    parser.add_argument(
        "--max-width", 
        type=int, 
        default=1920,
        help="Maximum image width in pixels (default: 1920)"
    )
    parser.add_argument(
        "--max-height", 
        type=int, 
        default=1080,
        help="Maximum image height in pixels (default: 1080)"
    )
    parser.add_argument(
        "--quality", 
        type=int, 
        default=85,
        help="JPEG quality 1-100 (default: 85, lower = more compression)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be done without actually compressing"
    )
    
    args = parser.parse_args()
    
    max_size = (args.max_width, args.max_height)
    compress_word_documents(
        args.folder, 
        max_size=max_size, 
        quality=args.quality, 
        dry_run=args.dry_run
    )
    