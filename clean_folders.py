import os
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict

# ==========================================
# CONFIGURATION - EDIT THESE PATHS
# ==========================================
# Add as many source folders as you want to compare and merge
SOURCE_FOLDERS = [
    r"C:\Users\ZICO\Desktop\medzone-documents\2025\Hématologie",
    r"C:\Users\ZICO\Desktop\medzone-documents\2025\_après_comparaison\Hématologie",
    # r"C:\Users\ZICO\Desktop\medzone-documents\2025\_comparaison\Pédiatrie et urgence pédiatrique",
    # r"C:\path\to\your\third_folder", 
]

# The dedicated path where the clean, combined folder will be created
OUTPUT_FOLDER = r"C:\Users\ZICO\Desktop\medzone-documents\2025\_version_finale\Hématologie"

# Set to True if you want the script to physically delete the duplicate 
# files from the SOURCE_FOLDERS to free up space. 
# WARNING: Set to False first to test safely!
DELETE_DUPLICATES = False 
# ==========================================

def get_file_hash(filepath, chunk_size=8192):
    """Calculate MD5 hash of a file to compare contents."""
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def merge_and_deduplicate():
    source_paths = [Path(f) for f in SOURCE_FOLDERS]
    output_path = Path(OUTPUT_FOLDER)
    
    # Ensure output folder exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    seen_hashes = {} # hash -> {'rel_path': relative_path, 'source': source_folder}
    duplicates_log = defaultdict(list) # hash -> [list of duplicate paths]
    
    stats = {
        'total_files': 0,
        'unique_files': 0,
        'duplicates_skipped': 0,
        'total_size_bytes': 0,
        'duplicate_size_bytes': 0,
    }
    
    print("Scanning folders and comparing contents...\n")
    
    for source in source_paths:
        if not source.exists() or not source.is_dir():
            print(f"Warning: {source} does not exist. Skipping.")
            continue
            
        for root, dirs, files in os.walk(source):
            for file in files:
                filepath = Path(root) / file
                rel_path = filepath.relative_to(source)
                file_size = filepath.stat().st_size
                
                stats['total_files'] += 1
                stats['total_size_bytes'] += file_size
                
                file_hash = get_file_hash(filepath)
                if not file_hash:
                    continue
                
                if file_hash in seen_hashes:
                    # --- DUPLICATE FOUND ---
                    stats['duplicates_skipped'] += 1
                    stats['duplicate_size_bytes'] += file_size
                    duplicates_log[file_hash].append(str(filepath))
                    
                    if DELETE_DUPLICATES:
                        try:
                            filepath.unlink() # Delete the duplicate file
                        except Exception as e:
                            print(f"Failed to delete duplicate {filepath}: {e}")
                else:
                    # --- UNIQUE FILE ---
                    seen_hashes[file_hash] = {
                        'rel_path': rel_path,
                        'source': source
                    }
                    stats['unique_files'] += 1
                    
                    # Copy to output folder preserving the exact folder structure
                    dest_path = output_path / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Edge case: If two different source folders have a file with the 
                    # exact same relative path but DIFFERENT content, we avoid overwriting.
                    if dest_path.exists():
                        stem = dest_path.stem
                        suffix = dest_path.suffix
                        counter = 1
                        while dest_path.exists():
                            dest_path = output_path / f"{stem}_{counter}{suffix}"
                            counter += 1
                            
                    shutil.copy2(filepath, dest_path)
                    
    return stats, seen_hashes, duplicates_log

if __name__ == "__main__":
    print("--- DEDUPLICATION & MERGE TOOL ---")
    print(f"Sources: {SOURCE_FOLDERS}")
    print(f"Output:  {OUTPUT_FOLDER}")
    print(f"Delete Original Dupes: {DELETE_DUPLICATES}\n")
    
    stats, seen, dupes = merge_and_deduplicate()
    
    print("\n--- PROCESS COMPLETE ---")
    print(f"Total files scanned:   {stats['total_files']}")
    print(f"Unique files kept:     {stats['unique_files']}")
    print(f"Duplicates removed:    {stats['duplicates_skipped']}")
    print(f"Total size scanned:    {format_size(stats['total_size_bytes'])}")
    print(f"Space saved (dupes):   {format_size(stats['duplicate_size_bytes'])}")
    
    if dupes:
        print("\n--- DUPLICATE DETAILS (First 10) ---")
        count = 0
        for hash_val, paths in dupes.items():
            if count >= 10:
                print(f"... and {len(dupes) - 10} more duplicate groups.")
                break
            original = seen[hash_val]['rel_path']
            print(f"\n[KEPT] {original}")
            for p in paths:
                print(f"   [DELETED/SKIPPED] {p}")
            count += 1
            
    print("\nDone! You can now ZIP the output folder and upload it to your Django server.")


