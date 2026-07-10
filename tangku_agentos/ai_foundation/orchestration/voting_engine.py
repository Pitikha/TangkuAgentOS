"""
Voting Engine for TangkuAgentOS AI Foundation Framework.

Implements voting mechanisms for multi-model consensus.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import statistics
from ..models.base_model import AIModel

logger = logging.getLogger(__name__)


@dataclass
class Vote:
    """Represents a vote from a model."""
    model_name: str
    response: Dict[str, Any]
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VotingResult:
    """Result of a voting operation."""
    query: str
    votes: List[Vote]
    consensus: Optional[Dict[str, Any]]
    winning_model: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class VotingEngine:
    """Implements voting mechanisms for multi-model consensus in TangkuAgentOS.

    This class provides methods for collecting votes from multiple models
    and determining consensus based on various voting strategies.
    """

    def __init__(self):
        """Initialize the VotingEngine."""
        logger.info("VotingEngine initialized.")

    async def vote(
        self,
        query: str,
        models: List[AIModel],
        **kwargs: Any,
    ) -> VotingResult:
        """Collect votes from multiple models and determine consensus.

        Args:
            query: The query to vote on.
            models: List of AI models to collect votes from.
            **kwargs: Additional arguments for the AI models.

        Returns:
            VotingResult containing the votes and consensus.
        """
        votes = []
        for model in models:
            try:
                response = await model.chat([{"role": "user", "content": query}])
                score = self._calculate_score(response)
                votes.append(
                    Vote(
                        model_name=model.name,
                        response=response,
                        score=score,
                        metadata={"model": model.name},
                    )
                )
                logger.info(f"Collected vote from model {model.name} with score: {score}")
            except Exception as e:
                votes.append(
                    Vote(
                        model_name=model.name,
                        response={"error": str(e)},
                        score=0.0,
                        metadata={"error": str(e)},
                    )
                )
                logger.error(f"Model {model.name} failed to vote: {e}")

        # Determine consensus
        consensus, winning_model = self._determine_consensus(votes)

        return VotingResult(
            query=query,
            votes=votes,
            consensus=consensus,
            winning_model=winning_model,
            metadata={"total_votes": len(votes)},
        )

    def _calculate_score(self, response: Dict[str, Any]) -> float:
        """Calculate a score for a response.

        Args:
            response: The response to score.

        Returns:
            Score between 0.0 and 1.0.
        """
        if "error" in response:
            return 0.0
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Simple scoring: longer responses get higher scores (up to a point)
        return min(len(content) / 1000.0, 1.0)

    def _determine_consensus(self, votes: List[Vote]) -> tuple:
        """Determine consensus from a list of votes.

        Args:
            votes: List of votes to analyze.

        Returns:
            Tuple of (consensus_response, winning_model_name).
        """
        if not votes:
            return None, None

        # Filter out failed votes
        valid_votes = [vote for vote in votes if vote.score > 0]
        if not valid_votes:
            return None, None

        # Find the vote with the highest score
        winning_vote = max(valid_votes, key=lambda x: x.score)
        return winning_vote.response, winning_vote.model_name

    async def weighted_vote(
        self,
        query: str,
        models: List[AIModel],
        weights: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> VotingResult:
        """Collect weighted votes from multiple models and determine consensus.

        Args:
            query: The query to vote on.
            models: List of AI models to collect votes from.
            weights: Optional dictionary of model weights.
            **kwargs: Additional arguments for the AI models.

        Returns:
            VotingResult containing the weighted votes and consensus.
        """
        weights = weights or {model.name: 1.0 for model in models}
        votes = []

        for model in models:
            try:
                response = await model.chat([{"role": "user", "content": query}])
                score = self._calculate_score(response) * weights.get(model.name, 1.0)
                votes.append(
                    Vote(
                        model_name=model.name,
                        response=response,
                        score=score,
                        metadata={"weight": weights.get(model.name, 1.0)},
                    )
                )
            except Exception as e:
                votes.append(
                    Vote(
                        model_name=model.name,
                        response={"error": str(e)},
                        score=0.0,
                        metadata={"error": str(e)},
                    )
                )

        consensus, winning_model = self._determine_consensus(votes)
        return VotingResult(
            query=query,
            votes=votes,
            consensus=consensus,
            winning_model=winning_model,
            metadata={"weights": weights},
        )

    async def majority_vote(
        self,
        query: str,
        models: List[AIModel],
        **kwargs: Any,
    ) -> VotingResult:
        """Collect votes and determine consensus by majority.

        Args:
            query: The query to vote on.
            models: List of AI models to collect votes from.
            **kwargs: Additional arguments for the AI models.

        Returns:
            VotingResult containing the votes and majority consensus.
        """
        votes = []
        for model in models:
            try:
                response = await model.chat([{"role": "user", "content": query}])
                # For majority voting, we need categorical responses
                # This is a placeholder: in a real implementation, responses would be categorized
                category = self._extract_category(response)
                votes.append(
                    Vote(
                        model_name=model.name,
                        response=response,
                        score=1.0,  # Each vote counts equally for majority
                        metadata={"category": category},
                    )
                )
            except Exception as e:
                votes.append(
                    Vote(
                        model_name=model.name,
                        response={"error": str(e)},
                        score=0.0,
                        metadata={"error": str(e)},
                    )
                )

        # Determine majority consensus
        consensus, winning_model = self._determine_majority_consensus(votes)
        return VotingResult(
            query=query,
            votes=votes,
            consensus=consensus,
            winning_model=winning_model,
            metadata={"strategy": "majority"},
        )

    def _extract_category(self, response: Dict[str, Any]) -> str:
        """Extract a category from a response.

        Args:
            response: The response to categorize.

        Returns:
            The extracted category.
        """
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Simple placeholder: return the first word as the category
        return content.split()[0] if content else "unknown"

    def _determine_majority_consensus(self, votes: List[Vote]) -> tuple:
        """Determine consensus by majority vote.

        Args:
            votes: List of votes to analyze.

        Returns:
            Tuple of (consensus_response, winning_model_name).
        """
        if not votes:
            return None, None

        # Count categories
        category_counts = {}
        for vote in votes:
            if vote.score > 0:
                category = vote.metadata.get("category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

        if not category_counts:
            return None, None

        # Find the most common category
        winning_category = max(category_counts, key=category_counts.get)
        winning_votes = [vote for vote in votes if vote.metadata.get("category") == winning_category]
        winning_vote = winning_votes[0] if winning_votes else None

        if winning_vote:
            return winning_vote.response, winning_vote.model_name
        return None, None
