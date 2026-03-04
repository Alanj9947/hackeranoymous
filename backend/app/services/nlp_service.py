"""NLP and sentiment analysis service."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SentimentScore(str, Enum):
    """Sentiment classification."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    LOCATION = "location"
    ISSUE = "issue"


@dataclass
class Entity:
    """Named entity."""
    text: str
    entity_type: EntityType
    confidence: float
    metadata: Optional[Dict] = None


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    sentiment: SentimentScore
    score: float  # -1.0 to 1.0
    confidence: float
    emotions: Dict[str, float]  # anger, joy, sadness, fear, surprise
    entities: List[Entity]
    keywords: List[str]
    language: str
    timestamp: datetime


class NLPService:
    """Natural language processing and sentiment analysis service."""

    def __init__(self):
        """Initialize NLP service."""
        self.sentiment_history: Dict[str, List[SentimentResult]] = {}
        self.entity_cache: Dict[str, List[Entity]] = {}

    async def analyze_sentiment(
        self,
        company_id: str,
        text: str,
        context: Optional[Dict] = None
    ) -> Optional[SentimentResult]:
        """
        Analyze sentiment of text.
        
        Args:
            company_id: Company identifier
            text: Text to analyze
            context: Optional context
            
        Returns:
            SentimentResult or None
        """
        try:
            if not text or len(text.strip()) == 0:
                return None

            # Sentiment scoring
            sentiment_score = self._calculate_sentiment(text)
            sentiment, confidence = self._score_to_sentiment(sentiment_score)

            # Emotion detection
            emotions = self._detect_emotions(text)

            # Entity extraction
            entities = await self._extract_entities(text)

            # Keyword extraction
            keywords = self._extract_keywords(text)

            result = SentimentResult(
                text=text,
                sentiment=sentiment,
                score=sentiment_score,
                confidence=confidence,
                emotions=emotions,
                entities=entities,
                keywords=keywords,
                language="en",
                timestamp=datetime.utcnow()
            )

            # Store in history
            if company_id not in self.sentiment_history:
                self.sentiment_history[company_id] = []

            self.sentiment_history[company_id].append(result)

            # Keep last 1000 results
            if len(self.sentiment_history[company_id]) > 1000:
                self.sentiment_history[company_id] = self.sentiment_history[company_id][-1000:]

            logger.info(f"Analyzed sentiment: {sentiment.value} ({confidence:.2%})")
            return result
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return None

    async def analyze_batch(
        self,
        company_id: str,
        texts: List[str]
    ) -> List[SentimentResult]:
        """Analyze sentiment for multiple texts."""
        results = []

        for text in texts:
            result = await self.analyze_sentiment(company_id, text)
            if result:
                results.append(result)

        return results

    async def get_sentiment_trend(
        self,
        company_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get sentiment trend over time.
        
        Args:
            company_id: Company identifier
            days: Days to analyze
            
        Returns:
            Trend analysis
        """
        try:
            history = self.sentiment_history.get(company_id, [])
            if not history:
                return {}

            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)

            recent = [r for r in history if r.timestamp >= cutoff]

            if not recent:
                return {}

            # Calculate average sentiment score
            avg_score = sum(r.score for r in recent) / len(recent)

            # Count by sentiment
            sentiment_counts = {}
            for result in recent:
                sentiment_val = result.sentiment.value
                sentiment_counts[sentiment_val] = sentiment_counts.get(sentiment_val, 0) + 1

            # Average emotions
            emotion_avgs = {}
            emotion_keys = list(recent[0].emotions.keys())

            for emotion in emotion_keys:
                avg = sum(r.emotions.get(emotion, 0) for r in recent) / len(recent)
                emotion_avgs[emotion] = avg

            # Trend direction
            if len(recent) > 1:
                first_half = recent[:len(recent)//2]
                second_half = recent[len(recent)//2:]
                first_avg = sum(r.score for r in first_half) / len(first_half)
                second_avg = sum(r.score for r in second_half) / len(second_half)

                if second_avg > first_avg * 1.05:
                    trend = "improving"
                elif second_avg < first_avg * 0.95:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            return {
                "average_score": avg_score,
                "sentiment_distribution": sentiment_counts,
                "emotion_averages": emotion_avgs,
                "trend": trend,
                "sample_size": len(recent)
            }
        except Exception as e:
            logger.error(f"Error calculating sentiment trend: {e}")
            return {}

    async def extract_intent(self, text: str) -> Dict[str, Any]:
        """
        Extract intent from text.
        
        Returns: {
            "primary_intent": "complaint|question|feedback|request",
            "confidence": 0.0-1.0,
            "related_intents": []
        }
        """
        text_lower = text.lower()

        # Intent patterns
        complaint_words = ["issue", "problem", "broken", "not working", "error", "bug", "fail"]
        question_words = ["?", "how", "what", "when", "where", "why", "which"]
        feedback_words = ["great", "excellent", "good", "bad", "worse", "better", "love", "hate"]
        request_words = ["please", "want", "need", "request", "can", "could", "would"]

        scores = {
            "complaint": sum(1 for word in complaint_words if word in text_lower) / len(complaint_words),
            "question": sum(1 for word in question_words if word in text_lower) / len(question_words),
            "feedback": sum(1 for word in feedback_words if word in text_lower) / len(feedback_words),
            "request": sum(1 for word in request_words if word in text_lower) / len(request_words)
        }

        primary = max(scores.items(), key=lambda x: x[1])
        confidence = primary[1]

        return {
            "primary_intent": primary[0],
            "confidence": min(confidence, 1.0),
            "related_intents": [
                k for k, v in sorted(
                    scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[1:3]
            ]
        }

    async def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language of text. Returns (language_code, confidence)."""
        # Simplified language detection
        # For now, assume English
        return ("en", 0.95)

    def _calculate_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score (-1.0 to 1.0).
        
        Simple lexicon-based approach.
        """
        positive_words = {
            "good": 0.8, "great": 0.9, "excellent": 1.0, "amazing": 1.0,
            "love": 0.9, "awesome": 1.0, "wonderful": 0.9, "perfect": 1.0,
            "happy": 0.8, "pleased": 0.7, "satisfied": 0.7, "helpful": 0.7,
            "best": 0.9, "better": 0.6, "nice": 0.7, "brilliant": 0.9
        }

        negative_words = {
            "bad": -0.8, "terrible": -1.0, "awful": -1.0, "horrible": -1.0,
            "hate": -0.9, "useless": -1.0, "worst": -1.0, "disappointing": -0.8,
            "unhappy": -0.8, "frustrated": -0.7, "angry": -0.8, "annoyed": -0.6,
            "broken": -0.9, "error": -0.7, "fail": -0.8, "problem": -0.6
        }

        text_lower = text.lower()
        words = text_lower.split()

        scores = []
        for word in words:
            word_clean = word.strip(".,!?;:")
            if word_clean in positive_words:
                scores.append(positive_words[word_clean])
            elif word_clean in negative_words:
                scores.append(negative_words[word_clean])

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def _score_to_sentiment(self, score: float) -> Tuple[SentimentScore, float]:
        """Convert numeric score to sentiment classification."""
        abs_score = abs(score)

        if score >= 0.7:
            return (SentimentScore.VERY_POSITIVE, abs_score)
        elif score >= 0.3:
            return (SentimentScore.POSITIVE, abs_score)
        elif score <= -0.7:
            return (SentimentScore.VERY_NEGATIVE, abs_score)
        elif score <= -0.3:
            return (SentimentScore.NEGATIVE, abs_score)
        else:
            return (SentimentScore.NEUTRAL, 0.5)

    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotions in text."""
        emotion_keywords = {
            "anger": ["angry", "furious", "mad", "frustrated", "irritated"],
            "joy": ["happy", "joyful", "excited", "delighted", "wonderful"],
            "sadness": ["sad", "unhappy", "disappointed", "depressed", "down"],
            "fear": ["afraid", "scared", "worried", "anxious", "nervous"],
            "surprise": ["surprised", "shocked", "amazed", "astonished"]
        }

        text_lower = text.lower()
        emotions = {}

        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            emotions[emotion] = min(count / len(keywords), 1.0)

        return emotions

    async def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text."""
        entities = []

        # Simple entity patterns
        entity_patterns = {
            EntityType.PRODUCT: ["product", "service", "app", "software", "feature"],
            EntityType.ISSUE: ["issue", "problem", "error", "bug", "complaint"],
        }

        text_lower = text.lower()
        words = text_lower.split()

        for word in words:
            word_clean = word.strip(".,!?;:")

            for entity_type, patterns in entity_patterns.items():
                if word_clean in patterns:
                    entities.append(
                        Entity(
                            text=word_clean,
                            entity_type=entity_type,
                            confidence=0.8
                        )
                    )

        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction: words > 4 characters, not common words
        stop_words = {
            "the", "is", "at", "which", "on", "and", "a", "an", "or",
            "but", "in", "with", "to", "for", "of", "from", "by"
        }

        words = text.lower().split()
        keywords = []

        for word in words:
            word_clean = word.strip(".,!?;:")
            if len(word_clean) > 4 and word_clean not in stop_words:
                keywords.append(word_clean)

        return list(dict.fromkeys(keywords))[:10]  # Top 10


# Global instance
nlp_service = NLPService()
