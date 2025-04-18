import os
import uuid

import chromadb
from dotenv import load_dotenv

# Import the OpenAIChat model and the Agent struct
from swarms import Agent, data_to_text

from fot.agent_name_creator import create_agent_name

# Load the environment variables
load_dotenv()


def agent_metadata(agent: Agent, task: str, output: str):
    """
    Returns the metadata for the agent.

    Returns:
        dict: The metadata for the agent.
    """
    out = {
        "Agent Name": f"{agent.agent_name}",
        "Agent ID": agent.id,
        "Agent History": agent.short_memory,
        "Agent System Prompt": agent.system_prompt,
        "task": task,
        "output": output,
    }
    return str(out)


class ForestOfAgents:
    """
    Represents a forest of agents that can perform tasks.

    Args:
        num_agents (int): The number of agents in the forest.
        max_loops (int): The maximum number of loops each agent can run.
        max_new_tokens (int): The maximum number of new tokens each agent can generate.
    """

    def __init__(
        self,
        llm,
        num_agents: int,
        max_loops: int,
        max_new_tokens: int,
        docs: str = None,
    ):
        super().__init__()
        self.llm = llm
        self.num_agents = num_agents
        self.max_loops = max_loops
        self.max_new_tokens = max_new_tokens
        self.docs = docs

        # A list of agents in the forest
        self.forest = []

        # Connect
        self.db = chromadb.Client()

        # Create a collection
        self.collection = self.db.create_collection(name="forest-of-thoughts")

        # Convert all files in folders to text
        for i in range(num_agents):
            self.forest.append(self.create_agent())

        # Docs
        if docs:
            self.traverse_directory()
            
    def create_agent(self):
        """
        Creates a new agent with the specified parameters.

        Returns:
            Agent: The created agent.
        """
        return Agent(
            llm=self.llm,
            max_loops=self.max_loops,
            name=create_agent_name(),
            system_prompt=None,
            autosave=True,
        )

    def create_agents(self):
        """
        Creates a list of agents based on the specified number of agents.

        Returns:
            list[Agent]: The list of created agents.
        """
        agents = [self.create_agent() for _ in range(self.num_agents)]

        # Add the agents to the forest
        self.forest.extend(agents)

    def run(self, task: str, *args, **kwargs):
        """
        Runs the specified task on all agents in the forest.

        Args:
            task (str): The task to be performed.
            *args: Additional positional arguments for the task.
            **kwargs: Additional keyword arguments for the task.
        """
        pass

    def distribute_task_to_agents(self, task: str, *args, **kwargs):
        """
        Distributes the specified task to all agents in the forest.

        Args:
            task (str): The task to be performed.
            *args: Additional positional arguments for the task.
            **kwargs: Additional keyword arguments for the task.
        """
        
        outputs = []
        for agent in self.forest:
            out = agent.run(task, *args, **kwargs)
            save_metadata = self.get_agent_metadata(agent, task, out)
            self.add_document(save_metadata)
            
            outputs.append(out)
        return outputs

    def convert_doc_files_to_text(self):
        # Get all files in the folder using os
        # Convert all files to text
        pass

    def add_document(self, document: str):
        doc_id = str(uuid.uuid4())
        self.collection.add(ids=[doc_id], documents=[document])

        return doc_id

    def query_documents(self, query: str, n_docs: int = 1):
        docs = self.collection.query(query_texts=[query], n_results=n_docs)["documents"]

        return docs[0]

    def get_agent_metadata(self, agent: Agent, task: str, output: str):
        """
        Returns the metadata for the specified agent.

        Args:
            agent (Agent): The agent to get metadata for.
            task (str): The task the agent is performing.

        Returns:
            dict: The metadata for the agent.
        """
        return agent_metadata(agent, task, output)
    
    def traverse_directory(self):
        """
        Traverse through every file in the given directory and its subdirectories,
        and return the paths of all files.
        Parameters:
        - directory_name (str): The name of the directory to traverse.
        Returns:
        - list: A list of paths to each file in the directory and its subdirectories.
        """
        for root, dirs, files in os.walk(self.docs):
            for file in files:
                data = data_to_text(file)
                added_to_db = self.add_document(data)
        return added_to_db
            