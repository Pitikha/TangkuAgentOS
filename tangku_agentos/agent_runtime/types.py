"""
TangkuAgentOS Agent Runtime - Type Definitions

This module defines all type aliases and custom types used throughout the Agent Runtime.

Type Definitions:
- Agent identifiers (AgentID, AgentName, AgentType, AgentVersion)
- Component identifiers (SkillID, ToolID, TaskID, MemoryID, KnowledgeID, PlanID, ReasoningID)
- Capability types
- Permission types
- Task types
- Memory types
- Knowledge types

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from datetime import datetime


# =============================================================================
# AGENT IDENTIFIERS
# =============================================================================

AgentID = str
"""Unique identifier for an agent. Format: agent_{uuid} or custom string."""

AgentName = str
"""Human-readable name for an agent."""

AgentType = str
"""Type of agent (e.g., 'researcher', 'coder', 'analyst', 'coordinator')."""

AgentVersion = str
"""Version of the agent. Format: X.Y.Z or semantic version."""

AgentInstanceID = str
"""Unique identifier for a specific agent instance."""


# =============================================================================
# COMPONENT IDENTIFIERS
# =============================================================================

SkillID = str
"""Unique identifier for a skill."""

ToolID = str
"""Unique identifier for a tool."""

TaskID = str
"""Unique identifier for a task."""

MemoryID = str
"""Unique identifier for a memory entry."""

KnowledgeID = str
"""Unique identifier for a knowledge entry."""

PlanID = str
"""Unique identifier for a plan."""

ReasoningID = str
"""Unique identifier for a reasoning session."""

ConversationID = str
"""Unique identifier for a conversation."""

SessionID = str
"""Unique identifier for a session."""


# =============================================================================
# CAPABILITY TYPES
# =============================================================================

class Capability(Enum):
    """
    Standard agent capabilities.
    
    These represent the fundamental abilities an agent can have.
    Custom capabilities can also be defined.
    """

    # Core capabilities
    REASONING = auto()
    PLANNING = auto()
    MEMORY = auto()
    KNOWLEDGE = auto()
    COMMUNICATION = auto()
    EXECUTION = auto()
    LEARNING = auto()
    SELF_IMPROVEMENT = auto()

    # Domain-specific capabilities
    CODING = auto()
    RESEARCH = auto()
    WRITING = auto()
    ANALYSIS = auto()
    DEBUGGING = auto()
    TESTING = auto()
    DOCUMENTATION = auto()
    REVIEW = auto()

    # Tool capabilities
    TERMINAL = auto()
    GIT = auto()
    WEB_SEARCH = auto()
    FILE_SYSTEM = auto()
    DATABASE = auto()
    API_CALLS = auto()
    BROWSER = auto()

    # Special capabilities
    MULTI_AGENT = auto()
    PARALLEL_EXECUTION = auto()
    LONG_RUNNING = auto()
    REAL_TIME = auto()
    SCHEDULED = auto()

    # Memory capabilities
    SHORT_TERM_MEMORY = auto()
    LONG_TERM_MEMORY = auto()
    SEMANTIC_MEMORY = auto()
    EPISODIC_MEMORY = auto()
    WORKING_MEMORY = auto()

    # Knowledge capabilities
    KNOWLEDGE_SEARCH = auto()
    KNOWLEDGE_INDEXING = auto()
    KNOWLEDGE_RETRIEVAL = auto()
    KNOWLEDGE_UPDATES = auto()

    # Planning capabilities
    GOAL_DECOMPOSITION = auto()
    TASK_PLANNING = auto()
    DEPENDENCY_GRAPHS = auto()
    PROGRESS_TRACKING = auto()
    REPLANNING = auto()

    # Reasoning capabilities
    REFLECTION = auto()
    DECISION_MAKING = auto()
    MULTI_STEP_REASONING = auto()
    VERIFICATION = auto()
    SELF_EVALUATION = auto()
    CONFIDENCE_ESTIMATION = auto()


# =============================================================================
# AGENT TYPES
# =============================================================================

class AgentType(Enum):
    """
    Standard agent types.
    
    These represent common agent archetypes. Custom types can also be defined.
    """

    # General purpose
    GENERAL = "general"
    ASSISTANT = "assistant"
    CHATBOT = "chatbot"

    # Specialized
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    CODER = "coder"
    WRITER = "writer"
    DEBUGGER = "debugger"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    REVIEWER = "reviewer"

    # Coordination
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ORCHESTRATOR = "orchestrator"

    # Domain-specific
    DATA_ANALYST = "data_analyst"
    SOFTWARE_ENGINEER = "software_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    SECURITY_ANALYST = "security_analyst"
    SYSTEM_ARCHITECT = "system_architect"
    PROJECT_MANAGER = "project_manager"

    # Multi-agent
    TEAM_LEADER = "team_leader"
    TEAM_MEMBER = "team_member"
    NEGOTIATOR = "negotiator"
    MEDIATOR = "mediator"


# =============================================================================
# AGENT STATUS
# =============================================================================

class AgentStatus(Enum):
    """
    Runtime status of an agent.
    
    This represents the current operational state of the agent.
    """

    CREATED = auto()
    INITIALIZING = auto()
    IDLE = auto()
    ACTIVE = auto()
    BUSY = auto()
    PAUSED = auto()
    STOPPED = auto()
    FAILED = auto()
    RECOVERING = auto()
    DESTROYED = auto()


# =============================================================================
# AGENT LIFECYCLE STATES
# =============================================================================

class AgentLifecycleState(Enum):
    """
    Lifecycle states of an agent.
    
    These represent the complete lifecycle of an agent from creation to destruction.
    """

    # Initial states
    CREATED = auto()
    INITIALIZING = auto()

    # Active states
    IDLE = auto()
    THINKING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    WAITING = auto()
    COMMUNICATING = auto()
    LEARNING = auto()
    SLEEPING = auto()

    # Inactive states
    PAUSED = auto()
    STOPPED = auto()
    FAILED = auto()
    RECOVERING = auto()
    DESTROYED = auto()


# =============================================================================
# TASK TYPES
# =============================================================================

class TaskType(Enum):
    """
    Types of tasks an agent can execute.
    """

    # Basic types
    SIMPLE = auto()
    COMPLEX = auto()
    COMPOSITE = auto()

    # Execution types
    SYNCHRONOUS = auto()
    ASYNCHRONOUS = auto()
    PARALLEL = auto()
    SEQUENTIAL = auto()

    # Scheduling types
    IMMEDIATE = auto()
    SCHEDULED = auto()
    PERIODIC = auto()
    DELAYED = auto()

    # Priority types
    LOW_PRIORITY = auto()
    NORMAL_PRIORITY = auto()
    HIGH_PRIORITY = auto()
    CRITICAL_PRIORITY = auto()


# =============================================================================
# TASK STATUS
# =============================================================================

class TaskStatus(Enum):
    """
    Status of an agent task.
    """

    PENDING = auto()
    QUEUED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()
    RETRYING = auto()


# =============================================================================
# MEMORY TYPES
# =============================================================================

class MemoryType(Enum):
    """
    Types of agent memory.
    """

    SHORT_TERM = auto()
    LONG_TERM = auto()
    WORKING = auto()
    CONVERSATION = auto()
    SEMANTIC = auto()
    EPISODIC = auto()
    PROCEDURAL = auto()


# =============================================================================
# KNOWLEDGE TYPES
# =============================================================================

class KnowledgeType(Enum):
    """
    Types of knowledge an agent can access.
    """

    DOCUMENTATION = auto()
    CODE = auto()
    DATA = auto()
    CONFIGURATION = auto()
    BEST_PRACTICES = auto()
    PATTERNS = auto()
    EXAMPLES = auto()
    REFERENCE = auto()


# =============================================================================
# PERMISSION TYPES
# =============================================================================

class PermissionType(Enum):
    """
    Types of permissions for agents.
    """

    # Resource permissions
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    DELETE = auto()
    LIST = auto()

    # Agent permissions
    CREATE_AGENT = auto()
    DESTROY_AGENT = auto()
    START_AGENT = auto()
    STOP_AGENT = auto()
    PAUSE_AGENT = auto()
    RESUME_AGENT = auto()
    CONFIGURE_AGENT = auto()

    # Tool permissions
    USE_TOOL = auto()
    CONFIGURE_TOOL = auto()
    INSTALL_TOOL = auto()
    REMOVE_TOOL = auto()

    # Skill permissions
    USE_SKILL = auto()
    INSTALL_SKILL = auto()
    REMOVE_SKILL = auto()

    # System permissions
    ACCESS_MEMORY = auto()
    ACCESS_KNOWLEDGE = auto()
    ACCESS_PLANNING = auto()
    ACCESS_REASONING = auto()
    COMMUNICATE = auto()
    BROADCAST = auto()


# =============================================================================
# COMMUNICATION TYPES
# =============================================================================

class CommunicationType(Enum):
    """
    Types of agent communication.
    """

    # Direct communication
    DIRECT = auto()
    REQUEST = auto()
    RESPONSE = auto()

    # Broadcast communication
    BROADCAST = auto()
    NOTIFICATION = auto()

    # Group communication
    GROUP = auto()
    TEAM = auto()

    # Asynchronous communication
    ASYNC = auto()
    STREAM = auto()


# =============================================================================
# SCHEDULING TYPES
# =============================================================================

class ScheduleType(Enum):
    """
    Types of agent scheduling.
    """

    IMMEDIATE = auto()
    DELAYED = auto()
    PERIODIC = auto()
    CRON = auto()
    EVENT_TRIGGERED = auto()
    DEPENDENCY_TRIGGERED = auto()


# =============================================================================
# RECOVERY TYPES
# =============================================================================

class RecoveryType(Enum):
    """
    Types of agent recovery.
    """

    RESTART = auto()
    RECREATE = auto()
    RESUME = auto()
    MIGRATE = auto()
    ROLLBACK = auto()


# =============================================================================
# HEALTH STATUS
# =============================================================================

class HealthStatus(Enum):
    """
    Health status of an agent.
    """

    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    CRITICAL = auto()


# =============================================================================
# AGENT PROFILE TYPES
# =============================================================================

class AgentProfileType(Enum):
    """
    Standard agent profile types.
    """

    DEFAULT = "default"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    GENERALIST = "generalist"


# =============================================================================
# SKILL CATEGORIES
# =============================================================================

class SkillCategory(Enum):
    """
    Categories of agent skills.
    """

    CORE = auto()
    CODING = auto()
    RESEARCH = auto()
    WRITING = auto()
    ANALYSIS = auto()
    PLANNING = auto()
    COMMUNICATION = auto()
    TOOL_USE = auto()
    PROBLEM_SOLVING = auto()
    CREATIVITY = auto()


# =============================================================================
# TOOL CATEGORIES
# =============================================================================

class ToolCategory(Enum):
    """
    Categories of agent tools.
    """

    SYSTEM = auto()
    DEVELOPMENT = auto()
    ANALYSIS = auto()
    DATA = auto()
    NETWORK = auto()
    FILE = auto()
    DATABASE = auto()
    API = auto()
    CUSTOM = auto()


# =============================================================================
# REASONING MODES
# =============================================================================

class ReasoningMode(Enum):
    """
    Modes of agent reasoning.
    """

    FAST = auto()
    BALANCED = auto()
    THOROUGH = auto()
    CREATIVE = auto()
    ANALYTICAL = auto()
    CRITICAL = auto()


# =============================================================================
# PLANNING STRATEGIES
# =============================================================================

class PlanningStrategy(Enum):
    """
    Strategies for agent planning.
    """

    SIMPLE = auto()
    HIERARCHICAL = auto()
    PARALLEL = auto()
    SEQUENTIAL = auto()
    OPTIMIZED = auto()
    ADAPTIVE = auto()


# =============================================================================
# EXECUTION MODES
# =============================================================================

class ExecutionMode(Enum):
    """
    Modes of agent execution.
    """

    SYNCHRONOUS = auto()
    ASYNCHRONOUS = auto()
    PARALLEL = auto()
    SEQUENTIAL = auto()
    BATCH = auto()
    STREAMING = auto()


# =============================================================================
# AGENT EVENT TYPES
# =============================================================================

class AgentEventType(Enum):
    """
    Types of agent events.
    """

    # Lifecycle events
    CREATED = auto()
    INITIALIZED = auto()
    STARTED = auto()
    PAUSED = auto()
    RESUMED = auto()
    STOPPED = auto()
    FAILED = auto()
    RECOVERED = auto()
    DESTROYED = auto()

    # Task events
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_CANCELLED = auto()

    # Communication events
    MESSAGE_SENT = auto()
    MESSAGE_RECEIVED = auto()
    COMMUNICATION_ERROR = auto()

    # Memory events
    MEMORY_UPDATED = auto()
    MEMORY_RETRIEVED = auto()
    MEMORY_CLEARED = auto()

    # Knowledge events
    KNOWLEDGE_SEARCHED = auto()
    KNOWLEDGE_RETRIEVED = auto()
    KNOWLEDGE_UPDATED = auto()

    # Planning events
    PLAN_CREATED = auto()
    PLAN_EXECUTED = auto()
    PLAN_COMPLETED = auto()
    PLAN_FAILED = auto()

    # Reasoning events
    REASONING_STARTED = auto()
    REASONING_COMPLETED = auto()
    REASONING_FAILED = auto()

    # Health events
    HEALTH_CHECK = auto()
    HEALTH_DEGRADED = auto()
    HEALTH_RECOVERED = auto()


# =============================================================================
# TYPE ALIASES
# =============================================================================

# Agent identifiers
AgentIDList = List[AgentID]
AgentIDSet = Set[AgentID]
AgentNameList = List[AgentName]
AgentTypeList = List[AgentType]

# Capabilities
CapabilityList = List[Capability]
CapabilitySet = Set[Capability]

# Task identifiers
TaskIDList = List[TaskID]
TaskIDSet = Set[TaskID]

# Skill identifiers
SkillIDList = List[SkillID]
SkillIDSet = Set[SkillID]

# Tool identifiers
ToolIDList = List[ToolID]
ToolIDSet = Set[ToolID]

# Memory identifiers
MemoryIDList = List[MemoryID]
MemoryIDSet = Set[MemoryID]

# Knowledge identifiers
KnowledgeIDList = List[KnowledgeID]
KnowledgeIDSet = Set[KnowledgeID]

# Timestamps
Timestamp = datetime
TimestampList = List[datetime]

# Metadata
Metadata = Dict[str, Any]
MetadataList = List[Dict[str, Any]]

# Configuration
Config = Dict[str, Any]
ConfigList = List[Dict[str, Any]]

# Results
Result = Any
ResultList = List[Any]

# Errors
Error = Exception
ErrorList = List[Exception]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_agent_id(name: Optional[str] = None) -> AgentID:
    """
    Generate a unique agent ID.
    
    Args:
        name: Optional name to include in the ID.
        
    Returns:
        Unique agent ID.
    """
    if name:
        return f"agent_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
    return f"agent_{uuid.uuid4().hex[:12]}"


def generate_task_id(agent_id: Optional[AgentID] = None) -> TaskID:
    """
    Generate a unique task ID.
    
    Args:
        agent_id: Optional agent ID to include in the task ID.
        
    Returns:
        Unique task ID.
    """
    if agent_id:
        return f"task_{agent_id}_{uuid.uuid4().hex[:8]}"
    return f"task_{uuid.uuid4().hex[:12]}"


def generate_skill_id(name: str) -> SkillID:
    """
    Generate a unique skill ID.
    
    Args:
        name: Name of the skill.
        
    Returns:
        Unique skill ID.
    """
    return f"skill_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"


def generate_tool_id(name: str) -> ToolID:
    """
    Generate a unique tool ID.
    
    Args:
        name: Name of the tool.
        
    Returns:
        Unique tool ID.
    """
    return f"tool_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"


def generate_memory_id(agent_id: AgentID, index: int = 0) -> MemoryID:
    """
    Generate a unique memory ID.
    
    Args:
        agent_id: ID of the agent.
        index: Optional index for ordering.
        
    Returns:
        Unique memory ID.
    """
    return f"memory_{agent_id}_{index}_{uuid.uuid4().hex[:8]}"


def generate_knowledge_id(source: str, index: int = 0) -> KnowledgeID:
    """
    Generate a unique knowledge ID.
    
    Args:
        source: Source of the knowledge.
        index: Optional index for ordering.
        
    Returns:
        Unique knowledge ID.
    """
    return f"knowledge_{source.lower().replace(' ', '_')}_{index}_{uuid.uuid4().hex[:8]}"


def generate_plan_id(agent_id: AgentID, index: int = 0) -> PlanID:
    """
    Generate a unique plan ID.
    
    Args:
        agent_id: ID of the agent.
        index: Optional index for ordering.
        
    Returns:
        Unique plan ID.
    """
    return f"plan_{agent_id}_{index}_{uuid.uuid4().hex[:8]}"


def generate_reasoning_id(agent_id: AgentID, index: int = 0) -> ReasoningID:
    """
    Generate a unique reasoning ID.
    
    Args:
        agent_id: ID of the agent.
        index: Optional index for ordering.
        
    Returns:
        Unique reasoning ID.
    """
    return f"reasoning_{agent_id}_{index}_{uuid.uuid4().hex[:8]}"


# =============================================================================
# CONSTANTS
# =============================================================================

# Default values
DEFAULT_AGENT_TIMEOUT = 300.0  # 5 minutes
DEFAULT_TASK_TIMEOUT = 60.0  # 1 minute
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_PARALLEL_TASKS = 10
DEFAULT_MAX_AGENTS = 100
DEFAULT_MAX_MEMORY_ENTRIES = 1000
DEFAULT_MAX_KNOWLEDGE_ENTRIES = 10000

# Agent limits
MAX_AGENT_NAME_LENGTH = 100
MAX_AGENT_DESCRIPTION_LENGTH = 1000
MAX_AGENT_CAPABILITIES = 50
MAX_AGENT_SKILLS = 100
MAX_AGENT_TOOLS = 50

# Task limits
MAX_TASK_NAME_LENGTH = 200
MAX_TASK_DESCRIPTION_LENGTH = 2000
MAX_TASK_PARAMETERS = 100
MAX_TASK_RETRIES = 5

# Memory limits
MAX_MEMORY_CONTENT_LENGTH = 100000  # 100KB
MAX_MEMORY_METADATA_LENGTH = 1000

# Knowledge limits
MAX_KNOWLEDGE_CONTENT_LENGTH = 1000000  # 1MB
MAX_KNOWLEDGE_METADATA_LENGTH = 5000

# Communication limits
MAX_MESSAGE_SIZE = 1000000  # 1MB
MAX_CONVERSATION_LENGTH = 100  # Messages

# Scheduling limits
MAX_SCHEDULED_TASKS = 1000
MAX_PARALLEL_AGENTS = 20
