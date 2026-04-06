import os
import time
import json
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import subprocess
from pathlib import Path
from database.db import add_product

# Configuration
API_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")

def get_api_key():
    if not os.path.exists(API_KEY_FILE):
        print(f"CRITICAL: API key file not found at {API_KEY_FILE}")
        print("Please create this file and paste your Google AI Studio API key in it.")
        return None
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()

def setup_gemini():
    api_key = get_api_key()
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def render_pdf_to_image(pdf_path, output_path):
    """
    Renders a single-page PDF to a JPG image using Ghostscript.
    """
    gs_path = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"
    if not os.path.exists(gs_path):
        return False
        
    cmd = [
        gs_path,
        "-sDEVICE=jpeg",
        "-dJPEGQ=90",
        "-r150", # Render at 150 DPI for clarity
        "-dNOPAUSE",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        pdf_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return True
    except Exception as e:
        print(f"Error rendering PDF debug image: {e}")
        return False

def save_debug_image(source_file, deals, output_dir):
    """
    Draws bounding boxes and labels on the source file (rendering it first if PDF).
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(source_file)
    base_name = os.path.splitext(filename)[0]
    debug_image_path = os.path.join(output_dir, f"{base_name}_debug.jpg")
    
    # 1. Get the image to draw on
    if source_file.lower().endswith(".pdf"):
        if not render_pdf_to_image(source_file, debug_image_path):
            return
        img = Image.open(debug_image_path)
    else:
        img = Image.open(source_file)
        
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # 2. Draw boxes
    for deal in deals:
        box = deal.get("box_2d") # [ymin, xmin, ymax, xmax] 0-1000
        if not box: continue
        
        ymin, xmin, ymax, xmax = box
        
        # Convert to pixels
        abs_ymin = (ymin / 1000) * h
        abs_xmin = (xmin / 1000) * w
        abs_ymax = (ymax / 1000) * h
        abs_xmax = (xmax / 1000) * w
        
        # Draw rectangle
        draw.rectangle([abs_xmin, abs_ymin, abs_xmax, abs_ymax], outline="red", width=3)
        
        # Draw label (Product Name + Price)
        label = f"{deal.get('product_name', 'Unknown')}\n{deal.get('price_deal', '?')}"
        
        # Draw text background
        text_pos = (abs_xmin, max(0, abs_ymin - 40))
        bbox = draw.textbbox(text_pos, label)
        draw.rectangle(bbox, fill="red")
        draw.text(text_pos, label, fill="white")
        
    # 3. Save
    img.save(debug_image_path)
    print(f"  -> Saved debug image: {debug_image_path}")

def save_masked_image(source_file, deals, output_dir):
    """
    Draws FILLED black boxes on the source file to mask detected deals.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(source_file)
    base_name = os.path.splitext(filename)[0]
    masked_image_path = os.path.join(output_dir, f"{base_name}_masked.jpg")
    
    # 1. Get the image to draw on
    if source_file.lower().endswith(".pdf"):
        # We can reuse the debug image if it exists to save rendering time, 
        # but to be clean/independent, let's render again or check cache.
        # For now, just render.
        if not render_pdf_to_image(source_file, masked_image_path):
            return
        img = Image.open(masked_image_path)
    else:
        img = Image.open(source_file)
        
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # 2. Draw Black Boxes
    for deal in deals:
        box = deal.get("box_2d")
        if not box: continue
        
        ymin, xmin, ymax, xmax = box
        
        # Convert to pixels
        abs_ymin = (ymin / 1000) * h
        abs_xmin = (xmin / 1000) * w
        abs_ymax = (ymax / 1000) * h
        abs_xmax = (xmax / 1000) * w
        
        # Draw filled rectangle (Black)
        draw.rectangle([abs_xmin, abs_ymin, abs_xmax, abs_ymax], fill="black", outline="black")
        
    # 3. Save
    img.save(masked_image_path)
    print(f"  -> Saved masked image: {masked_image_path}")

def extract_from_batch(file_paths, primary_model_name):
    """
    Uploads 4 files and sends them in a single request to Gemini.
    Implements fallback logic: Primary -> 2.5 Flash -> 2.0 Flash.
    """
    print(f"Analyzing batch of {len(file_paths)} pages...")
    
    fallback_chain = [
        primary_model_name,
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash" # Ultimate safety net
    ]
    
    # Remove duplicates while preserving order
    models_to_try = []
    seen = set()
    for m in fallback_chain:
        if m not in seen:
            models_to_try.append(m)
            seen.add(m)
            
    uploaded_files = []
    
    try:
        for path in file_paths:
            # print(f"  -> Uploading {os.path.basename(path)}...")
            f = genai.upload_file(path=path, display_name=os.path.basename(path))
            uploaded_files.append(f)
            
        # Prompt
        prompt = """
**Role:**
You are a highly accurate Data Extraction AI specialized in analyzing Dutch supermarket flyers. Your goal is to extract structured data for every single product deal visible on the page.

**Task:**
Analyze the provided flyer pages (up to 5). For each distinct product deal, extract the following fields into a JSON object.

**Input Context:**
The input is a sequence of PDF pages (Page Index 0, 1, 2, 3, 4). Process them in order.

**Visual Grouping:**
Identify the visual cluster for each deal: Product Image + Text + Price.

**Extraction Fields:**
1.  **page_index**: (Integer) Index of the file (0, 1, etc.).
2.  **product_category**: (String) The general category in Dutch (e.g., "Koffie", "Wasmiddel", "Luiers", "Bier"). Keep it high-level.
3.  **product_name**: (String) The FULL descriptive name including Brand AND Product Type (e.g., "Douwe Egberts Aroma Rood Snelfiltermaling", "Robijn Color Wasmiddel", "Ah Huismerk Pindakaas").
    *   **CRITICAL**: Do NOT use vague names like "3 pakken" or "Alle varianten". You MUST identify the product type (e.g., "Koffie", "Chips", "Shampoo").
    *   If the text says "Alle Unox Soep in Zak", the name should be "Unox Soep in Zak".
4.  **brand**: (String) The specific brand (e.g., "Douwe Egberts", "Robijn", "Ah Huismerk").
5.  **volume_weight**: (String) The content/weight (e.g., "500g", "1.5 liter", "4 stuks"). If unknown, use null.
6.  **amount_logic**: (String) The deal rule (e.g., "1+1 gratis", "2e halve prijs", "2 voor €5"). If just a price cut, use "per stuk".
7.  **item_count**: (Integer) The number of items required for the deal (e.g., "1+1 gratis" -> 2). Default to 1.
8.  **price_deal**: (Float) The final discounted price (e.g., 4.99).
    *   **CRITICAL**: If you cannot find a price, LOOK AGAIN closely at the visual cluster. Prices are often large and bold. If absolutely no price is visible, use null.
9.  **box_2d**: (Array) [ymin, xmin, ymax, xmax] normalized to 0-1000. Tightly bound the product image and text.

**Response Format:**
Output strictly valid JSON.

Example:
{
  "deals": [
    {
      "page_index": 0,
      "product_category": "Wasmiddel",
      "product_name": "Robijn Color Wasmiddel",
      "brand": "Robijn",
      "volume_weight": "700ml",
      "amount_logic": "1+1 gratis",
      "item_count": 2,
      "price_deal": 4.99,
      "box_2d": [100, 200, 300, 400]
    }
  ]
}
"""
        content = uploaded_files + [prompt]
        
        for model_name in models_to_try:
            try:
                print(f"  -> Sending request to {model_name}...", end="", flush=True)
                start_time = time.time()
                
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(content)
                
                elapsed = time.time() - start_time
                print(f" Done ({elapsed:.1f}s)")
                
                # Clean up response text
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                    
                data = json.loads(text)
                deals = data.get("deals", [])
                
                # If successful, print and break
                print(f"  -> Success with {model_name}: Found {len(deals)} deals.")
                
                # Map back to file paths
                results = []
                for deal in deals:
                    idx = deal.get("page_index", 0)
                    if 0 <= idx < len(file_paths):
                        deal["source_file"] = file_paths[idx]
                        results.append(deal)
                
                return results
                
            except Exception as e:
                print(f"  -> Failed with {model_name}: {e}")
                time.sleep(1) # Brief pause before retry
                continue
        
        print("  -> All models failed.")
        return []
        
    except Exception as e:
        print(f"Error preparing batch: {e}")
        return []

def run_extraction(folder_path, model_name="models/gemini-2.0-flash", debug_mode=False):
    if not setup_gemini():
        return

    print(f"Starting extraction in: {folder_path} using model: {model_name} (Debug: {debug_mode})")
    
    for root, dirs, files in os.walk(folder_path):
        # Determine store from path structure
        parts = Path(root).parts
        if "week" in parts[-2] and "pages" not in parts: 
            store_name = parts[-1]
            try:
                week_str = parts[-2]
                week = int(week_str.split(" ")[1])
                year = 2025 
            except:
                continue
            
            # Debug directories
            debug_dir = os.path.join(root, "debug")
            masked_dir = os.path.join(root, "masked")
            
            # Collect all files to process
            files_to_process = []
            pages_dir = os.path.join(root, "pages")
            
            if os.path.exists(pages_dir):
                print(f"Found preprocessed pages for {store_name}")
                # Sort by page number
                page_files = [f for f in os.listdir(pages_dir) if f.lower().startswith("page_") and f.lower().endswith(".pdf")]
                # Sort logic: page_1, page_2, page_10...
                page_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]) if "_" in x else 0)
                files_to_process = [os.path.join(pages_dir, f) for f in page_files]
            else:
                print(f"Using original files for {store_name}")
                files_to_process = [os.path.join(root, f) for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]

            # Batch processing (5 at a time)
            batch_size = 5
            for i in range(0, len(files_to_process), batch_size):
                batch = files_to_process[i : i + batch_size]
                
                print(f"Processing batch {i//batch_size + 1} ({len(batch)} pages)...")
                
                deals = extract_from_batch(batch, model_name)
                
                if deals:
                    print(f"  -> Found {len(deals)} deals in batch.")
                    
                    # Group deals by source file for debugging
                    deals_by_file = {}
                    
                    for deal in deals:
                        # Determine page number from filename
                        fpath = deal.get("source_file", "")
                        if fpath not in deals_by_file: deals_by_file[fpath] = []
                        deals_by_file[fpath].append(deal)
                        
                        fname = os.path.basename(fpath)
                        page_num = 1
                        try:
                            if "page_" in fname:
                                page_num = int(fname.split("page_")[1].split(".")[0])
                        except:
                            pass
                            
                        # Map Gemini fields to DB fields
                        if "product_category" in deal:
                            deal["category"] = deal.pop("product_category")
                            
                        add_product(store_name, week, year, page_num, deal)
                    
                    # Generate debug images
                    if debug_mode:
                        for fpath, file_deals in deals_by_file.items():
                            save_debug_image(fpath, file_deals, debug_dir)
                            save_masked_image(fpath, file_deals, masked_dir)
                    
                    # Rate limit sleep
                    time.sleep(2) 
                else:
                    print("  -> No deals found in batch.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to folder to extract from")
    parser.add_argument("--model", default="models/gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--debug", action="store_true", help="Enable visual debugging (draw bounding boxes)")
    args = parser.parse_args()
    
    run_extraction(args.path, args.model, debug_mode=args.debug)
