import unittest
import sys
import os
import json
import tempfile
import shutil

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the registry
from symphony.agent_registry import AgentRegistry


class TestAgentRegistry(unittest.TestCase):
    """Test suite for the AgentRegistry class."""

    def setUp(self):
        """Set up a temporary directory with fake agent configurations."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid agent
        self.agent1_name = "agent_alpha"
        self.agent1_dir = os.path.join(self.temp_dir, self.agent1_name)
        os.makedirs(self.agent1_dir)
        self.agent1_config = {
            "name": self.agent1_name,
            "description": "The first test agent, focused on alpha tasks."
        }
        with open(os.path.join(self.agent1_dir, "config.json"), 'w') as f:
            json.dump(self.agent1_config, f)

        # Create a second valid agent
        self.agent2_name = "agent_beta"
        self.agent2_dir = os.path.join(self.temp_dir, self.agent2_name)
        os.makedirs(self.agent2_dir)
        self.agent2_config = {
            "name": self.agent2_name,
            "description": "A second agent for beta testing and logging."
        }
        with open(os.path.join(self.agent2_dir, "config.json"), 'w') as f:
            json.dump(self.agent2_config, f)

        # Create a directory that is NOT an agent (no config.json)
        os.makedirs(os.path.join(self.temp_dir, "not_an_agent"))

        self.registry = AgentRegistry()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_discovers_agents(self):
        """Verifies the registry successfully discovers agents in a given path."""
        self.registry.register_agents_from_path(self.temp_dir)
        
        self.assertEqual(len(self.registry.agents), 2)
        self.assertIn(self.agent1_name, self.registry.agents)
        self.assertIn(self.agent2_name, self.registry.agents)
        
        # Check that the non-agent directory was ignored
        self.assertNotIn("not_an_agent", self.registry.agents)

    def test_find_agent_by_keyword(self):
        """Tests the find_agent() method with relevant keywords."""
        self.registry.register_agents_from_path(self.temp_dir)

        # Test keyword matching for agent_alpha
        found_agent = self.registry.find_agent("I need help with alpha")
        self.assertEqual(found_agent, self.agent1_name)

        # FIX: Use a query with keywords that won't be filtered out
        found_agent = self.registry.find_agent("beta testing")
        self.assertEqual(found_agent, self.agent2_name)

        # Test with a keyword that appears in both (should find the first/best match)
        found_agent = self.registry.find_agent("agent")
        self.assertIn(found_agent, [self.agent1_name, self.agent2_name])

    def test_find_agent_returns_none_on_fail(self):
        """Verifies the method returns None when no agent matches a query."""
        self.registry.register_agents_from_path(self.temp_dir)
        
        # FIX: Use a more specific query that is unlikely to match common words.
        found_agent = self.registry.find_agent("I need a specialized gamma quantum function")
        self.assertIsNone(found_agent)
        
        # Test with an empty registry
        empty_registry = AgentRegistry()
        found_agent = empty_registry.find_agent("any query")
        self.assertIsNone(found_agent)