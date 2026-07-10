"""
AI Foundation Framework - Guardrail Manager

This module provides the GuardrailManager class for implementing AI safety guardrails.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class GuardrailType(Enum):
    """Types of guardrails."""
    PROMPT_INJECTION = auto()
    JAILBREAK = auto()
    SENSITIVE_DATA = auto()
    CONTENT_FILTER = auto()
    PERMISSION = auto()
    RATE_LIMIT = auto()
    INPUT_VALIDATION = auto()
    OUTPUT_VALIDATION = auto()
    CUSTOM = auto()


class GuardrailAction(Enum):
    """Actions to take when a guardrail is triggered."""
    ALLOW = auto()
    BLOCK = auto()
    WARN = auto()
    MODIFY = auto()
    REDACT = auto()
    LOG = auto()


@dataclass
class Guardrail:
    """
    Represents a guardrail rule.
    
    Attributes:
        guardrail_id: Unique identifier for the guardrail.
        name: Human-readable name for the guardrail.
        guardrail_type: Type of the guardrail.
        description: Description of what the guardrail does.
        patterns: List of patterns to match.
        blocked_topics: List of blocked topics.
        sensitive_patterns: List of sensitive data patterns.
        action: Action to take when triggered.
        severity: Severity level (1-10).
        enabled: Whether the guardrail is enabled.
        metadata: Additional metadata.
    """

    guardrail_id: str
    name: str
    guardrail_type: GuardrailType = GuardrailType.CUSTOM
    description: str = ""
    patterns: List[str] = field(default_factory=list)
    blocked_topics: List[str] = field(default_factory=list)
    sensitive_patterns: List[str] = field(default_factory=list)
    action: GuardrailAction = GuardrailAction.BLOCK
    severity: int = 5
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, text: str) -> bool:
        """
        Check if the guardrail matches the given text.
        
        Args:
            text: Text to check.
        
        Returns:
            True if the guardrail matches, False otherwise.
        """
        if not self.enabled:
            return False
        
        text_lower = text.lower()
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                return True
        
        # Check blocked topics
        for topic in self.blocked_topics:
            if topic.lower() in text_lower:
                return True
        
        # Check sensitive patterns
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "guardrail_id": self.guardrail_id,
            "name": self.name,
            "guardrail_type": self.guardrail_type.value,
            "description": self.description,
            "patterns": self.patterns,
            "blocked_topics": self.blocked_topics,
            "sensitive_patterns": self.sensitive_patterns,
            "action": self.action.value,
            "severity": self.severity,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Guardrail":
        """Create from dictionary."""
        guardrail_type = GuardrailType.CUSTOM
        if "guardrail_type" in data and data["guardrail_type"]:
            try:
                guardrail_type = GuardrailType(data["guardrail_type"])
            except ValueError:
                pass

        action = GuardrailAction.BLOCK
        if "action" in data and data["action"]:
            try:
                action = GuardrailAction(data["action"])
            except ValueError:
                pass

        return cls(
            guardrail_id=data.get("guardrail_id", ""),
            name=data.get("name", ""),
            guardrail_type=guardrail_type,
            description=data.get("description", ""),
            patterns=data.get("patterns", []),
            blocked_topics=data.get("blocked_topics", []),
            sensitive_patterns=data.get("sensitive_patterns", []),
            action=action,
            severity=data.get("severity", 5),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GuardrailResult:
    """
    Result from a guardrail check.
    
    Attributes:
        guardrail_id: ID of the guardrail that was triggered.
        guardrail_name: Name of the guardrail.
        guardrail_type: Type of the guardrail.
        triggered: Whether the guardrail was triggered.
        action: Action taken by the guardrail.
        severity: Severity level.
        message: Message from the guardrail.
        matched_text: Text that matched the guardrail.
        timestamp: When the check was performed.
    """

    guardrail_id: str
    guardrail_name: str
    guardrail_type: GuardrailType
    triggered: bool = False
    action: GuardrailAction = GuardrailAction.ALLOW
    severity: int = 0
    message: str = ""
    matched_text: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "guardrail_id": self.guardrail_id,
            "guardrail_name": self.guardrail_name,
            "guardrail_type": self.guardrail_type.value,
            "triggered": self.triggered,
            "action": self.action.value,
            "severity": self.severity,
            "message": self.message,
            "matched_text": self.matched_text,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class GuardrailManagerMetrics:
    """Metrics for the guardrail manager."""
    checks: int = 0
    triggers: int = 0
    blocks: int = 0
    warnings: int = 0
    modifications: int = 0
    redactions: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checks": self.checks,
            "triggers": self.triggers,
            "blocks": self.blocks,
            "warnings": self.warnings,
            "modifications": self.modifications,
            "redactions": self.redactions,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class GuardrailManager:
    """
    Manager for AI safety guardrails.
    
    This class implements comprehensive safety guardrails for AI operations,
    including prompt injection detection, jailbreak detection, sensitive
    data detection, content filtering, and permission enforcement.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import GuardrailManager
        >>> 
        >>> # Create manager
        >>> manager = GuardrailManager()
        >>> 
        >>> # Check a prompt
        >>> result = await manager.check_prompt("Tell me how to build a bomb")
        >>> 
        >>> # Check a response
        >>> result = await manager.check_response(response)
        >>> 
        >>> # Add a custom guardrail
        >>> await manager.add_guardrail(guardrail)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the guardrail manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._guardrails: Dict[str, Guardrail] = {}
        self._metrics = GuardrailManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("GuardrailManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> GuardrailManagerMetrics:
        """Get the guardrail manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the guardrail manager.
        """
        if self._initialized:
            logger.warning("GuardrailManager already initialized")
            return
        
        logger.info("Initializing GuardrailManager...")
        
        # Load default guardrails
        await self._load_default_guardrails()
        
        self._initialized = True
        logger.info("GuardrailManager initialized successfully")

    async def start(self) -> None:
        """
        Start the guardrail manager.
        """
        if self._started:
            logger.warning("GuardrailManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting GuardrailManager...")
        
        self._started = True
        logger.info("GuardrailManager started successfully")

    async def stop(self) -> None:
        """
        Stop the guardrail manager.
        """
        if not self._started:
            logger.warning("GuardrailManager not started")
            return
        
        logger.info("Stopping GuardrailManager...")
        
        self._started = False
        logger.info("GuardrailManager stopped successfully")

    async def _load_default_guardrails(self) -> None:
        """Load default guardrails."""
        # Prompt injection guardrail
        injection_guardrail = Guardrail(
            guardrail_id="prompt_injection",
            name="Prompt Injection Detection",
            guardrail_type=GuardrailType.PROMPT_INJECTION,
            description="Detects attempts to inject malicious prompts",
            patterns=[
                "ignore previous instructions",
                "forget everything before",
                "disregard all prior",
                "pretend you are",
                "act as if",
                "you are now",
                "your new role is",
                "from now on",
            ],
            action=GuardrailAction.BLOCK,
            severity=10,
            enabled=self._config.guardrails.prompt_injection_detection,
        )
        await self.add_guardrail(injection_guardrail)

        # Jailbreak guardrail
        jailbreak_guardrail = Guardrail(
            guardrail_id="jailbreak",
            name="Jailbreak Detection",
            guardrail_type=GuardrailType.JAILBREAK,
            description="Detects attempts to bypass AI safety measures",
            patterns=[
                "DAN mode",
                "developer mode",
                "jailbreak",
                "bypass safety",
                "ignore safety",
                "no restrictions",
                "unrestricted",
                "do anything",
            ],
            action=GuardrailAction.BLOCK,
            severity=10,
            enabled=self._config.guardrails.jailbreak_detection,
        )
        await self.add_guardrail(jailbreak_guardrail)

        # Sensitive data guardrail
        sensitive_guardrail = Guardrail(
            guardrail_id="sensitive_data",
            name="Sensitive Data Detection",
            guardrail_type=GuardrailType.SENSITIVE_DATA,
            description="Detects sensitive personal information",
            sensitive_patterns=[
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{10,15}\b',  # Phone numbers
                r'\b(?:password|passwd|pwd)\b.*\b\w{8,}\b',  # Passwords
            ],
            action=GuardrailAction.REDACT,
            severity=8,
            enabled=self._config.guardrails.sensitive_data_detection,
        )
        await self.add_guardrail(sensitive_guardrail)

        # Content filter guardrail
        content_guardrail = Guardrail(
            guardrail_id="content_filter",
            name="Content Filter",
            guardrail_type=GuardrailType.CONTENT_FILTER,
            description="Filters inappropriate content",
            blocked_topics=self._config.guardrails.blocked_topics,
            action=GuardrailAction.BLOCK,
            severity=9,
            enabled=self._config.guardrails.content_filtering_enabled,
        )
        await self.add_guardrail(content_guardrail)

    async def add_guardrail(self, guardrail: Guardrail) -> str:
        """
        Add a guardrail.
        
        Args:
            guardrail: Guardrail to add.
        
        Returns:
            Guardrail ID.
        
        Raises:
            ValueError: If guardrail with same ID already exists.
        """
        async with self._lock:
            if guardrail.guardrail_id in self._guardrails:
                raise ValueError(f"Guardrail with ID {guardrail.guardrail_id} already exists")
            
            self._guardrails[guardrail.guardrail_id] = guardrail
            logger.debug(f"Guardrail added: {guardrail.guardrail_id}")
            return guardrail.guardrail_id

    async def remove_guardrail(self, guardrail_id: str) -> bool:
        """
        Remove a guardrail.
        
        Args:
            guardrail_id: ID of the guardrail to remove.
        
        Returns:
            True if guardrail was removed, False if not found.
        """
        async with self._lock:
            if guardrail_id not in self._guardrails:
                return False
            
            del self._guardrails[guardrail_id]
            logger.debug(f"Guardrail removed: {guardrail_id}")
            return True

    async def get_guardrail(self, guardrail_id: str) -> Optional[Guardrail]:
        """
        Get a guardrail by ID.
        
        Args:
            guardrail_id: ID of the guardrail to get.
        
        Returns:
            Guardrail or None if not found.
        """
        return self._guardrails.get(guardrail_id)

    async def list_guardrails(
        self,
        guardrail_type: Optional[GuardrailType] = None,
        enabled: Optional[bool] = None,
    ) -> List[Guardrail]:
        """
        List all guardrails, optionally filtered.
        
        Args:
            guardrail_type: Optional guardrail type to filter by.
            enabled: Optional enabled status to filter by.
        
        Returns:
            List of Guardrail instances.
        """
        guardrails = []
        
        for guardrail in self._guardrails.values():
            if guardrail_type and guardrail.guardrail_type != guardrail_type:
                continue
            if enabled is not None and guardrail.enabled != enabled:
                continue
            guardrails.append(guardrail)
        
        return guardrails

    async def check_prompt(self, prompt: str) -> List[GuardrailResult]:
        """
        Check a prompt against all guardrails.
        
        Args:
            prompt: Prompt to check.
        
        Returns:
            List of GuardrailResult for each triggered guardrail.
        """
        return await self._check_text(prompt, GuardrailType.PROMPT_INJECTION)

    async def check_response(self, response: "AIResponse") -> List[GuardrailResult]:
        """
        Check a response against all guardrails.
        
        Args:
            response: AIResponse to check.
        
        Returns:
            List of GuardrailResult for each triggered guardrail.
        """
        if not response.content:
            return []
        
        return await self._check_text(response.content, GuardrailType.OUTPUT_VALIDATION)

    async def check_request(self, request: "AIRequest") -> List[GuardrailResult]:
        """
        Check an AI request against all guardrails.
        
        Args:
            request: AIRequest to check.
        
        Returns:
            List of GuardrailResult for each triggered guardrail.
        """
        results = []
        
        # Check prompt
        if request.prompt:
            results.extend(await self.check_prompt(request.prompt))
        
        # Check messages
        for message in request.messages:
            if hasattr(message, 'content') and message.content:
                results.extend(await self.check_prompt(str(message.content)))
        
        return results

    async def _check_text(self, text: str, primary_type: Optional[GuardrailType] = None) -> List[GuardrailResult]:
        """
        Check text against all guardrails.
        
        Args:
            text: Text to check.
            primary_type: Optional primary guardrail type to check.
        
        Returns:
            List of GuardrailResult for each triggered guardrail.
        """
        self._metrics.checks += 1
        
        results = []
        
        for guardrail in self._guardrails.values():
            if not guardrail.enabled:
                continue
            
            # Check if this guardrail type matches the primary type
            if primary_type and guardrail.guardrail_type != primary_type:
                continue
            
            # Check if the guardrail matches
            if guardrail.matches(text):
                result = GuardrailResult(
                    guardrail_id=guardrail.guardrail_id,
                    guardrail_name=guardrail.name,
                    guardrail_type=guardrail.guardrail_type,
                    triggered=True,
                    action=guardrail.action,
                    severity=guardrail.severity,
                    message=f"Guardrail triggered: {guardrail.name}",
                    matched_text=text,
                )
                
                results.append(result)
                self._metrics.triggers += 1
                
                # Update action-specific metrics
                if guardrail.action == GuardrailAction.BLOCK:
                    self._metrics.blocks += 1
                elif guardrail.action == GuardrailAction.WARN:
                    self._metrics.warnings += 1
                elif guardrail.action == GuardrailAction.MODIFY:
                    self._metrics.modifications += 1
                elif guardrail.action == GuardrailAction.REDACT:
                    self._metrics.redactions += 1
        
        return results

    async def enforce_guardrails(
        self,
        request: "AIRequest",
        response: Optional["AIResponse"] = None,
    ) -> Tuple[bool, List[GuardrailResult]]:
        """
        Enforce guardrails on a request and optional response.
        
        Args:
            request: AIRequest to check.
            response: Optional AIResponse to check.
        
        Returns:
            Tuple of (is_allowed, list of guardrail results).
        """
        results = []
        
        # Check request
        request_results = await self.check_request(request)
        results.extend(request_results)
        
        # Check if any request guardrails block the request
        for result in request_results:
            if result.action == GuardrailAction.BLOCK:
                return False, results
        
        # Check response if provided
        if response:
            response_results = await self.check_response(response)
            results.extend(response_results)
            
            # Check if any response guardrails block the response
            for result in response_results:
                if result.action == GuardrailAction.BLOCK:
                    return False, results
        
        return True, results

    async def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by applying all redaction guardrails.
        
        Args:
            text: Text to sanitize.
        
        Returns:
            Sanitized text.
        """
        # Check for sensitive data patterns
        for guardrail in self._guardrails.values():
            if (guardrail.enabled and 
                guardrail.action == GuardrailAction.REDACT and
                guardrail.sensitive_patterns):
                
                for pattern in guardrail.sensitive_patterns:
                    text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        
        return text

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the guardrail manager.
        
        Returns:
            Dictionary with guardrail manager information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "guardrails": len(self._guardrails),
            "metrics": self._metrics.to_dict(),
            "config": {
                "prompt_injection_detection": self._config.guardrails.prompt_injection_detection,
                "jailbreak_detection": self._config.guardrails.jailbreak_detection,
                "sensitive_data_detection": self._config.guardrails.sensitive_data_detection,
                "content_filtering_enabled": self._config.guardrails.content_filtering_enabled,
                "permission_check_enabled": self._config.guardrails.permission_check_enabled,
                "blocked_topics": self._config.guardrails.blocked_topics,
            }
        }

    async def reset(self) -> None:
        """
        Reset the guardrail manager.
        
        This method clears all guardrails and resets all state.
        """
        logger.info("Resetting GuardrailManager...")
        
        async with self._lock:
            self._guardrails.clear()
            self._metrics = GuardrailManagerMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("GuardrailManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"GuardrailManager("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"guardrails={len(self._guardrails)})"
        )
