import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger('config')

class BountyConfig:
    """
    Configuration handler for the bounty finder.
    Manages loading configuration from files and environment variables.
    """
    
    def __init__(self, bounties_dir: str = 'bounties'):
        """
        Initialize the configuration handler.
        
        Args:
            bounties_dir: Directory where bounty files are stored
        """
        self.bounties_dir = bounties_dir
        self.github_token = self._get_github_token()
        
    def _get_github_token(self) -> Optional[str]:
        """
        Get GitHub token from environment variable.
        
        Returns:
            GitHub token or None if not found
        """
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.error("GITHUB_TOKEN environment variable is required")
            return None
        return token
    
    def load_tracked_repos(self) -> List[Dict[str, str]]:
        """
        Load tracked repositories from configuration file.
        
        Returns:
            List of repository objects with 'owner' and 'repo' keys
        """
        try:
            with open(f'{self.bounties_dir}/tracked_repos.json', 'r') as f:
                repos = json.load(f)
                logger.info(f"Loaded {len(repos)} tracked repositories")
                return repos
        except Exception as e:
            logger.error(f"Error reading {self.bounties_dir}/tracked_repos.json: {e}")
            return []
    
    def load_tracked_orgs(self) -> List[Dict[str, str]]:
        """
        Load tracked organizations from configuration file.
        
        Returns:
            List of organization objects with 'org' key
        """
        try:
            with open(f'{self.bounties_dir}/tracked_orgs.json', 'r') as f:
                orgs = json.load(f)
                logger.info(f"Loaded {len(orgs)} tracked organizations")
                return orgs
        except Exception as e:
            logger.warning(f"Error reading {self.bounties_dir}/tracked_orgs.json: {e}")
            return []
    
    def load_extra_bounties(self) -> List[Dict[str, Any]]:
        """
        Load manually added bounties from extra_bounties.json file.
        
        Returns:
            List of bounty objects with all required fields
        """
        try:
            with open(f'{self.bounties_dir}/extra_bounties.json', 'r') as f:
                extra_bounties = json.load(f)
                # Update timestamp for each bounty to ensure it's current
                for bounty in extra_bounties:
                    if 'timestamp' not in bounty or not bounty['timestamp']:
                        bounty['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Loaded {len(extra_bounties)} extra bounties")
                return extra_bounties
        except Exception as e:
            logger.warning(f"Error reading {self.bounties_dir}/extra_bounties.json: {e}")
            return []
    
    def is_valid(self) -> bool:
        """
        Check if the configuration is valid.
        
        Returns:
            True if the configuration is valid, False otherwise
        """
        return self.github_token is not None
