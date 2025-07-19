"""
Generic commit message bank for creating realistic but non-descriptive commit history
"""

import random
from typing import List

class CommitMessageBank:
    """Bank of generic commit messages that don't indicate specific features"""
    
    def __init__(self):
        self.messages = [
            # Simple generic messages
            "work",
            "...",
            "test",
            "pls",
            "WHY",
            "doesn't work"
            "oops"
        ]
        
        # More descriptive but still vague messages
        self.descriptive_messages = [
            "made it work",
            "broke something",
            "oops",
            "this should work",
            "trying again",
            "one more time",
            "final attempt",
            "last try",
            "hopefully this works",
            "please work",
            "come on",
            "why not working",
            "working now",
            "finally",
            "at last",
            "success",
            "victory",
            "nailed it",
            "got it",
            "done deal",
            "adding feat"
        ]
    
    def get_random_message(self) -> str:
        """Get a random commit message from the bank"""
        # 70% chance for simple messages, 30% for descriptive
        if random.random() < 0.7:
            return random.choice(self.messages)
        else:
            return random.choice(self.descriptive_messages)
    
    def get_message_sequence(self, count: int) -> List[str]:
        """Get a sequence of commit messages for a project"""
        messages = []
        used_messages = set()
        
        for i in range(count):
            # Try to avoid duplicates in small sequences
            attempts = 0
            while attempts < 10:  # Avoid infinite loop
                message = self.get_random_message()
                if message not in used_messages or len(used_messages) > len(self.messages) * 0.8:
                    messages.append(message)
                    used_messages.add(message)
                    break
                attempts += 1
            else:
                # If we can't find a unique message, just use a random one
                messages.append(self.get_random_message())
        
        return messages
    
    def get_hackathon_sequence(self, count: int, hackathon_duration: int) -> List[str]:
        """Get commit messages appropriate for a hackathon timeline"""
        messages = []
        
        # Early hackathon messages (setup, initial work)
        early_phase = max(1, count // 4)
        early_messages = [
            "setup", "init", "start", "begin", "basic", "foundation", 
            "initial"
        ]
        
        # Mid hackathon messages (development, iteration)
        mid_phase = max(1, count // 2)
        mid_messages = [
            "work", "progress", "development", "iteration", "changes",
            "updates", "improvements", "fixes", "tweaks", "adjustments"
        ]
        
        # Late hackathon messages (final push, cleanup)
        late_phase = count - early_phase - mid_phase
        late_messages = [
            "final", "polish", "cleanup", "ready", "done", "complete",
            "finish", "last"
        ]
        
        # Distribute messages across phases
        for i in range(count):
            if i < early_phase:
                phase_messages = early_messages
            elif i < early_phase + mid_phase:
                phase_messages = mid_messages
            else:
                phase_messages = late_messages
            
            # Mix with random messages for variety
            if random.random() < 0.6:
                message = random.choice(phase_messages)
            else:
                message = self.get_random_message()
            
            messages.append(message)
        
        return messages

# Global instance
commit_bank = CommitMessageBank() 