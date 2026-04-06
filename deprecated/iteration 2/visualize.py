import os
import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess
from database.db import get_products

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
    Draws bounding boxes and labels on the source file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(source_file)
    base_name = os.path.splitext(filename)[0]
    debug_image_path = os.path.join(output_dir, f"{base_name}_viz.jpg")
    
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
        box_json = deal.get("box_2d")
        if not box_json: continue
        
        try:
            box = json.loads(box_json)
        except:
            continue
            
        ymin, xmin, ymax, xmax = box
        
        # Convert to pixels
        abs_ymin = (ymin / 1000) * h
        abs_xmin = (xmin / 1000) * w
        abs_ymax = (ymax / 1000) * h
        abs_xmax = (xmax / 1000) * w
        
        # Draw rectangle
        draw.rectangle([abs_xmin, abs_ymin, abs_xmax, abs_ymax], outline="blue", width=3)
        
        # Draw label
        label = f"{deal.get('product_name', 'Unknown')}\n{deal.get('deal_price', '?')}"
        
        # Draw text background
        text_pos = (abs_xmin, max(0, abs_ymin - 40))
        bbox = draw.textbbox(text_pos, label)
        draw.rectangle(bbox, fill="blue")
        draw.text(text_pos, label, fill="white")
        
    # 3. Save
    img.save(debug_image_path)
    print(f"  -> Saved visualization: {debug_image_path}")

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
        if not render_pdf_to_image(source_file, masked_image_path):
            return
        img = Image.open(masked_image_path)
    else:
        img = Image.open(source_file)
        
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # 2. Draw Black Boxes
    for deal in deals:
        box_json = deal.get("box_2d")
        if not box_json: continue
        
        try:
            box = json.loads(box_json)
        except:
            continue
            
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

def run_visualization(folder_path):
    print(f"Visualizing data for: {folder_path}")
    
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
            
            debug_dir = os.path.join(root, "debug_viz")
            masked_dir = os.path.join(root, "masked_viz")
            pages_dir = os.path.join(root, "pages")
            
            # Get all products for this store/week
            products = get_products(store_name, week, year)
            
            # Filter for products with bounding boxes
            products_with_boxes = [p for p in products if p.get('box_2d')]
                
            # Group by page number
            products_by_page = {}
            for p in products_with_boxes:
                pn = p['page_number']
                if pn not in products_by_page: products_by_page[pn] = []
                products_by_page[pn].append(p)
            
            # Process pages
            if os.path.exists(pages_dir):
                for file in os.listdir(pages_dir):
                    if file.lower().startswith("page_") and file.lower().endswith(".pdf"):
                        # Extract page number
                        try:
                            page_num = int(file.split("page_")[1].split(".")[0])
                        except:
                            continue
                            
                        file_path = os.path.join(pages_dir, file)
                        page_products = products_by_page.get(page_num, [])
                        
                        # Always generate both debug and masked images
                        # If page_products is empty, it will just render the original image
                        save_debug_image(file_path, page_products, debug_dir)
                        save_masked_image(file_path, page_products, masked_dir)
    
    generate_debug_html(folder_path)

def generate_debug_html(folder_path):
    """
    Generates a static HTML file to view debug/masked images.
    """
    output_file = os.path.join(os.path.dirname(folder_path), "debug_view.html")
    # If folder_path is specific week, put it in root of Boodschappen?
    # folder_path is .../Folders/week 48
    # We want it in .../Boodschappen/debug_view.html
    
    # Let's try to find the root "Boodschappen" dir
    # folder_path = .../Folders/week 48
    # parent = .../Folders
    # root = .../Boodschappen
    root_dir = os.path.dirname(os.path.dirname(folder_path))
    output_file = os.path.join(root_dir, "debug_view.html")
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug Visualization</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #333; color: #fff; }
        .page-container { 
            margin-bottom: 30px; 
            border: 1px solid #555; 
            padding: 15px; 
            background-color: #222;
            border-radius: 8px;
        }
        .controls { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #444; }
        h3 { margin-top: 0; color: #eee; }
        img { max-width: 100%; border: 1px solid #000; display: block; }
        label { cursor: pointer; font-size: 1.1em; user-select: none; }
        input[type="checkbox"] { transform: scale(1.5); margin-right: 10px; }
    </style>
    <script>
        function toggleMask(checkbox) {
            const container = checkbox.closest('.page-container');
            const img = container.querySelector('img');
            const debugSrc = img.getAttribute('data-debug');
            const maskedSrc = img.getAttribute('data-masked');
            
            if (checkbox.checked) {
                img.src = maskedSrc;
            } else {
                img.src = debugSrc;
            }
        }
    </script>
</head>
<body>
    <h1>Debug Visualization</h1>
    <p>Check the box to see the "Masked" (Blackout) version.</p>
"""
    
    # Scan for images
    # We need to walk the folder_path (week folder)
    
    found_images = False
    
    for root, dirs, files in os.walk(folder_path):
        # We are looking for 'debug_viz' folders
        if os.path.basename(root) == "debug_viz":
            # Parent is store name
            store_name = os.path.basename(os.path.dirname(root))
            
            # Find corresponding masked dir
            masked_dir = os.path.join(os.path.dirname(root), "masked_viz")
            
            for file in files:
                if file.endswith("_debug.jpg") or file.endswith("_viz.jpg"):
                    found_images = True
                    debug_path = os.path.join(root, file)
                    
                    # Construct masked path
                    # debug file: page_1_viz.jpg or page_1_debug.jpg
                    # masked file: page_1_masked.jpg
                    
                    base_name = file.replace("_debug.jpg", "").replace("_viz.jpg", "")
                    masked_file = f"{base_name}_masked.jpg"
                    masked_path = os.path.join(masked_dir, masked_file)
                    
                    if not os.path.exists(masked_path):
                        masked_path = debug_path # Fallback
                        
                    # Create relative paths for HTML (relative to output_file)
                    # output_file is in Boodschappen/
                    # paths are in Boodschappen/Folders/week 48/Store/...
                    
                    rel_debug = os.path.relpath(debug_path, root_dir)
                    rel_masked = os.path.relpath(masked_path, root_dir)
                    
                    html_content += f"""
    <div class="page-container">
        <h3>{store_name} - {base_name}</h3>
        <div class="controls">
            <label>
                <input type="checkbox" onchange="toggleMask(this)"> Show Masked (Blackout)
            </label>
        </div>
        <img src="{rel_debug}" 
             data-debug="{rel_debug}" 
             data-masked="{rel_masked}">
    </div>
"""

    if not found_images:
        html_content += "<p>No debug images found.</p>"

    html_content += """
</body>
</html>
"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Generated debug view at: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to folder to visualize")
    args = parser.parse_args()
    
    run_visualization(args.path)
