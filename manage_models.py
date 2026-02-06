#!/usr/bin/env python3
"""
Project Chimera - Admin Interface (Final Version)
A command-line script to manage the model registry with comprehensive safety features:
- Live metadata display with clear units.
- Warnings for beta models.
- Warnings for models exceeding cost thresholds.
- Warnings for models lacking required capabilities.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to Python path to import core_tools
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Step 1: Define Model Capabilities ---
# This mapping is used for the capability safety check.
# The API provides capabilities, but this static map serves as a definitive
# source for roles that have strict requirements.
MODEL_CAPABILITIES = {
    "qwen3-vl-235b-a22b": ["text", "vision"],
    "llama-3.3-70b": ["text"],
    "llama-3.2-3b": ["text"],
    "claude-opus-4-6": ["text"],
    "claude-sonnet-45": ["text"],
    "deepseek-v3.2": ["text", "code"],
    "grok-code-fast-1": ["text", "code"],
    # Add other models as needed, defaulting to ["text"] if unsure.
    # The script will fall back to API capabilities if a model is not listed here.
}

try:
    from core_tools.config import get_venice_client
    from core_tools.model_manager import ModelManager, ModelRoleNotFoundError, ModelIsBetaError
    from core_tools.model_discovery_tool import ModelDiscoveryTool, ModelDiscoveryError
except ImportError as e:
    print(f"Error: Could not import necessary modules. Ensure you're running from the project root. Details: {e}")
    sys.exit(1)

def discover_and_print_models(client):
    """Fetches and prints a rich table of available models with metadata."""
    print("--- Discovering Available Models ---")
    try:
        discovery_tool = ModelDiscoveryTool(api_client=client)
        models = discovery_tool.list_models_with_metadata()
        if not models:
            print("No models found or an error occurred.")
            return
        
        # Header with updated units
        print(f"{'Model ID':<35} | {'Input Cost / 1M Tok':<20} | {'Output Cost / 1M Tok':<21} | {'Traits':<25} | {'Beta?'}")
        print("-" * 110)

        for model in sorted(models, key=lambda x: x["id"]):
            model_id = model["id"]
            pricing = model.get("pricing", {})
            input_cost = pricing.get("input", {}).get("usd", 0.0)
            output_cost = pricing.get("output", {}).get("usd", 0.0)
            traits_str = ", ".join(model.get("traits", []))
            is_beta = "Yes" if model.get("is_beta", False) else "No"
            print(f"{model_id:<35} | ${input_cost:<19.2f} | ${output_cost:<20.2f} | {traits_str:<25} | {is_beta}")

    except ModelDiscoveryError as e:
        print(f"Error: Could not discover models. {e}")
    except Exception as e:
        print(f"An unexpected error occurred during discovery: {e}")
    print("-" * 110)

def print_status(manager, available_models=None):
    """Reads and prints the current model role mappings with live metadata."""
    print("--- Current Model Status ---")
    try:
        config = manager._config
        roles = config.get("model_roles", {})
        if not roles:
            print("No model roles are configured.")
            return
        
        model_map = {m["id"]: m for m in available_models} if available_models else None

        # Header with updated units
        print(f"{'Role':<15} | {'Model ID':<35} | {'Input Cost / 1M Tok':<20} | {'Beta?'}")
        print("-" * 80)

        for role, role_config in sorted(roles.items()):
            # Handle new role config structure
            if isinstance(role_config, dict):
                model_id = role_config.get("model")
            else: # Backward compatibility for old string-based config
                model_id = role_config

            try:
                if model_map and model_id in model_map:
                    metadata = model_map[model_id]
                else:
                    metadata = manager.get_model_metadata(role)
                
                pricing = metadata.get("pricing", {})
                input_cost = pricing.get("input", {}).get("usd", 0.0)
                is_beta = "Yes" if metadata.get("is_beta", False) else "No"
                print(f"{role:<15} | {model_id:<35} | ${input_cost:<19.2f} | {is_beta}")
            except (ModelIsBetaError, ModelDiscoveryError, ValueError, KeyError) as e:
                print(f"{role:<15} | {model_id:<35} | {'Error: ' + str(e):<30}")
            
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"Error: Could not read model configuration. {e}")
    except Exception as e:
        print(f"An unexpected error occurred while reading status: {e}")
    print("-" * 80)

def interactive_update(client, config_path):
    """Guides the user through an interactive session to update model roles with safety warnings."""
    print("--- Interactive Model Update ---")
    
    try:
        manager = ModelManager(config_path, enforce_safety=False, api_client=client)
        config = manager._config
        admin_policy = config.get("admin_policy", {})
        
        # Discover models once
        print("\n1. Discovering Available Models...")
        discovery_tool = ModelDiscoveryTool(api_client=client)
        try:
            available_models = discovery_tool.list_models_with_metadata()
            if not available_models:
                print("Could not retrieve available models. Aborting update.")
                return
        except ModelDiscoveryError as e:
            print(f"Could not discover models. Aborting update. Error: {e}")
            return
        model_map = {m["id"]: m for m in available_models}

        print("\n2. Current Configuration:")
        print_status(manager, available_models)

        roles = config.get("model_roles", {})
        
        while True:
            print("\n" + "="*80)
            role_to_update = input("Enter a role to update (or 'done' to finish): ").strip()
            
            if role_to_update.lower() == 'done':
                break
            
            if not role_to_update or role_to_update not in roles:
                print(f"Error: Role '{role_to_update}' not found or is empty. Available roles: {', '.join(sorted(roles.keys()))}")
                continue

            role_config = roles.get(role_to_update)
            required_capabilities = role_config.get("required_capabilities", []) if isinstance(role_config, dict) else []
            current_model = role_config.get("model") if isinstance(role_config, dict) else role_config
            
            print(f"Current model for '{role_to_update}' is '{current_model}'.")
            new_model = input(f"Enter new model name for '{role_to_update}': ").strip()
            
            if not new_model:
                print("Error: New model name cannot be empty. Update cancelled for this role.")
                continue
            
            if new_model not in model_map:
                print(f"Warning: Model '{new_model}' is not in the list of available models from the API.")
                if input("Are you sure you want to use this model? (yes/no): ").strip().lower() != 'yes':
                    print("Update cancelled.")
                    continue

            new_model_metadata = model_map.get(new_model, {})
            should_proceed = True
            warning_reasons = []

            # --- Safety Check 1: Beta Model Warning ---
            if new_model_metadata.get("is_beta", False):
                warning_reasons.append(f"The model '{new_model}' is marked as a BETA model.")

            # --- Safety Check 2: Cost Warning ---
            pricing = new_model_metadata.get("pricing", {})
            input_cost = pricing.get("input", {}).get("usd", 0.0)
            output_cost = pricing.get("output", {}).get("usd", 0.0)
            max_input = admin_policy.get("max_input_cost_per_million_tokens", float('inf'))
            max_output = admin_policy.get("max_output_cost_per_million_tokens", float('inf'))
            
            if input_cost > max_input:
                warning_reasons.append(f"The input cost (${input_cost:.2f}/1M tok) exceeds the policy maximum (${max_input:.2f}/1M tok).")
            if output_cost > max_output:
                warning_reasons.append(f"The output cost (${output_cost:.2f}/1M tok) exceeds the policy maximum (${max_output:.2f}/1M tok).")

            # --- Safety Check 3: Capability Warning ---
            if required_capabilities:
                # Use static map first, then fall back to API capabilities
                model_caps = set(MODEL_CAPABILITIES.get(new_model, ["text"]))
                api_caps = set(new_model_metadata.get("capabilities", {}).keys())
                model_caps.update(api_caps) # Combine for a comprehensive check
                
                missing_caps = set(required_capabilities) - model_caps
                if missing_caps:
                    warning_reasons.append(f"The model lacks required capabilities: {', '.join(missing_caps)}.")
            
            # --- Consolidated Warning Prompt ---
            if warning_reasons:
                print(f"\n!!! WARNING !!!")
                print("You are about to make a change that violates one or more administrative policies:")
                for reason in warning_reasons:
                    print(f"  - {reason}")
                print("\nThis may lead to instability, unexpected costs, or functional incompatibility.")
                confirm = input("Type 'yes I am sure' to proceed despite the warnings: ").strip()
                if confirm != 'yes I am sure':
                    print("Update cancelled due to policy warnings.")
                    should_proceed = False
            
            if should_proceed:
                # Update in memory
                if isinstance(role_config, dict):
                    role_config["model"] = new_model
                else: # Backward compatibility
                    roles[role_to_update] = new_model
                print(f"Role '{role_to_update}' updated to '{new_model}'.")

        # Save changes
        print("\n" + "="*80)
        if input("Save changes to config/models.json? (yes/no): ").strip().lower() == 'yes':
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                print("Configuration saved successfully.")
            except IOError as e:
                print(f"Error: Could not write to configuration file. {e}")
        else:
            print("Changes discarded.")
            
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"Error: Could not initialize or read configuration. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    print("-" * 80)


def main():
    """Main function to parse arguments and execute actions."""
    parser = argparse.ArgumentParser(description="Manage model registry for Project Chimera.")
    parser.add_argument('--discover', action='store_true', help="Fetch and display a rich table of available models.")
    parser.add_argument('--status', action='store_true', help="Display the current role-to-model mappings with live status.")
    parser.add_argument('--update', action='store_true', help="Enter interactive mode to update model roles with safety warnings.")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()

    try:
        client = get_venice_client()
    except Exception as e:
        print(f"Fatal Error: Could not initialize Venice client. Is your config set up correctly? Details: {e}")
        sys.exit(1)

    config_path = "config/models.json"

    if args.discover:
        discover_and_print_models(client)
    elif args.status:
        manager = ModelManager(config_path, enforce_safety=True, api_client=client)
        print_status(manager)
    elif args.update:
        interactive_update(client, config_path)

if __name__ == "__main__":
    main()