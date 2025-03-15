#!/usr/bin/env python3
"""
Test script to verify that the bounty finder program works correctly.
This script:
1. Loads the GitHub token from the .env file
2. Sets it as an environment variable
3. Runs the bounty_finder.py script
4. Verifies that all the expected .md files are generated with correct content

This ensures that the entire program functions correctly.
"""

import os
import sys
import subprocess
import logging
import requests
import unittest
import tempfile
import shutil
import json
import re
import time
import threading
from datetime import datetime
from pathlib import Path

# Add colorful output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORED_OUTPUT = True
except ImportError:
    print("Installing colorama for colored output...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORED_OUTPUT = True

# Configure logging with custom formatter for pretty output
class PrettyFormatter(logging.Formatter):
    """Custom formatter for pretty logging output."""
    
    def format(self, record):
        """Format the log record with colors and symbols."""
        if COLORED_OUTPUT:
            level_colors = {
                'DEBUG': Fore.BLUE,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.RED + Style.BRIGHT
            }
            level_symbols = {
                'DEBUG': '🔍',
                'INFO': '✓',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '💥'
            }
            
            level_color = level_colors.get(record.levelname, '')
            level_symbol = level_symbols.get(record.levelname, '')
            
            # Format timestamp
            timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            
            # Format message
            formatted_msg = f"{Fore.CYAN}{timestamp}{Style.RESET_ALL} {level_color}{level_symbol} {record.message}"
            
            return formatted_msg
        else:
            return super().format(record)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(PrettyFormatter())
logger = logging.getLogger('bounty_finder_test')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False  # Prevent duplicate logs

# Get the absolute path to the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..'))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, '.github', 'workflows', 'scripts')
ENV_FILE = os.path.join(SCRIPTS_DIR, '.env')
BOUNTY_FINDER = os.path.join(SCRIPTS_DIR, 'bounty_finder.py')

# Spinner for long-running operations
class Spinner:
    """A simple spinner for indicating progress."""
    
    def __init__(self, message="Working"):
        """Initialize the spinner with a message."""
        self.message = message
        self.running = False
        self.spinner_thread = None
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current = 0
    
    def spin(self):
        """Spin the spinner."""
        while self.running:
            sys.stdout.write(f"\r{Fore.CYAN}{self.message} {self.spinner_chars[self.current]}{Style.RESET_ALL}")
            sys.stdout.flush()
            self.current = (self.current + 1) % len(self.spinner_chars)
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()
    
    def start(self):
        """Start the spinner."""
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self):
        """Stop the spinner."""
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()

def print_header(title):
    """Print a section header."""
    if COLORED_OUTPUT:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(80)}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'=' * 80}")
        print(f"{title.center(80)}")
        print(f"{'=' * 80}\n")

def print_success(message):
    """Print a success message."""
    if COLORED_OUTPUT:
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    else:
        print(f"✓ {message}")

def print_error(message):
    """Print an error message."""
    if COLORED_OUTPUT:
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    else:
        print(f"❌ {message}")

def print_warning(message):
    """Print a warning message."""
    if COLORED_OUTPUT:
        print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")
    else:
        print(f"⚠️ {message}")

def print_info(message):
    """Print an info message."""
    if COLORED_OUTPUT:
        print(f"{Fore.BLUE}ℹ️ {message}{Style.RESET_ALL}")
    else:
        print(f"ℹ️ {message}")

def print_step(step_number, total_steps, message):
    """Print a step message."""
    if COLORED_OUTPUT:
        print(f"{Fore.CYAN}[{step_number}/{total_steps}] {message}{Style.RESET_ALL}")
    else:
        print(f"[{step_number}/{total_steps}] {message}")

class TestBountyFinder(unittest.TestCase):
    """Test case for the bounty finder program."""
    
    def setUp(self):
        """Set up the test environment."""
        print_header("Setting up test environment")
        
        # Create a timestamp for verification
        self.test_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_info(f"Test timestamp: {self.test_timestamp}")
        
        # Create a temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.bounties_dir = os.path.join(self.temp_dir, 'bounties')
        os.makedirs(self.bounties_dir, exist_ok=True)
        print_success(f"Created temporary directory: {self.temp_dir}")
        
        # Copy necessary files to the temporary directory
        self._copy_required_files()
        
        # Load the GitHub token from .env file
        self.github_token = self._load_github_token()
        
        # Set the environment variable
        os.environ['GITHUB_TOKEN'] = self.github_token
        print_success("GitHub token loaded and set as environment variable")
    
    def tearDown(self):
        """Clean up after the test."""
        print_header("Cleaning up test environment")
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
        print_success(f"Removed temporary directory: {self.temp_dir}")
    
    def _copy_required_files(self):
        """Copy required files to the temporary directory."""
        print_step(1, 3, "Copying required files to temporary directory")
        
        # Copy tracked_repos.json and tracked_orgs.json
        src_repos = os.path.join(PROJECT_ROOT, 'bounties', 'tracked_repos.json')
        dst_repos = os.path.join(self.bounties_dir, 'tracked_repos.json')
        
        src_orgs = os.path.join(PROJECT_ROOT, 'bounties', 'tracked_orgs.json')
        dst_orgs = os.path.join(self.bounties_dir, 'tracked_orgs.json')
        
        src_extra = os.path.join(PROJECT_ROOT, 'bounties', 'extra_bounties.json')
        dst_extra = os.path.join(self.bounties_dir, 'extra_bounties.json')
        
        try:
            shutil.copy2(src_repos, dst_repos)
            print_success(f"Copied {src_repos} to {dst_repos}")
            
            shutil.copy2(src_orgs, dst_orgs)
            print_success(f"Copied {src_orgs} to {dst_orgs}")
            
            shutil.copy2(src_extra, dst_extra)
            print_success(f"Copied {src_extra} to {dst_extra}")
            
            # Modify extra_bounties.json to add a test bounty with current timestamp
            self._add_test_bounty(dst_extra)
            
        except Exception as e:
            print_error(f"Error copying required files: {e}")
            raise
    
    def _add_test_bounty(self, extra_bounties_path):
        """Add a test bounty to extra_bounties.json with current timestamp."""
        print_step(2, 3, "Adding test bounty to extra_bounties.json")
        
        try:
            # Read the existing extra bounties
            with open(extra_bounties_path, 'r') as f:
                extra_bounties = json.load(f)
            
            # Add a test bounty with current timestamp
            test_bounty = {
                "timestamp": self.test_timestamp,
                "owner": "test-owner",
                "repo": "test-repo",
                "title": f"Test Bounty {self.test_timestamp}",
                "url": "https://github.com/test-owner/test-repo/issues/1",
                "amount": "100",
                "currency": "ERG",
                "primary_lang": "JavaScript",
                "secondary_lang": "None",
                "labels": ["test", "bounty"],
                "issue_number": 1,
                "creator": "test-user"
            }
            
            extra_bounties.append(test_bounty)
            
            # Write the modified extra bounties back to the file
            with open(extra_bounties_path, 'w') as f:
                json.dump(extra_bounties, f, indent=2)
                
            print_success(f"Added test bounty with timestamp {self.test_timestamp}")
            
        except Exception as e:
            print_error(f"Error adding test bounty: {e}")
            raise
    
    def _load_github_token(self):
        """Load the GitHub token from .env file."""
        print_step(3, 3, "Loading GitHub token from .env file")
        
        try:
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key.strip() == 'github_token':
                            # Remove quotes if present
                            token = value.strip('"\'')
                            print_success("GitHub token found in .env file")
                            # Mask the token for security
                            masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:]
                            print_info(f"Token: {masked_token}")
                            return token
            
            print_error("GitHub token not found in .env file")
            raise ValueError("GitHub token not found in .env file")
        except Exception as e:
            print_error(f"Error reading .env file: {e}")
            raise
    
    def test_github_token_validity(self):
        """Test if the GitHub token is valid."""
        print_header("Testing GitHub Token Validity")
        
        spinner = Spinner("Validating GitHub token")
        spinner.start()
        
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get('https://api.github.com/user', headers=headers)
            
            spinner.stop()
            
            self.assertEqual(response.status_code, 200, 
                            f"GitHub token is invalid. Status code: {response.status_code}, Response: {response.json()}")
            
            user_data = response.json()
            print_success(f"GitHub token is valid! Authenticated as: {user_data.get('login')}")
            
            # Print rate limit information
            rate_limit = response.headers.get('X-RateLimit-Remaining', 'Unknown')
            print_info(f"GitHub API rate limit remaining: {rate_limit}")
            
        except Exception as e:
            spinner.stop()
            print_error(f"Error validating GitHub token: {e}")
            raise
    
    def test_bounty_finder_execution(self):
        """Test if the bounty finder executes successfully and generates files."""
        print_header("Testing Bounty Finder Execution")
        
        # Create a temporary modified version of bounty_finder.py
        temp_bounty_finder = os.path.join(self.temp_dir, 'temp_bounty_finder.py')
        
        try:
            print_step(1, 5, "Preparing bounty finder script")
            
            # Read the original bounty_finder.py
            with open(BOUNTY_FINDER, 'r') as f:
                content = f.read()
            
            # Replace bounties_dir = 'bounties' with absolute path to the temporary bounties folder
            modified_content = content.replace(
                "bounties_dir = 'bounties'", 
                f"bounties_dir = '{self.bounties_dir}'"
            )
            
            # Write the modified content to a temporary file
            with open(temp_bounty_finder, 'w') as f:
                f.write(modified_content)
            
            # Make the temporary file executable
            os.chmod(temp_bounty_finder, 0o755)
            print_success("Bounty finder script prepared")
            
            print_step(2, 5, "Setting up environment")
            # Set PYTHONPATH to include the scripts directory
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{SCRIPTS_DIR}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = SCRIPTS_DIR
                
            print_info(f"PYTHONPATH set to: {env['PYTHONPATH']}")
            
            print_step(3, 5, "Running bounty finder")
            print_info("This may take a minute or two...")
            
            spinner = Spinner("Running bounty finder")
            spinner.start()
            
            start_time = time.time()
            result = subprocess.run([sys.executable, temp_bounty_finder], 
                                   env=env, 
                                   capture_output=True, 
                                   text=True)
            end_time = time.time()
            
            spinner.stop()
            
            # Check if the process completed successfully
            if result.returncode == 0:
                print_success(f"Bounty finder completed successfully in {end_time - start_time:.2f} seconds")
                
                # Parse and display important information from the output
                print_header("Bounty Finder Output Summary")
                
                # Extract and display repository count
                repo_count_match = re.search(r"Processing (\d+) repositories", result.stderr)
                if repo_count_match:
                    repo_count = repo_count_match.group(1)
                    print_info(f"Repositories processed: {repo_count}")
                
                # Extract and display bounty count
                bounty_count_match = re.search(r"Total bounties found: (\d+)", result.stderr)
                if bounty_count_match:
                    bounty_count = bounty_count_match.group(1)
                    print_success(f"Total bounties found: {bounty_count}")
                
                # Extract and display total value
                value_match = re.search(r"Total ERG equivalent value: ([\d\.]+)", result.stderr)
                if value_match:
                    total_value = value_match.group(1)
                    print_success(f"Total ERG equivalent value: {total_value}")
                
                # Extract and display conversion rates
                rates_match = re.search(r"Using conversion rates: ({[^}]+})", result.stderr)
                if rates_match:
                    rates_str = rates_match.group(1).replace("'", '"')
                    try:
                        # Try to parse as JSON
                        rates = json.loads(rates_str)
                        print_info("Conversion rates:")
                        for currency, rate in rates.items():
                            print_info(f"  - {currency}: {rate}")
                    except json.JSONDecodeError:
                        # If parsing fails, just display the raw string
                        print_info(f"Conversion rates: {rates_str}")
                
                # Extract and display found bounties by label
                bounty_labels = re.findall(r"Found bounty in label: ([\w\s]+)", result.stderr)
                if bounty_labels:
                    print_info(f"Found {len(bounty_labels)} bounties in labels:")
                    # Group by currency and amount
                    bounty_groups = {}
                    for label in bounty_labels:
                        parts = label.split()
                        if len(parts) >= 2:
                            amount = parts[0]
                            currency = parts[1]
                            key = f"{currency}"
                            if key not in bounty_groups:
                                bounty_groups[key] = []
                            bounty_groups[key].append(amount)
                    
                    # Display grouped bounties
                    for currency, amounts in bounty_groups.items():
                        print_info(f"  - {currency}: {len(amounts)} bounties")
                        # Count occurrences of each amount
                        amount_counts = {}
                        for amount in amounts:
                            if amount not in amount_counts:
                                amount_counts[amount] = 0
                            amount_counts[amount] += 1
                        
                        # Display amount counts
                        for amount, count in amount_counts.items():
                            print_info(f"    - {amount} {currency}: {count} bounties")
                
                # Display full output if requested
                if os.environ.get('VERBOSE', '').lower() in ('true', '1', 'yes'):
                    print_header("Full Bounty Finder Output")
                    print(result.stderr)
            else:
                print_error(f"Bounty finder failed with return code {result.returncode}")
                print_info("Stdout:")
                print(result.stdout)
                print_info("Stderr:")
                print(result.stderr)
                self.assertEqual(result.returncode, 0, 
                                f"Bounty finder failed with return code {result.returncode}")
            
            print_step(4, 5, "Verifying generated files")
            self._verify_generated_files()
            
            print_step(5, 5, "Verifying test bounty inclusion")
            self._verify_test_bounty_included()
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_bounty_finder):
                os.remove(temp_bounty_finder)
    
    def _verify_generated_files(self):
        """Verify that all expected files were generated."""
        expected_files = [
            'all.md',
            'summary.md',
            'featured_bounties.md',
            'currency_prices.md'
        ]
        
        # Also check if README.md in the project root was updated
        readme_path = os.path.join(PROJECT_ROOT, 'README.md')
        if os.path.exists(readme_path) and os.path.getsize(readme_path) > 0:
            # Check if the file was modified recently (within the last 2 minutes)
            mtime = os.path.getmtime(readme_path)
            if time.time() - mtime < 120:  # 2 minutes
                print_success(f"README.md in project root was updated recently")
                
                # Check if the README.md contains the test timestamp
                with open(readme_path, 'r') as f:
                    content = f.read()
                    
                # Look for today's date in the README.md
                today_date = datetime.now().strftime("%b %d, %Y")
                if today_date in content:
                    print_success(f"README.md contains today's date: {today_date}")
                else:
                    print_warning(f"README.md does not contain today's date: {today_date}")
            else:
                print_warning(f"README.md in project root was not modified recently")
        else:
            print_warning(f"README.md in project root does not exist or is empty")
        
        expected_dirs = [
            'by_language',
            'by_currency',
            'by_org'
        ]
        
        # Check if expected files exist
        for file in expected_files:
            path = os.path.join(self.bounties_dir, file)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                print_success(f"File {file} was generated successfully")
            else:
                if not os.path.exists(path):
                    print_error(f"File {file} was not generated")
                    self.assertTrue(os.path.exists(path), f"Expected file {file} was not generated")
                else:
                    print_error(f"File {file} is empty")
                    self.assertTrue(os.path.getsize(path) > 0, f"Generated file {file} is empty")
            
            # Check if the file was modified recently (within the last minute)
            mtime = os.path.getmtime(path)
            if time.time() - mtime < 120:  # 2 minutes
                print_success(f"File {file} was modified recently")
            else:
                print_warning(f"File {file} was not modified recently")
                self.assertTrue(time.time() - mtime < 120, 
                               f"File {file} was not modified recently")
        
        # Check if expected directories exist and contain files
        for directory in expected_dirs:
            dir_path = os.path.join(self.bounties_dir, directory)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                print_success(f"Directory {directory} was created successfully")
            else:
                if not os.path.exists(dir_path):
                    print_error(f"Directory {directory} was not created")
                    self.assertTrue(os.path.exists(dir_path), f"Expected directory {directory} was not generated")
                else:
                    print_error(f"{directory} is not a directory")
                    self.assertTrue(os.path.isdir(dir_path), f"{directory} is not a directory")
            
            # Check if the directory contains files
            files = os.listdir(dir_path)
            if len(files) > 0:
                print_success(f"Directory {directory} contains {len(files)} files")
            else:
                print_error(f"Directory {directory} is empty")
                self.assertTrue(len(files) > 0, f"Directory {directory} is empty")
            
            # Check if at least one .md file exists in the directory
            md_files = [f for f in files if f.endswith('.md')]
            if len(md_files) > 0:
                print_success(f"Directory {directory} contains {len(md_files)} .md files")
            else:
                print_error(f"No .md files found in {directory}")
                self.assertTrue(len(md_files) > 0, f"No .md files found in {directory}")
            
            # Print the list of .md files
            print_info(f"Files in {directory}: {', '.join(md_files)}")
    
    def _verify_test_bounty_included(self):
        """Verify that the test bounty was included in the generated files."""
        # Check if the test bounty is included in all.md
        all_md_path = os.path.join(self.bounties_dir, 'all.md')
        with open(all_md_path, 'r') as f:
            content = f.read()
            
        # Look for the test bounty title
        test_bounty_title = f"Test Bounty {self.test_timestamp}"
        if test_bounty_title in content:
            print_success(f"Test bounty '{test_bounty_title}' found in all.md")
        else:
            print_error(f"Test bounty '{test_bounty_title}' not found in all.md")
            self.assertIn(test_bounty_title, content, 
                         f"Test bounty '{test_bounty_title}' not found in all.md")
        
        # Check if the test bounty is included in by_language/javascript.md
        test_lang_path = os.path.join(self.bounties_dir, 'by_language', 'javascript.md')
        if os.path.exists(test_lang_path):
            with open(test_lang_path, 'r') as f:
                content = f.read()
                
            if test_bounty_title in content:
                print_success(f"Test bounty '{test_bounty_title}' found in by_language/javascript.md")
            else:
                print_error(f"Test bounty '{test_bounty_title}' not found in by_language/javascript.md")
                self.assertIn(test_bounty_title, content, 
                             f"Test bounty '{test_bounty_title}' not found in by_language/javascript.md")
        else:
            print_warning(f"File by_language/javascript.md does not exist")
        
        # Check if the test bounty is included in by_org/test-owner.md
        test_org_path = os.path.join(self.bounties_dir, 'by_org', 'test-owner.md')
        if os.path.exists(test_org_path):
            with open(test_org_path, 'r') as f:
                content = f.read()
                
            if test_bounty_title in content:
                print_success(f"Test bounty '{test_bounty_title}' found in by_org/test-owner.md")
            else:
                print_error(f"Test bounty '{test_bounty_title}' not found in by_org/test-owner.md")
                self.assertIn(test_bounty_title, content, 
                             f"Test bounty '{test_bounty_title}' not found in by_org/test-owner.md")
        else:
            print_warning(f"File by_org/test-owner.md does not exist")
        
        # Check if the test bounty is included in by_currency/erg.md
        test_currency_path = os.path.join(self.bounties_dir, 'by_currency', 'erg.md')
        if os.path.exists(test_currency_path):
            with open(test_currency_path, 'r') as f:
                content = f.read()
                
            if test_bounty_title in content:
                print_success(f"Test bounty '{test_bounty_title}' found in by_currency/erg.md")
            else:
                print_error(f"Test bounty '{test_bounty_title}' not found in by_currency/erg.md")
                self.assertIn(test_bounty_title, content, 
                             f"Test bounty '{test_bounty_title}' not found in by_currency/erg.md")
        else:
            print_warning(f"File by_currency/erg.md does not exist")
        
        print_success("Test bounty was successfully included in the generated files")

def print_summary(result):
    """Print a summary of the test results."""
    print_header("Test Summary")
    
    if result.wasSuccessful():
        print_success("All tests passed successfully!")
    else:
        print_error("Some tests failed.")
        
    print_info(f"Tests run: {result.testsRun}")
    print_info(f"Errors: {len(result.errors)}")
    print_info(f"Failures: {len(result.failures)}")

def main():
    """Run the tests with pretty output."""
    print_header("Ergo Bounties Test Suite")
    print_info("Testing GitHub token and bounty finder functionality")
    
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBountyFinder)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    
    # Print summary
    print_summary(result)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
