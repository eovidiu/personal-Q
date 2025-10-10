"""
ABOUTME: Obsidian vault integration with proper async file I/O using aiofiles.
ABOUTME: All file operations are non-blocking to prevent event loop starvation.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles

logger = logging.getLogger(__name__)


class ObsidianClient:
    """Obsidian vault client with async file operations."""

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

    def _validate_note_path(self, note_path: str) -> Optional[Path]:
        """
        Validate and sanitize note path to prevent path traversal attacks.

        Args:
            note_path: User-provided note path

        Returns:
            Validated Path object or None if invalid

        Security:
            - Blocks path traversal attempts (.., absolute paths)
            - Ensures resolved path stays within vault
            - Only allows .md files
            - Logs suspicious attempts
        """
        try:
            vault = self._get_vault_path().resolve()

            # Block absolute paths
            if note_path.startswith("/") or note_path.startswith("\\"):
                logger.warning(f"Path traversal attempt blocked: absolute path '{note_path}'")
                return None

            # Block any path containing .. (path traversal)
            if ".." in note_path:
                logger.warning(f"Path traversal attempt blocked: '..' found in '{note_path}'")
                return None

            # Remove leading slashes
            safe_path = note_path.lstrip("/").lstrip("\\")

            # Build full path and resolve symlinks
            full_path = (vault / safe_path).resolve()

            # Critical: Ensure resolved path is still within vault
            try:
                full_path.relative_to(vault)
            except ValueError:
                logger.warning(f"Path traversal attempt blocked: '{note_path}' escapes vault")
                return None

            # Only allow markdown files (or no extension for new files)
            if full_path.suffix and full_path.suffix not in [".md"]:
                logger.warning(f"Invalid file type blocked: '{note_path}' (only .md allowed)")
                return None

            return full_path

        except Exception as e:
            logger.error(f"Error validating path '{note_path}': {e}")
            return None

    async def list_notes(
        self,
        folder: str = "",
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        List notes in vault (async).

        Args:
            folder: Subfolder (relative to vault)
            recursive: Include subfolders

        Returns:
            List of notes
        """
        try:
            vault = self._get_vault_path().resolve()
            
            # Block path traversal in folder parameter
            if folder and ".." in folder:
                return {
                    "success": False,
                    "error": "Invalid folder path: path traversal detected"
                }
            
            target_dir = vault / folder if folder else vault

            # Validate folder path is within vault
            if folder:
                try:
                    target_dir.resolve().relative_to(vault)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid folder path: escapes vault"
                    }

            if not target_dir.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder}"
                }

            notes = []
            pattern = "**/*.md" if recursive else "*.md"

            # File system globbing is sync but fast, run in executor for safety
            def _list_notes_sync():
                result = []
                for note_path in target_dir.glob(pattern):
                    if note_path.is_file():
                        relative_path = note_path.relative_to(vault)
                        result.append({
                            "name": note_path.stem,
                            "path": str(relative_path),
                            "size": note_path.stat().st_size,
                            "modified": note_path.stat().st_mtime
                        })
                return result

            notes = await asyncio.to_thread(_list_notes_sync)

            return {
                "success": True,
                "notes": notes,
                "count": len(notes)
            }

        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def read_note(
        self,
        note_path: str
    ) -> Dict[str, Any]:
        """
        Read note content (async with aiofiles).

        Args:
            note_path: Note path (relative to vault)

        Returns:
            Note content
        """
        try:
            # Validate path to prevent traversal attacks
            full_path = self._validate_note_path(note_path)

            if full_path is None:
                return {
                    "success": False,
                    "error": "Invalid path: path traversal or invalid file type detected"
                }

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Note not found: {note_path}"
                }

            # Use aiofiles for async file reading
            async with aiofiles.open(full_path, mode='r', encoding='utf-8') as f:
                content = await f.read()

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
            logger.error(f"Error reading note {note_path}: {e}")
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
        Write note to vault (async with aiofiles).

        Args:
            note_path: Note path (relative to vault)
            content: Note content
            frontmatter: Optional frontmatter metadata

        Returns:
            Write status
        """
        try:
            # Validate path to prevent traversal attacks
            full_path = self._validate_note_path(note_path)

            if full_path is None:
                return {
                    "success": False,
                    "error": "Invalid path: path traversal or invalid file type detected"
                }

            vault = self._get_vault_path().resolve()

            # Ensure parent directory is within vault
            parent = full_path.parent
            try:
                parent.relative_to(vault)
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid directory path: escapes vault"
                }

            # Create parent directories if needed (sync but fast)
            await asyncio.to_thread(parent.mkdir, parents=True, exist_ok=True)

            # Build final content
            final_content = content

            if frontmatter:
                fm_lines = ["---"]
                for key, value in frontmatter.items():
                    fm_lines.append(f"{key}: {value}")
                fm_lines.append("---")
                fm_lines.append("")
                final_content = "\n".join(fm_lines) + content

            # Use aiofiles for async file writing
            async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f:
                await f.write(final_content)

            return {
                "success": True,
                "path": note_path
            }

        except Exception as e:
            logger.error(f"Error writing note {note_path}: {e}")
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
        Search notes by content (async).

        Args:
            query: Search query
            folder: Limit search to folder

        Returns:
            Matching notes
        """
        try:
            # Limit query length to prevent DoS
            if len(query) > 1000:
                return {
                    "success": False,
                    "error": "Query too long (max 1000 characters)"
                }

            vault = self._get_vault_path().resolve()
            
            # Block path traversal in folder parameter
            if folder and ".." in folder:
                return {
                    "success": False,
                    "error": "Invalid folder path: path traversal detected"
                }
            
            target_dir = vault / folder if folder else vault

            # Validate target directory is within vault
            try:
                target_dir.resolve().relative_to(vault)
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid folder path: escapes vault"
                }

            matches = []

            # Run search in executor to avoid blocking
            def _search_sync():
                results = []
                for note_path in target_dir.glob("**/*.md"):
                    # Ensure each found file is actually within vault (no symlink escape)
                    try:
                        note_path.resolve().relative_to(vault)
                    except ValueError:
                        logger.warning(f"Skipping file outside vault: {note_path}")
                        continue

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

                                results.append({
                                    "name": note_path.stem,
                                    "path": str(relative_path),
                                    "snippet": f"...{snippet}..."
                                })
                        except Exception:
                            continue
                return results

            matches = await asyncio.to_thread(_search_sync)

            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }

        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_note(
        self,
        note_path: str
    ) -> Dict[str, Any]:
        """
        Delete note from vault (async).

        Args:
            note_path: Note path (relative to vault)

        Returns:
            Delete status
        """
        try:
            # Validate path to prevent traversal attacks
            full_path = self._validate_note_path(note_path)

            if full_path is None:
                return {
                    "success": False,
                    "error": "Invalid path: path traversal or invalid file type detected"
                }

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Note not found: {note_path}"
                }

            # Only delete files, not directories
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": "Can only delete files, not directories"
                }

            # Run unlink in executor
            await asyncio.to_thread(full_path.unlink)

            return {"success": True}

        except Exception as e:
            logger.error(f"Error deleting note {note_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def validate_vault_path(self, vault_path: str) -> bool:
        """
        Validate vault path (async).

        Args:
            vault_path: Path to validate

        Returns:
            True if valid Obsidian vault
        """
        try:
            def _validate_sync():
                path = Path(vault_path)
                if not path.exists():
                    return False

                # Check for .obsidian folder (indicator of Obsidian vault)
                obsidian_folder = path / ".obsidian"
                return obsidian_folder.exists() and obsidian_folder.is_dir()

            return await asyncio.to_thread(_validate_sync)

        except Exception as e:
            logger.error(f"Error validating vault path: {e}")
            return False


# Global client instance
obsidian_client = ObsidianClient()


def get_obsidian_client() -> ObsidianClient:
    """Get Obsidian client instance."""
    return obsidian_client
