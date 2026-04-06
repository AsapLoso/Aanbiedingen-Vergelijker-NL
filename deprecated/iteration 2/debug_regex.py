import re

def test_regex():
    samples = [
        'ACTIE.van 1.59.89',
        'ACTIE.van 2.39.1.99',
        'van 2.49.1.79',
        'ACTIE.van 1.98.1.78',
        'ACTIE.van 0.99.79',
        'ACTIE.van 0.89.79'
    ]
    
    for price_text in samples:
        print(f"Testing '{price_text}'")
        try:
            matches = re.findall(r'(\d*[.,]?\d+)', price_text)
            print(f"Matches: {matches}")
            
            valid_prices = []
            for m in matches:
                clean = m.replace(',', '.')
                if clean.startswith('.'):
                    clean = '0' + clean
                try:
                    val = float(clean)
                    if 0.1 < val < 1000:
                        valid_prices.append(val)
                except:
                    continue
            
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
    test_regex()
