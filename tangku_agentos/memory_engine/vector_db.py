#!/usr/bin/env python3
"""
Vector Database for the TangkuAgentOS Memory Engine.

This module implements vector database backends for storing and querying
vector embeddings. It supports multiple vector database providers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .interfaces import IMemoryVectorDB
from .models import Memory, MemoryMetadata, MemoryType, MemoryConfig
from .exceptions import (
    MemoryError,
    MemoryBackendError,
    MemoryVectorError,
    MemoryNotFoundError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Vector Database
# =============================================================================


@dataclass
class VectorDBConfig:
    """Configuration for a vector database."""
    dimension: int = 768
    metric: str = "cosine"  # cosine, dot_product, euclidean, etc.
    max_index_size: int = 100000
    index_path: Optional[Union[str, Path]] = None
    persistence: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseVectorDB(IMemoryVectorDB):
    """
    Base class for all vector database implementations.
    
    This class provides common functionality and implements the IMemoryVectorDB
    interface. Subclasses should implement the backend-specific operations.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the vector database.
        
        Args:
            config: Configuration for the vector database
        """
        self.config = config or VectorDBConfig()
        self._initialized = False
        self._lock = asyncio.Lock()
        self._index = None
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the vectors."""
        return self.config.dimension
    
    @property
    def metric(self) -> str:
        """Get the similarity metric."""
        return self.config.metric
    
    async def initialize(
        self,
        dimension: int = 768,
        metric: str = "cosine",
        **kwargs: Any,
    ) -> None:
        """Initialize the vector database."""
        async with self._lock:
            if self._initialized:
                return
            
            # Update config
            self.config.dimension = dimension
            self.config.metric = metric
            for key, value in kwargs.items():
                setattr(self.config, key, value)
            
            # Initialize the index
            await self._initialize_index()
            
            self._initialized = True
            logger.info(f"Initialized {self.__class__.__name__} with dimension={dimension}, metric={metric}")
    
    async def shutdown(self) -> None:
        """Shutdown the vector database and clean up resources."""
        async with self._lock:
            if not self._initialized:
                return
            
            await self._cleanup()
            self._initialized = False
            logger.info(f"Shut down {self.__class__.__name__}")
    
    async def _initialize_index(self) -> None:
        """
        Initialize the vector index.
        
        Subclasses should override this method to implement their index initialization.
        """
        pass
    
    async def _cleanup(self) -> None:
        """
        Clean up resources.
        
        Subclasses should override this method to implement their cleanup logic.
        """
        pass
    
    async def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a vector to the database."""
        if not self._initialized:
            await self.initialize()
        
        # Validate vector
        self._validate_vector(vector)
        
        await self._add_vector(vector_id, vector, metadata or {})
        logger.debug(f"Added vector {vector_id}")
    
    async def add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """Add multiple vectors to the database."""
        if not self._initialized:
            await self.initialize()
        
        # Validate all vectors
        for vector_id, vector in vectors.items():
            self._validate_vector(vector)
        
        await self._add_vectors(vectors, metadata or {})
        logger.debug(f"Added {len(vectors)} vectors")
    
    async def get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Retrieve a vector and its metadata by ID."""
        if not self._initialized:
            await self.initialize()
        
        return await self._get_vector(vector_id)
    
    async def get_vectors(
        self,
        vector_ids: List[str],
    ) -> Dict[str, Optional[Tuple[List[float], Dict[str, Any]]]]:
        """Retrieve multiple vectors and their metadata by IDs."""
        if not self._initialized:
            await self.initialize()
        
        results = {}
        for vector_id in vector_ids:
            result = await self.get_vector(vector_id)
            results[vector_id] = result
        
        return results
    
    async def update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update a vector in the database."""
        if not self._initialized:
            await self.initialize()
        
        # Validate vector
        self._validate_vector(vector)
        
        await self._update_vector(vector_id, vector, metadata or {})
        logger.debug(f"Updated vector {vector_id}")
    
    async def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the database."""
        if not self._initialized:
            await self.initialize()
        
        result = await self._delete_vector(vector_id)
        if result:
            logger.debug(f"Deleted vector {vector_id}")
        return result
    
    async def delete_vectors(self, vector_ids: List[str]) -> int:
        """Delete multiple vectors from the database."""
        if not self._initialized:
            await self.initialize()
        
        count = 0
        for vector_id in vector_ids:
            if await self.delete_vector(vector_id):
                count += 1
        
        logger.debug(f"Deleted {count} vectors")
        return count
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors."""
        if not self._initialized:
            await self.initialize()
        
        # Validate query vector
        self._validate_vector(query_vector)
        
        return await self._search(query_vector, top_k, threshold, filters)
    
    async def batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        if not self._initialized:
            await self.initialize()
        
        # Validate all query vectors
        for vector in query_vectors:
            self._validate_vector(vector)
        
        return await self._batch_search(query_vectors, top_k, threshold, filters)
    
    async def clear(self) -> None:
        """Clear all vectors from the database."""
        if not self._initialized:
            await self.initialize()
        
        await self._clear()
        logger.info("Cleared all vectors")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        if not self._initialized:
            await self.initialize()
        
        return await self._get_stats()
    
    def _validate_vector(self, vector: List[float]) -> None:
        """Validate a vector."""
        if not isinstance(vector, list):
            raise MemoryVectorError(
                operation="validation",
                dimension=self.dimension,
                message=f"Vector must be a list, got {type(vector)}",
            )
        
        if len(vector) != self.dimension:
            raise MemoryVectorError(
                operation="validation",
                dimension=self.dimension,
                message=f"Vector dimension must be {self.dimension}, got {len(vector)}",
            )
        
        # Check that all elements are numeric
        for i, value in enumerate(vector):
            if not isinstance(value, (int, float)):
                raise MemoryVectorError(
                    operation="validation",
                    dimension=self.dimension,
                    message=f"Vector element {i} must be numeric, got {type(value)}",
                )
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Backend-specific add vector operation."""
        pass
    
    @abstractmethod
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Backend-specific add vectors operation."""
        pass
    
    @abstractmethod
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Backend-specific get vector operation."""
        pass
    
    @abstractmethod
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Backend-specific update vector operation."""
        pass
    
    @abstractmethod
    async def _delete_vector(self, vector_id: str) -> bool:
        """Backend-specific delete vector operation."""
        pass
    
    @abstractmethod
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Backend-specific search operation."""
        pass
    
    @abstractmethod
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Backend-specific batch search operation."""
        pass
    
    @abstractmethod
    async def _clear(self) -> None:
        """Backend-specific clear operation."""
        pass
    
    @abstractmethod
    async def _get_stats(self) -> Dict[str, Any]:
        """Backend-specific get stats operation."""
        pass


# =============================================================================
# FAISS Backend
# =============================================================================


class FAISSBackend(BaseVectorDB):
    """
    FAISS vector database backend.
    
    This backend uses the FAISS library for efficient similarity search
    in high-dimensional spaces.
    
    Attributes:
        index: FAISS index
        metadata: Dictionary storing metadata for each vector
        vector_to_id: Mapping from vector indices to IDs
        id_to_vector: Mapping from IDs to vector indices
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the FAISS backend.
        
        Args:
            config: Configuration for the FAISS backend
        """
        super().__init__(config)
        self.index = None
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.vector_to_id: Dict[int, str] = {}
        self.id_to_vector: Dict[str, int] = {}
        self._next_index = 0
    
    async def _initialize_index(self) -> None:
        """Initialize the FAISS index."""
        try:
            import faiss
        except ImportError:
            raise MemoryBackendError(
                backend="faiss",
                message="FAISS is required for FAISS backend. Install with: pip install faiss-cpu",
            )
        
        # Convert metric to FAISS metric
        faiss_metric = self._get_faiss_metric()
        
        # Create the index
        self.index = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
        
        # Load from file if persistence is enabled
        if self.config.persistence and self.config.index_path:
            index_path = Path(self.config.index_path)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
                self._load_metadata()
    
    def _get_faiss_metric(self) -> int:
        """Get the FAISS metric constant for the configured metric."""
        import faiss
        
        metric_map = {
            "cosine": faiss.METRIC_INNER_PRODUCT,
            "dot_product": faiss.METRIC_INNER_PRODUCT,
            "euclidean": faiss.METRIC_L2,
            "l2": faiss.METRIC_L2,
        }
        
        return metric_map.get(self.metric, faiss.METRIC_INNER_PRODUCT)
    
    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        if self.config.index_path:
            metadata_path = Path(self.config.index_path).with_suffix(".metadata.json")
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", {})
                    self.vector_to_id = data.get("vector_to_id", {})
                    self.id_to_vector = data.get("id_to_vector", {})
                    self._next_index = data.get("_next_index", 0)
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        if self.config.index_path:
            metadata_path = Path(self.config.index_path).with_suffix(".metadata.json")
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, "w") as f:
                json.dump({
                    "metadata": self.metadata,
                    "vector_to_id": self.vector_to_id,
                    "id_to_vector": self.id_to_vector,
                    "_next_index": self._next_index,
                }, f)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.config.persistence and self.config.index_path:
            import faiss
            index_path = Path(self.config.index_path)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(index_path))
            self._save_metadata()
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to the FAISS index."""
        # Convert to numpy array
        vector_array = np.array([vector], dtype=np.float32)
        
        # Add to index
        self.index.add(vector_array)
        
        # Store metadata
        index = self._next_index
        self._next_index += 1
        
        self.metadata[vector_id] = metadata
        self.vector_to_id[index] = vector_id
        self.id_to_vector[vector_id] = index
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to the FAISS index."""
        # Convert to numpy array
        vector_array = np.array([vectors[vid] for vid in vectors], dtype=np.float32)
        
        # Add to index
        self.index.add(vector_array)
        
        # Store metadata
        for vector_id, vector in vectors.items():
            index = self._next_index
            self._next_index += 1
            
            self.metadata[vector_id] = metadata.get(vector_id, {})
            self.vector_to_id[index] = vector_id
            self.id_to_vector[vector_id] = index
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from the FAISS index."""
        if vector_id not in self.id_to_vector:
            return None
        
        index = self.id_to_vector[vector_id]
        vector = self.index.reconstruct(index)
        metadata = self.metadata.get(vector_id, {})
        
        return (vector.tolist(), metadata)
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in the FAISS index."""
        if vector_id not in self.id_to_vector:
            # Vector doesn't exist, add it as new
            await self._add_vector(vector_id, vector, metadata)
            return
        
        # Remove old vector
        index = self.id_to_vector[vector_id]
        self.index.remove_ids(np.array([index], dtype=np.int64))
        
        # Add new vector
        await self._add_vector(vector_id, vector, metadata)
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the FAISS index."""
        if vector_id not in self.id_to_vector:
            return False
        
        index = self.id_to_vector[vector_id]
        
        # Remove from index
        self.index.remove_ids(np.array([index], dtype=np.int64))
        
        # Remove from metadata
        del self.metadata[vector_id]
        del self.vector_to_id[index]
        del self.id_to_vector[vector_id]
        
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in the FAISS index."""
        # Convert to numpy array
        query_array = np.array([query_vector], dtype=np.float32)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(query_array)
        
        # Search
        distances, indices = self.index.search(query_array, top_k)
        
        # Convert results
        results = []
        for i in range(min(top_k, len(indices[0]))):
            index = indices[0][i]
            distance = distances[0][i]
            
            # Convert distance to similarity score
            if self.metric == "cosine":
                # For cosine, distance is already similarity (inner product of normalized vectors)
                score = float(distance)
            elif self.metric == "euclidean":
                # For Euclidean, convert distance to similarity
                score = 1.0 / (1.0 + distance)
            else:
                score = float(distance)
            
            # Apply threshold
            if threshold is not None and score < threshold:
                continue
            
            # Get vector ID and metadata
            if index in self.vector_to_id:
                vector_id = self.vector_to_id[index]
                metadata = self.metadata.get(vector_id, {})
                results.append((vector_id, score, metadata))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        # Convert to numpy array
        query_array = np.array(query_vectors, dtype=np.float32)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(query_array)
        
        # Search
        distances, indices = self.index.search(query_array, top_k)
        
        # Convert results
        all_results = []
        for i in range(len(query_vectors)):
            results = []
            for j in range(min(top_k, indices.shape[1])):
                index = indices[i][j]
                distance = distances[i][j]
                
                # Convert distance to similarity score
                if self.metric == "cosine":
                    score = float(distance)
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + distance)
                else:
                    score = float(distance)
                
                # Apply threshold
                if threshold is not None and score < threshold:
                    continue
                
                # Get vector ID and metadata
                if index in self.vector_to_id:
                    vector_id = self.vector_to_id[index]
                    metadata = self.metadata.get(vector_id, {})
                    results.append((vector_id, score, metadata))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from the FAISS index."""
        self.index.reset()
        self.metadata.clear()
        self.vector_to_id.clear()
        self.id_to_vector.clear()
        self._next_index = 0
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAISS index."""
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": self.index.ntotal,
            "metadata_count": len(self.metadata),
            "backend": "faiss",
        }


# =============================================================================
# ChromaDB Backend
# =============================================================================


class ChromaDBBackend(BaseVectorDB):
    """
    ChromaDB vector database backend.
    
    This backend uses the ChromaDB library for vector storage and search.
    ChromaDB is an open-source vector database that can be run locally or
    in client-server mode.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the ChromaDB backend.
        
        Args:
            config: Configuration for the ChromaDB backend
        """
        super().__init__(config)
        self.client = None
        self.collection = None
    
    async def _initialize_index(self) -> None:
        """Initialize the ChromaDB collection."""
        try:
            import chromadb
        except ImportError:
            raise MemoryBackendError(
                backend="chromadb",
                message="ChromaDB is required for ChromaDB backend. Install with: pip install chromadb",
            )
        
        # Create client
        if self.config.persistence and self.config.index_path:
            self.client = chromadb.PersistentClient(path=str(self.config.index_path))
        else:
            self.client = chromadb.Client()
        
        # Create or get collection
        metric_map = {
            "cosine": "cosine",
            "dot_product": "dot",
            "euclidean": "l2",
        }
        
        chroma_metric = metric_map.get(self.metric, "cosine")
        
        self.collection = self.client.get_or_create_collection(
            name="tangku_memory",
            metadata={"hnsw:space": chroma_metric},
        )
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            self.client.__exit__()
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to ChromaDB."""
        self.collection.add(
            documents=[json.dumps(metadata)],
            embeddings=[vector],
            ids=[vector_id],
            metadatas=[metadata],
        )
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to ChromaDB."""
        vector_ids = list(vectors.keys())
        vector_list = [vectors[vid] for vid in vector_ids]
        metadata_list = [metadata.get(vid, {}) for vid in vector_ids]
        
        self.collection.add(
            documents=[json.dumps(m) for m in metadata_list],
            embeddings=vector_list,
            ids=vector_ids,
            metadatas=metadata_list,
        )
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from ChromaDB."""
        result = self.collection.get(ids=[vector_id])
        
        if not result["ids"] or not result["ids"][0]:
            return None
        
        vector = result["embeddings"][0] if result["embeddings"] else None
        metadata = result["metadatas"][0] if result["metadatas"] else {}
        
        if vector is None:
            return None
        
        return (vector, metadata)
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in ChromaDB."""
        # ChromaDB doesn't have a direct update method, so we delete and re-add
        await self._delete_vector(vector_id)
        await self._add_vector(vector_id, vector, metadata)
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from ChromaDB."""
        self.collection.delete(ids=[vector_id])
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in ChromaDB."""
        # Convert filters to ChromaDB format
        chroma_filters = None
        if filters:
            chroma_filters = {
                "$and": [
                    {key: {"$eq": value}} for key, value in filters.items()
                ]
            }
        
        result = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=chroma_filters,
        )
        
        # Convert results
        results = []
        for i in range(min(top_k, len(result["ids"][0]))):
            vector_id = result["ids"][0][i]
            distance = result["distances"][0][i]
            metadata = result["metadatas"][0][i] if result["metadatas"] else {}
            
            # Convert distance to similarity score
            if self.metric == "cosine":
                score = 1.0 - distance
            elif self.metric == "euclidean":
                score = 1.0 / (1.0 + distance)
            else:
                score = 1.0 - distance
            
            # Apply threshold
            if threshold is not None and score < threshold:
                continue
            
            results.append((vector_id, score, metadata))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        # Convert filters to ChromaDB format
        chroma_filters = None
        if filters:
            chroma_filters = {
                "$and": [
                    {key: {"$eq": value}} for key, value in filters.items()
                ]
            }
        
        result = self.collection.query(
            query_embeddings=query_vectors,
            n_results=top_k,
            where=chroma_filters,
        )
        
        # Convert results
        all_results = []
        for i in range(len(query_vectors)):
            results = []
            for j in range(min(top_k, len(result["ids"][i]))):
                vector_id = result["ids"][i][j]
                distance = result["distances"][i][j]
                metadata = result["metadatas"][i][j] if result["metadatas"] else {}
                
                # Convert distance to similarity score
                if self.metric == "cosine":
                    score = 1.0 - distance
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + distance)
                else:
                    score = 1.0 - distance
                
                # Apply threshold
                if threshold is not None and score < threshold:
                    continue
                
                results.append((vector_id, score, metadata))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from ChromaDB."""
        self.collection.delete(where={})
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": self.collection.count(),
            "backend": "chromadb",
        }


# =============================================================================
# Qdrant Backend
# =============================================================================


class QdrantBackend(BaseVectorDB):
    """
    Qdrant vector database backend.
    
    This backend uses the Qdrant vector database, which can be run locally
    or as a distributed service.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the Qdrant backend.
        
        Args:
            config: Configuration for the Qdrant backend
        """
        super().__init__(config)
        self.client = None
        self.collection_name = "tangku_memory"
    
    async def _initialize_index(self) -> None:
        """Initialize the Qdrant collection."""
        try:
            from qdrant_client import QdrantClient, models
        except ImportError:
            raise MemoryBackendError(
                backend="qdrant",
                message="Qdrant client is required for Qdrant backend. Install with: pip install qdrant-client",
            )
        
        # Create client
        if self.config.connection_string:
            # Parse connection string (e.g., "localhost:6333" or "http://localhost:6333")
            if self.config.connection_string.startswith("http"):
                self.client = QdrantClient(url=self.config.connection_string)
            else:
                self.client = QdrantClient(host=self.config.connection_string)
        else:
            self.client = QdrantClient(":memory:")
        
        # Convert metric to Qdrant metric
        metric_map = {
            "cosine": models.Distance.COSINE,
            "dot_product": models.Distance.DOT,
            "euclidean": models.Distance.EUCLID,
        }
        
        qdrant_metric = metric_map.get(self.metric, models.Distance.COSINE)
        
        # Create collection if it doesn't exist
        collections = await self.client.get_collections()
        if self.collection_name not in [c.name for c in collections.collections]:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.dimension,
                    distance=qdrant_metric,
                ),
            )
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to Qdrant."""
        from qdrant_client import models
        
        await self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=[vector_id],
                vectors=[vector],
                payloads=[metadata],
            ),
        )
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to Qdrant."""
        from qdrant_client import models
        
        vector_ids = list(vectors.keys())
        vector_list = [vectors[vid] for vid in vector_ids]
        metadata_list = [metadata.get(vid, {}) for vid in vector_ids]
        
        await self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=vector_ids,
                vectors=vector_list,
                payloads=metadata_list,
            ),
        )
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from Qdrant."""
        result = await self.client.retrieve(
            collection_name=self.collection_name,
            ids=[vector_id],
        )
        
        if not result or not result[0]:
            return None
        
        point = result[0]
        return (point.vector, point.payload)
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in Qdrant."""
        from qdrant_client import models
        
        await self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=[vector_id],
                vectors=[vector],
                payloads=[metadata],
            ),
        )
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from Qdrant."""
        from qdrant_client import models
        
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points=[vector_id],
            ),
        )
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Qdrant."""
        from qdrant_client import models
        
        # Convert filters to Qdrant format
        qdrant_filters = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                ))
            qdrant_filters = models.Filter(
                must=conditions,
            )
        
        result = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            filter=qdrant_filters,
            score_threshold=threshold,
        )
        
        # Convert results
        results = []
        for point in result:
            # Convert distance to similarity score
            if self.metric == "cosine":
                score = 1.0 - point.score
            elif self.metric == "euclidean":
                score = 1.0 / (1.0 + point.score)
            else:
                score = 1.0 - point.score
            
            results.append((point.id, score, point.payload))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        from qdrant_client import models
        
        # Convert filters to Qdrant format
        qdrant_filters = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                ))
            qdrant_filters = models.Filter(
                must=conditions,
            )
        
        # Perform batch search
        all_results = []
        for query_vector in query_vectors:
            result = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                filter=qdrant_filters,
                score_threshold=threshold,
            )
            
            # Convert results
            results = []
            for point in result:
                # Convert distance to similarity score
                if self.metric == "cosine":
                    score = 1.0 - point.score
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + point.score)
                else:
                    score = 1.0 - point.score
                
                results.append((point.id, score, point.payload))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from Qdrant."""
        await self.client.clear(
            collection_name=self.collection_name,
        )
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Qdrant collection."""
        collection = await self.client.get_collection(self.collection_name)
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": collection.points_count,
            "backend": "qdrant",
        }


# =============================================================================
# Pinecone Backend
# =============================================================================


class PineconeBackend(BaseVectorDB):
    """
    Pinecone vector database backend.
    
    This backend uses the Pinecone managed vector database service.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the Pinecone backend.
        
        Args:
            config: Configuration for the Pinecone backend
        """
        super().__init__(config)
        self.client = None
        self.index = None
    
    async def _initialize_index(self) -> None:
        """Initialize the Pinecone index."""
        try:
            import pinecone
        except ImportError:
            raise MemoryBackendError(
                backend="pinecone",
                message="Pinecone client is required for Pinecone backend. Install with: pip install pinecone-client",
            )
        
        # Initialize Pinecone
        api_key = self.config.extra.get("api_key")
        environment = self.config.extra.get("environment", "us-west1-gcp")
        
        if not api_key:
            raise MemoryBackendError(
                backend="pinecone",
                message="Pinecone API key is required",
            )
        
        pinecone.init(api_key=api_key, environment=environment)
        self.client = pinecone
        
        # Get or create index
        index_name = self.config.extra.get("index_name", "tangku-memory")
        
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=self.dimension,
                metric=self.metric,
            )
        
        self.index = pinecone.Index(index_name)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass  # Pinecone doesn't require explicit cleanup
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to Pinecone."""
        self.index.upsert([(vector_id, vector, metadata)])
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to Pinecone."""
        vector_tuples = [
            (vid, vectors[vid], metadata.get(vid, {}))
            for vid in vectors
        ]
        self.index.upsert(vector_tuples)
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from Pinecone."""
        result = self.index.fetch(ids=[vector_id])
        
        if not result or "vectors" not in result or vector_id not in result["vectors"]:
            return None
        
        vector_data = result["vectors"][vector_id]
        return (vector_data["values"], vector_data["metadata"])
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in Pinecone."""
        self.index.upsert([(vector_id, vector, metadata)])
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from Pinecone."""
        self.index.delete(ids=[vector_id])
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Pinecone."""
        result = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filters,
        )
        
        # Convert results
        results = []
        for match in result["matches"]:
            # Convert distance to similarity score
            if self.metric == "cosine":
                score = 1.0 - match["score"]
            elif self.metric == "euclidean":
                score = 1.0 / (1.0 + match["score"])
            else:
                score = 1.0 - match["score"]
            
            # Apply threshold
            if threshold is not None and score < threshold:
                continue
            
            results.append((match["id"], score, match["metadata"]))
        
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        all_results = []
        for query_vector in query_vectors:
            result = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filters,
            )
            
            # Convert results
            results = []
            for match in result["matches"]:
                # Convert distance to similarity score
                if self.metric == "cosine":
                    score = 1.0 - match["score"]
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + match["score"])
                else:
                    score = 1.0 - match["score"]
                
                # Apply threshold
                if threshold is not None and score < threshold:
                    continue
                
                results.append((match["id"], score, match["metadata"]))
            
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from Pinecone."""
        # Pinecone doesn't have a direct clear method, so we delete all vectors
        # This is not efficient for large indexes
        all_vectors = self.index.fetch(ids=[])
        if "vectors" in all_vectors:
            vector_ids = list(all_vectors["vectors"].keys())
            if vector_ids:
                self.index.delete(ids=vector_ids)
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        index_stats = self.index.describe_index_stats()
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": index_stats.get("total_vector_count", 0),
            "backend": "pinecone",
        }


# =============================================================================
# Weaviate Backend
# =============================================================================


class WeaviateBackend(BaseVectorDB):
    """
    Weaviate vector database backend.
    
    This backend uses the Weaviate vector search engine, which can be run
    locally or as a managed service.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the Weaviate backend.
        
        Args:
            config: Configuration for the Weaviate backend
        """
        super().__init__(config)
        self.client = None
        self.class_name = "TangkuMemory"
    
    async def _initialize_index(self) -> None:
        """Initialize the Weaviate class."""
        try:
            import weaviate
        except ImportError:
            raise MemoryBackendError(
                backend="weaviate",
                message="Weaviate client is required for Weaviate backend. Install with: pip install weaviate-client",
            )
        
        # Create client
        if self.config.connection_string:
            self.client = weaviate.Client(self.config.connection_string)
        else:
            self.client = weaviate.Client(":memory:")
        
        # Define the class
        class_obj = {
            "class": self.class_name,
            "vectorizer": "none",  # We'll provide our own vectors
            "vectorIndexType": "hnsw",
            "moduleConfig": {
                "hnsw": {
                    "vectorCacheType": "memory",
                    "cleanupIntervalSeconds": 60,
                    "maxIndexingThreads": 4,
                    "onDisk": False,
                    "ef": -1,
                    "efConstruction": 128,
                    "m": 16,
                }
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                },
                {
                    "name": "memory_type",
                    "dataType": ["text"],
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                },
            ],
        }
        
        # Create the class if it doesn't exist
        if not self.client.schema.contains(self.class_name):
            self.client.schema.create_class(class_obj)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            self.client.close()
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to Weaviate."""
        data_obj = {
            "content": metadata.get("content", ""),
            "memory_type": metadata.get("memory_type", "unknown"),
            "metadata": json.dumps(metadata),
        }
        
        self.client.data_object.create(
            data_obj,
            self.class_name,
            vector=vector,
            uuid=vector_id,
        )
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to Weaviate."""
        batch = []
        for vector_id, vector in vectors.items():
            data_obj = {
                "content": metadata.get(vector_id, {}).get("content", ""),
                "memory_type": metadata.get(vector_id, {}).get("memory_type", "unknown"),
                "metadata": json.dumps(metadata.get(vector_id, {})),
            }
            batch.append({
                "data": data_obj,
                "class": self.class_name,
                "vector": vector,
                "uuid": vector_id,
            })
        
        self.client.batch.create_objects(batch)
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from Weaviate."""
        result = self.client.data_object.get_by_uuid(
            vector_id,
            class_name=self.class_name,
            with_vector=True,
        )
        
        if not result:
            return None
        
        metadata = json.loads(result["metadata"])
        return (result["_additional"]["vector"], metadata)
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in Weaviate."""
        data_obj = {
            "content": metadata.get("content", ""),
            "memory_type": metadata.get("memory_type", "unknown"),
            "metadata": json.dumps(metadata),
        }
        
        self.client.data_object.update(
            data_obj,
            self.class_name,
            vector=vector,
            uuid=vector_id,
        )
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from Weaviate."""
        self.client.data_object.delete(
            uuid=vector_id,
            class_name=self.class_name,
        )
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Weaviate."""
        # Convert filters to Weaviate format
        weaviate_filters = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append({
                    "path": [key],
                    "operator": "Equal",
                    "valueText": str(value),
                })
            weaviate_filters = {"operator": "And", "operands": conditions}
        
        result = self.client.query.get(
            class_name=self.class_name,
            properties=["content", "memory_type", "metadata"],
            vector=query_vector,
            limit=top_k,
            where=weaviate_filters,
            certainty=threshold,
        )
        
        # Convert results
        results = []
        for i, item in enumerate(result["data"]["Get"][self.class_name]):
            score = item["_additional"]["certainty"]
            metadata = json.loads(item["metadata"])
            results.append((item["_additional"]["id"], score, metadata))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        all_results = []
        for query_vector in query_vectors:
            result = self.client.query.get(
                class_name=self.class_name,
                properties=["content", "memory_type", "metadata"],
                vector=query_vector,
                limit=top_k,
                where=filters,
                certainty=threshold,
            )
            
            # Convert results
            results = []
            for i, item in enumerate(result["data"]["Get"][self.class_name]):
                score = item["_additional"]["certainty"]
                metadata = json.loads(item["metadata"])
                results.append((item["_additional"]["id"], score, metadata))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from Weaviate."""
        self.client.schema.delete_class(self.class_name)
        self.client.schema.create_class({
            "class": self.class_name,
            "vectorizer": "none",
            "vectorIndexType": "hnsw",
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "memory_type", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["text"]},
            ],
        })
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Weaviate class."""
        result = self.client.query.aggregate(
            class_name=self.class_name,
            properties=["content"],
        )
        
        count = result["data"]["Aggregate"][self.class_name][0]["count"]
        
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": count,
            "backend": "weaviate",
        }


# =============================================================================
# Milvus Backend
# =============================================================================


class MilvusBackend(BaseVectorDB):
    """
    Milvus vector database backend.
    
    This backend uses the Milvus vector database, which is designed for
    scalable vector search.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the Milvus backend.
        
        Args:
            config: Configuration for the Milvus backend
        """
        super().__init__(config)
        self.client = None
        self.collection = None
    
    async def _initialize_index(self) -> None:
        """Initialize the Milvus collection."""
        try:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections
        except ImportError:
            raise MemoryBackendError(
                backend="milvus",
                message="Milvus client is required for Milvus backend. Install with: pip install pymilvus",
            )
        
        # Connect to Milvus
        host = self.config.extra.get("host", "localhost")
        port = self.config.extra.get("port", "19530")
        
        connections.connect("default", host=host, port=port)
        self.client = connections
        
        # Define the collection schema
        fields = [
            FieldSchema(name="memory_id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(fields, description="TangkuAgentOS Memory Collection")
        
        # Create the collection if it doesn't exist
        collection_name = self.config.extra.get("collection_name", "tangku_memory")
        if not connections.has_collection(collection_name):
            self.collection = Collection(name=collection_name, schema=schema)
        else:
            self.collection = Collection(name=collection_name)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            connections.disconnect("default")
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to Milvus."""
        data = [
            [vector_id],
            [vector],
            [json.dumps(metadata)],
        ]
        
        self.collection.insert(data)
        self.collection.flush()
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to Milvus."""
        vector_ids = list(vectors.keys())
        vector_list = [vectors[vid] for vid in vector_ids]
        metadata_list = [json.dumps(metadata.get(vid, {})) for vid in vector_ids]
        
        data = [
            vector_ids,
            vector_list,
            metadata_list,
        ]
        
        self.collection.insert(data)
        self.collection.flush()
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from Milvus."""
        result = self.collection.query(
            expr=f"memory_id == '{vector_id}'",
            output_fields=["embedding", "metadata"],
        )
        
        if not result:
            return None
        
        embedding = result[0]["embedding"]
        metadata = json.loads(result[0]["metadata"])
        
        return (embedding, metadata)
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in Milvus."""
        # Milvus doesn't have a direct update method, so we delete and re-add
        await self._delete_vector(vector_id)
        await self._add_vector(vector_id, vector, metadata)
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from Milvus."""
        self.collection.delete(expr=f"memory_id == '{vector_id}'")
        self.collection.flush()
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in Milvus."""
        # Convert filters to Milvus expression
        filter_expr = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"json_contains(metadata, '{json.dumps({key: value})}')")
            filter_expr = " and ".join(conditions)
        
        result = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": self.metric.upper(), "params": {"nprobe": 10}},
            limit=top_k,
            expr=filter_expr,
        )
        
        # Convert results
        results = []
        for hit in result[0]:
            # Convert distance to similarity score
            if self.metric == "cosine":
                score = 1.0 - hit.distance
            elif self.metric == "euclidean":
                score = 1.0 / (1.0 + hit.distance)
            else:
                score = 1.0 - hit.distance
            
            # Apply threshold
            if threshold is not None and score < threshold:
                continue
            
            metadata = json.loads(hit.entity.get("metadata", "{}"))
            results.append((hit.id, score, metadata))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        all_results = []
        for query_vector in query_vectors:
            result = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": self.metric.upper(), "params": {"nprobe": 10}},
                limit=top_k,
                expr=filters,
            )
            
            # Convert results
            results = []
            for hit in result[0]:
                # Convert distance to similarity score
                if self.metric == "cosine":
                    score = 1.0 - hit.distance
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + hit.distance)
                else:
                    score = 1.0 - hit.distance
                
                # Apply threshold
                if threshold is not None and score < threshold:
                    continue
                
                metadata = json.loads(hit.entity.get("metadata", "{}"))
                results.append((hit.id, score, metadata))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from Milvus."""
        self.collection.delete(expr="memory_id != ''")
        self.collection.flush()
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Milvus collection."""
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": self.collection.num_entities,
            "backend": "milvus",
        }


# =============================================================================
# LanceDB Backend
# =============================================================================


class LanceDBBackend(BaseVectorDB):
    """
    LanceDB vector database backend.
    
    This backend uses the LanceDB vector database, which is designed for
    efficient vector search with minimal resources.
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        Initialize the LanceDB backend.
        
        Args:
            config: Configuration for the LanceDB backend
        """
        super().__init__(config)
        self.db = None
        self.table = None
    
    async def _initialize_index(self) -> None:
        """Initialize the LanceDB table."""
        try:
            import lance
        except ImportError:
            raise MemoryBackendError(
                backend="lancedb",
                message="LanceDB is required for LanceDB backend. Install with: pip install lancedb",
            )
        
        # Connect to database
        db_path = self.config.index_path or ":memory:"
        self.db = lance.connect(str(db_path))
        
        # Create or open table
        table_name = self.config.extra.get("table_name", "tangku_memory")
        
        if table_name not in self.db.table_names():
            # Create new table
            schema = lance.Schema([
                lance.Column("memory_id", dtype=lance.String),
                lance.Column("vector", dtype=lance.Vector(self.dimension)),
                lance.Column("metadata", dtype=lance.Json),
            ])
            self.table = self.db.create_table(table_name, schema)
        else:
            self.table = self.db.open_table(table_name)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass  # LanceDB doesn't require explicit cleanup
    
    async def _add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Add a vector to LanceDB."""
        data = {
            "memory_id": [vector_id],
            "vector": [vector],
            "metadata": [metadata],
        }
        
        self.table.add(data)
    
    async def _add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> None:
        """Add multiple vectors to LanceDB."""
        vector_ids = list(vectors.keys())
        data = {
            "memory_id": vector_ids,
            "vector": [vectors[vid] for vid in vector_ids],
            "metadata": [metadata.get(vid, {}) for vid in vector_ids],
        }
        
        self.table.add(data)
    
    async def _get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """Get a vector from LanceDB."""
        result = self.table.search()
        
        # Filter by memory_id
        result = result.where(f"memory_id = '{vector_id}'")
        result = result.limit(1)
        result = result.to_list()
        
        if not result:
            return None
        
        return (result[0]["vector"], result[0]["metadata"])
    
    async def _update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> None:
        """Update a vector in LanceDB."""
        # LanceDB doesn't have a direct update method, so we delete and re-add
        await self._delete_vector(vector_id)
        await self._add_vector(vector_id, vector, metadata)
    
    async def _delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from LanceDB."""
        # Create a new table without the deleted vector
        result = self.table.search()
        result = result.where(f"memory_id != '{vector_id}'")
        new_data = result.to_list()
        
        if len(new_data) == len(self.table):
            return False
        
        # Replace the table
        self.table = self.db.create_table(
            self.table.name,
            self.table.schema,
        )
        
        if new_data:
            self.table.add({
                "memory_id": [item["memory_id"] for item in new_data],
                "vector": [item["vector"] for item in new_data],
                "metadata": [item["metadata"] for item in new_data],
            })
        
        return True
    
    async def _search(
        self,
        query_vector: List[float],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors in LanceDB."""
        # Build filter expression
        filter_expr = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"metadata['{key}'] = '{value}'")
            filter_expr = " and ".join(conditions)
        
        # Perform search
        result = self.table.search()
        
        if filter_expr:
            result = result.where(filter_expr)
        
        result = result.nearest(query_vector, k=top_k)
        result = result.limit(top_k)
        result = result.to_list()
        
        # Convert results
        results = []
        for i, item in enumerate(result):
            # Convert distance to similarity score
            distance = item["_distance"]
            if self.metric == "cosine":
                score = 1.0 - distance
            elif self.metric == "euclidean":
                score = 1.0 / (1.0 + distance)
            else:
                score = 1.0 - distance
            
            # Apply threshold
            if threshold is not None and score < threshold:
                continue
            
            results.append((item["memory_id"], score, item["metadata"]))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    async def _batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int,
        threshold: Optional[float],
        filters: Optional[Dict[str, Any]],
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """Perform batch search for multiple query vectors."""
        all_results = []
        for query_vector in query_vectors:
            result = self.table.search()
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"metadata['{key}'] = '{value}'")
                filter_expr = " and ".join(conditions)
                result = result.where(filter_expr)
            
            result = result.nearest(query_vector, k=top_k)
            result = result.limit(top_k)
            result = result.to_list()
            
            # Convert results
            results = []
            for item in result:
                # Convert distance to similarity score
                distance = item["_distance"]
                if self.metric == "cosine":
                    score = 1.0 - distance
                elif self.metric == "euclidean":
                    score = 1.0 / (1.0 + distance)
                else:
                    score = 1.0 - distance
                
                # Apply threshold
                if threshold is not None and score < threshold:
                    continue
                
                results.append((item["memory_id"], score, item["metadata"]))
            
            # Sort by score (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            all_results.append(results)
        
        return all_results
    
    async def _clear(self) -> None:
        """Clear all vectors from LanceDB."""
        # Drop and recreate the table
        self.db.drop_table(self.table.name)
        
        schema = lance.Schema([
            lance.Column("memory_id", dtype=lance.String),
            lance.Column("vector", dtype=lance.Vector(self.dimension)),
            lance.Column("metadata", dtype=lance.Json),
        ])
        self.table = self.db.create_table(self.table.name, schema)
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about the LanceDB table."""
        return {
            "dimension": self.dimension,
            "metric": self.metric,
            "index_size": len(self.table),
            "backend": "lancedb",
        }


# =============================================================================
# Vector DB Factory
# =============================================================================


class VectorDBFactory:
    """
    Factory for creating vector database backends.
    """
    
    @staticmethod
    def create_vector_db(
        backend_type: Union[str, str],
        **kwargs: Any,
    ) -> BaseVectorDB:
        """
        Create a vector database of the specified type.
        
        Args:
            backend_type: Type of vector database to create
            **kwargs: Configuration parameters for the backend
            
        Returns:
            An instance of the specified vector database
            
        Raises:
            ValueError: If the backend type is not supported
        """
        backend_type = backend_type.upper()
        
        if backend_type == "FAISS":
            return FAISSBackend(**kwargs)
        elif backend_type == "CHROMADB":
            return ChromaDBBackend(**kwargs)
        elif backend_type == "QDRANT":
            return QdrantBackend(**kwargs)
        elif backend_type == "PINECONE":
            return PineconeBackend(**kwargs)
        elif backend_type == "WEAVIATE":
            return WeaviateBackend(**kwargs)
        elif backend_type == "MILVUS":
            return MilvusBackend(**kwargs)
        elif backend_type == "LANCEDB":
            return LanceDBBackend(**kwargs)
        else:
            raise ValueError(f"Unsupported vector database backend: {backend_type}")
