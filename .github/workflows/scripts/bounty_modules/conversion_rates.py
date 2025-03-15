import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('conversion_rates')

# Constants
SPECTRUM_API_URL = "https://api.spectrum.fi/v1/price-tracking/markets"
XAU_ERG_ORACLE_NFT = "3c45f29a5165b030fdb5eaf5d81f8108f9d8f507b31487dd51f4ae08fe07cf4a"
ERGO_EXPLORER_API = "https://api.ergoplatform.com/api/v1"

def get_conversion_rates():
    """
    Get conversion rates for various currencies to ERG.
    
    Returns:
        dict: Dictionary of currency rates
    """
    # Initialize rates dictionary
    rates = {}
    
    try:
        # Get Spectrum API data for crypto rates
        logger.info("Fetching market data from Spectrum API")
        spectrum_response = requests.get(SPECTRUM_API_URL, timeout=30)
        
        if spectrum_response.status_code != 200:
            logger.error(f"Error fetching Spectrum API conversion rates: {spectrum_response.status_code}")
            raise Exception("Failed to fetch Spectrum API data")
            
        markets = spectrum_response.json()
        logger.debug(f"Spectrum API returned {len(markets)} markets")
        
        # Process SigUSD rate
        sigusd_markets = [m for m in markets if m.get("quoteSymbol") == "SigUSD" and 
                         m.get("baseSymbol") == "ERG"]
        if sigusd_markets:
            # Sort by volume if available, otherwise use the first market
            if 'baseVolume' in sigusd_markets[0]:
                sigusd_markets.sort(key=lambda m: float(m.get('baseVolume', {}).get('value', 0)), reverse=True)
            
            # Use the first (or most liquid) market
            rates["SigUSD"] = float(sigusd_markets[0].get("lastPrice"))
            logger.info(f"Found SigUSD rate: {rates['SigUSD']}")
        else:
            logger.error("No SigUSD markets found, cannot proceed without SigUSD rate")
            raise Exception("SigUSD rate not found in API data")
        
        # Process GORT rate
        gort_markets = [m for m in markets if m.get("quoteSymbol") == "GORT" and 
                       m.get("baseSymbol") == "ERG"]
        if gort_markets:
            rates["GORT"] = float(gort_markets[0].get("lastPrice"))
            logger.info(f"Found GORT rate: {rates['GORT']}")
        else:
            logger.warning("No GORT markets found in API data")
            # Continue without GORT rate
        
        # Process RSN rate
        rsn_markets = [m for m in markets if m.get("quoteSymbol") == "RSN" and 
                      m.get("baseSymbol") == "ERG"]
        if rsn_markets:
            rates["RSN"] = float(rsn_markets[0].get("lastPrice"))
            logger.info(f"Found RSN rate: {rates['RSN']}")
        else:
            logger.warning("No RSN markets found in API data")
            # Continue without RSN rate
        
        # Set BENE to $1 worth of ERG
        if "SigUSD" in rates:
            rates["BENE"] = rates["SigUSD"]
            logger.info(f"Setting BENE rate to {rates['BENE']} (equivalent to $1 worth of ERG)")
        else:
            rates["BENE"] = 0.0
            logger.warning("SigUSD rate not available, setting BENE to 0")
        
        # Get gold price from XAU/ERG oracle pool
        logger.info("Getting gold price from XAU/ERG oracle pool")
        
        try:
            # Using the explorer API to get boxes containing the oracle pool NFT
            oracle_url = f"{ERGO_EXPLORER_API}/boxes/unspent/byTokenId/{XAU_ERG_ORACLE_NFT}"
            
            response = requests.get(oracle_url, timeout=60)
            if response.status_code != 200:
                logger.error(f"Oracle API returned status code {response.status_code}")
                raise Exception(f"Failed to access oracle API: {response.status_code}")
                
            oracle_data = response.json()
            if not oracle_data.get('items') or len(oracle_data['items']) == 0:
                logger.error("No oracle pool boxes found")
                raise Exception("No oracle pool boxes found")
                
            # Get the most recent box (usually the first one)
            latest_box = oracle_data['items'][0]
            
            # Extract the R4 register value
            if 'additionalRegisters' not in latest_box or 'R4' not in latest_box['additionalRegisters']:
                logger.error("R4 register not found in oracle pool box")
                raise Exception("R4 register not found")
                
            r4_register = latest_box['additionalRegisters']['R4']
            r4_value = None
            
            if 'renderedValue' in r4_register:
                r4_value = r4_register['renderedValue']
            elif 'value' in r4_register:
                r4_value = r4_register['value']
                
            if not r4_value:
                logger.error("Could not extract R4 value from register")
                raise Exception("R4 value not found")
                
            # Convert R4 value to float
            r4_value = float(r4_value)
            
            # Calculate the gold price using the formula: 10^18 / (R4_value * 100)
            # This scaling factor is derived from the oracle pool's data format and testing
            gold_price_per_gram_erg = (10**18) / (r4_value * 100)
            
            logger.info(f"Gold price from oracle: {gold_price_per_gram_erg:.6f} ERG per gram")
            rates["gGOLD"] = gold_price_per_gram_erg
            
        except Exception as e:
            logger.error(f"Error getting gold price from oracle: {e}")
            # No fallbacks - if we can't get the oracle price, we don't set a value
        
        logger.info(f"Using conversion rates: {rates}")
        return rates
    except Exception as e:
        logger.error(f"Exception fetching conversion rates: {e}")
        return rates  # Return what we have so far

def convert_to_erg(amount, currency, conversion_rates):
    """
    Convert an amount in a specific currency to ERG equivalent.
    
    Args:
        amount (str): Amount to convert
        currency (str): Currency to convert from
        conversion_rates (dict): Dictionary of conversion rates
        
    Returns:
        str: ERG equivalent amount or original amount if conversion not possible
    """
    if amount == "Not specified":
        return amount
        
    try:
        if currency == "ERG":
            return amount
        elif currency == "SigUSD" and "SigUSD" in conversion_rates:
            return f"{float(amount) / conversion_rates['SigUSD']:.2f}"
        elif currency == "GORT" and "GORT" in conversion_rates:
            return f"{float(amount) / conversion_rates['GORT']:.2f}"
        elif currency == "RSN" and "RSN" in conversion_rates:
            return f"{float(amount) / conversion_rates['RSN']:.2f}"
        elif currency == "BENE" and "BENE" in conversion_rates:
            return f"{float(amount) / conversion_rates['BENE']:.2f}"  # BENE is worth $1 in ERG
        elif currency == "g GOLD" and "gGOLD" in conversion_rates:
            return f"{float(amount) * conversion_rates['gGOLD']:.2f}"
        else:
            return amount  # For other currencies, just use the amount
    except ValueError:
        return amount
