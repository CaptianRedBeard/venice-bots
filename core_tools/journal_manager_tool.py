import os
from pathlib import Path
from datetime import date, timedelta
from .exceptions import ToolError
from .tool_registry import ToolRegistry

# --- JSON Schemas for LLM Discovery ---
CREATE_ENTRY_SCHEMA = {
    "type": "function",
    "description": "Creates a new journal entry (daily or weekly) from a template if it doesn't already exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_type": {
                "type": "string",
                "description": "The type of entry to create. Must be 'daily' or 'weekly'.",
                "enum": ["daily", "weekly"]
            },
            "target_date": {
                "type": "string",
                "description": "A target date for the entry, in a natural language format like 'yesterday', 'last Friday', or 'YYYY-MM-DD'. Defaults to today."
            }
        },
        "required": ["file_type"]
    }
}

APPEND_SECTION_SCHEMA = {
    "type": "function",
    "description": "Appends text to a specific section in a Markdown journal file.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "The full path to the Markdown file."},
            "section_header": {"type": "string", "description": "The exact section header, e.g., '## Mood'."},
            "text": {"type": "string", "description": "The text to append."}
        },
        "required": ["file_path", "section_header", "text"]
    }
}

GET_HEADERS_SCHEMA = {
    "type": "function",
    "description": "Reads a journal file and returns a list of all available section headers.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_type": {
                "type": "string",
                "description": "The type of entry to read headers from ('daily' or 'weekly').",
                "enum": ["daily", "weekly"]
            },
            "target_date": {
                "type": "string",
                "description": "A target date for the entry, in a natural language format like 'yesterday', 'last Friday', or 'YYYY-MM-DD'. Defaults to today."
            }
        },
        "required": ["file_type"]
    }
}

class JournalManagerTool:
    """Manages journaling operations for a specific persona."""
    def __init__(self, persona_name: str):
        self.persona_name = persona_name
        self.base_path = Path("data") / "personas" / self.persona_name / "user"

    def create_entry_from_template(self, file_type: str, target_date: str = None) -> str:
        """Creates a daily or weekly file from its template if it doesn't exist."""
        if file_type not in ['daily', 'weekly']:
            raise ToolError("Invalid file_type. Must be 'daily' or 'weekly'.")
        
        target_date_obj = self._parse_date(target_date) if target_date else date.today()

        if file_type == 'daily':
            dir_path = self.base_path / "daily"
            file_name = f"{target_date_obj.isoformat()}.md"
        else: # weekly
            dir_path = self.base_path / "weekly"
            week_num = target_date_obj.isocalendar()[1]
            file_name = f"{target_date_obj.year}-W{week_num}.md"
        
        file_path = dir_path / file_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        if not file_path.exists():
            template_path = Path(f"data/personas/{self.persona_name}/templates/{file_type}_template.md")
            if not template_path.exists():
                raise ToolError(f"Template not found at {template_path}")
            
            content = template_path.read_text(encoding='utf-8')
            if file_type == 'daily':
                content = content.replace("{{DATE}}", target_date_obj.isoformat())
            
            file_path.write_text(content, encoding='utf-8')
            return f"Created new {file_type} entry at {file_path}"
        else:
            return f"Entry already exists at {file_path}"

    def append_to_section(self, file_path: str, section_header: str, text: str) -> str:
        """Appends text to a specific section in a Markdown file."""
        if not text.startswith('- '):
            text = f"- {text}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            target_word = section_header.replace('#', '').strip().lower()
            found_section = False

            for i, line in enumerate(lines):
                if line.startswith('#') and target_word in line.lower():
                    found_section = True
                    insert_index = i + 1
                    if insert_index < len(lines) and lines[insert_index].strip() == '':
                        insert_index += 1
                    
                    while insert_index < len(lines):
                        next_line = lines[insert_index]
                        if next_line.startswith('#'):
                            break
                        if next_line.strip().startswith(('- ', '* ', '+ ')):
                            insert_index += 1
                        else:
                            break
                    
                    text_to_insert = text + '\n'
                    lines.insert(insert_index, text_to_insert)
                    break
            
            if not found_section:
                return f"Error: Section '{section_header.strip()}' not found."

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            return f"Successfully appended text to the '{section_header.strip()}' section."

        except FileNotFoundError:
            raise ToolError(f"The file at {file_path} was not found.")
        except Exception as e:
            raise ToolError(f"Failed to append to section. Original error: {e}")

    def get_headers(self, file_type: str = 'daily', target_date: str = None) -> list:
        """Reads a journal file and returns a list of all available section headers."""
        file_path = self._resolve_file_path(file_type, target_date)
        self.create_entry_from_template(file_type=file_type, target_date_str=target_date)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            headers = []
            for line in lines:
                if line.startswith('#') and line.strip() != '#':
                    headers.append(line.strip())
            
            return headers
        except Exception as e:
            raise ToolError(f"Failed to read headers from {file_path}: {e}")

    def _resolve_file_path(self, file_type: str, target_date_str: str = None) -> Path:
        """Resolves the correct file path based on type and date."""
        if file_type == 'daily':
            target_date = self._parse_date(target_date_str) if target_date_str else date.today()
            dir_path = self.base_path / "daily"
            file_name = f"{target_date.isoformat()}.md"
        elif file_type == 'weekly':
            target_date = self._parse_date(target_date_str) if target_date_str else date.today()
            dir_path = self.base_path / "weekly"
            week_num = target_date.isocalendar()[1]
            file_name = f"{target_date.year}-W{week_num}.md"
        else:
            raise ToolError("Invalid file_type. Must be 'daily' or 'weekly'.")
        
        return dir_path / file_name

    def _parse_date(self, date_str: str) -> date:
        """Parses a natural language date string into a date object."""
        date_str = date_str.lower().replace("for ", "")
        today = date.today()
        if date_str == "today":
            return today
        if date_str == "yesterday":
            return today - timedelta(days=1)
        if date_str == "tomorrow":
            return today + timedelta(days=1)
        
        if date_str.startswith("last ") or date_str.startswith("next "):
            day_name = date_str.split(" ")[1]
            target_day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
            if day_name in target_day_map:
                days_ahead = target_day_map[day_name] - today.weekday()
                if date_str.startswith("last "):
                    days_ahead -= 7
                elif days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        try:
            return date.fromisoformat(date_str)
        except ValueError:
            pass
        
        raise ToolError(f"Could not understand date: '{date_str}'. Use formats like 'today', 'yesterday', 'last Friday', or 'YYYY-MM-DD'.")

def prepare_append_to_section(**kwargs) -> dict:
    """
    An init_hook for append_to_section. Resolves the file_path based on optional
    file_type and target_date arguments.
    """
    persona_name = "captains_log"
    instance = JournalManagerTool(persona_name)

    file_type = kwargs.get('file_type', 'daily')
    target_date_str = kwargs.get('target_date', None)

    instance.create_entry_from_template(file_type=file_type, target_date=target_date_str)
    
    resolved_path = instance._resolve_file_path(file_type, target_date_str)
    kwargs['file_path'] = str(resolved_path)
    return kwargs

def initialize_and_register(tool_registry: ToolRegistry, persona_name: str):
    """Initializes the JournalManagerTool and registers its methods."""
    instance = JournalManagerTool(persona_name)
    
    tool_registry.register(
        tool_name="create_entry_from_template",
        tool_callable=instance.create_entry_from_template,
        schema=CREATE_ENTRY_SCHEMA
    )
    tool_registry.register(
        tool_name="append_to_section",
        tool_callable=instance.append_to_section,
        schema=APPEND_SECTION_SCHEMA,
        init_hook=prepare_append_to_section
    )
    tool_registry.register(
        tool_name="get_headers",
        tool_callable=instance.get_headers,
        schema=GET_HEADERS_SCHEMA
    )
    return instance