import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Story:
    project: str
    subject: str
    description: str = ""
    epic: Optional[int] = None
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class Issue:
    project: str
    subject: str
    description: str = ""
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class Task:
    project: str
    subject: str
    description: str = ""
    parent: Optional[int] = None
    epic: Optional[int] = None
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None


@dataclass
class Epic:
    project: str
    subject: str
    description: str = ""
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    color: Optional[str] = None


@dataclass
class Milestone:
    project: str
    subject: str
    estimated_start: datetime.date
    estimated_finish: datetime.date
    closed: bool = False
    assignee: Optional[str] = None
