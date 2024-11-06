import logging
import os
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> None:
    """Creates directory if it doesn't exist and sets permissions"""
    os.makedirs(path, exist_ok=True)
    os.chmod(path, 0o755)

def categorize_errors_by_severity(errors: List[Dict]) -> Dict[str, int]:
    """Helper method to categorize errors by severity"""
    categories = {'high': 0, 'medium': 0, 'low': 0}
    for error in errors:
        categories[error['severity']] += 1
    return categories

def identify_common_problems(errors: List[Dict]) -> List[str]:
    """Identifies and ranks the most common issues in the composition"""
    error_types = {}
    for error in errors:
        if error['type'] not in error_types:
            error_types[error['type']] = {
                'count': 0,
                'severity': error['severity']
            }
        error_types[error['type']]['count'] += 1

    # Sort problems by count and severity
    ranked_problems = sorted(
        error_types.items(),
        key=lambda x: (x[1]['count'], {'high': 3, 'medium': 2, 'low': 1}[x[1]['severity']]),
        reverse=True
    )

    return [
        f"{problem[0]}: {problem[1]['count']} occurrences ({problem[1]['severity']} severity)"
        for problem in ranked_problems[:5]  # Show top 5 issues
    ]