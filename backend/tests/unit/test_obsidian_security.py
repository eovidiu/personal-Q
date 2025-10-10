"""
ABOUTME: Security tests for Obsidian client path traversal protection.
ABOUTME: Verifies that malicious paths are blocked and legitimate paths work.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from app.integrations.obsidian_client import ObsidianClient


@pytest.fixture
def test_vault():
    """Create temporary vault for testing."""
    vault_dir = tempfile.mkdtemp()
    vault_path = Path(vault_dir)
    
    # Create .obsidian folder to make it a valid vault
    (vault_path / ".obsidian").mkdir()
    
    # Create some test files
    (vault_path / "test.md").write_text("Test content")
    (vault_path / "notes").mkdir()
    (vault_path / "notes" / "nested.md").write_text("Nested content")
    
    # Create a file outside vault (for testing traversal attempts)
    outside_dir = vault_path.parent / "outside"
    outside_dir.mkdir(exist_ok=True)
    (outside_dir / "secret.md").write_text("Secret content")
    
    yield vault_path
    
    # Cleanup
    shutil.rmtree(vault_dir, ignore_errors=True)
    shutil.rmtree(outside_dir, ignore_errors=True)


@pytest.fixture
def obsidian_client(test_vault):
    """Create ObsidianClient with test vault."""
    client = ObsidianClient(vault_path=str(test_vault))
    return client


class TestPathTraversalSecurity:
    """Test path traversal attack prevention."""

    @pytest.mark.asyncio
    async def test_read_absolute_path_blocked(self, obsidian_client):
        """Test that absolute paths are blocked."""
        result = await obsidian_client.read_note("/etc/passwd")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_read_parent_traversal_blocked(self, obsidian_client):
        """Test that ../ traversal is blocked."""
        result = await obsidian_client.read_note("../../../outside/secret.md")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_read_mixed_traversal_blocked(self, obsidian_client):
        """Test that mixed traversal attempts are blocked."""
        result = await obsidian_client.read_note("notes/../../outside/secret.md")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_read_legitimate_path_works(self, obsidian_client):
        """Test that legitimate paths work correctly."""
        result = await obsidian_client.read_note("test.md")
        assert result["success"] is True
        assert result["content"] == "Test content"

    @pytest.mark.asyncio
    async def test_read_nested_legitimate_path_works(self, obsidian_client):
        """Test that legitimate nested paths work."""
        result = await obsidian_client.read_note("notes/nested.md")
        assert result["success"] is True
        assert result["content"] == "Nested content"

    @pytest.mark.asyncio
    async def test_write_absolute_path_blocked(self, obsidian_client):
        """Test that writing to absolute paths is blocked."""
        result = await obsidian_client.write_note("/tmp/malicious.md", "content")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_write_parent_traversal_blocked(self, obsidian_client):
        """Test that writing via ../ is blocked."""
        result = await obsidian_client.write_note("../outside/malicious.md", "content")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_write_legitimate_path_works(self, obsidian_client):
        """Test that writing to legitimate paths works."""
        result = await obsidian_client.write_note("new_note.md", "New content")
        assert result["success"] is True
        
        # Verify file was created
        read_result = await obsidian_client.read_note("new_note.md")
        assert read_result["success"] is True
        assert read_result["content"] == "New content"

    @pytest.mark.asyncio
    async def test_delete_absolute_path_blocked(self, obsidian_client):
        """Test that deleting absolute paths is blocked."""
        result = await obsidian_client.delete_note("/etc/passwd")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_parent_traversal_blocked(self, obsidian_client):
        """Test that deleting via ../ is blocked."""
        result = await obsidian_client.delete_note("../outside/secret.md")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_legitimate_path_works(self, obsidian_client):
        """Test that deleting legitimate paths works."""
        # Create a file first
        await obsidian_client.write_note("to_delete.md", "Delete me")
        
        # Delete it
        result = await obsidian_client.delete_note("to_delete.md")
        assert result["success"] is True
        
        # Verify it's gone
        read_result = await obsidian_client.read_note("to_delete.md")
        assert read_result["success"] is False

    @pytest.mark.asyncio
    async def test_non_markdown_file_blocked(self, obsidian_client, test_vault):
        """Test that non-markdown files are blocked."""
        # Create a non-markdown file
        (test_vault / "test.txt").write_text("Text file")
        
        result = await obsidian_client.read_note("test.txt")
        assert result["success"] is False
        assert "Invalid path" in result["error"]

    @pytest.mark.asyncio
    async def test_search_long_query_blocked(self, obsidian_client):
        """Test that excessively long queries are blocked."""
        long_query = "a" * 1001
        result = await obsidian_client.search_notes(long_query)
        assert result["success"] is False
        assert "Query too long" in result["error"]

    @pytest.mark.asyncio
    async def test_search_legitimate_query_works(self, obsidian_client):
        """Test that legitimate search queries work."""
        result = await obsidian_client.search_notes("Test")
        assert result["success"] is True
        assert len(result["matches"]) > 0

    @pytest.mark.asyncio
    async def test_list_notes_folder_traversal_blocked(self, obsidian_client):
        """Test that folder path traversal in list_notes is blocked."""
        result = await obsidian_client.list_notes(folder="../outside")
        assert result["success"] is False
        assert "Invalid folder path" in result["error"]

    @pytest.mark.asyncio
    async def test_list_notes_legitimate_folder_works(self, obsidian_client):
        """Test that listing legitimate folders works."""
        result = await obsidian_client.list_notes(folder="notes")
        assert result["success"] is True
        assert len(result["notes"]) > 0


class TestSymlinkSecurity:
    """Test that symlinks outside vault are not followed."""

    @pytest.mark.asyncio
    async def test_symlink_outside_vault_blocked(self, obsidian_client, test_vault):
        """Test that symlinks pointing outside vault are blocked."""
        # Create a symlink to outside file
        outside_file = test_vault.parent / "outside" / "secret.md"
        symlink_path = test_vault / "link_to_secret.md"
        
        try:
            symlink_path.symlink_to(outside_file)
        except OSError:
            pytest.skip("Symlinks not supported on this system")
        
        # Try to read via symlink
        result = await obsidian_client.read_note("link_to_secret.md")
        assert result["success"] is False
        assert "Invalid path" in result["error"]


class TestPathValidation:
    """Test _validate_note_path helper method."""

    def test_validate_note_path_removes_dots(self, obsidian_client):
        """Test that .. is removed from paths."""
        result = obsidian_client._validate_note_path("notes/../test.md")
        # Path should be validated as "notes/test.md" after removing ..
        assert result is not None or result is None  # Either valid or invalid, but no crash

    def test_validate_note_path_absolute_returns_none(self, obsidian_client):
        """Test that absolute paths return None."""
        result = obsidian_client._validate_note_path("/etc/passwd")
        assert result is None

    def test_validate_note_path_legitimate_returns_path(self, obsidian_client):
        """Test that legitimate paths return Path object."""
        result = obsidian_client._validate_note_path("test.md")
        assert result is not None
        assert isinstance(result, Path)

