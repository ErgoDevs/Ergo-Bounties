import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from .api_client import get_org_repos, get_repo_languages, get_issues
from .extractors import check_bounty_labels, extract_bounty_from_labels, extract_bounty_from_text
from .utils import calculate_erg_value

# Configure logging
logger = logging.getLogger('processor')

class BountyProcessor:
    """
    Processor for bounty data.
    Handles fetching and processing bounty information from GitHub.
    """
    
    # Class variable to store the singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'BountyProcessor':
        """
        Get the singleton instance of the BountyProcessor.
        
        Returns:
            The BountyProcessor instance
        """
        if cls._instance is None:
            raise RuntimeError("BountyProcessor instance not initialized. Call the constructor first.")
        return cls._instance
    
    def __init__(self, github_token: str, conversion_rates: Dict[str, float]):
        # Set the singleton instance
        BountyProcessor._instance = self
        """
        Initialize the bounty processor.
        
        Args:
            github_token: GitHub API token
            conversion_rates: Dictionary of conversion rates
        """
        self.github_token = github_token
        self.conversion_rates = conversion_rates
        self.bounty_data = []
        self.project_totals = {}
        
    def process_repositories(self, repos_to_query: List[Dict[str, str]]) -> None:
        """
        Process repositories to find bounties.
        
        Args:
            repos_to_query: List of repository objects with 'owner' and 'repo' keys
        """
        for repo in repos_to_query:
            owner = repo['owner']
            repo_name = repo['repo']
            
            logger.info(f"Processing {owner}/{repo_name}...")
            
            # Get repository languages
            languages = get_repo_languages(owner, repo_name, self.github_token)
            primary_lang = languages[0] if languages else "Unknown"
            secondary_lang = languages[1] if len(languages) > 1 else "None"
            
            # Initialize project counter if not exists
            if owner not in self.project_totals:
                self.project_totals[owner] = {"count": 0, "value": 0.0}
            
            # Get issues
            issues = get_issues(owner, repo_name, self.github_token)
            
            # Process each issue
            for issue in issues:
                self._process_issue(issue, owner, repo_name, primary_lang, secondary_lang)
    
    def process_organizations(self, orgs_to_query: List[Dict[str, str]], repos_to_query: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process organizations to find repositories.
        
        Args:
            orgs_to_query: List of organization objects with 'org' key
            repos_to_query: Current list of repositories
            
        Returns:
            Updated list of repositories
        """
        updated_repos = repos_to_query.copy()
        
        for org_entry in orgs_to_query:
            org = org_entry['org']
            logger.info(f"Fetching repositories for organization: {org}")
            
            org_repos = get_org_repos(org, self.github_token)
            for repo in org_repos:
                # Skip archived repositories
                if repo.get('archived', False):
                    logger.debug(f"Skipping archived repository: {org}/{repo['name']}")
                    continue
                    
                # Skip forks if they don't have issues
                if repo.get('fork', False) and not repo.get('has_issues', False):
                    logger.debug(f"Skipping fork without issues: {org}/{repo['name']}")
                    continue
                    
                # Add to repos_to_query if not already there
                repo_entry = {"owner": org, "repo": repo['name']}
                if repo_entry not in updated_repos:
                    logger.info(f"Adding repository from organization: {org}/{repo['name']}")
                    updated_repos.append(repo_entry)
        
        return updated_repos
    
    def _process_issue(self, issue: Dict[str, Any], owner: str, repo_name: str, primary_lang: str, secondary_lang: str) -> None:
        """
        Process a single issue to check if it's a bounty.
        
        Args:
            issue: Issue object from GitHub API
            owner: Repository owner
            repo_name: Repository name
            primary_lang: Primary language of the repository
            secondary_lang: Secondary language of the repository
        """
        if issue['state'] == 'open':
            if ("bounty" in issue["title"].lower() or 
                "b-" in issue["title"].lower() or 
                check_bounty_labels(issue["labels"])):
                
                title = issue['title'].replace(",", " ")
                
                # First check labels for bounty amount
                amount, currency = extract_bounty_from_labels(issue["labels"])
                
                # If no bounty found in labels, check title and body
                if not amount:
                    amount, currency = extract_bounty_from_text(title, issue.get('body', ''))
                
                # If still no bounty found, mark as "Not specified"
                if not amount:
                    amount = "Not specified"
                    currency = "Not specified"
                
                # Store the bounty information
                bounty_info = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "owner": owner,
                    "repo": repo_name,
                    "title": title,
                    "url": issue['html_url'],
                    "amount": amount,
                    "currency": currency,
                    "primary_lang": primary_lang,
                    "secondary_lang": secondary_lang,
                    "labels": [label['name'] for label in issue['labels']],
                    "issue_number": issue['number'],
                    "creator": issue['user']['login']  # GitHub username of the issue creator
                }
                
                self.bounty_data.append(bounty_info)
                
                # Update project totals
                self.project_totals[owner]["count"] += 1
                
                # Try to convert amount to float for totals
                self.project_totals[owner]["value"] += calculate_erg_value(amount, currency, self.conversion_rates)
    
    def get_bounty_data(self) -> List[Dict[str, Any]]:
        """
        Get the processed bounty data.
        
        Returns:
            List of bounty information dictionaries
        """
        return self.bounty_data
    
    def get_project_totals(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the project totals.
        
        Returns:
            Dictionary of project totals
        """
        return self.project_totals
    
    def add_extra_bounties(self, extra_bounties: List[Dict[str, Any]]) -> None:
        """
        Add manually specified bounties from extra_bounties.json.
        
        Args:
            extra_bounties: List of bounty objects with all required fields
        """
        for bounty in extra_bounties:
            # Add the bounty to the bounty data
            self.bounty_data.append(bounty)
            
            # Update project totals
            owner = bounty["owner"]
            if owner not in self.project_totals:
                self.project_totals[owner] = {"count": 0, "value": 0.0}
            
            self.project_totals[owner]["count"] += 1
            
            # Try to convert amount to float for totals
            amount = bounty.get("amount", "Not specified")
            currency = bounty.get("currency", "Not specified")
            self.project_totals[owner]["value"] += calculate_erg_value(amount, currency, self.conversion_rates)
    
    def get_total_stats(self) -> Tuple[int, float]:
        """
        Get overall total statistics.
        
        Returns:
            Tuple of (total_bounties, total_value)
        """
        total_bounties = sum(project["count"] for project in self.project_totals.values())
        total_value = sum(project["value"] for project in self.project_totals.values())
        return total_bounties, total_value
    
    def group_by_language(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group bounties by language.
        
        Returns:
            Dictionary of language -> list of bounties
        """
        languages = {}
        for bounty in self.bounty_data:
            # Skip bounties with "Not specified" amounts for "Unknown" language
            if bounty["primary_lang"] == "Unknown" and bounty["amount"] == "Not specified":
                continue
                
            primary_lang = bounty["primary_lang"]
            if primary_lang not in languages:
                languages[primary_lang] = []
            languages[primary_lang].append(bounty)
            
        # Remove "Unknown" language if it's empty after filtering
        if "Unknown" in languages and len(languages["Unknown"]) == 0:
            del languages["Unknown"]
            
        return languages
    
    def group_by_organization(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group bounties by organization.
        
        Returns:
            Dictionary of organization -> list of bounties
        """
        orgs = {}
        for bounty in self.bounty_data:
            owner = bounty["owner"]
            if owner not in orgs:
                orgs[owner] = []
            orgs[owner].append(bounty)
        return orgs
    
    def group_by_currency(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group bounties by currency.
        
        Returns:
            Dictionary of currency -> list of bounties
        """
        currencies_dict = {}
        for bounty in self.bounty_data:
            currency = bounty["currency"]
            
            # Skip "Not specified" currency
            if currency == "Not specified":
                continue
                
            if currency not in currencies_dict:
                currencies_dict[currency] = []
            currencies_dict[currency].append(bounty)
        return currencies_dict
