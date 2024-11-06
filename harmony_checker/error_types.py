from dataclasses import dataclass
from typing import Optional

@dataclass
class HarmonyError:
    """Data class for storing harmony analysis errors"""
    type: str
    measure: int
    description: str
    severity: str  # 'low', 'medium', 'high'
    voice1: Optional[int] = None
    voice2: Optional[int] = None