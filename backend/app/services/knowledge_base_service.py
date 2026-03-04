"""Knowledge base search service with semantic search and context injection."""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Document types for knowledge base."""
    FAQ = "faq"
    ARTICLE = "article"
    GUIDE = "guide"
    TROUBLESHOOTING = "troubleshooting"
    POLICY = "policy"
    PRODUCT = "product"


class Document:
    """Knowledge base document."""

    def __init__(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: DocumentType,
        category: str = "general",
        tags: List[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Initialize document."""
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.doc_type = doc_type
        self.category = category
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.embedding = None  # Will be set by search service
        self.relevance_score = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "type": self.doc_type.value,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score
        }


class SearchResult:
    """Search result with context."""

    def __init__(
        self,
        documents: List[Document],
        query: str,
        total_results: int,
        search_time_ms: float
    ):
        """Initialize search result."""
        self.documents = documents
        self.query = query
        self.total_results = total_results
        self.search_time_ms = search_time_ms

    def get_context(self, max_docs: int = 3) -> str:
        """Get context string for LLM injection."""
        context_docs = self.documents[:max_docs]
        
        context = "# Knowledge Base Context\n\n"
        for i, doc in enumerate(context_docs, 1):
            context += f"## Document {i}: {doc.title}\n"
            context += f"Type: {doc.doc_type.value}\n"
            context += f"Relevance: {doc.relevance_score:.2%}\n"
            context += f"Content: {doc.content[:500]}...\n\n"
        
        return context

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "total_results": self.total_results,
            "documents": [d.to_dict() for d in self.documents],
            "search_time_ms": self.search_time_ms
        }


class KnowledgeBaseService:
    """Service for knowledge base search and context injection."""

    def __init__(self):
        """Initialize knowledge base service."""
        self.documents: Dict[str, Document] = {}
        self.company_docs: Dict[str, List[str]] = {}  # company_id -> doc_ids
        self.doc_index: Dict[str, List[str]] = {}  # word -> doc_ids (simple inverted index)

    async def index_document(
        self,
        company_id: str,
        doc_id: str,
        title: str,
        content: str,
        doc_type: DocumentType,
        category: str = "general",
        tags: List[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Index document in knowledge base.
        
        Args:
            company_id: Company identifier
            doc_id: Document ID
            title: Document title
            content: Document content
            doc_type: Document type
            category: Document category
            tags: Document tags
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            doc = Document(
                doc_id=f"{company_id}:{doc_id}",
                title=title,
                content=content,
                doc_type=doc_type,
                category=category,
                tags=tags,
                metadata=metadata
            )

            # Generate embedding (TODO: use actual embedding model)
            doc.embedding = self._generate_embedding(content)

            # Store document
            self.documents[doc.doc_id] = doc

            # Add to company docs
            if company_id not in self.company_docs:
                self.company_docs[company_id] = []
            self.company_docs[company_id].append(doc.doc_id)

            # Index for keyword search
            self._index_keywords(doc)

            logger.info(f"Indexed document {doc_id} for {company_id}")
            return True
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return False

    async def search(
        self,
        company_id: str,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> SearchResult:
        """
        Search knowledge base.
        
        Args:
            company_id: Company identifier
            query: Search query
            limit: Result limit
            category: Filter by category
            
        Returns:
            Search results
        """
        import time
        start_time = time.time()

        try:
            # Get company documents
            doc_ids = self.company_docs.get(company_id, [])
            if not doc_ids:
                return SearchResult([], query, 0, 0)

            # Get documents
            company_docs = [
                self.documents[doc_id]
                for doc_id in doc_ids
                if doc_id in self.documents
            ]

            # Filter by category
            if category:
                company_docs = [d for d in company_docs if d.category == category]

            # Score documents
            scored_docs = []
            for doc in company_docs:
                score = self._score_document(doc, query)
                if score > 0:
                    doc.relevance_score = score
                    scored_docs.append(doc)

            # Sort by score
            scored_docs.sort(key=lambda d: d.relevance_score, reverse=True)

            # Get top results
            results = scored_docs[:limit]

            search_time_ms = (time.time() - start_time) * 1000

            return SearchResult(results, query, len(scored_docs), search_time_ms)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return SearchResult([], query, 0, 0)

    async def get_document(self, company_id: str, doc_id: str) -> Optional[Document]:
        """
        Get specific document.
        
        Args:
            company_id: Company identifier
            doc_id: Document ID
            
        Returns:
            Document or None
        """
        full_id = f"{company_id}:{doc_id}"
        return self.documents.get(full_id)

    async def delete_document(self, company_id: str, doc_id: str) -> bool:
        """
        Delete document from knowledge base.
        
        Args:
            company_id: Company identifier
            doc_id: Document ID
            
        Returns:
            Success status
        """
        full_id = f"{company_id}:{doc_id}"
        
        if full_id in self.documents:
            del self.documents[full_id]
            
            if company_id in self.company_docs:
                self.company_docs[company_id].remove(full_id)
            
            logger.info(f"Deleted document {doc_id}")
            return True
        
        return False

    async def get_context_for_query(
        self,
        company_id: str,
        query: str,
        max_docs: int = 3
    ) -> str:
        """
        Get context for LLM from knowledge base.
        
        Args:
            company_id: Company identifier
            query: User query
            max_docs: Max documents to include
            
        Returns:
            Context string
        """
        results = await self.search(company_id, query, limit=max_docs)
        return results.get_context(max_docs)

    async def list_documents(
        self,
        company_id: str,
        category: Optional[str] = None,
        doc_type: Optional[DocumentType] = None
    ) -> List[Document]:
        """
        List documents in knowledge base.
        
        Args:
            company_id: Company identifier
            category: Filter by category
            doc_type: Filter by type
            
        Returns:
            List of documents
        """
        doc_ids = self.company_docs.get(company_id, [])
        docs = [
            self.documents[doc_id]
            for doc_id in doc_ids
            if doc_id in self.documents
        ]

        # Filter by category
        if category:
            docs = [d for d in docs if d.category == category]

        # Filter by type
        if doc_type:
            docs = [d for d in docs if d.doc_type == doc_type]

        return docs

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        TODO: Use actual embedding model (sentence-transformers, OpenAI, etc.)
        For now, return dummy embedding.
        """
        # Simple hash-based dummy embedding (not for production)
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> i) % 256 / 256.0 for i in range(384)]

    def _score_document(self, doc: Document, query: str) -> float:
        """Score document relevance to query."""
        score = 0.0
        query_lower = query.lower()

        # Title match (highest weight)
        if query_lower in doc.title.lower():
            score += 5.0

        # Content match
        content_lower = doc.content.lower()
        query_words = query_lower.split()
        matches = sum(1 for word in query_words if word in content_lower)
        score += matches * 2.0

        # Tag match
        tag_matches = sum(1 for tag in doc.tags if tag.lower() in query_lower)
        score += tag_matches * 1.5

        # Category relevance
        if doc.category in ["faq", "troubleshooting"]:
            score *= 1.2

        return score

    def _index_keywords(self, doc: Document) -> None:
        """Index document keywords for quick lookup."""
        words = (doc.title + " " + doc.content).lower().split()
        for word in set(words):
            if len(word) > 3:  # Skip short words
                if word not in self.doc_index:
                    self.doc_index[word] = []
                if doc.doc_id not in self.doc_index[word]:
                    self.doc_index[word].append(doc.doc_id)


# Global instance
knowledge_base = KnowledgeBaseService()
