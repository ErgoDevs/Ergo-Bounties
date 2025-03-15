#!/usr/bin/env python3
"""
Test script for API functionality.
This combines functionality from:
- test_price_api.py
- test_updated_rates.py
"""

import sys
import os
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_api')

# Add the parent directory to the path so Python can find the bounty_modules package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bounty_modules.conversion_rates import get_conversion_rates

def test_spectrum_api():
    """
    Test the Spectrum Finance API for token prices
    """
    logger.info("Testing Spectrum Finance API for token prices")
    
    # Fetch all markets
    logger.info("Fetching all markets...")
    try:
        response = requests.get("https://api.spectrum.fi/v1/price-tracking/markets", timeout=30)
        response.raise_for_status()
        
        markets = response.json()
        logger.info(f"Successfully fetched {len(markets)} markets")
        
        # Print all markets with SigUSD, GORT, or RSN in their symbols
        tokens_of_interest = ["SigUSD", "GORT", "RSN"]
        
        for token in tokens_of_interest:
            logger.info(f"Markets related to {token}:")
            count = 0
            
            for market in markets:
                base_symbol = market.get("baseSymbol", "")
                quote_symbol = market.get("quoteSymbol", "")
                
                if token.lower() in base_symbol.lower() or token.lower() in quote_symbol.lower():
                    count += 1
                    if count <= 3:  # Limit output to first 3 markets
                        logger.info(f"  Market {count}: {base_symbol}/{quote_symbol} - Price: {market.get('lastPrice')}")
            
            if count == 0:
                logger.info(f"No markets found for {token}")
            else:
                logger.info(f"Found {count} markets for {token}")
        
        # Check for ERG pairs with tokens of interest
        logger.info("Checking for ERG pairs with tokens of interest:")
        for token in tokens_of_interest:
            token_markets = [m for m in markets if m.get("quoteSymbol") == token and 
                            m.get("baseSymbol") == "ERG"]
            if token_markets:
                logger.info(f"Found {len(token_markets)} ERG/{token} markets")
                for i, market in enumerate(token_markets[:2]):  # Show just the first 2
                    logger.info(f"  {i+1}. ERG/{token} - Price: {market.get('lastPrice')}")
            else:
                logger.info(f"No ERG/{token} markets found")
        
        return True
    except Exception as e:
        logger.error(f"Error testing Spectrum API: {e}")
        return False

def test_conversion_rates():
    """
    Test the conversion rates functionality
    """
    logger.info("Testing conversion rates functionality")
    
    try:
        # Get conversion rates using the module function
        rates = get_conversion_rates()
        
        # Check if we got rates for the expected currencies
        expected_currencies = ["SigUSD", "GORT", "RSN", "BENE", "gGOLD"]
        for currency in expected_currencies:
            if currency in rates:
                logger.info(f"{currency} rate: {rates[currency]}")
            else:
                logger.warning(f"{currency} rate not found")
        
        # Validate the rates are reasonable
        if "SigUSD" in rates:
            if 0.1 <= rates["SigUSD"] <= 10:
                logger.info("SigUSD rate is within reasonable range")
            else:
                logger.warning(f"SigUSD rate {rates['SigUSD']} seems unusual")
        
        if "gGOLD" in rates:
            if 50 <= rates["gGOLD"] <= 500:
                logger.info("Gold price is within expected range (50-500 ERG per gram)")
            else:
                logger.warning(f"Gold price {rates['gGOLD']} ERG per gram is outside expected range")
        
        return rates
    except Exception as e:
        logger.error(f"Error testing conversion rates: {e}")
        return {}

def main():
    """Run all API tests"""
    logger.info("=== API Testing Suite ===")
    
    # Test Spectrum API
    spectrum_result = test_spectrum_api()
    logger.info(f"Spectrum API test {'succeeded' if spectrum_result else 'failed'}")
    
    # Test conversion rates
    rates = test_conversion_rates()
    logger.info(f"Conversion rates test {'succeeded' if rates else 'failed'}")
    
    logger.info("=== API Testing Complete ===")

if __name__ == "__main__":
    main()
