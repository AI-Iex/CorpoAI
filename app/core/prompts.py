from pathlib import Path
from functools import lru_cache
from app.core.enums import PromptType
from app.core.exceptions import BaseAppException


class PromptNotFoundError(BaseAppException):
    """Raised when a prompt file is not found."""

    def __init__(self, prompt_type: PromptType):
        self.prompt_type = prompt_type
        super().__init__(f"Prompt file not found for type: {prompt_type.value}")


class PromptLoader:
    """
    Loader for LLM prompts from markdown files.
    """

    # Mapping from PromptType to filename (without extension)
    _PROMPT_FILES: dict[PromptType, str] = {
        PromptType.SYSTEM: "system",
        PromptType.RAG_CONTEXT: "rag_context",
        PromptType.TITLE_GENERATOR: "title_generator",
        PromptType.SUMMARIZER: "summarizer",
    }

    def __init__(self, prompts_dir: Path | None = None):
        """
        Initialize the prompt loader.
        """
        if prompts_dir is None:
            # Get project root (3 levels up from this file: core -> app -> project)
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = project_root / "prompts"

        self._prompts_dir = prompts_dir
        self._cache: dict[PromptType, str] = {}

    def get(self, prompt_type: PromptType) -> str:
        """
        Get a prompt by type.
        """
        # Check cache first
        if prompt_type in self._cache:
            return self._cache[prompt_type]

        # Get filename for this prompt type
        filename = self._PROMPT_FILES.get(prompt_type)
        if filename is None:
            raise PromptNotFoundError(prompt_type)

        # Build full path
        file_path = self._prompts_dir / f"{filename}.md"

        if not file_path.exists():
            raise PromptNotFoundError(prompt_type)

        # Read and cache the prompt
        content = file_path.read_text(encoding="utf-8").strip()
        self._cache[prompt_type] = content

        return content

    def get_or_default(self, prompt_type: PromptType, default: str = "") -> str:
        """
        Get a prompt by type, returning a default if not found.
        """
        try:
            return self.get(prompt_type)
        except PromptNotFoundError:
            return default

    def reload(self, prompt_type: PromptType | None = None) -> None:
        """
        Clear the cache and reload prompts.
        """
        if prompt_type is not None:
            self._cache.pop(prompt_type, None)
        else:
            self._cache.clear()

    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory path."""
        return self._prompts_dir

    def list_available(self) -> list[PromptType]:
        """
        List all prompt types that have corresponding files.
        """
        available = []
        for prompt_type, filename in self._PROMPT_FILES.items():
            file_path = self._prompts_dir / f"{filename}.md"
            if file_path.exists():
                available.append(prompt_type)
        return available


# Singleton instance
@lru_cache(maxsize=1)
def get_prompt_loader() -> PromptLoader:
    """
    Get the singleton PromptLoader instance.
    """
    return PromptLoader()
