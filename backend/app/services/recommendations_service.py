"""AI-driven recommendations engine for agent optimization."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Recommendation types."""
    AGENT_TRAINING = "agent_training"
    PROCESS_IMPROVEMENT = "process_improvement"
    COST_REDUCTION = "cost_reduction"
    QUALITY_BOOST = "quality_boost"
    EFFICIENCY_GAIN = "efficiency_gain"
    CUSTOMER_SATISFACTION = "customer_satisfaction"


class RecommendationPriority(str, Enum):
    """Recommendation priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Recommendation:
    """Single recommendation."""
    recommendation_id: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    target: str  # agent_id, process, system
    impact_score: float  # 0-100
    estimated_benefit: Dict[str, Any]  # cost_savings, efficiency_gain, quality_improvement
    action_items: List[str]
    created_at: datetime
    status: str = "pending"  # pending, accepted, rejected, implemented


class RecommendationEngine:
    """AI-driven recommendations engine."""

    def __init__(self):
        """Initialize recommendations engine."""
        self.recommendations: Dict[str, List[Recommendation]] = {}
        self.metrics_history: Dict[str, List[Dict]] = {}

    async def analyze_agent(
        self,
        company_id: str,
        agent_id: str,
        metrics: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Analyze agent metrics and generate recommendations.
        
        Args:
            company_id: Company identifier
            agent_id: Agent identifier
            metrics: Agent metrics (accuracy, handle_time, satisfaction, etc.)
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            # Training recommendations
            if metrics.get("accuracy", 100) < 85:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        agent_id,
                        RecommendationType.AGENT_TRAINING,
                        "Accuracy Improvement Training",
                        f"Agent's accuracy ({metrics.get('accuracy', 0):.1f}%) is below target. Recommend focused training.",
                        estimated_benefit={
                            "accuracy_improvement": "5-10%",
                            "quality_score_impact": "+50-100 points"
                        }
                    )
                )

            # Handle time optimization
            avg_handle_time = metrics.get("avg_handle_time", 0)
            team_avg = metrics.get("team_avg_handle_time", avg_handle_time)

            if avg_handle_time > team_avg * 1.2:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        agent_id,
                        RecommendationType.EFFICIENCY_GAIN,
                        "Handle Time Optimization",
                        f"Agent's handle time is {((avg_handle_time / team_avg - 1) * 100):.0f}% above team average. Consider shadowing top performers.",
                        estimated_benefit={
                            "time_reduction": "10-20%",
                            "cost_savings": f"${(avg_handle_time - team_avg) * 50:.0f}/week"
                        }
                    )
                )

            # Customer satisfaction
            satisfaction = metrics.get("customer_satisfaction", 0)
            if satisfaction < 3.5:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        agent_id,
                        RecommendationType.CUSTOMER_SATISFACTION,
                        "Customer Service Excellence",
                        f"Customer satisfaction score ({satisfaction:.1f}/5) is below target. Soft skills training recommended.",
                        estimated_benefit={
                            "satisfaction_increase": "0.5-1.0 points",
                            "retention_improvement": "5-10%"
                        },
                        priority=RecommendationPriority.HIGH
                    )
                )

            # Store recommendations
            key = f"{company_id}:{agent_id}"
            if key not in self.recommendations:
                self.recommendations[key] = []

            self.recommendations[key].extend(recommendations)

            logger.info(f"Generated {len(recommendations)} recommendations for {agent_id}")
            return recommendations
        except Exception as e:
            logger.error(f"Error analyzing agent: {e}")
            return []

    async def analyze_team(
        self,
        company_id: str,
        agents_metrics: Dict[str, Dict]
    ) -> List[Recommendation]:
        """
        Analyze team metrics and generate recommendations.
        
        Args:
            company_id: Company identifier
            agents_metrics: Dict of agent metrics
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            if not agents_metrics:
                return recommendations

            # Calculate team averages
            accuracies = [m.get("accuracy", 100) for m in agents_metrics.values()]
            satisfactions = [m.get("customer_satisfaction", 0) for m in agents_metrics.values()]
            handle_times = [m.get("avg_handle_time", 0) for m in agents_metrics.values()]

            avg_accuracy = sum(accuracies) / len(accuracies)
            avg_satisfaction = sum(satisfactions) / len(satisfactions)
            avg_handle_time = sum(handle_times) / len(handle_times)

            # Team-wide process improvements
            if avg_accuracy < 90:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        "team",
                        RecommendationType.PROCESS_IMPROVEMENT,
                        "Quality Assurance Program",
                        f"Team accuracy average ({avg_accuracy:.1f}%) is below industry standard (95%). Implement QA program.",
                        estimated_benefit={
                            "accuracy_improvement": "5-15%",
                            "customer_impact": "Significant"
                        },
                        priority=RecommendationPriority.HIGH
                    )
                )

            # Team efficiency
            variance = sum((t - avg_handle_time) ** 2 for t in handle_times) / len(handle_times)
            std_dev = variance ** 0.5

            if std_dev > avg_handle_time * 0.3:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        "team",
                        RecommendationType.EFFICIENCY_GAIN,
                        "Process Standardization",
                        f"High variance in handle times (σ={std_dev:.0f}s). Standardize workflows.",
                        estimated_benefit={
                            "consistency_improvement": "30-40%",
                            "efficiency_gain": "10-15%"
                        }
                    )
                )

            # Knowledge management
            if avg_satisfaction < 4.0:
                recommendations.append(
                    self._create_recommendation(
                        company_id,
                        "team",
                        RecommendationType.CUSTOMER_SATISFACTION,
                        "Knowledge Base Enhancement",
                        "Build comprehensive knowledge base to improve customer satisfaction.",
                        estimated_benefit={
                            "satisfaction_increase": "0.5-1.0 points",
                            "handle_time_reduction": "5-10%"
                        }
                    )
                )

            logger.info(f"Generated {len(recommendations)} team recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Error analyzing team: {e}")
            return []

    async def get_recommendations(
        self,
        company_id: str,
        agent_id: Optional[str] = None,
        priority: Optional[RecommendationPriority] = None,
        status: Optional[str] = None
    ) -> List[Recommendation]:
        """Get recommendations."""
        if agent_id:
            key = f"{company_id}:{agent_id}"
            recs = self.recommendations.get(key, [])
        else:
            recs = []
            for k, v in self.recommendations.items():
                if k.startswith(company_id):
                    recs.extend(v)

        # Filter by priority
        if priority:
            recs = [r for r in recs if r.priority == priority]

        # Filter by status
        if status:
            recs = [r for r in recs if r.status == status]

        return recs

    async def accept_recommendation(
        self,
        recommendation_id: str,
        agent_id: str,
        company_id: str
    ) -> bool:
        """Mark recommendation as accepted."""
        key = f"{company_id}:{agent_id}"
        recs = self.recommendations.get(key, [])

        for rec in recs:
            if rec.recommendation_id == recommendation_id:
                rec.status = "accepted"
                logger.info(f"Accepted recommendation {recommendation_id}")
                return True

        return False

    async def reject_recommendation(
        self,
        recommendation_id: str,
        agent_id: str,
        company_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Mark recommendation as rejected."""
        key = f"{company_id}:{agent_id}"
        recs = self.recommendations.get(key, [])

        for rec in recs:
            if rec.recommendation_id == recommendation_id:
                rec.status = "rejected"
                logger.info(f"Rejected recommendation {recommendation_id}: {reason}")
                return True

        return False

    async def get_impact_score(
        self,
        company_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Calculate agent's potential impact from implementing recommendations.
        
        Returns: {
            "current_productivity": 0-100,
            "potential_productivity": 0-100,
            "improvement_potential": 0-100,
            "estimated_roi": 0-1000
        }
        """
        recs = await self.get_recommendations(company_id, agent_id, status="pending")

        if not recs:
            return {
                "current_productivity": 75.0,
                "potential_productivity": 75.0,
                "improvement_potential": 0.0,
                "estimated_roi": 0.0
            }

        total_impact = sum(r.impact_score for r in recs) / len(recs)

        return {
            "current_productivity": 75.0,
            "potential_productivity": min(75.0 + total_impact * 0.3, 100.0),
            "improvement_potential": min(total_impact * 0.3, 25.0),
            "estimated_roi": total_impact * 5.0
        }

    def _create_recommendation(
        self,
        company_id: str,
        target: str,
        rec_type: RecommendationType,
        title: str,
        description: str,
        estimated_benefit: Dict[str, Any],
        action_items: Optional[List[str]] = None,
        priority: Optional[RecommendationPriority] = None
    ) -> Recommendation:
        """Create recommendation object."""
        import uuid

        # Calculate impact score based on type
        impact_multipliers = {
            RecommendationType.AGENT_TRAINING: 70,
            RecommendationType.PROCESS_IMPROVEMENT: 85,
            RecommendationType.COST_REDUCTION: 80,
            RecommendationType.QUALITY_BOOST: 75,
            RecommendationType.EFFICIENCY_GAIN: 70,
            RecommendationType.CUSTOMER_SATISFACTION: 80
        }

        priority_score_boost = {
            RecommendationPriority.CRITICAL: 20,
            RecommendationPriority.HIGH: 10,
            RecommendationPriority.MEDIUM: 0,
            RecommendationPriority.LOW: -10
        }

        impact = impact_multipliers.get(rec_type, 70)
        priority = priority or RecommendationPriority.MEDIUM
        impact += priority_score_boost.get(priority, 0)

        return Recommendation(
            recommendation_id=str(uuid.uuid4()),
            type=rec_type,
            priority=priority,
            title=title,
            description=description,
            target=target,
            impact_score=impact,
            estimated_benefit=estimated_benefit,
            action_items=action_items or [],
            created_at=datetime.utcnow()
        )


# Global instance
recommendations_engine = RecommendationEngine()
