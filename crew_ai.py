from crewai import Agent, Task, Crew
from crewai_tools import DirectoryReadTool, ScrapeWebsiteTool
from decouple import config
from langchain_groq import ChatGroq
import agentops
import os

agentops.init()

os.environ["AGENT_OPS_KEY"] = config("AGENT_OPS_KEY")
llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    api_key=config("GROQ_API_KEY"),
)

tool12111 = ScrapeWebsiteTool(website_url="https://docs.crewai.com")

gavin = Agent(
    role="document_abstract",
    goal="fetch relivant information from the doc",
    backstory="Your primary task is to get relivant information from the doc",
    llm=llm,
    tools=[tool12111],
)

task1 = Task(
    description="Find content from the documentation of how to use agent monitoring with agentops, if you encounter new/more urls, then browse through them in detail and write the content related to the question to the file ai_code_summary.txt",
    expected_output="Detailed summary in the file",
    agent=gavin,
    output_file="ai_code_summary.txt",
    tool=[tool12111],
)

crew = Crew(agents=[gavin], tasks=[task1])

result = crew.kickoff()