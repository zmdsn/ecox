"""上下文和实体模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from .message import Message


@dataclass
class Entities:
    """提取的实体"""
    stock_codes: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    company_names: List[str] = field(default_factory=list)


@dataclass
class Context:
    """对话上下文"""
    session_id: str
    history: List[Message] = field(default_factory=list)
    entities: Entities = field(default_factory=Entities)
    current_messages: List[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
