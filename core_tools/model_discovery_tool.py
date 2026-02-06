import json
from typing import List, Dict, Any
from .exceptions import ModelDiscoveryError

class ModelDiscoveryTool:
    """
    A tool to query the Venice.ai API to discover available models and their metadata.
    """
    def __init__(self, api_client):
        """
        Initializes the tool with a Venice API client.

        Args:
            api_client: An initialized Venice API client instance.
        """
        if not api_client:
            raise ValueError("A valid API client instance is required.")
        self.client = api_client

    def list_models_with_metadata(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of available models and their full metadata from the Venice.ai API.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary contains
                                  the metadata for a single model.
            
        Raises:
            ModelDiscoveryError: If the API call fails or the response is invalid.
        """
        try:
            response = self.client.models.list()
            
            if not hasattr(response, 'data') or not isinstance(response.data, list):
                raise ModelDiscoveryError("Invalid response structure from API: 'data' list not found.")
                
            models_metadata = []
            for model_data in response.data:
                if hasattr(model_data, 'id') and hasattr(model_data, 'model_spec'):
                    metadata = {
                        "id": model_data.id,
                        "pricing": model_data.model_spec.get("pricing", {}),
                        "capabilities": model_data.model_spec.get("capabilities", {}),
                        "traits": model_data.model_spec.get("traits", []),
                        # FIX: Explicitly convert betaModel to a boolean to ensure correct type
                        "is_beta": bool(model_data.model_spec.get("betaModel", False)),
                    }
                    models_metadata.append(metadata)
            
            return models_metadata

        except Exception as e:
            raise ModelDiscoveryError(f"Failed to discover models from API: {e}")

    # Legacy method for backward compatibility, though it's now less useful.
    def list_models(self) -> List[str]:
        """Legacy method to return just model IDs."""
        metadata = self.list_models_with_metadata()
        return [model["id"] for model in metadata]