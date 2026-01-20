"""
Wakapedia Daily News Generator Crew.
Multi-agent system for generating daily tech newsletters.
"""

import logging
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from wakapedia_daily_news_generator.tools.news_memory_tool import (
    CheckNewsUrlTool,
    SaveNewsUrlTool,
    ListUsedNewsUrlsTool,
)
from wakapedia_daily_news_generator.tools.tool_memory import (
    CheckToolUrlTool,
    SaveToolTool,
    ListUsedToolsTool,
)
from wakapedia_daily_news_generator.tools.facts_memory_tool import (
    CheckFactTool,
    SaveFactTool,
    ListUsedFactsTool,
)

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_MODEL = "openai/gpt-4o-mini"
CHAT_MODEL = "openai/gpt-4o-mini"

# Agent configurations
AGENT_CONFIG = {
    "tech_news_researcher": {
        "temperature": 0.2,
        "max_iter": 8,
        "max_execution_time": 300,  # 5 minutes
    },
    "tech_tool_scout": {
        "temperature": 0.3,
        "max_iter": 8,
        "max_execution_time": 300,
    },
    "tech_fact_finder": {
        "temperature": 0.3,
        "max_iter": 8,
        "max_execution_time": 300,
    },
    "newsletter_editor": {
        "temperature": 0.2,
        "max_iter": 5,
        "max_execution_time": 180,  # 3 minutes
    },
}


@CrewBase
class WakapediaDailyNewsGeneratorCrew:
    """Wakapedia Daily News Generator crew."""

    @agent
    def tech_news_researcher(self) -> Agent:
        """Agent that researches today's tech news."""
        config = AGENT_CONFIG["tech_news_researcher"]
        return Agent(
            config=self.agents_config["tech_news_researcher"],
            tools=[
                SerperDevTool(),
                CheckNewsUrlTool(),
                SaveNewsUrlTool(),
                ListUsedNewsUrlsTool(),
            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=config["max_iter"],
            max_rpm=None,
            max_execution_time=config["max_execution_time"],
            llm=LLM(
                model=DEFAULT_MODEL,
                temperature=config["temperature"],
            ),
        )

    @agent
    def tech_tool_scout(self) -> Agent:
        """Agent that discovers new tech tools."""
        config = AGENT_CONFIG["tech_tool_scout"]
        return Agent(
            config=self.agents_config["tech_tool_scout"],
            tools=[
                SerperDevTool(),
                CheckToolUrlTool(),
                SaveToolTool(),
                ListUsedToolsTool(),
            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=config["max_iter"],
            max_rpm=None,
            max_execution_time=config["max_execution_time"],
            llm=LLM(
                model=DEFAULT_MODEL,
                temperature=config["temperature"],
            ),
        )

    @agent
    def tech_fact_finder(self) -> Agent:
        """Agent that finds interesting tech facts."""
        config = AGENT_CONFIG["tech_fact_finder"]
        return Agent(
            config=self.agents_config["tech_fact_finder"],
            tools=[
                SerperDevTool(),
                CheckFactTool(),
                SaveFactTool(),
                ListUsedFactsTool(),
            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=config["max_iter"],
            max_rpm=None,
            max_execution_time=config["max_execution_time"],
            llm=LLM(
                model=DEFAULT_MODEL,
                temperature=config["temperature"],
            ),
        )

    @agent
    def newsletter_editor(self) -> Agent:
        """Agent that compiles the final newsletter."""
        config = AGENT_CONFIG["newsletter_editor"]
        return Agent(
            config=self.agents_config["newsletter_editor"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=config["max_iter"],
            max_rpm=None,
            max_execution_time=config["max_execution_time"],
            llm=LLM(
                model=DEFAULT_MODEL,
                temperature=config["temperature"],
            ),
        )

    @task
    def recherche_actualite_tech_du_jour(self) -> Task:
        """Task to research today's tech news."""
        return Task(
            config=self.tasks_config["recherche_actualite_tech_du_jour"],
            markdown=False,
        )

    @task
    def decouverte_outil_du_jour(self) -> Task:
        """Task to discover today's tech tool."""
        return Task(
            config=self.tasks_config["decouverte_outil_du_jour"],
            markdown=False,
        )

    @task
    def recherche_fait_insolite_du_jour(self) -> Task:
        """Task to find an interesting tech fact."""
        return Task(
            config=self.tasks_config["recherche_fait_insolite_du_jour"],
            markdown=False,
        )

    @task
    def compilation_newsletter_wakapedia_daily_news(self) -> Task:
        """Task to compile the final newsletter."""
        return Task(
            config=self.tasks_config["compilation_newsletter_wakapedia_daily_news"],
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Wakapedia Daily News Generator crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model=CHAT_MODEL),
        )
