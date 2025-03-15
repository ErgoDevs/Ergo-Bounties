#!/usr/bin/env python3
"""
Consolidated test script for gold price functionality.
This combines the functionality from the previous test scripts:
- test_gold_price.py
- test_formula.py
- test_gold_implementation.py
- test_gold_simple.py
"""

import sys
import os
import requests
import json

# Add the parent directory to the path so Python can find the bounty_modules package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bounty_modules.conversion_rates import get_conversion_rates

def test_gold_oracle():
    """Test gold price from Ergo oracle pool using explorer API"""
    print("\n=== Testing Gold Price from Oracle Pool ===")
    
    # Oracle pool NFT ID for ERG/XAU
    xau_erg_oracle_nft = "3c45f29a5165b030fdb5eaf5d81f8108f9d8f507b31487dd51f4ae08fe07cf4a"
    
    try:
        # Using the explorer API to get boxes containing the oracle pool NFT
        oracle_url = f"https://api.ergoplatform.com/api/v1/boxes/unspent/byTokenId/{xau_erg_oracle_nft}"
        print(f"Querying oracle pool at: {oracle_url}")
        
        response = requests.get(oracle_url, timeout=60)
        if response.status_code != 200:
            print(f"Error: Oracle API returned status code {response.status_code}")
            return
            
        oracle_data = response.json()
        if not oracle_data.get('items') or len(oracle_data['items']) == 0:
            print("Error: No oracle pool boxes found")
            return
            
        # Get the most recent box (usually the first one)
        latest_box = oracle_data['items'][0]
        
        # Extract the R4 register value
        if 'additionalRegisters' not in latest_box or 'R4' not in latest_box['additionalRegisters']:
            print("Error: R4 register not found in oracle pool box")
            return
            
        r4_register = latest_box['additionalRegisters']['R4']
        r4_value = None
        
        if 'renderedValue' in r4_register:
            r4_value = r4_register['renderedValue']
        elif 'value' in r4_register:
            r4_value = r4_register['value']
            
        if not r4_value:
            print("Error: Could not extract R4 value from register")
            return
            
        print(f"Raw R4 value from oracle: {r4_value}")
        
        # Convert R4 value to float
        r4_value = float(r4_value)
        
        # Calculate gold price using the formula: 10^18 / (R4_value * 100)
        gold_price_per_gram_erg = (10**18) / (r4_value * 100)
        
        print(f"Gold price: {gold_price_per_gram_erg:.6f} ERG per gram")
        
        # Validate the gold price is reasonable
        if 50 <= gold_price_per_gram_erg <= 500:
            print("Gold price is within expected range (50-500 ERG per gram)")
        else:
            print(f"WARNING: Gold price {gold_price_per_gram_erg:.6f} ERG per gram is outside expected range")
        
    except Exception as e:
        print(f"Error: {e}")

def test_formula():
    """Test gold price calculation formula with different R4 values"""
    print("\n=== Testing Gold Price Calculation Formula ===")
    print("Expected result: ~122.635 ERG per gram")
    
    # Test with different R4 values
    test_values = [
        8154910.0,           # Original test value
        8154910.0 * 100,     # Original * 100 (scaling factor used in production)
        8154910.0 * (10**6), # Original * 10^6
    ]
    
    for r4_value in test_values:
        # Calculate gold price using the formula: 10^18 / R4_value
        gold_price_per_gram_erg = (10**18) / r4_value
        
        print(f"R4 value: {r4_value}")
        print(f"Formula: 10^18 / R4_value = 10^18 / {r4_value}")
        print(f"Result: {gold_price_per_gram_erg:.6f} ERG per gram")
        print()
    
    # Reverse calculation - what R4 value would give us 122.635 ERG per gram?
    target_price = 122.635
    required_r4 = (10**18) / target_price
    
    print(f"Reverse calculation:")
    print(f"Target price: {target_price} ERG per gram")
    print(f"Required R4 value: {required_r4:.6f}")
    print(f"Formula check: 10^18 / {required_r4:.6f} = {(10**18) / required_r4:.6f} ERG per gram")

def test_sigusd_rate():
    """Test SigUSD rate from Spectrum API"""
    print("\n=== Testing SigUSD Rate from Spectrum API ===")
    
    try:
        # Get Spectrum API data for crypto rates
        spectrum_response = requests.get("https://api.spectrum.fi/v1/price-tracking/markets")
        
        if spectrum_response.status_code != 200:
            print(f"Error: API returned status code {spectrum_response.status_code}")
            return
        
        markets = spectrum_response.json()
        print(f"Spectrum API returned {len(markets)} markets")
        
        # Find ERG/SigUSD pairs (where baseSymbol is ERG and quoteSymbol is SigUSD)
        sigusd_markets = [m for m in markets if m.get("quoteSymbol") == "SigUSD" and 
                         m.get("baseSymbol") == "ERG"]
        
        if not sigusd_markets:
            print("Error: No SigUSD markets found")
            return
        
        # Sort by volume if available, otherwise use the first market
        if 'baseVolume' in sigusd_markets[0]:
            sigusd_markets.sort(key=lambda m: float(m.get('baseVolume', {}).get('value', 0)), reverse=True)
            print(f"Sorted SigUSD markets by volume, using the most liquid market")
        
        # Use the first (or most liquid) market
        sigusd_rate = float(sigusd_markets[0].get("lastPrice"))
        print(f"SigUSD rate: {sigusd_rate} (1 ERG = {sigusd_rate} SigUSD)")
        print(f"Inverse rate: {1/sigusd_rate:.6f} (1 SigUSD = {1/sigusd_rate:.6f} ERG)")
    
    except Exception as e:
        print(f"Error: {e}")

def test_conversion_rates_module():
    """Test the gold price implementation in conversion_rates.py"""
    print("\n=== Testing Conversion Rates Module ===")
    
    try:
        # Get conversion rates
        rates = get_conversion_rates()
        
        # Check if gGOLD rate was successfully retrieved
        if "gGOLD" in rates:
            gold_price = rates["gGOLD"]
            print("\nSUCCESS: Gold price retrieved successfully!")
            print(f"Gold price: {gold_price:.6f} ERG per gram")
            
            # Validate the gold price is reasonable
            if 50 <= gold_price <= 500:
                print("Gold price is within expected range (50-500 ERG per gram)")
            else:
                print(f"WARNING: Gold price {gold_price:.6f} ERG per gram is outside expected range")
        else:
            print("\nERROR: Failed to retrieve gold price")
            
        # Print all rates for reference
        print("\nAll conversion rates:")
        for currency, rate in rates.items():
            print(f"{currency}: {rate}")
            
    except Exception as e:
        print(f"\nERROR: Exception during test: {e}")

def main():
    """Run all tests"""
    print("=== Gold Price Testing Suite ===")
    
    # Run all tests
    test_gold_oracle()
    test_formula()
    test_sigusd_rate()
    test_conversion_rates_module()
    
    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
