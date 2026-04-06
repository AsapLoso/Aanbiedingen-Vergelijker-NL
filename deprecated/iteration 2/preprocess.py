import os
import subprocess
import shutil
from pathlib import Path
from pypdf import PdfReader, PdfWriter

# Ghostscript path provided by user
GS_PATH = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"

def split_and_optimize_pdf(pdf_path, force=False):
    """
    Splits a PDF into single pages using pypdf (lossless).
    Then downsamples each page to 96 DPI using Ghostscript.
    Keeps the smaller of the two files.
    """
    if not os.path.exists(GS_PATH):
        print(f"CRITICAL: Ghostscript not found at {GS_PATH}")
        return False

    parent_dir = os.path.dirname(pdf_path)
    pages_dir = os.path.join(parent_dir, "pages")
    
    # Check if already processed (Smart Check)
    if os.path.exists(pages_dir) and not force:
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            # Check if all expected pages exist
            all_pages_exist = True
            for i in range(total_pages):
                expected_page = os.path.join(pages_dir, f"page_{i+1}.pdf")
                if not os.path.exists(expected_page):
                    all_pages_exist = False
                    break
            
            if all_pages_exist:
                print(f"Skipping {os.path.basename(pdf_path)}: All {total_pages} pages already exist.")
                return True
            else:
                print(f"Resuming {os.path.basename(pdf_path)}: Some pages missing.")
        except Exception as e:
            print(f"Error checking existing pages for {pdf_path}: {e}")
            # If error reading PDF, proceed to try processing it
            pass
    
    os.makedirs(pages_dir, exist_ok=True)
    print(f"Preprocessing {os.path.basename(pdf_path)}...")

    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            base_name = f"page_{page_num}"
            orig_path = os.path.join(pages_dir, f"{base_name}_orig.pdf")
            opt_path = os.path.join(pages_dir, f"{base_name}_opt.pdf")
            final_path = os.path.join(pages_dir, f"{base_name}.pdf")
            
            # 1. Save Original Page (Split)
            writer = PdfWriter()
            writer.add_page(page)
            with open(orig_path, "wb") as f:
                writer.write(f)
            
            # 2. Downsample with Ghostscript (96 DPI)
            cmd = [
                GS_PATH,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dDownsampleColorImages=true",
                "-dColorImageResolution=72", # Lowered to 72 DPI
                "-dNOPAUSE",
                "-dBATCH",
                f"-sOutputFile={opt_path}",
                orig_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            # Small delay to let OS release handles/Explorer release locks
            import time
            time.sleep(0.5)
            
            # 3. Compare Sizes
            orig_size = os.path.getsize(orig_path)
            opt_size = os.path.getsize(opt_path)
            
            def safe_move_or_copy(src, dst, is_move=True):
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        if is_move:
                            shutil.move(src, dst)
                        else:
                            shutil.copy(src, dst)
                        return True
                    except PermissionError:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            print(f"  -> Failed to {'move' if is_move else 'copy'} {src} to {dst} (File in use)")
                            raise
            
            def safe_remove(path):
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                        return
                    except PermissionError:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            print(f"  -> Failed to remove {path} (File in use)")

            if opt_size < orig_size:
                # Optimized is smaller, keep it
                if os.path.exists(final_path):
                    safe_remove(final_path)
                safe_move_or_copy(opt_path, final_path, is_move=True)
                print(f"  Page {page_num}: Optimized ({orig_size/1024:.1f}KB -> {opt_size/1024:.1f}KB)")
            else:
                # Original is smaller (or GS failed to compress), keep original
                if os.path.exists(final_path):
                    safe_remove(final_path)
                safe_move_or_copy(orig_path, final_path, is_move=False)
                print(f"  Page {page_num}: Original kept ({orig_size/1024:.1f}KB)")
            
            # Cleanup temp files
            safe_remove(orig_path)
            safe_remove(opt_path)

        return True
        
    except Exception as e:
        print(f"  -> Error processing PDF: {e}")
        return False

def run_preprocessing(folder_path, force=False):
    print(f"Scanning for PDFs to preprocess in: {folder_path}")
    
    for root, dirs, files in os.walk(folder_path):
        if "pages" in os.path.basename(root):
            continue
            
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                split_and_optimize_pdf(pdf_path, force)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to folder to preprocess")
    parser.add_argument("--force", action='store_true', help="Force overwrite")
    args = parser.parse_args()
    
    run_preprocessing(args.path, args.force)
