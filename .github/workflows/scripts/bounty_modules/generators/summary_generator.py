"""
Module for generating summary markdown files.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from ..utils import ensure_directory, create_claim_url, format_navigation_badges, calculate_erg_value
from ..conversion_rates import convert_to_erg

# Configure logging
logger = logging.getLogger('summary_generator')

def generate_main_file(
    bounty_data: List[Dict[str, Any]], 
    project_totals: Dict[str, Dict[str, Any]], 
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    total_value: float, 
    bounties_dir: str
) -> None:
    """
    Generate the main markdown file with all bounties.
    
    Args:
        bounty_data: List of bounty data
        project_totals: Dictionary of project totals
        languages: Dictionary of languages and their bounties
        currencies_dict: Dictionary of currencies and their bounties
        orgs: Dictionary of organizations and their bounties
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        total_value: Total value of bounties
        bounties_dir: Bounties directory
    """
    logger.info("Generating main bounty file")
    
    md_file = f'{bounties_dir}/all.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# All Open Bounties\n\n")
        f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
        
        # Add navigation badges
        f.write("## Navigation\n\n")
        f.write(format_navigation_badges(
            total_bounties, 
            len(languages), 
            len(currencies_dict), 
            len(orgs), 
            len(conversion_rates)
        ))
        f.write("\n\n")
        
        # Create a unified filter section
        f.write("## Filter Bounties\n\n")
        
        # Programming Languages
        f.write("**By Programming Language:** ")
        lang_links = []
        for lang, lang_bounties in languages.items():
            lang_links.append(f"[{lang} ({len(lang_bounties)})](by_language/{lang.lower()}.md)")
        f.write(" • ".join(lang_links))
        f.write("\n\n")
        
        # Currencies
        f.write("**By Currency:** ")
        currency_links = []
        for currency, currency_bounties in currencies_dict.items():
            # Format the currency name for the file link
            if currency == "Not specified":
                currency_file_name = "not_specified"
            elif currency == "g GOLD":
                currency_file_name = "gold"
            else:
                currency_file_name = currency.lower()
            currency_links.append(f"[{currency} ({len(currency_bounties)})](by_currency/{currency_file_name}.md)")
        f.write(" • ".join(currency_links))
        f.write("\n\n")
        
        # Organizations
        f.write("**By Organization:** ")
        org_links = []
        for org, org_bounties in orgs.items():
            org_links.append(f"[{org} ({len(org_bounties)})](by_org/{org.lower()}.md)")
        f.write(" • ".join(org_links))
        f.write("\n\n")
        
        
        # Check if there are any ongoing programs
        ongoing_programs = [b for b in bounty_data if b["amount"] == "Ongoing"]
        
        if ongoing_programs:
            # Write ongoing programs section with link to dedicated page
            f.write("## Ongoing Reward Programs\n\n")
            f.write("The Ergo ecosystem offers ongoing reward programs to encourage continuous contributions in key areas.\n\n")
            f.write("**[View Ongoing Programs →](/docs/ongoing-programs.md)**\n\n")
        
        # Write all bounties table
        f.write("## All Bounties\n\n")
        f.write("|Organisation|Repository|Title & Link|Primary Language|ERG Value|Paid In|Reserve|\n")
        f.write("|---|---|---|---|---|---|---|\n")
        
        # Calculate ERG equivalent for each bounty for sorting
        for bounty in bounty_data:
            amount = bounty["amount"]
            currency = bounty["currency"]
            try:
                # Calculate ERG value for sorting
                erg_value = calculate_erg_value(amount, currency, conversion_rates)
                bounty["erg_value"] = erg_value
            except (ValueError, TypeError):
                bounty["erg_value"] = 0.0
        
        # Sort all bounties by ERG value (highest first)
        sorted_bounties = sorted(bounty_data, key=lambda x: x.get("erg_value", 0.0), reverse=True)
        
        # Add rows for each bounty (excluding those with "Not specified" amounts)
        for bounty in sorted_bounties:
            owner = bounty["owner"]
            title = bounty["title"]
            url = bounty["url"]
            amount = bounty["amount"]
            currency = bounty["currency"]
            primary_lang = bounty["primary_lang"]
            
            # Skip bounties with "Not specified" amounts or "Ongoing" programs
            if amount == "Not specified" or amount == "Ongoing":
                continue
            
            # Try to convert to ERG equivalent
            erg_equiv = convert_to_erg(amount, currency, conversion_rates)
            
            # Create a claim link that opens a PR template
            issue_number = bounty["issue_number"]
            creator = bounty["creator"]
            repo_name = bounty["repo"]
            
            claim_url = create_claim_url(owner, repo_name, issue_number, title, url, currency, amount, creator)
            
            # Format the currency name for the file link
            if currency == "Not specified":
                currency_file_name = "not_specified"
            elif currency == "g GOLD":
                currency_file_name = "gold"
            else:
                currency_file_name = currency.lower()
            
            # Add links to organization, language, and currency pages
            org_link = f"[{owner}](by_org/{owner.lower()}.md)"
            currency_link = f"[{currency}](by_currency/{currency_file_name}.md)"
            primary_lang_link = f"[{primary_lang}](by_language/{primary_lang.lower()}.md)"
            
            # Create a nicer reserve button
            reserve_button = f"[<kbd>Reserve</kbd>]({claim_url})"
            
            # Format the row with the new columns
            f.write(f"| {org_link} | [{repo_name}](https://github.com/{owner}/{repo_name}) | [{title}]({url}) | {primary_lang_link} | {erg_equiv} | {currency_link} | {reserve_button} |\n")
    
    logger.info("Generated main bounty file")

def generate_summary_file(
    project_totals: Dict[str, Dict[str, Any]], 
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    total_value: float, 
    bounties_dir: str
) -> None:
    """
    Generate a summary markdown file for README reference.
    
    Args:
        project_totals: Dictionary of project totals
        languages: Dictionary of languages and their bounties
        currencies_dict: Dictionary of currencies and their bounties
        orgs: Dictionary of organizations and their bounties
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        total_value: Total value of bounties
        bounties_dir: Bounties directory
    """
    logger.info("Generating summary file")
    
    summary_file = f'{bounties_dir}/summary.md'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("## 📋 Open Bounties\n\n")
        f.write(f"**[View Current Open Bounties →](/{bounties_dir}/all.md)**\n\n")
        
        # Add navigation badges
        f.write("## Navigation\n\n")
        f.write(format_navigation_badges(
            total_bounties, 
            len(languages), 
            len(currencies_dict), 
            len(orgs), 
            len(conversion_rates), 
            f"/{bounties_dir}/"
        ))
        f.write("\n\n")
        
        f.write("## Projects\n\n")
        f.write("| Project | Count | Value |\n")
        f.write("|----------|-------|-------|\n")
        
        # Add rows for major projects (those with more than 1 bounty)
        for owner, totals in sorted(project_totals.items(), key=lambda x: x[1]["value"], reverse=True):
            if totals["count"] > 0:
                # Add link to organization page
                org_link = f"[{owner}](/{bounties_dir}/by_org/{owner.lower()}.md)"
                f.write(f"| {org_link} | {totals['count']} | {totals['value']:,.2f} ERG |\n")
        
        # Add overall total
        f.write(f"| **Total** | **{total_bounties}** | **{total_value:,.2f} ERG** |\n\n")
        
        # Calculate totals by currency (excluding bounties with "Not specified" amounts)
        currency_totals = {}
        for currency, currency_bounties in currencies_dict.items():
            # Count only bounties with specified amounts (excluding "Ongoing" programs)
            specified_bounties = [b for b in currency_bounties if b["amount"] != "Not specified" and b["amount"] != "Ongoing"]
            currency_totals[currency] = {"count": len(specified_bounties), "value": 0.0}
            
            for bounty in specified_bounties:
                amount = bounty["amount"]
                currency_totals[currency]["value"] += calculate_erg_value(amount, currency, conversion_rates)
        
        # Add currency breakdown
        f.write("## Currencies\n\n")
        f.write("| Currency | Count | Total Value (ERG) |\n")
        f.write("|----------|-------|------------------|\n")
        
        # Write currency rows
        for currency, totals in sorted(currency_totals.items(), key=lambda x: x[1]["value"], reverse=True)[:5]:  # Top 5 currencies
            # Format the currency name for the file link
            if currency == "Not specified":
                currency_file_name = "not_specified"
            elif currency == "g GOLD":
                currency_file_name = "gold"
            else:
                currency_file_name = currency.lower()
            
            # Add link to currency page
            currency_link = f"[{currency}](/{bounties_dir}/by_currency/{currency_file_name}.md)"
            
            f.write(f"| {currency_link} | {totals['count']} | {totals['value']:.2f} |\n")
        
        f.write(f"\n[View all currencies →](/{bounties_dir}/by_currency/)\n\n")
        
        # Add language breakdown
        f.write("## Languages\n\n")
        f.write("| Language | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")
        
        # Write language rows
        for lang, lang_bounties in sorted(languages.items(), key=lambda x: len(x[1]), reverse=True)[:5]:  # Top 5 languages
            count = len(lang_bounties)
            percentage = (count / total_bounties) * 100 if total_bounties > 0 else 0
            f.write(f"| [{lang}](/{bounties_dir}/by_language/{lang.lower()}.md) | {count} | {percentage:.1f}% |\n")
        
        f.write(f"\n[View all languages →](/{bounties_dir}/by_language/)\n\n")
        
        f.write("Open bounties are updated daily with values shown in ERG equivalent. Some bounties may be paid in other tokens as noted in the \"Paid in\" column of the bounty listings.\n")
        
        f.write(f"\n[View current currency prices →](/{bounties_dir}/currency_prices.md)\n")
    
    logger.info("Generated summary file")

def update_ongoing_programs_table(
    bounty_data: List[Dict[str, Any]], 
    bounties_dir: str
) -> None:
    """
    Update the table in the ongoing programs markdown file.
    
    Args:
        bounty_data: List of bounty data
        bounties_dir: Bounties directory
    """
    logger.info("Updating ongoing programs table")
    
    # Filter for ongoing programs
    ongoing_programs = [b for b in bounty_data if b["amount"] == "Ongoing"]
    
    if not ongoing_programs:
        logger.info("No ongoing programs found, skipping table update")
        return
    
    # Path to the ongoing programs file
    ongoing_file = 'docs/ongoing-programs.md'
    
    try:
        # Read the existing file
        with open(ongoing_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table section
        table_start = content.find("## Current Ongoing Programs")
        if table_start == -1:
            # If the section doesn't exist, add it
            table_start = content.find("# 🔄 Ongoing Reward Programs")
            if table_start == -1:
                logger.error("Could not find a place to insert the table in ongoing-programs.md")
                return
            
            # Find the end of the introduction paragraph
            intro_end = content.find("\n\n", table_start)
            if intro_end == -1:
                intro_end = len(content)
            
            # Insert the table section after the introduction
            before_table = content[:intro_end + 2]  # Include the newlines
            after_table = content[intro_end + 2:]
            
            # Create the new table content
            table_content = "## Current Ongoing Programs\n\n"
            table_content += "|Organisation|Repository|Title & Link|Primary Language|Value|ERG Value|Paid In|Reserve|\n"
            table_content += "|---|---|---|---|---|---|---|---|\n"
            
            for program in ongoing_programs:
                owner = program["owner"]
                title = program["title"]
                url = program["url"]
                primary_lang = program["primary_lang"]
                repo = program["repo"]
                
                # Add links to organization pages
                org_link = f"[{owner}](../bounties/by_org/{owner.lower()}.md)"
                
                # Create a nicer details button
                details_button = f"[<kbd>Details</kbd>](#{title.lower().replace(' ', '-').replace('/', '').replace('[', '').replace(']', '')})"
                
                # For each program, add a row to the table
                table_content += f"| {org_link} | [{repo}](https://github.com/{owner}/{repo}) | [{title}]({url}) | {primary_lang} | Varies | Based on contribution | ERG | {details_button} |\n"
            
            # Combine the parts
            new_content = before_table + table_content + "\n" + after_table
        else:
            # If the section exists, find where the table ends
            table_end = content.find("\n\n", table_start)
            if table_end == -1:
                table_end = len(content)
            
            # Create the new table content
            table_content = "## Current Ongoing Programs\n\n"
            table_content += "|Organisation|Repository|Title & Link|Primary Language|Value|ERG Value|Paid In|Reserve|\n"
            table_content += "|---|---|---|---|---|---|---|---|\n"
            
            for program in ongoing_programs:
                owner = program["owner"]
                title = program["title"]
                url = program["url"]
                primary_lang = program["primary_lang"]
                repo = program["repo"]
                
                # Add links to organization pages
                org_link = f"[{owner}](../bounties/by_org/{owner.lower()}.md)"
                
                # Create a nicer details button
                details_button = f"[<kbd>Details</kbd>](#{title.lower().replace(' ', '-').replace('/', '').replace('[', '').replace(']', '')})"
                
                # For each program, add a row to the table
                table_content += f"| {org_link} | [{repo}](https://github.com/{owner}/{repo}) | [{title}]({url}) | {primary_lang} | Varies | Based on contribution | ERG | {details_button} |\n"
            
            # Combine the parts
            new_content = content[:table_start] + table_content + content[table_end:]
        
        # Write the updated content back to the file
        with open(ongoing_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("Updated ongoing programs table")
    except FileNotFoundError:
        logger.error(f"File {ongoing_file} not found")
    except Exception as e:
        logger.error(f"Error updating ongoing programs table: {e}")

def generate_featured_bounties_file(
    bounty_data: List[Dict[str, Any]], 
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    total_value: float,
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    bounties_dir: str
) -> None:
    """
    Generate a featured bounties markdown file.
    
    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        total_value: Total value of bounties
        languages: Dictionary of languages and their bounties
        currencies_dict: Dictionary of currencies and their bounties
        orgs: Dictionary of organizations and their bounties
        bounties_dir: Bounties directory
    """
    logger.info("Generating featured bounties file")
    
    featured_bounties_file = f'{bounties_dir}/featured_bounties.md'
    with open(featured_bounties_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Featured Bounties\n\n")
        f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
        
        # Add navigation badges
        f.write("## Navigation\n\n")
        f.write(format_navigation_badges(
            total_bounties, 
            len(languages), 
            len(currencies_dict), 
            len(orgs), 
            len(conversion_rates)
        ))
        f.write("\n\n")
        
        # Get current date for the week row
        current_date = datetime.now().strftime("%b %d, %Y")
        
        # Find top 2 highest value bounties to feature
        top_bounties = []
        for bounty in bounty_data:
            amount = bounty["amount"]
            currency = bounty["currency"]
            title = bounty["title"]
            url = bounty["url"]
            owner = bounty["owner"]
            
            if amount != "Not specified" and amount != "Ongoing":
                try:
                    # Convert to ERG equivalent
                    value = calculate_erg_value(amount, currency, conversion_rates)
                    
                    top_bounties.append({
                        "title": title,
                        "value": value,
                        "amount": amount,
                        "currency": currency,
                        "url": url,
                        "owner": owner
                    })
                except ValueError:
                    pass
        
        # Sort by value and get top 2
        top_bounties.sort(key=lambda x: x["value"], reverse=True)
        top_bounties = top_bounties[:2]
        
        # Write the featured bounties table
        f.write("## Top Bounties by Value\n\n")
        f.write("| Bounty | Organization | Value | Currency |\n")
        f.write("|--------|--------------|-------|----------|\n")
        
        # Add rows for featured bounties
        for bounty in top_bounties:
            # Format the currency name for the file link
            currency = bounty["currency"]
            if currency == "Not specified":
                currency_file_name = "not_specified"
            elif currency == "g GOLD":
                currency_file_name = "gold"
            else:
                currency_file_name = currency.lower()
            
            # Add links to organization and currency pages
            org_link = f"[{bounty['owner']}](by_org/{bounty['owner'].lower()}.md)"
            currency_link = f"[{currency}](by_currency/{currency_file_name}.md)"
            
            # Calculate ERG equivalent
            erg_equiv = bounty["value"]
            
            f.write(f"| [{bounty['title']}]({bounty['url']}) | {org_link} | {erg_equiv:.2f} ERG | {currency_link} |\n")
        
        f.write("\n## Weekly Summary\n\n")
        f.write("| Date | Open Bounties | Total Value |\n")
        f.write("|------|--------------|-------------|\n")
        f.write(f"| {current_date} | {total_bounties} | {total_value:,.2f} ERG |\n\n")
    
    logger.info("Generated featured bounties file")
