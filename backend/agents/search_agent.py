"""
Search agent for finding hackathon projects based on technologies.
Handles GitHub API interactions and project filtering.
"""

from typing import List, Dict, Optional
import time
import json
from core.base_agent import BaseAgent
from core.config import Config
from utils.github_client import GitHubClient
from prompts.search_prompts import SearchPrompts


class TechnologyProjectSearchAgent(BaseAgent):
    """Agent that searches for hackathon winner projects using specific technologies."""
    
    def __init__(self):
        super().__init__("TechnologyProjectSearchAgent", temperature=0.3)
        self.github_client = GitHubClient()
    
    def execute(self, technologies: List[str] = None) -> List[Dict]:
        """
        Main execution method for searching projects.
        
        Args:
            technologies: List of technologies to search for
            
        Returns:
            List of found hackathon projects
        """
        return self.search_projects_by_technologies(technologies)
    
    def search_projects_by_technologies(self, technologies: List[str] = None) -> List[Dict]:
        """Search for HACKATHON WINNER projects using specific technologies."""
        
        if not technologies:
            self.log("No technologies specified, searching for general hackathon winners...")
            return self._search_general_hackathon_winners()
        
        self.log(f"Searching for HACKATHON WINNERS using technologies: {', '.join(technologies)}")
        
        all_projects = []
        seen_projects = set()
        
        # Strategy 1: Direct hackathon winner searches with technologies
        for tech in technologies:
            if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                break
            
            self.log_step(f"Searching for hackathon winners using {tech}...")
            
            # Hackathon-specific search patterns for each technology
            search_queries = [
                f"hackathon winner {tech}",
                f"hackathon {tech} project",
                f"{tech} hackathon winning",
                f"hackathon award {tech}",
                f"student hackathon {tech}",
                f"university hackathon {tech}",
                f"hackathon competition {tech}",
                f"winning hackathon {tech}"
            ]
            
            for query in search_queries:
                if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                    break
                
                try:
                    self.log_step(f"Searching: {query}")
                    repos = self.github_client.search_repositories(query, per_page=5, max_pages=1, add_filters=True)
                    
                    for repo in repos:
                        if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                            break
                        
                        if repo['full_name'] not in seen_projects:
                            if self._is_hackathon_project_with_tech(repo, technologies):
                                seen_projects.add(repo['full_name'])
                                all_projects.append(repo)
                                self.log_step(f"Found: {repo['name']} ({repo.get('stars', 0)} stars)")
                    
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        self.log("Rate limited, waiting...", "WARN")
                        time.sleep(60)
                    continue
        
        # Strategy 2: General hackathon searches with technology filters
        if len(all_projects) < self.config.MAX_PROJECTS_TO_FIND:
            self.log_step("Searching general hackathon winners and filtering by technology...")
            
            hackathon_queries = [
                "hackathon winner",
                "hackathon winning project", 
                "student hackathon winner",
                "university hackathon project",
                "hackathon competition winner",
                "coding competition winner",
                "hackathon award",
                "winning hackathon project"
            ]
            
            for query in hackathon_queries:
                if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                    break
                
                try:
                    self.log_step(f"Searching: {query}")
                    repos = self.github_client.search_repositories(query, per_page=6, max_pages=1, add_filters=True)
                    
                    for repo in repos:
                        if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                            break
                        
                        if repo['full_name'] not in seen_projects:
                            if self._is_hackathon_project_with_tech(repo, technologies):
                                seen_projects.add(repo['full_name'])
                                all_projects.append(repo)
                                self.log_step(f"Found hackathon project: {repo['name']} ({repo.get('stars', 0)} stars)")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        self.log("Rate limited, waiting...", "WARN")
                        time.sleep(60)
                    continue
        
        # Strategy 3: Multi-technology combinations in hackathons
        if len(all_projects) < self.config.MAX_PROJECTS_TO_FIND and len(technologies) > 1:
            self.log_step("Searching for hackathon projects using technology combinations...")
            
            # Try pairs of technologies in hackathon context
            for i in range(len(technologies)):
                for j in range(i + 1, len(technologies)):
                    if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                        break
                    
                    tech1, tech2 = technologies[i], technologies[j]
                    combo_queries = [
                        f"hackathon {tech1} {tech2}",
                        f"hackathon winner {tech1} {tech2}",
                        f"student hackathon {tech1} {tech2}"
                    ]
                    
                    for query in combo_queries:
                        if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                            break
                        
                        try:
                            self.log_step(f"Searching: {query}")
                            repos = self.github_client.search_repositories(query, per_page=3, max_pages=1, add_filters=True)
                            
                            for repo in repos:
                                if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                                    break
                                
                                if repo['full_name'] not in seen_projects:
                                    if self._is_hackathon_project_with_tech(repo, technologies):
                                        seen_projects.add(repo['full_name'])
                                        all_projects.append(repo)
                                        self.log_step(f"Found combo hackathon project: {repo['name']} ({repo.get('stars', 0)} stars)")
                            
                            time.sleep(2)
                            
                        except Exception as e:
                            continue
        
        # Strategy 4: If still not enough, search general hackathon winners
        if len(all_projects) < self.config.MAX_PROJECTS_TO_FIND:
            self.log_step("Adding general hackathon winners to reach target count...")
            general_hackathon = self._search_general_hackathon_winners()
            
            for project in general_hackathon:
                if len(all_projects) >= self.config.MAX_PROJECTS_TO_FIND:
                    break
                
                if project['full_name'] not in seen_projects:
                    seen_projects.add(project['full_name'])
                    all_projects.append(project)
                    self.log_step(f"Added general hackathon project: {project['name']} ({project.get('stars', 0)} stars)")
        
        # Sort by hackathon relevance and technology match
        all_projects.sort(key=lambda p: self._calculate_hackathon_tech_score(p, technologies), reverse=True)
        
        final_projects = all_projects[:self.config.MAX_PROJECTS_TO_FIND]
        self.log(f"Found {len(final_projects)} hackathon projects for evaluation")
        
        return final_projects
    
    def _is_hackathon_project_with_tech(self, repo: Dict, technologies: List[str]) -> bool:
        """Check if a project is a hackathon project with the specified technologies."""
        stars = repo.get('stars', 0)
        forks = repo.get('forks', 0)
        size = repo.get('size', 0)
        
        # Basic filtering
        if not (self.config.MIN_STARS <= stars <= self.config.MAX_STARS):
            return False
        if forks > self.config.MAX_FORKS:
            return False
        if size > self.config.MAX_REPO_SIZE_KB:
            return False
        
        # Check for hackathon context AND technology relevance
        description = repo.get('description', '').lower()
        topics = [topic.lower() for topic in repo.get('topics', [])]
        name = repo.get('name', '').lower()
        language = repo.get('language', '').lower()
        
        all_text = f"{description} {' '.join(topics)} {name} {language}"
        
        # Must have hackathon context
        hackathon_keywords = ['hackathon', 'hack', 'competition', 'contest', 'winner', 'winning', 'award', 'student', 'university']
        has_hackathon_context = any(keyword in all_text for keyword in hackathon_keywords)
        
        # Must contain at least one of the specified technologies (if any)
        tech_match = True
        if technologies:
            tech_match = any(tech.lower() in all_text for tech in technologies)
        
        return has_hackathon_context and tech_match
    
    def _calculate_hackathon_tech_score(self, project: Dict, technologies: List[str]) -> float:
        """Calculate relevance score prioritizing hackathon context and technology match."""
        description = project.get('description', '').lower()
        topics = [topic.lower() for topic in project.get('topics', [])]
        name = project.get('name', '').lower()
        language = project.get('language', '').lower()
        
        all_text = f"{description} {' '.join(topics)} {name} {language}"
        
        score = 0
        
        # Hackathon relevance score (highest priority)
        hackathon_keywords = {
            'hackathon': 20,
            'winner': 15,
            'winning': 15,
            'award': 12,
            'competition': 10,
            'contest': 10,
            'hack': 8,
            'student': 5,
            'university': 5
        }
        
        for keyword, points in hackathon_keywords.items():
            if keyword in all_text:
                score += points
        
        # Technology match score
        if technologies:
            for tech in technologies:
                if tech.lower() in all_text:
                    score += 15
                if tech.lower() in language:
                    score += 10  # Language match is very valuable
                if tech.lower() in topics:
                    score += 8   # Topic match is good
                if tech.lower() in name:
                    score += 5   # Name match is decent
        
        # Project size preference (hackathon-sized projects)
        stars = project.get('stars', 0)
        if 10 <= stars <= 50:
            score += 8
        elif 5 <= stars <= 100:
            score += 5
        elif stars > 0:
            score += 2
        
        # Prefer fewer forks (more unique hackathon projects)
        forks = project.get('forks', 0)
        if forks <= 3:
            score += 5
        elif forks <= 10:
            score += 3
        elif forks <= 20:
            score += 1
        
        # Description quality
        if len(description) > 30:
            score += 3
        
        return score
    
    def _search_general_hackathon_winners(self) -> List[Dict]:
        """Search for general hackathon winner projects."""
        hackathon_queries = [
            "hackathon winner",
            "hackathon winning project",
            "student hackathon winner",
            "university hackathon",
            "hackathon competition",
            "coding competition winner"
        ]
        
        projects = []
        seen = set()
        
        for query in hackathon_queries:
            if len(projects) >= 8:  # Limit general hackathon projects
                break
            
            try:
                repos = self.github_client.search_repositories(query, per_page=4, max_pages=1, add_filters=True)
                
                for repo in repos:
                    if len(projects) >= 8:
                        break
                    
                    if repo['full_name'] not in seen:
                        stars = repo.get('stars', 0)
                        forks = repo.get('forks', 0)
                        
                        if self.config.MIN_STARS <= stars <= self.config.MAX_STARS and forks <= self.config.MAX_FORKS:
                            # Check for hackathon context
                            description = repo.get('description', '').lower()
                            topics = ' '.join(repo.get('topics', [])).lower()
                            name = repo.get('name', '').lower()
                            all_text = f"{description} {topics} {name}"
                            
                            hackathon_keywords = ['hackathon', 'hack', 'competition', 'winner', 'award', 'contest']
                            if any(keyword in all_text for keyword in hackathon_keywords):
                                seen.add(repo['full_name'])
                                projects.append(repo)
                
                time.sleep(2)
                
            except Exception as e:
                continue
        
        return projects 