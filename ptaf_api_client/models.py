from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Tenant:
    id: str
    name: str
    description: str
    is_default: bool

@dataclass
class PolicyTemplate:
    id: str
    name: str
    type: str
    has_user_rules: bool
    templates: List[str]

@dataclass
class Rule:
    id: str
    name: str
    enabled: bool
    is_system: bool
    configuration: Dict[str, Any]

@dataclass
class Action:
    id: str
    name: str
    description: str