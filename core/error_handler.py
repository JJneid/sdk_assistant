# core/error_handler.py
import re
from typing import Dict, List
import traceback

class ErrorHandler:
    def __init__(self):
        self.error_patterns = {
            "import_error": r"ImportError: No module named '(\w+)'",
            "syntax_error": r"SyntaxError: (.*)",
            "permission_error": r"PermissionError: (.*)",
            "value_error": r"ValueError: (.*)",
            "connection_error": r"ConnectionError: (.*)",
        }

    def analyze_error(self, command_data: Dict) -> Dict:
        error_output = command_data.get("error", "")
        exit_code = command_data.get("exit_code", 0)
        
        error_info = {
            "type": self._determine_error_type(error_output),
            "summary": self._generate_error_summary(error_output),
            "description": self._generate_error_description(command_data),
            "labels": self._generate_error_labels(error_output, exit_code),
            "severity": self._determine_severity(error_output, exit_code),
            "command_context": command_data
        }
        
        return error_info

    def _determine_error_type(self, error_output: str) -> str:
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, error_output):
                return error_type
        return "unknown_error"

    def _generate_error_summary(self, error_output: str) -> str:
        # Extract the first line of the error message
        first_line = error_output.split('\n')[0].strip()
        return first_line[:100]  # Limit length for GitHub issue title

    def _generate_error_description(self, command_data: Dict) -> str:
        description = [
            "## Error Details",
            "```",
            command_data.get("error", "No error message available"),
            "```",
            "",
            "## Command Information",
            f"- Command: `{command_data['command']}`",
            f"- Exit Code: {command_data['exit_code']}",
            f"- Execution Time: {command_data['execution_time']:.2f} seconds",
            "",
            "## System Information",
            "```python",
            f"Python Version: {sys.version}",
            f"Platform: {sys.platform}",
            "```",
            "",
            "## Output",
            "```",
            command_data.get("output", "No output available"),
            "```"
        ]
        
        return "\n".join(description)

    def _generate_error_labels(self, error_output: str, exit_code: int) -> List[str]:
        labels = ["bug"]
        
        # Add specific labels based on error type
        error_type = self._determine_error_type(error_output)
        labels.append(error_type)
        
        # Add severity label
        severity = self._determine_severity(error_output, exit_code)
        labels.append(f"severity:{severity}")
        
        return labels

    def _determine_severity(self, error_output: str, exit_code: int) -> str:
        if "critical" in error_output.lower() or exit_code > 2:
            return "critical"
        elif "warning" in error_output.lower() or exit_code == 2:
            return "warning"
        elif exit_code == 1:
            return "minor"
        return "low"
