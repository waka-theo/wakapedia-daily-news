"""
Custom tools for Wakapedia Daily News newsletter.
Memory tools to prevent duplicate content across newsletter editions.
"""

from wakapedia_daily_news_generator.tools.facts_memory_tool import (
    CheckFactTool,
    ListUsedFactsTool,
    SaveFactTool,
)
from wakapedia_daily_news_generator.tools.news_memory_tool import (
    CheckNewsUrlTool,
    ListUsedNewsUrlsTool,
    SaveNewsUrlTool,
)
from wakapedia_daily_news_generator.tools.tool_memory import (
    CheckToolNameTool,
    CheckToolTool,  # Alias for CheckToolNameTool
    CheckToolUrlTool,
    ListUsedToolsTool,
    SaveToolTool,
)

__all__ = [
    # News memory tools
    "CheckNewsUrlTool",
    "SaveNewsUrlTool",
    "ListUsedNewsUrlsTool",
    # Tool memory tools
    "CheckToolUrlTool",
    "CheckToolNameTool",
    "CheckToolTool",
    "SaveToolTool",
    "ListUsedToolsTool",
    # Facts memory tools
    "CheckFactTool",
    "SaveFactTool",
    "ListUsedFactsTool",
]
