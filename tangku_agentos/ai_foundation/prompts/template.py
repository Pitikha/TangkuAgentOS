"""
AI Foundation Framework - Prompt Template

This module defines the PromptTemplate class for managing AI prompts.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts."""
    CHAT = auto()
    COMPLETION = auto()
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL = auto()
    EMBEDDING = auto()
    CUSTOM = auto()


class PromptFormat(Enum):
    """Formats for prompts."""
    TEXT = auto()
    JSON = auto()
    XML = auto()
    YAML = auto()
    MARKDOWN = auto()


@dataclass
class PromptVariable:
    """
    Represents a variable in a prompt template.
    
    Attributes:
        name: Name of the variable.
        default: Default value for the variable.
        required: Whether the variable is required.
        description: Description of the variable.
        type: Type of the variable.
        options: Optional list of allowed values.
    """

    name: str
    default: Any = None
    required: bool = False
    description: str = ""
    type: str = "string"
    options: Optional[List[Any]] = None

    def validate(self, value: Any) -> bool:
        """Validate a value for this variable."""
        if self.required and value is None:
            return False
        
        if self.options is not None and value not in self.options:
            return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "default": self.default,
            "required": self.required,
            "description": self.description,
            "type": self.type,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVariable":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            default=data.get("default"),
            required=data.get("required", False),
            description=data.get("description", ""),
            type=data.get("type", "string"),
            options=data.get("options"),
        )


@dataclass
class PromptTemplate:
    """
    Represents a prompt template for AI operations.
    
    A prompt template defines a reusable prompt structure with variables
    that can be filled in when the prompt is used.
    
    Attributes:
        template_id: Unique identifier for the template.
        name: Human-readable name for the template.
        content: Template content with variable placeholders.
        variables: List of variables defined in the template.
        prompt_type: Type of prompt.
        format: Format of the prompt.
        description: Description of the template.
        examples: Example usages of the template.
        tags: Tags for categorizing the template.
        version: Version of the template.
        created_at: When the template was created.
        updated_at: When the template was last updated.
        metadata: Additional metadata.
    """

    template_id: str
    name: str
    content: str
    variables: List[PromptVariable] = field(default_factory=list)
    prompt_type: PromptType = PromptType.CUSTOM
    format: PromptFormat = PromptFormat.TEXT
    description: str = ""
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.template_id:
            self.template_id = self._generate_id()
        
        # Extract variables from content if not provided
        if not self.variables:
            self.variables = self._extract_variables()

    def _generate_id(self) -> str:
        """Generate a unique template ID."""
        unique_str = f"{self.name}:{self.content[:50]}"
        return f"prompt_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"

    def _extract_variables(self) -> List[PromptVariable]:
        """Extract variables from the template content."""
        variables = []
        
        # Find all variable placeholders in the content
        # Pattern: {variable_name} or {variable_name:default}
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)(?:\:[^\}]*)?\}'
        matches = re.findall(pattern, self.content)
        
        for match in set(matches):
            # Split variable name and default value
            parts = match.split(':')
            var_name = parts[0]
            var_default = parts[1] if len(parts) > 1 else None
            
            variables.append(PromptVariable(
                name=var_name,
                default=var_default,
                required=False,
                description="",
                type="string"
            ))
        
        return variables

    def render(self, variables: Dict[str, Any], validate: bool = True) -> str:
        """
        Render the template with the given variables.
        
        Args:
            variables: Dictionary of variable values.
            validate: Whether to validate variables before rendering.
        
        Returns:
            Rendered prompt string.
        
        Raises:
            ValueError: If validation fails and validate is True.
        """
        if validate:
            self.validate_variables(variables)
        
        # Replace variable placeholders
        rendered = self.content
        
        for var in self.variables:
            placeholder = f"{{{var.name}}}"
            value = variables.get(var.name, var.default)
            
            if value is not None:
                rendered = rendered.replace(placeholder, str(value))
            else:
                # Remove the placeholder if no value
                rendered = rendered.replace(placeholder, "")
        
        return rendered

    def validate_variables(self, variables: Dict[str, Any]) -> None:
        """
        Validate the given variables against the template.
        
        Args:
            variables: Dictionary of variable values.
        
        Raises:
            ValueError: If validation fails.
        """
        errors = []
        
        for var in self.variables:
            if var.required and var.name not in variables:
                errors.append(f"Missing required variable: {var.name}")
            
            if var.name in variables:
                if not var.validate(variables[var.name]):
                    errors.append(f"Invalid value for variable: {var.name}")
        
        if errors:
            raise ValueError(f"Prompt validation failed: {'; '.join(errors)}")

    def get_variable(self, name: str) -> Optional[PromptVariable]:
        """
        Get a variable by name.
        
        Args:
            name: Name of the variable.
        
        Returns:
            PromptVariable or None if not found.
        """
        for var in self.variables:
            if var.name == name:
                return var
        return None

    def add_variable(self, variable: PromptVariable) -> None:
        """
        Add a variable to the template.
        
        Args:
            variable: Variable to add.
        """
        # Check if variable already exists
        for i, var in enumerate(self.variables):
            if var.name == variable.name:
                self.variables[i] = variable
                return
        
        self.variables.append(variable)
        self.updated_at = datetime.utcnow()

    def remove_variable(self, name: str) -> bool:
        """
        Remove a variable from the template.
        
        Args:
            name: Name of the variable to remove.
        
        Returns:
            True if variable was removed, False if not found.
        """
        for i, var in enumerate(self.variables):
            if var.name == name:
                del self.variables[i]
                self.updated_at = datetime.utcnow()
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "content": self.content,
            "variables": [v.to_dict() for v in self.variables],
            "prompt_type": self.prompt_type.value,
            "format": self.format.value,
            "description": self.description,
            "examples": self.examples,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create from dictionary."""
        prompt_type = PromptType.CUSTOM
        if "prompt_type" in data and data["prompt_type"]:
            try:
                prompt_type = PromptType(data["prompt_type"])
            except ValueError:
                pass
        
        format_ = PromptFormat.TEXT
        if "format" in data and data["format"]:
            try:
                format_ = PromptFormat(data["format"])
            except ValueError:
                pass
        
        return cls(
            template_id=data.get("template_id", ""),
            name=data.get("name", ""),
            content=data.get("content", ""),
            variables=[PromptVariable.from_dict(v) for v in data.get("variables", [])],
            prompt_type=prompt_type,
            format=format_,
            description=data.get("description", ""),
            examples=data.get("examples", []),
            tags=data.get("tags", []),
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PromptTemplate("
            f"id={self.template_id}, "
            f"name={self.name}, "
            f"variables={len(self.variables)})"
        )
