# core/command_tracker.py
from datetime import datetime
import json
from pathlib import Path

class CommandTracker:
    def __init__(self):
        self.command_history = []
        self.command_frequencies = {}

    def track_command(self, command_data: dict):
        self.command_history.append(command_data)
        
        # Track command frequency
        cmd = command_data["command"]
        self.command_frequencies[cmd] = self.command_frequencies.get(cmd, 0) + 1
        
        if self.command_frequencies[cmd] > 1:
            return {
                "repeated": True,
                "frequency": self.command_frequencies[cmd],
                "previous_executions": [
                    c for c in self.command_history 
                    if c["command"] == cmd
                ]
            }
        return {"repeated": False}

    def save_history(self, filepath: str = "command_history.json"):
        with open(filepath, 'w') as f:
            json.dump(self.command_history, f, indent=2)