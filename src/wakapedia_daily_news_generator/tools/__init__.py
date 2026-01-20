"""
Custom tools for Wakapedia Daily News newsletter.
Memory tools to prevent duplicate content across newsletter editions.
"""

from wakapedia_daily_news_generator.tools.news_memory_tool import (
    CheckNewsUrlTool,
    SaveNewsUrlTool,
    ListUsedNewsUrlsTool,
)
from wakapedia_daily_news_generator.tools.tool_memory import (
    CheckToolUrlTool,
    CheckToolNameTool,
    CheckToolTool,  # Alias for CheckToolNameTool
    SaveToolTool,
    ListUsedToolsTool,
)
from wakapedia_daily_news_generator.tools.facts_memory_tool import (
    CheckFactTool,
    SaveFactTool,
    ListUsedFactsTool,
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
