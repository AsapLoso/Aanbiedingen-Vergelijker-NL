import sqlite3
import os
import datetime
import subprocess
import base64
import shutil

# Ghostscript path (same as in preprocess.py)
GS_PATH = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'flyers_categorized.db')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'index.html')

def get_flyer_image_base64(store_path, page_num):
    """
    Finds the image for the given store and page.
    If it's a PDF, converts it to JPG using Ghostscript.
    Returns base64 string.
    """
    if not page_num:
        return None
        
    # Handle case where store_path is a file (e.g. the PDF itself)
    if os.path.isfile(store_path):
        store_dir = os.path.dirname(store_path)
        main_pdf = store_path
    else:
        store_dir = store_path
        main_pdf = None
        
    # 1. Check for existing image in 'images' folder (if scraped as images)
    potential_images = [
        os.path.join(store_dir, "images", f"page_{page_num}.jpg"),
        os.path.join(store_dir, f"page_{page_num}.jpg"),
    ]
    
    for img_path in potential_images:
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"Error reading image {img_path}: {e}")
                
    # 2. Check for PDF page in 'pages' folder (created by preprocess.py)
    pdf_page_path = os.path.join(store_dir, "pages", f"page_{page_num}.pdf")
    
    # If not in pages, maybe main PDF?
    if not main_pdf and not os.path.exists(pdf_page_path):
        # Find main PDF in directory
        if os.path.exists(store_dir):
            for f in os.listdir(store_dir):
                if f.lower().endswith('.pdf'):
                    main_pdf = os.path.join(store_dir, f)
                    break
    
    # Target image path (cache it in 'images' folder)
    images_dir = os.path.join(store_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    target_image = os.path.join(images_dir, f"page_{page_num}.jpg")
    
    # If target image exists, return it
    if os.path.exists(target_image):
        with open(target_image, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
            
    # Convert PDF to Image
    source_pdf = pdf_page_path if os.path.exists(pdf_page_path) else main_pdf
    
    if source_pdf and os.path.exists(GS_PATH):
        # print(f"Converting {os.path.basename(source_pdf)} page {page_num} to image...")
        try:
            cmd = [
                GS_PATH,
                "-sDEVICE=jpeg",
                "-dJPEGQ=80",
                "-r100", 
                "-dNOPAUSE",
                "-dBATCH",
                f"-sOutputFile={target_image}",
            ]
            
            if source_pdf == main_pdf:
                cmd.extend([f"-dFirstPage={page_num}", f"-dLastPage={page_num}"])
                
            cmd.append(source_pdf)
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            if os.path.exists(target_image):
                with open(target_image, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            
    return None

def get_latest_week_year(cursor):
    cursor.execute("SELECT MAX(year), MAX(week) FROM flyers")
    return cursor.fetchone()

def get_stores(cursor, week, year):
    cursor.execute("SELECT DISTINCT store FROM flyers WHERE week = ? AND year = ? ORDER BY store", (week, year))
    return [row[0] for row in cursor.fetchall()]

def get_flyer_paths(cursor, week, year):
    cursor.execute("SELECT store, path, type FROM flyers WHERE week = ? AND year = ?", (week, year))
    return {row[0]: {'path': row[1], 'type': row[2]} for row in cursor.fetchall()}

def get_products(cursor, week, year):
    cursor.execute("""
        SELECT store, product_name, deal_price, page_number, category, standardized_name 
        FROM products 
        WHERE week = ? AND year = ?
    """, (week, year))
    return cursor.fetchall()

def generate_html():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Get latest week/year
    year, week = get_latest_week_year(c)
    if not year or not week:
        print("No data found in database.")
        conn.close()
        return

    print(f"Generating report for Week {week}, {year}...")

    # 2. Get all stores for that week
    stores = get_stores(c, week, year)
    
    # 3. Get flyer paths (for links)
    flyer_info = get_flyer_paths(c, week, year)

    # 4. Get all products
    products_raw = get_products(c, week, year)
    
    # 5. Pivot data: {category: {standardized_name: {store: [items]}}}
    # Structure:
    # categorized_data = {
    #   "Category A": {
    #       "Std Name 1": {
    #           "Store A": [ {price, page, original_name}, ... ],
    #           "Store B": [ ... ]
    #       }
    #   }
    # }
    
    categorized_data = {}
    all_categories = set()

    for store, name, price, page, category, std_name in products_raw:
        # Use standardized name if available, else fallback to original name
        # If std_name is IGNORE, skip? Or put in Overige?
        # User said "IGNORE" in prompt for nonsense.
        if std_name == "IGNORE":
            continue
            
        display_name = std_name if std_name else name
        if not display_name: continue
        
        cat = category if category else "Overige"
        if cat == "Nonsense": continue # Skip nonsense
        
        all_categories.add(cat)

        if cat not in categorized_data:
            categorized_data[cat] = {}
        
        if display_name not in categorized_data[cat]:
            categorized_data[cat][display_name] = {}
            
        if store not in categorized_data[cat][display_name]:
            categorized_data[cat][display_name][store] = []
            
        categorized_data[cat][display_name][store].append({
            'price': price, 
            'page': page, 
            'original_name': name
        })

    conn.close()

    # 6. Generate HTML
    
    # Collect all needed images first
    # Map: "Store_Page" -> Base64
    flyer_images = {}
    print("Collecting and converting flyer images (this may take a moment)...")
    
    # Iterate all products to find used pages
    used_pages = set()
    for store, name, price, page, category, std_name in products_raw:
        if store and page:
            used_pages.add((store, page))
            
    for store, page in used_pages:
        store_info = flyer_info.get(store)
        if store_info:
            path = store_info['path']
            # Convert/Get image
            b64 = get_flyer_image_base64(path, page)
            if b64:
                key = f"{store}_{page}"
                flyer_images[key] = b64
                
    print(f"Embedded {len(flyer_images)} flyer pages.")

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grocery Deals - Week {week} {year}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f4f4; }}
        h1 {{ margin-bottom: 20px; color: #333; }}
        
        /* Category Accordion */
        details {{
            background-color: #fff;
            margin-bottom: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        
        summary {{
            padding: 15px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            background-color: #e0e0e0;
            list-style: none; /* Hide default triangle */
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        summary::-webkit-details-marker {{ display: none; }}
        
        summary:hover {{ background-color: #d0d0d0; }}
        
        summary::after {{
            content: '+'; 
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        details[open] summary::after {{
            content: '-';
        }}

        /* Table Styles */
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        
        th {{ 
            background-color: #f8f8f8; 
            font-weight: 600;
            color: #555;
            position: sticky;
            top: 0;
        }}
        
        /* Main Row (Standardized Product) */
        tr.main-row {{
            background-color: #fff;
            cursor: pointer;
        }}
        tr.main-row:hover {{ background-color: #f9f9f9; }}
        
        tr.main-row td.product-cell {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        tr.main-row td.price-cell {{
            font-weight: bold;
            color: #27ae60;
        }}
        
        /* Child Row (Specific Items) */
        tr.child-row {{
            background-color: #fafafa;
            display: none; /* Hidden by default */
            font-size: 0.9em;
        }}
        
        tr.child-row.expanded {{
            display: table-row;
        }}
        
        tr.child-row td.product-cell {{
            padding-left: 30px; /* Indent */
            color: #666;
        }}
        
        .deal-link {{ 
            color: #3498db; 
            text-decoration: none; 
            cursor: pointer;
        }}
        .deal-link:hover {{ text-decoration: underline; }}
        
        .na {{ color: #ccc; font-style: italic; font-size: 0.8em; }}
        
        .toggle-icon {{
            display: inline-block;
            width: 20px;
            text-align: center;
            margin-right: 5px;
            color: #999;
            transition: transform 0.2s;
        }}
        
        tr.main-row.open .toggle-icon {{
            transform: rotate(90deg);
        }}
        
        /* Modal Styles */
        .modal {{
            display: none; 
            position: fixed; 
            z-index: 1000; 
            left: 0;
            top: 0;
            width: 100%; 
            height: 100%; 
            overflow: auto; 
            background-color: rgba(0,0,0,0.8); 
        }}
        
        .modal-content {{
            margin: 5% auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
        }}
        
        .close {{
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        
    </style>
    <script>
        // Embedded Images Data
        var flyerImages = {{
            {','.join(f'"{k}": "{v}"' for k, v in flyer_images.items())}
        }};
    
        function toggleRows(rowId) {{
            var mainRow = document.getElementById('main-' + rowId);
            mainRow.classList.toggle('open');
            
            var childRows = document.getElementsByClassName('child-' + rowId);
            for (var i = 0; i < childRows.length; i++) {{
                childRows[i].classList.toggle('expanded');
            }}
        }}
        
        function showFlyer(store, page) {{
            var key = store + "_" + page;
            var b64 = flyerImages[key];
            var modal = document.getElementById("imageModal");
            var modalImg = document.getElementById("modalImage");
            
            if (b64) {{
                modal.style.display = "block";
                modalImg.src = "data:image/jpeg;base64," + b64;
            }} else {{
                alert("Image not available for " + store + " page " + page);
            }}
        }}
        
        function closeModal() {{
            document.getElementById("imageModal").style.display = "none";
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            var modal = document.getElementById("imageModal");
            if (event.target == modal) {{
                modal.style.display = "none";
            }}
        }}
    </script>
</head>
<body>
    <h1>Week {week} / {year}</h1>
    
    <!-- The Modal -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>
"""
    
    # Sort categories
    sorted_categories = sorted(list(all_categories))
    
    # Move 'Overige' to end if exists
    if "Overige" in sorted_categories:
        sorted_categories.remove("Overige")
        sorted_categories.append("Overige")

    row_counter = 0

    for cat in sorted_categories:
        html_content += f"""
    <details>
        <summary>{cat}</summary>
        <table>
            <thead>
                <tr>
                    <th style="width: 30%">Product</th>
                    {''.join(f'<th>{store}</th>' for store in stores)}
                </tr>
            </thead>
            <tbody>
"""
        
        # Sort products within category
        products_in_cat = categorized_data[cat]
        sorted_products = sorted(products_in_cat.keys())
        
        for product in sorted_products:
            row_id = row_counter
            row_counter += 1
            
            # 1. Calculate Summary Row Data
            summary_cells = ""
            
            # Check if we have any child rows to show (i.e. any store has items)
            has_items = False
            
            for store in stores:
                items = products_in_cat[product].get(store, [])
                if items:
                    has_items = True
                    # Determine "Lowest" price logic
                    # User feedback: "why doesn't it just say 0.89??"
                    # New Logic: Prioritize numerical prices. Only show "See Flyer" if NO numerical price exists.
                    
                    prices = [i['price'] for i in items]
                    
                    # Filter for valid numbers
                    valid_prices = [p for p in prices if isinstance(p, (int, float))]
                    
                    if valid_prices:
                        min_price = min(valid_prices)
                        display_price = f"{min_price:.2f}"
                    else:
                        display_price = "See Flyer"
                            
                    summary_cells += f"<td class='price-cell'>{display_price}</td>"
                else:
                    summary_cells += "<td class='na'>-</td>"
            
            if not has_items: continue

            # Main Row
            html_content += f"""
                <tr class="main-row" id="main-{row_id}" onclick="toggleRows({row_id})">
                    <td class="product-cell"><span class="toggle-icon">▶</span>{product}</td>
                    {summary_cells}
                </tr>
            """
            
            # 2. Generate Child Rows
            # We need to list ALL unique original items across ALL stores?
            # Or just list items per store?
            # The table structure implies we align by store.
            # But different stores have different original items.
            # Strategy: Collect all unique original names for this standardized product across all stores.
            # Then create a row for each original name.
            
            unique_items = set()
            for store in stores:
                items = products_in_cat[product].get(store, [])
                for item in items:
                    unique_items.add(item['original_name'])
            
            sorted_items = sorted(list(unique_items))
            
            for item_name in sorted_items:
                html_content += f"<tr class='child-row child-{row_id}'>"
                html_content += f"<td class='product-cell'>{item_name}</td>"
                
                for store in stores:
                    # Check if this store has this item
                    store_items = products_in_cat[product].get(store, [])
                    matching_item = next((i for i in store_items if i['original_name'] == item_name), None)
                    
                    if matching_item:
                        price = matching_item['price']
                        page = matching_item['page']
                        
                        disp = f"{price:.2f}" if isinstance(price, (int, float)) else "See Flyer"
                        
                        # Link Logic
                        # Use embedded image if available
                        link_action = f"onclick=\"showFlyer('{store}', '{page}')\""
                        link_href = "javascript:void(0)"
                        
                        html_content += f"<td><a href='{link_href}' {link_action} class='deal-link'>{disp}</a></td>"
                    else:
                        html_content += "<td class='na'></td>"
                
                html_content += "</tr>"

        html_content += """
            </tbody>
        </table>
    </details>
"""

    html_content += """
</body>
</html>
"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html()
