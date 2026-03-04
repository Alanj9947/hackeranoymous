"""NLP and sentiment analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.nlp_service import nlp_service

router = APIRouter(prefix="/api/v1/nlp", tags=["nlp"])


@router.post("/sentiment")
async def analyze_sentiment(
    text: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Analyze sentiment of text.
    
    Args:
        text: Text to analyze
        db: Database session
        company_id: Company identifier
        
    Returns:
        Sentiment analysis result
    """
    result = await nlp_service.analyze_sentiment(company_id, text)

    if not result:
        raise HTTPException(status_code=400, detail="Failed to analyze sentiment")

    return {
        "text": result.text,
        "sentiment": result.sentiment.value,
        "score": result.score,
        "confidence": result.confidence,
        "emotions": result.emotions,
        "entities": [
            {
                "text": e.text,
                "type": e.entity_type.value,
                "confidence": e.confidence
            }
            for e in result.entities
        ],
        "keywords": result.keywords
    }


@router.post("/sentiment-batch")
async def analyze_sentiment_batch(
    texts: list,
    company_id: str = Depends(get_company_id)
):
    """
    Analyze sentiment for multiple texts.
    
    Args:
        texts: List of texts to analyze
        company_id: Company identifier
        
    Returns:
        List of sentiment results
    """
    results = await nlp_service.analyze_batch(company_id, texts)

    return {
        "results": [
            {
                "text": r.text,
                "sentiment": r.sentiment.value,
                "score": r.score,
                "confidence": r.confidence
            }
            for r in results
        ],
        "count": len(results)
    }


@router.get("/sentiment-trend")
async def get_sentiment_trend(
    days: int = 7,
    company_id: str = Depends(get_company_id)
):
    """
    Get sentiment trend over time.
    
    Args:
        days: Number of days to analyze
        company_id: Company identifier
        
    Returns:
        Trend analysis
    """
    trend = await nlp_service.get_sentiment_trend(company_id, days)

    if not trend:
        raise HTTPException(status_code=400, detail="No sentiment data available")

    return trend


@router.post("/intent")
async def extract_intent(text: str):
    """
    Extract intent from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Intent classification
    """
    intent = await nlp_service.extract_intent(text)

    return intent


@router.post("/language-detect")
async def detect_language(text: str):
    """
    Detect language of text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language detection result
    """
    language, confidence = await nlp_service.detect_language(text)

    return {
        "language": language,
        "confidence": confidence
    }
