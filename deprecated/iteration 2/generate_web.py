import sqlite3
import os
import datetime

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'web_deals.db')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web_deals.html')

def get_products():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM web_products ORDER BY store, product_name")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def generate_html():
    products = get_products()
    
    # Group by store
    products_by_store = {}
    for p in products:
        store = p['store']
        if store not in products_by_store:
            products_by_store[store] = []
        products_by_store[store].append(p)
        
    html_content = f"""
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Boodschappen Aanbiedingen (Web)</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; margin: 0; padding: 20px; }}
            h1 {{ text-align: center; color: #333; }}
            .store-section {{ margin-bottom: 40px; }}
            .store-header {{ background-color: #2c3e50; color: white; padding: 10px 20px; border-radius: 5px; margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column; }}
            .card-image {{ width: 100%; height: 150px; object-fit: contain; background: #fff; padding: 10px; box-sizing: border-box; }}
            .card-content {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
            .product-name {{ font-weight: bold; margin-bottom: 5px; font-size: 1.1em; }}
            .product-unit {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
            .price-container {{ margin-top: auto; display: flex; align-items: baseline; justify-content: space-between; }}
            .deal-price {{ color: #e74c3c; font-weight: bold; font-size: 1.2em; }}
            .deal-tag {{ background-color: #f1c40f; color: #2c3e50; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
            .timestamp {{ text-align: center; color: #95a5a6; margin-top: 40px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <h1>Boodschappen Aanbiedingen (Web Scraper)</h1>
        <p style="text-align: center;">Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    """
    
    for store, items in products_by_store.items():
        html_content += f"""
        <div class="store-section">
            <div class="store-header">
                <h2>{store} ({len(items)} aanbiedingen)</h2>
            </div>
            <div class="grid">
        """
        
        for item in items:
            image_url = item.get('image_url') or 'https://via.placeholder.com/200x150?text=No+Image'
            price_display = f"€ {item['deal_price']:.2f}" if item['deal_price'] else item['price_text'] or "?"
            deal_tag = item.get('deal_tag') or ""
            
            html_content += f"""
                <div class="card">
                    <img src="{image_url}" alt="{item['product_name']}" class="card-image" loading="lazy">
                    <div class="card-content">
                        <div class="product-name">{item['product_name']}</div>
                        <div class="product-unit">{item['unit_size'] or ''}</div>
                        <div class="price-container">
                            <span class="deal-price">{price_display}</span>
                            {f'<span class="deal-tag">{deal_tag}</span>' if deal_tag else ''}
                        </div>
                    </div>
                </div>
            """
            
        html_content += """
            </div>
        </div>
        """
        
    html_content += """
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Report generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html()
