import requests
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger('api_client')

def get_org_repos(org: str, github_token: str) -> List[Dict[str, Any]]:
    """
    Get all repositories for an organization.
    
    Args:
        org: Organization name
        github_token: GitHub API token
        
    Returns:
        List of repository objects
    """
    headers = {"Authorization": f"token {github_token}"}
    url = f"https://api.github.com/orgs/{org}/repos?per_page=100"
    all_repos = []
    
    logger.info(f"Fetching repositories for organization: {org}")
    
    while url:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            repos = response.json()
            all_repos.extend(repos)
            url = response.links.get('next', {}).get('url')
            
            logger.debug(f"Fetched {len(repos)} repositories from {org}, total: {len(all_repos)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repositories for organization {org}: {e}")
            return all_repos  # Return what we have so far
    
    logger.info(f"Successfully fetched {len(all_repos)} repositories from {org}")
    return all_repos

def get_repo_languages(owner: str, repo: str, github_token: str) -> List[str]:
    """
    Get languages used in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        github_token: GitHub API token
        
    Returns:
        List of languages (top 2 by usage)
    """
    headers = {"Authorization": f"token {github_token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    
    logger.debug(f"Fetching languages for repository: {owner}/{repo}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        languages = response.json()
        # Sort languages by bytes of code and get top 2
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:2]
        result = [lang[0] for lang in sorted_languages]
        
        logger.debug(f"Languages for {owner}/{repo}: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching languages for {owner}/{repo}: {e}")
        return []

def get_issues(owner: str, repo: str, github_token: str, state: str = 'open') -> List[Dict[str, Any]]:
    """
    Get issues from a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        github_token: GitHub API token
        state: Issue state (open, closed, all)
        
    Returns:
        List of issue objects
    """
    headers = {"Authorization": f"token {github_token}"}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues?state={state}&per_page=100'
    all_issues = []
    
    logger.info(f"Fetching {state} issues from repository: {owner}/{repo}")
    
    while url:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            issues = response.json()
            all_issues.extend(issues)
            url = response.links.get('next', {}).get('url')
            
            logger.debug(f"Fetched {len(issues)} issues from {owner}/{repo}, total: {len(all_issues)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues from {owner}/{repo}: {e}")
            return all_issues  # Return what we have so far
    
    logger.info(f"Successfully fetched {len(all_issues)} issues from {owner}/{repo}")
    return all_issues
