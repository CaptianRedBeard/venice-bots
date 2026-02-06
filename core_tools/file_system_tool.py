import os
import glob
from typing import List, Optional

# --- Custom Exception Classes ---
class FileSystemToolError(Exception):
    """Base exception for the FileSystemTool."""
    pass

class FileNotFoundError(FileSystemToolError):
    """Raised when a specified file is not found."""
    pass

class PathTraversalError(FileSystemToolError):
    """Raised when a path attempts to traverse outside the allowed root directory."""
    pass

class NotADirectoryError(FileSystemToolError):
    """Raised when a path that should be a directory is not."""
    pass

# --- FileSystemTool Class ---
class FileSystemTool:
    """
    A tool for interacting with the local file system within a restricted root directory.
    """
    def __init__(self, root_directory: str = "."):
        """
        Initializes the FileSystemTool.
        
        Args:
            root_directory (str): The root directory that the tool is restricted to.
                                  Defaults to the current working directory.
        """
        self.root_directory = os.path.abspath(root_directory)

    def _validate_path(self, path: str) -> str:
        """
        Validates that a given path is within the root directory and returns its absolute path.
        
        Args:
            path (str): The relative path to validate.
            
        Returns:
            str: The absolute, validated path.
            
        Raises:
            PathTraversalError: If the path is outside the root directory or is absolute.
        """
        if not isinstance(path, str) or not path:
            raise PathTraversalError("Path must be a non-empty string.")

        # Reject absolute paths to enforce relative-path-only usage
        if os.path.isabs(path):
            raise PathTraversalError(f"Access denied. Absolute paths like '{path}' are not allowed.")

        # Construct the full path and resolve it to its real path (canonical form)
        full_path = os.path.realpath(os.path.join(self.root_directory, path))
        
        # Get the real path of the root directory to compare against
        real_root_path = os.path.realpath(self.root_directory)

        # Ensure the resolved path is within the real root directory
        if not full_path.startswith(real_root_path + os.sep) and full_path != real_root_path:
            raise PathTraversalError(f"Access denied. Path '{path}' is outside the allowed root directory.")
            
        return full_path

    def read_file(self, path: str) -> str:
        """
        Reads the full content of a file at the given path.
        
        Args:
            path (str): The relative path to the file from the root directory.
            
        Returns:
            str: The content of the file as a string.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PathTraversalError: If the path is outside the root directory.
        """
        safe_path = self._validate_path(path)

        if not os.path.isfile(safe_path):
            raise FileNotFoundError(f"File not found at '{path}'.")

        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            # Re-raise as a generic tool error for other I/O issues
            raise FileSystemToolError(f"Error reading file '{path}': {e}")

    def list_directory(self, path: str) -> List[str]:
        """
        Lists the files and subdirectories in the directory at the given path.
        
        Args:
            path (str): The relative path to the directory from the root directory.
            
        Returns:
            List[str]: A list of names of files and directories.
            
        Raises:
            NotADirectoryError: If the path is not a directory.
            PathTraversalError: If the path is outside the root directory.
        """
        safe_path = self._validate_path(path)

        if not os.path.isdir(safe_path):
            raise NotADirectoryError(f"Directory not found at '{path}'.")
            
        try:
            return sorted(os.listdir(safe_path))
        except Exception as e:
            raise FileSystemToolError(f"Error listing directory '{path}': {e}")

    def find_files(self, pattern: str, root_path: str = ".") -> List[str]:
        """
        Recursively searches for files matching a Unix shell-style pattern.
        
        Args:
            pattern (str): The pattern to match (e.g., '*.py', 'test_*.txt').
            root_path (str): The relative directory to start the search from.
        
        Returns:
            List[str]: A list of relative file paths that match the pattern.
            
        Raises:
            PathTraversalError: If the root_path is outside the allowed directory.
            FileSystemToolError: For other errors during search.
        """
        safe_root_path = self._validate_path(root_path)
            
        try:
            # Use recursive glob to find all matching files
            search_pattern = os.path.join(safe_root_path, '**', pattern)
            found_files = glob.glob(search_pattern, recursive=True)
            
            # Convert absolute paths back to relative paths from the tool's root
            relative_files = []
            for f_path in found_files:
                if os.path.isfile(f_path):
                    rel_path = os.path.relpath(f_path, start=self.root_directory)
                    relative_files.append(rel_path)
            
            return sorted(relative_files)
        except Exception as e:
            raise FileSystemToolError(f"Error during file search for pattern '{pattern}': {e}")

# Instantiate the tool for registration with the ToolRegistry
file_system_tool_instance = FileSystemTool()

# Expose the methods as standalone functions for the registry to discover
def read_file(path: str):
    """Reads the full content of a file at the given path."""
    return file_system_tool_instance.read_file(path)

def list_directory(path: str):
    """Lists the files and subdirectories in the directory at the given path."""
    return file_system_tool_instance.list_directory(path)

def find_files(pattern: str, root_path: str = "."):
    """Recursively searches for files matching a Unix shell-style pattern."""
    return file_system_tool_instance.find_files(pattern, root_path)