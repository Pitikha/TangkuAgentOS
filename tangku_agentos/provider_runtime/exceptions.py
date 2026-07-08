"""Exceptions for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations


class ProviderRuntimeError(Exception):
    """Base exception for the provider runtime."""


# --- Provider Exceptions ---
class ProviderError(ProviderRuntimeError):
    """Base exception for provider-related errors."""


class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not found."""


class ProviderAlreadyExistsError(ProviderError):
    """Raised when a provider already exists."""


class ProviderInitializationError(ProviderError):
    """Raised when a provider fails to initialize."""


class ProviderConnectionError(ProviderError):
    """Raised when a provider fails to connect."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderCapabilityError(ProviderError):
    """Raised when a provider lacks a required capability."""


class ProviderDisabledError(ProviderError):
    """Raised when a provider is disabled."""


# --- Request Exceptions ---
class RequestError(ProviderRuntimeError):
    """Base exception for request-related errors."""


class InvalidRequestError(RequestError):
    """Raised when a request is invalid."""


class RequestTimeoutError(RequestError):
    """Raised when a request times out."""


class RequestRateLimitedError(RequestError):
    """Raised when a request is rate-limited."""


class RequestFailedError(RequestError):
    """Raised when a request fails."""


# --- Plugin Exceptions ---
class PluginError(ProviderRuntimeError):
    """Base exception for plugin-related errors."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin is not found."""


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""


class PluginInitializationError(PluginError):
    """Raised when a plugin fails to initialize."""


# --- Key Management Exceptions ---
class KeyError(ProviderRuntimeError):
    """Base exception for key-related errors."""


class KeyNotFoundError(KeyError):
    """Raised when an API key is not found."""


class InvalidKeyError(KeyError):
    """Raised when an API key is invalid."""


class KeyStorageError(KeyError):
    """Raised when key storage fails."""


class KeyEncryptionError(KeyError):
    """Raised when key encryption/decryption fails."""


# --- Routing Exceptions ---
class RoutingError(ProviderRuntimeError):
    """Base exception for routing-related errors."""


class NoProviderAvailableError(RoutingError):
    """Raised when no provider is available for a request."""


class RoutingPolicyError(RoutingError):
    """Raised when a routing policy is invalid."""


class LoadBalancingError(RoutingError):
    """Raised when load balancing fails."""


# --- Health Exceptions ---
class HealthError(ProviderRuntimeError):
    """Base exception for health-related errors."""


class HealthCheckError(HealthError):
    """Raised when a health check fails."""


class ProviderUnhealthyError(HealthError):
    """Raised when a provider is unhealthy."""


# --- Retry Exceptions ---
class RetryError(ProviderRuntimeError):
    """Base exception for retry-related errors."""


class MaxRetriesExceededError(RetryError):
    """Raised when max retries are exceeded."""


# --- Rate Limit Exceptions ---
class RateLimitError(ProviderRuntimeError):
    """Base exception for rate limit-related errors."""


class RateLimitExceededError(RateLimitError):
    """Raised when rate limit is exceeded."""


# --- Session Exceptions ---
class SessionError(ProviderRuntimeError):
    """Base exception for session-related errors."""


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""


class SessionExpiredError(SessionError):
    """Raised when a session expires."""


# --- Benchmark Exceptions ---
class BenchmarkError(ProviderRuntimeError):
    """Base exception for benchmark-related errors."""


class BenchmarkFailedError(BenchmarkError):
    """Raised when a benchmark fails."""


# --- Configuration Exceptions ---
class ConfigurationError(ProviderRuntimeError):
    """Base exception for configuration-related errors."""


class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration is invalid."""


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""


# --- Security Exceptions ---
class SecurityError(ProviderRuntimeError):
    """Base exception for security-related errors."""


class PermissionDeniedError(SecurityError):
    """Raised when permission is denied."""


class InvalidInputError(SecurityError):
    """Raised when input validation fails."""


# --- Streaming Exceptions ---
class StreamingError(ProviderRuntimeError):
    """Base exception for streaming-related errors."""


class StreamConnectionError(StreamingError):
    """Raised when a streaming connection fails."""


class StreamTimeoutError(StreamingError):
    """Raised when a stream times out."""
