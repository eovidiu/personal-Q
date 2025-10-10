"""
Obsidian vault integration (local file I/O).
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class ObsidianClient:
    """Obsidian vault client for file operations."""

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Obsidian client.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path

    def set_vault_path(self, vault_path: str):
        """Set or update vault path."""
        self.vault_path = vault_path

    def _get_vault_path(self) -> Path:
        """Get vault path as Path object."""
        if not self.vault_path:
            raise ValueError("Obsidian vault path not configured")

        path = Path(self.vault_path)
        if not path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")

        return path

    async def list_notes(
        self,
        folder: str = "",
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        List notes in vault.

        Args:
            folder: Subfolder (relative to vault)
            recursive: Include subfolders

        Returns:
            List of notes
        """
        try:
            vault = self._get_vault_path()
            target_dir = vault / folder if folder else vault

            if not target_dir.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder}"
                }

            notes = []
            pattern = "**/*.md" if recursive else "*.md"

            for note_path in target_dir.glob(pattern):
                if note_path.is_file():
                    relative_path = note_path.relative_to(vault)
                    notes.append({
                        "name": note_path.stem,
                        "path": str(relative_path),
                        "size": note_path.stat().st_size,
                        "modified": note_path.stat().st_mtime
                    })

            return {
                "success": True,
                "notes": notes,
                "count": len(notes)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def read_note(
        self,
        note_path: str
    ) -> Dict[str, Any]:
        """
        Read note content.

        Args:
            note_path: Note path (relative to vault)

        Returns:
            Note content
        """
        try:
            vault = self._get_vault_path()
            full_path = vault / note_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Note not found: {note_path}"
                }

            content = full_path.read_text(encoding="utf-8")

            # Parse frontmatter if exists
            frontmatter = {}
            body = content

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    # Parse YAML frontmatter (simple parsing)
                    fm_lines = parts[1].strip().split("\n")
                    for line in fm_lines:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()
                    body = parts[2].strip()

            return {
                "success": True,
                "content": body,
                "frontmatter": frontmatter,
                "full_content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def write_note(
        self,
        note_path: str,
        content: str,
        frontmatter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Write note to vault.

        Args:
            note_path: Note path (relative to vault)
            content: Note content
            frontmatter: Optional frontmatter metadata

        Returns:
            Write status
        """
        try:
            vault = self._get_vault_path()
            full_path = vault / note_path

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Build final content
            final_content = content

            if frontmatter:
                fm_lines = ["---"]
                for key, value in frontmatter.items():
                    fm_lines.append(f"{key}: {value}")
                fm_lines.append("---")
                fm_lines.append("")
                final_content = "\n".join(fm_lines) + content

            full_path.write_text(final_content, encoding="utf-8")

            return {
                "success": True,
                "path": note_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def search_notes(
        self,
        query: str,
        folder: str = ""
    ) -> Dict[str, Any]:
        """
        Search notes by content.

        Args:
            query: Search query
            folder: Limit search to folder

        Returns:
            Matching notes
        """
        try:
            vault = self._get_vault_path()
            target_dir = vault / folder if folder else vault

            matches = []

            for note_path in target_dir.glob("**/*.md"):
                if note_path.is_file():
                    try:
                        content = note_path.read_text(encoding="utf-8")
                        if query.lower() in content.lower():
                            relative_path = note_path.relative_to(vault)
                            # Get snippet around match
                            idx = content.lower().find(query.lower())
                            start = max(0, idx - 50)
                            end = min(len(content), idx + len(query) + 50)
                            snippet = content[start:end]

                            matches.append({
                                "name": note_path.stem,
                                "path": str(relative_path),
                                "snippet": f"...{snippet}..."
                            })
                    except Exception:
                        continue

            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_note(
        self,
        note_path: str
    ) -> Dict[str, Any]:
        """
        Delete note from vault.

        Args:
            note_path: Note path (relative to vault)

        Returns:
            Delete status
        """
        try:
            vault = self._get_vault_path()
            full_path = vault / note_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Note not found: {note_path}"
                }

            full_path.unlink()

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def validate_vault_path(self, vault_path: str) -> bool:
        """
        Validate vault path.

        Args:
            vault_path: Path to validate

        Returns:
            True if valid Obsidian vault
        """
        try:
            path = Path(vault_path)
            if not path.exists():
                return False

            # Check for .obsidian folder (indicator of Obsidian vault)
            obsidian_folder = path / ".obsidian"
            return obsidian_folder.exists() and obsidian_folder.is_dir()

        except Exception:
            return False


# Global client instance
obsidian_client = ObsidianClient()


def get_obsidian_client() -> ObsidianClient:
    """Get Obsidian client instance."""
    return obsidian_client
