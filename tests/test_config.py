"""
Tests for the configuration of the Agent Name Service.
Validates environment, paths, and dependencies.
"""
import os
import sys
import pytest
import importlib
from pathlib import Path

class TestConfiguration:
    """Tests for validating the ANS configuration."""
    
    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        # Get the project root directory
        root_dir = Path(__file__).parent.parent
        
        # Essential directories that should exist
        required_dirs = [
            root_dir / "ans",
            root_dir / "ans/core",
            root_dir / "ans/api",
            root_dir / "ans/db",
            root_dir / "ans/crypto",
            root_dir / "ans/adapters",
            root_dir / "ans/schemas",
            root_dir / "ans/tests",
            root_dir / "frontend",
            root_dir / "tests",
            root_dir / "tests/logs"
        ]
        
        # Check each directory
        for dir_path in required_dirs:
            assert dir_path.exists(), f"Required directory {dir_path} doesn't exist"
            assert dir_path.is_dir(), f"Path {dir_path} is not a directory"
    
    def test_required_modules_can_be_imported(self):
        """Test that all required modules can be imported."""
        # List of critical modules to check
        required_modules = [
            "cryptography",
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "jsonschema",
            "semver",
            "uvicorn",
            "aiosqlite",
            "pytest"
        ]
        
        # Try importing each module
        for module_name in required_modules:
            try:
                importlib.import_module(module_name)
            except ImportError:
                pytest.fail(f"Required module {module_name} could not be imported")
    
    def test_ans_modules_can_be_imported(self):
        """Test that key ANS modules can be imported."""
        # Ensure the ANS package is in the Python path
        root_dir = str(Path(__file__).parent.parent)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        
        # Try importing key modules from the ANS package
        try:
            from ans.core.agent import Agent
            from ans.core.ans_name import ANSName
            from ans.core.agent_registry import AgentRegistry
            from ans.core.registration_authority import RegistrationAuthority
            from ans.crypto.certificate import Certificate
            from ans.crypto.certificate_authority import CertificateAuthority
            from ans.db.models import init_db, AgentModel
        except ImportError as e:
            pytest.fail(f"Failed to import ANS module: {e}")
    
    def test_log_directory_is_writable(self):
        """Test that the log directory is writable."""
        log_dir = Path(__file__).parent / "logs"
        
        # Ensure the log directory exists
        assert log_dir.exists(), "Log directory doesn't exist"
        
        # Test if we can write a file to the log directory
        test_file = log_dir / "test_write.log"
        try:
            with open(test_file, "w") as f:
                f.write("Test log entry")
            
            # Verify the file was written
            assert test_file.exists(), "Failed to write to log directory"
            
            # Clean up
            test_file.unlink()
        except IOError:
            pytest.fail("Log directory is not writable")
    
    def test_config_files_exist(self):
        """Test that configuration files exist."""
        root_dir = Path(__file__).parent.parent
        
        # Essential configuration files
        config_files = [
            root_dir / "requirements.txt",
            root_dir / "frontend/package.json",
            root_dir / "frontend/tsconfig.json"
        ]
        
        # Check each file
        for file_path in config_files:
            assert file_path.exists(), f"Required config file {file_path} doesn't exist"
            assert file_path.is_file(), f"Path {file_path} is not a file"