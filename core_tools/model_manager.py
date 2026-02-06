import json
from pathlib import Path
from .exceptions import ModelRoleNotFoundError, ModelIsBetaError, ModelDiscoveryError

class ModelManager:
    """
    Manages model-to-role mapping based on a centralized configuration file.
    This class serves as the single interface for agents to request a model for a specific role.
    """
    def __init__(self, config_path: str = "config/models.json", enforce_safety: bool = True, api_client=None):
        """
        Initializes the ModelManager by loading the model configuration.

        Args:
            config_path (str): The path to the JSON configuration file.
            enforce_safety (bool): If True, raises an error if a role maps to a beta model.
            api_client: An API client instance, required for safety checks and metadata lookups.
        
        Raises:
            FileNotFoundError: If the configuration file cannot be found.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        config_file = Path(config_path)
        if not config_file.is_file():
            raise FileNotFoundError(f"Model configuration file not found at: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error decoding JSON from {config_path}: {e.msg}", e.doc, e.pos)

        if "model_roles" not in self._config or not isinstance(self._config["model_roles"], dict):
            raise ValueError("Configuration file must contain a 'model_roles' dictionary.")

        self.enforce_safety = enforce_safety
        self.api_client = api_client

    def get_model(self, role: str) -> str:
        """
        Retrieves the model name for a given role, with optional safety checks.

        Args:
            role (str): The logical role of the model (e.g., "reasoning", "synthesis").

        Returns:
            str: The name of the model configured for that role.

        Raises:
            ModelRoleNotFoundError: If the specified role is not found in the configuration.
            ModelIsBetaError: If safety is enforced and the model is a beta model.
        """
        role_config = self._config.get("model_roles", {}).get(role)
        
        if not role_config:
            raise ModelRoleNotFoundError(f"Model role '{role}' not found in configuration.")
        
        # FIX: Handle new dictionary structure and old string structure
        if isinstance(role_config, dict):
            model_name = role_config.get("model")
        else:
            model_name = role_config

        if not model_name:
            raise ModelRoleNotFoundError(f"Model for role '{role}' not found in configuration.")
        
        if self.enforce_safety:
            if not self.api_client:
                raise ValueError("API client is required for safety enforcement.")
            from .model_discovery_tool import ModelDiscoveryTool
            try:
                discovery_tool = ModelDiscoveryTool(api_client=self.api_client)
                all_models = discovery_tool.list_models_with_metadata()
                model_metadata = next((m for m in all_models if m["id"] == model_name), None)
                if model_metadata and model_metadata.get("is_beta", False):
                    raise ModelIsBetaError(f"Model '{model_name}' for role '{role}' is a beta model and safety is enforced.")
            except ModelDiscoveryError:
                print(f"Warning: Could not verify model status for safety check. Proceeding with model '{model_name}'.")
        
        return model_name

    def get_model_metadata(self, role: str) -> dict:
        """
        Retrieves the live metadata for the model assigned to a given role.

        Args:
            role (str): The logical role of the model.

        Returns:
            dict: A dictionary containing the metadata for the assigned model.
        
        Raises:
            ModelRoleNotFoundError: If the specified role is not found in the configuration.
            ModelDiscoveryError: If the metadata cannot be fetched from the API.
        """
        if not self.api_client:
            raise ValueError("API client is required to fetch model metadata.")
        
        model_name = self.get_model(role) # Re-use get_model to handle role lookup and safety
        
        from .model_discovery_tool import ModelDiscoveryTool
        discovery_tool = ModelDiscoveryTool(api_client=self.api_client)
        all_models = discovery_tool.list_models_with_metadata()
        
        model_metadata = next((m for m in all_models if m["id"] == model_name), None)
        
        if not model_metadata:
            raise ModelDiscoveryError(f"Metadata for model '{model_name}' not found in live API response.")
            
        return model_metadata