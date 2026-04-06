import re

def test_aldi_regex():
    samples = [
        'OP=OP.29.99.Per set',
        'OP=OP.14.99.Per set',
        'OP=OP.4.99.Per set',
        'OP=OP.6.49.20 rollen',
        'OP=OP.2.29.3x100 g',
        '0.75',
        '1.29.1.99'
    ]
    
    for price_text in samples:
        print(f"Testing '{price_text}'")
        try:
            # Matches: 1.99, 1,99, .89, ,89
            matches = re.findall(r'(\d*[.,]?\d+)', price_text)
            print(f"Matches: {matches}")
            
            valid_prices = []
            for m in matches:
                clean = m.replace(',', '.')
                if clean.startswith('.'): clean = '0' + clean
                try:
                    val = float(clean)
                    if 0.1 < val < 1000: valid_prices.append(val)
                except: continue
            
            print(f"Valid prices: {valid_prices}")
            
            if valid_prices:
                deal_price = valid_prices[-1]
                print(f"Deal Price: {deal_price}")
            else:
                print("No valid prices found.")
                
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    test_aldi_regex()
