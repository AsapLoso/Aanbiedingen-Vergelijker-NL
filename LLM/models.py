from pydantic import BaseModel, Field
from typing import Optional, Literal

# --- CATEGORY DEFINITIONS ---
DutchCategory = Literal[
    "Aardappelen, Groente & Fruit",
    "Vlees, Kip & Vis",
    "Vegetarisch & Vegan",
    "Zuivel, Eieren & Boter",
    "Brood & Gebak",
    "Ontbijtgranen & Beleg",
    "Snoep, Koek & Chips",
    "Bier & Wijn",
    "Frisdrank & Sappen",
    "Koffie & Thee",
    "Pasta, Rijst & Wereldkeuken",
    "Soepen & Sauzen",
    "Diepvries",
    "Persoonlijke Verzorging",
    "Huishouden & Huisdier"
]

VALID_CATEGORIES_STRING = "\n".join([
    "Aardappelen, Groente & Fruit",
    "Vlees, Kip & Vis",
    "Vegetarisch & Vegan",
    "Zuivel, Eieren & Boter",
    "Brood & Gebak",
    "Ontbijtgranen & Beleg",
    "Snoep, Koek & Chips",
    "Bier & Wijn",
    "Frisdrank & Sappen",
    "Koffie & Thee",
    "Pasta, Rijst & Wereldkeuken",
    "Soepen & Sauzen",
    "Diepvries",
    "Persoonlijke Verzorging",
    "Huishouden & Huisdier"
])

# --- MODEL DEFINITIONS ---

class ItemAmount(BaseModel):
    """
    Structured package size extraction. 
    Example: '1.5 kg'
    """
    value: float = Field(..., description="The numerical value only (e.g., 1.5, 500, 1.0).")
    unit: str = Field(..., description="The unit ONLY (e.g., kg, g, l, stuks). STRIP descriptive words like 'zak', 'krat', 'pak'.")

class DutchGroceryModel(BaseModel):
    """
    Expert model for Dutch supermarket deal extraction.
    Designed for clean database grouping.
    """
    generic_name: str = Field(
        ..., 
        description="The base singular Dutch word for grouping (e.g., 'Appel', 'Bier', 'Gehakt'). Strip varieties like 'Elstar' out of this field."
    )
    
    size: ItemAmount = Field(..., description="The structured quantity of the product.")
    
    price: Optional[float] = Field(None, description="The listed price of the deal (e.g., 2.49). Use the final price shown.")
    
    paid_equivalent: float = Field(
        1.0, 
        description="The numerical discount logic value. 1.0 for standard, 1.5 for 2e halve prijs, 2.0 for 1+1 gratis (total items in cart)."
    )
    
    category: DutchCategory = Field(
        ..., 
        description="The Dutch supermarket category. MUST BE EXACTLY one of the valid strings."
    )

# --- PROMPT DEFINITIONS ---

DUTCH_GROCERY_PROMPT = f"""
You are an expert Dutch supermarket data analyst. Your job is to parse messy promotional text and extract structured data for a database.

CLEANLINESS RULES:
1. 'generic_name' must be the simplest singular Dutch word (e.g., "Appel", "Banaan", "Bier"). 
2. 'size' MUST be split into a numerical value and a string unit. 
   - Input: "1.5kg zak" -> value: 1.5, unit: "kg"
   - Input: "500 gram" -> value: 500.0, unit: "g"
   - Input: "Per stuk" -> value: 1.0, unit: "stuks"
   - ALWAYS strip words like 'zak', 'pak', 'krat' from the unit.

EXTRACTION RULES:
1. All input data is in Dutch.
2. 'paid_equivalent' represents the logic of the deal (e.g. 1+1 gratis means the user gets 2 items but pays for 1 price equivalent).
3. You must categorize using EXACTLY one of the valid categories.

Valid Dutch Categories:
{VALID_CATEGORIES_STRING}
"""

# --- TASK PAIRINGS ---
DUTCH_GROCERY_TASK = (DutchGroceryModel, DUTCH_GROCERY_PROMPT)
