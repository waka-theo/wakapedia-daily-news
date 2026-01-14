import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	SerperDevTool
)

from wakapedia_daily_news_generator.tools.news_memory_tool import (
    CheckNewsUrlTool,
    SaveNewsUrlTool,
    ListUsedNewsUrlsTool,
)





@CrewBase
class WakapediaDailyNewsGeneratorCrew:
    """WakapediaDailyNewsGenerator crew"""

    
    @agent
    def tech_news_researcher(self) -> Agent:
        
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
            max_iter=10,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.5,
            ),
        )

    @agent
    def tech_tool_scout(self) -> Agent:
        
        return Agent(
            config=self.agents_config["tech_tool_scout"],
            
            
            tools=[				SerperDevTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            max_rpm=None,
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.5,
            ),

        )

    @agent
    def tech_fact_finder(self) -> Agent:
        
        return Agent(
            config=self.agents_config["tech_fact_finder"],
            tools=[SerperDevTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o",
                temperature=0.3,
            ),
        )

    @agent
    def newsletter_editor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["newsletter_editor"],
            
            
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            max_rpm=None,
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o",
                temperature=0.3,
            ),

        )



    @task
    def recherche_actualite_tech_du_jour(self) -> Task:
        return Task(
            config=self.tasks_config["recherche_actualite_tech_du_jour"],
            markdown=False,
            
            
        )
    
    @task
    def decouverte_outil_du_jour(self) -> Task:
        return Task(
            config=self.tasks_config["decouverte_outil_du_jour"],
            markdown=False,
            
            
        )
    
    @task
    def recherche_fait_insolite_du_jour(self) -> Task:
        return Task(
            config=self.tasks_config["recherche_fait_insolite_du_jour"],
            markdown=False,
        )
    
    @task
    def compilation_newsletter_wakapedia_daily_news(self) -> Task:
        return Task(
            config=self.tasks_config["compilation_newsletter_wakapedia_daily_news"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the WakapediaDailyNewsGenerator crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )