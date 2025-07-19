"""
GitHub API client for repository search and information retrieval.
Handles rate limiting, authentication, and API interactions.
"""

import requests
import time
from typing import Dict, List, Optional
from core.config import Config


class GitHubClient:
    """Client for interacting with the GitHub API to search for repositories."""
    
    def __init__(self):
        self.base_url = Config.GITHUB_API_BASE_URL
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Chameleon-Hackathon-Discovery/1.0'
        }
        
        # Add authentication if token is available
        if Config.GITHUB_TOKEN:
            self.headers['Authorization'] = f'token {Config.GITHUB_TOKEN}'
        
        self.last_request_time = 0
        self.requests_made = 0
        self.request_window_start = time.time()
    
    def _rate_limit_check(self):
        """Implement rate limiting to stay within GitHub API limits."""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.request_window_start > 60:  # 1 minute window
            self.requests_made = 0
            self.request_window_start = current_time
        
        # Check if we're approaching the limit
        if self.requests_made >= Config.GITHUB_REQUESTS_PER_MINUTE - 5:  # Leave buffer
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                print(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.requests_made = 0
                self.request_window_start = time.time()
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < Config.GITHUB_SEARCH_DELAY:
            time.sleep(Config.GITHUB_SEARCH_DELAY - time_since_last)
        
        self.last_request_time = time.time()
        self.requests_made += 1
    
    def search_repositories(self, query: str, per_page: int = 10, max_pages: int = 1, 
                          add_filters: bool = True) -> List[Dict]:
        """
        Search for repositories using the GitHub API.
        
        Args:
            query: Search query string
            per_page: Number of results per page (max 100)
            max_pages: Maximum number of pages to fetch
            add_filters: Whether to add filtering criteria to the query
            
        Returns:
            List of repository dictionaries
        """
        repositories = []
        
        # Add filtering criteria if requested
        if add_filters:
            query = self._add_search_filters(query)
        
        for page in range(1, max_pages + 1):
            self._rate_limit_check()
            
            url = f"{self.base_url}/search/repositories"
            params = {
                'q': query,
                'sort': 'updated',  # Sort by recent activity instead of stars
                'order': 'desc',
                'per_page': min(per_page, 100),  # GitHub API max is 100
                'page': page
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 403:
                    # Rate limited
                    rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                    if rate_limit_reset:
                        reset_time = int(rate_limit_reset)
                        wait_time = reset_time - int(time.time()) + 1
                        if wait_time > 0:
                            print(f"Rate limited. Waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                    else:
                        time.sleep(60)  # Default wait time
                        continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'items' not in data:
                    break
                
                # Process each repository
                for repo in data['items']:
                    processed_repo = self._process_repository(repo)
                    if processed_repo:
                        repositories.append(processed_repo)
                
                # Break if we got fewer results than requested (last page)
                if len(data['items']) < per_page:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error searching repositories: {e}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        
        return repositories
    
    def _add_search_filters(self, query: str) -> str:
        """Add filtering criteria to the search query."""
        filters = []
        
        # Add star range filter
        if Config.MIN_STARS > 0 or Config.MAX_STARS < float('inf'):
            if Config.MIN_STARS == Config.MAX_STARS:
                filters.append(f"stars:{Config.MIN_STARS}")
            else:
                max_stars = Config.MAX_STARS if Config.MAX_STARS != float('inf') else '*'
                filters.append(f"stars:{Config.MIN_STARS}..{max_stars}")
        
        # Add fork filter
        if Config.MAX_FORKS < float('inf'):
            filters.append(f"forks:0..{Config.MAX_FORKS}")
        
        # Add size filter (in KB)
        if Config.MAX_REPO_SIZE_KB < float('inf'):
            filters.append(f"size:0..{Config.MAX_REPO_SIZE_KB}")
        
        # Combine query with filters
        if filters:
            return f"{query} {' '.join(filters)}"
        return query
    
    def _process_repository(self, repo_data: Dict) -> Optional[Dict]:
        """Process and validate a repository from the API response."""
        try:
            # Extract relevant information
            processed = {
                'name': repo_data.get('name', ''),
                'full_name': repo_data.get('full_name', ''),
                'description': repo_data.get('description', ''),
                'html_url': repo_data.get('html_url', ''),
                'clone_url': repo_data.get('clone_url', ''),
                'language': repo_data.get('language', ''),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'size': repo_data.get('size', 0),  # Size in KB
                'topics': repo_data.get('topics', []),
                'created_at': repo_data.get('created_at', ''),
                'updated_at': repo_data.get('updated_at', ''),
                'default_branch': repo_data.get('default_branch', 'main'),
                'has_issues': repo_data.get('has_issues', False),
                'has_wiki': repo_data.get('has_wiki', False),
                'archived': repo_data.get('archived', False),
                'disabled': repo_data.get('disabled', False),
                'private': repo_data.get('private', False)
            }
            
            # Skip private, archived, or disabled repositories
            if processed['private'] or processed['archived'] or processed['disabled']:
                return None
            
            # Apply basic filtering
            if not self._meets_criteria(processed):
                return None
            
            return processed
            
        except Exception as e:
            print(f"Error processing repository data: {e}")
            return None
    
    def _meets_criteria(self, repo: Dict) -> bool:
        """Check if a repository meets the basic filtering criteria."""
        stars = repo.get('stars', 0)
        forks = repo.get('forks', 0)
        size = repo.get('size', 0)
        
        # Check star range
        if not (Config.MIN_STARS <= stars <= Config.MAX_STARS):
            return False
        
        # Check fork limit
        if forks > Config.MAX_FORKS:
            return False
        
        # Check size limit
        if size > Config.MAX_REPO_SIZE_KB:
            return False
        
        # Must have a name
        if not repo.get('name'):
            return False
        
        return True
    
    def get_repository_details(self, full_name: str) -> Optional[Dict]:
        """Get detailed information about a specific repository."""
        self._rate_limit_check()
        
        url = f"{self.base_url}/repos/{full_name}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            repo_data = response.json()
            return self._process_repository(repo_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting repository details for {full_name}: {e}")
            return None
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status from GitHub API."""
        url = f"{self.base_url}/rate_limit"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"resources": {"search": {"remaining": "unknown"}}} 