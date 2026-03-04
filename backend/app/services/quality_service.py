"""Call quality scoring service."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class QualityScore(str, Enum):
    """Quality score levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class CallQualityService:
    """Service for analyzing and scoring call quality."""

    def __init__(self):
        """Initialize quality service."""
        self.weights = {
            "completion": 0.40,      # 40% - Was call completed?
            "duration": 0.25,        # 25% - Was duration appropriate?
            "sentiment": 0.20,       # 20% - Was sentiment positive?
            "efficiency": 0.15       # 15% - Was call efficient?
        }

    async def calculate_call_quality(
        self,
        db: AsyncSession,
        call_id: str,
        duration_seconds: int,
        success: bool,
        sentiment_score: Optional[float] = None,
        transcript_length: Optional[int] = None
    ) -> Dict:
        """
        Calculate quality score for a call.
        
        Args:
            db: Database session
            call_id: Call identifier
            duration_seconds: Call duration in seconds
            success: Was call successful
            sentiment_score: Sentiment score (0-1)
            transcript_length: Transcript word count
            
        Returns:
            Quality score data
        """
        scores = {}

        # 1. Completion Score (40%)
        completion_score = 100 if success else 50
        scores["completion"] = {
            "score": completion_score,
            "max": 100,
            "reason": "Call completed successfully" if success else "Call failed or incomplete"
        }

        # 2. Duration Score (25%)
        duration_score = self._calculate_duration_score(duration_seconds)
        scores["duration"] = {
            "score": duration_score,
            "max": 100,
            "reason": self._get_duration_reason(duration_seconds)
        }

        # 3. Sentiment Score (20%)
        sentiment = sentiment_score or 0.5
        sentiment_score_value = int(sentiment * 100)
        scores["sentiment"] = {
            "score": sentiment_score_value,
            "max": 100,
            "reason": self._get_sentiment_reason(sentiment)
        }

        # 4. Efficiency Score (15%)
        efficiency_score = self._calculate_efficiency_score(
            duration_seconds,
            transcript_length or 0
        )
        scores["efficiency"] = {
            "score": efficiency_score,
            "max": 100,
            "reason": self._get_efficiency_reason(duration_seconds, transcript_length)
        }

        # Calculate weighted total
        total_score = (
            scores["completion"]["score"] * self.weights["completion"] +
            scores["duration"]["score"] * self.weights["duration"] +
            scores["sentiment"]["score"] * self.weights["sentiment"] +
            scores["efficiency"]["score"] * self.weights["efficiency"]
        )

        quality_level = self._get_quality_level(total_score)

        return {
            "call_id": call_id,
            "overall_score": round(total_score, 1),
            "quality_level": quality_level,
            "component_scores": scores,
            "calculated_at": datetime.utcnow().isoformat(),
            "recommendations": self._generate_recommendations(scores)
        }

    def _calculate_duration_score(self, duration_seconds: int) -> int:
        """
        Calculate duration appropriateness score.
        Optimal duration is 3-5 minutes (180-300 seconds).
        """
        optimal_min = 180  # 3 minutes
        optimal_max = 300  # 5 minutes

        if optimal_min <= duration_seconds <= optimal_max:
            return 100
        elif duration_seconds < optimal_min:
            # Too short - deduct points
            return max(20, 100 - ((optimal_min - duration_seconds) // 10))
        else:
            # Too long - deduct points
            return max(20, 100 - ((duration_seconds - optimal_max) // 15))

    def _calculate_efficiency_score(self, duration_seconds: int, word_count: int) -> int:
        """
        Calculate efficiency score.
        Optimal is ~150 words per minute.
        """
        if duration_seconds == 0:
            return 0

        minutes = duration_seconds / 60
        words_per_minute = word_count / minutes if minutes > 0 else 0

        optimal_wpm = 150
        tolerance = 50  # +/- 50 words per minute is acceptable

        if optimal_wpm - tolerance <= words_per_minute <= optimal_wpm + tolerance:
            return 100
        elif words_per_minute < optimal_wpm - tolerance:
            # Too slow
            return max(30, 100 - ((optimal_wpm - tolerance - words_per_minute) // 5))
        else:
            # Too fast - might be rushing
            return max(30, 100 - ((words_per_minute - optimal_wpm - tolerance) // 5))

    def _get_quality_level(self, score: float) -> QualityScore:
        """Determine quality level from score."""
        if score >= 85:
            return QualityScore.EXCELLENT
        elif score >= 70:
            return QualityScore.GOOD
        elif score >= 55:
            return QualityScore.FAIR
        else:
            return QualityScore.POOR

    def _get_duration_reason(self, duration_seconds: int) -> str:
        """Get reason for duration score."""
        minutes = duration_seconds / 60
        if 3 <= minutes <= 5:
            return "Optimal call duration"
        elif minutes < 3:
            return f"Call too short ({minutes:.1f} min, target 3-5)"
        else:
            return f"Call too long ({minutes:.1f} min, target 3-5)"

    def _get_sentiment_reason(self, sentiment: float) -> str:
        """Get reason for sentiment score."""
        if sentiment >= 0.7:
            return "Very positive sentiment detected"
        elif sentiment >= 0.5:
            return "Neutral to positive sentiment"
        elif sentiment >= 0.3:
            return "Neutral sentiment"
        else:
            return "Negative sentiment detected"

    def _get_efficiency_reason(self, duration_seconds: int, word_count: int) -> str:
        """Get reason for efficiency score."""
        if duration_seconds == 0:
            return "Unable to calculate efficiency"

        minutes = duration_seconds / 60
        wpm = word_count / minutes if minutes > 0 else 0

        if 100 <= wpm <= 200:
            return f"Good speaking pace ({wpm:.0f} words/min)"
        elif wpm < 100:
            return f"Slow speaking pace ({wpm:.0f} words/min)"
        else:
            return f"Fast speaking pace ({wpm:.0f} words/min)"

    def _generate_recommendations(self, scores: Dict) -> list:
        """Generate improvement recommendations based on scores."""
        recommendations = []

        # Completion recommendations
        if scores["completion"]["score"] < 100:
            recommendations.append({
                "category": "completion",
                "priority": "high",
                "text": "Focus on completing all calls successfully",
                "action": "Review failed call logs to identify patterns"
            })

        # Duration recommendations
        if scores["duration"]["score"] < 70:
            duration_reason = scores["duration"]["reason"]
            if "too short" in duration_reason.lower():
                recommendations.append({
                    "category": "duration",
                    "priority": "medium",
                    "text": "Calls are ending too quickly",
                    "action": "Spend more time on customer needs"
                })
            else:
                recommendations.append({
                    "category": "duration",
                    "priority": "medium",
                    "text": "Calls are running too long",
                    "action": "Improve efficiency and focus"
                })

        # Sentiment recommendations
        if scores["sentiment"]["score"] < 60:
            recommendations.append({
                "category": "sentiment",
                "priority": "high",
                "text": "Customer sentiment is not positive",
                "action": "Review tone and approach with coaching"
            })

        # Efficiency recommendations
        if scores["efficiency"]["score"] < 60:
            recommendations.append({
                "category": "efficiency",
                "priority": "medium",
                "text": "Speech pace is not optimal",
                "action": "Practice speaking at a more natural pace"
            })

        return recommendations

    async def get_agent_quality_metrics(
        self,
        db: AsyncSession,
        agent_id: str,
        days: int = 7
    ) -> Dict:
        """
        Get quality metrics for an agent.
        
        Args:
            db: Database session
            agent_id: Agent identifier
            days: Number of days to analyze
            
        Returns:
            Agent quality metrics
        """
        return {
            "agent_id": agent_id,
            "period_days": days,
            "metrics": {
                "average_quality_score": 0.0,
                "calls_analyzed": 0,
                "excellent_calls": 0,
                "good_calls": 0,
                "fair_calls": 0,
                "poor_calls": 0,
                "quality_trend": "stable",
                "top_strength": "completion_rate",
                "improvement_area": "efficiency"
            },
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def get_quality_trend(
        self,
        db: AsyncSession,
        agent_id: str,
        days: int = 30
    ) -> list:
        """
        Get quality score trend over time.
        
        Args:
            db: Database session
            agent_id: Agent identifier
            days: Number of days to analyze
            
        Returns:
            Trend data points
        """
        trend = []
        for i in range(days, 0, -1):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            # Placeholder: in production, fetch from database
            trend.append({
                "date": date.isoformat(),
                "average_score": 75 + (i % 10),  # Placeholder trend
                "calls_count": 10 + (i % 5)
            })

        return trend

    async def batch_score_calls(
        self,
        db: AsyncSession,
        calls: list
    ) -> list:
        """
        Score multiple calls in batch.
        
        Args:
            db: Database session
            calls: List of call data
            
        Returns:
            List of scored calls
        """
        scored_calls = []
        for call in calls:
            score = await self.calculate_call_quality(
                db,
                call.get("call_id"),
                call.get("duration_seconds", 0),
                call.get("success", False),
                call.get("sentiment_score"),
                call.get("transcript_length")
            )
            scored_calls.append(score)

        return scored_calls

    def get_quality_stats_summary(self, scores: list) -> Dict:
        """
        Get summary statistics from a list of quality scores.
        
        Args:
            scores: List of quality scores
            
        Returns:
            Summary statistics
        """
        if not scores:
            return {
                "total_calls": 0,
                "average_score": 0,
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0
            }

        overall_scores = [s["overall_score"] for s in scores]
        quality_levels = [s["quality_level"] for s in scores]

        return {
            "total_calls": len(scores),
            "average_score": round(sum(overall_scores) / len(overall_scores), 1),
            "median_score": round(sorted(overall_scores)[len(overall_scores) // 2], 1),
            "min_score": round(min(overall_scores), 1),
            "max_score": round(max(overall_scores), 1),
            "excellent": quality_levels.count(QualityScore.EXCELLENT.value),
            "good": quality_levels.count(QualityScore.GOOD.value),
            "fair": quality_levels.count(QualityScore.FAIR.value),
            "poor": quality_levels.count(QualityScore.POOR.value)
        }


# Global instance
call_quality_service = CallQualityService()
