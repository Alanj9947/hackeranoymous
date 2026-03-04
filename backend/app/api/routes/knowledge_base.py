"""Knowledge base search API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.knowledge_base_service import (
    knowledge_base,
    DocumentType
)

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.post("/documents")
async def index_document(
    title: str,
    content: str,
    doc_type: str,
    category: str = "general",
    tags: list = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Index document in knowledge base.
    
    Args:
        title: Document title
        content: Document content
        doc_type: Document type (faq, article, guide, troubleshooting, policy, product)
        category: Document category
        tags: Document tags
        db: Database session
        company_id: Company identifier
        
    Returns:
        Indexing status
    """
    try:
        doc_type_enum = DocumentType(doc_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {doc_type}"
        )

    import uuid
    doc_id = str(uuid.uuid4())

    success = await knowledge_base.index_document(
        company_id,
        doc_id,
        title,
        content,
        doc_type_enum,
        category,
        tags,
        {"source": "api"}
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to index document")

    return {
        "doc_id": doc_id,
        "title": title,
        "indexed": True
    }


@router.get("/search")
async def search_documents(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = None,
    company_id: str = Depends(get_company_id)
):
    """
    Search knowledge base.
    
    Args:
        query: Search query
        limit: Result limit
        category: Filter by category
        company_id: Company identifier
        
    Returns:
        Search results
    """
    results = await knowledge_base.search(
        company_id,
        query,
        limit,
        category
    )

    return results.to_dict()


@router.get("/documents")
async def list_documents(
    category: Optional[str] = None,
    doc_type: Optional[str] = None,
    company_id: str = Depends(get_company_id)
):
    """
    List documents in knowledge base.
    
    Args:
        category: Filter by category
        doc_type: Filter by type
        company_id: Company identifier
        
    Returns:
        List of documents
    """
    doc_type_enum = None
    if doc_type:
        try:
            doc_type_enum = DocumentType(doc_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type: {doc_type}")

    docs = await knowledge_base.list_documents(company_id, category, doc_type_enum)

    return {
        "documents": [d.to_dict() for d in docs],
        "count": len(docs)
    }


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Get specific document.
    
    Args:
        doc_id: Document ID
        company_id: Company identifier
        
    Returns:
        Document details
    """
    doc = await knowledge_base.get_document(company_id, doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc.to_dict()


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Delete document from knowledge base.
    
    Args:
        doc_id: Document ID
        company_id: Company identifier
        
    Returns:
        Deletion status
    """
    success = await knowledge_base.delete_document(company_id, doc_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "doc_id": doc_id,
        "deleted": True
    }


@router.get("/context")
async def get_context_for_query(
    query: str,
    max_docs: int = Query(3, ge=1, le=5),
    company_id: str = Depends(get_company_id)
):
    """
    Get context for LLM from knowledge base.
    
    Args:
        query: User query
        max_docs: Max documents to include
        company_id: Company identifier
        
    Returns:
        Context string for LLM injection
    """
    context = await knowledge_base.get_context_for_query(company_id, query, max_docs)

    return {
        "query": query,
        "context": context,
        "max_docs": max_docs
    }
