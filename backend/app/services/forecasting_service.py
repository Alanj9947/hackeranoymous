"""ML Forecasting service with statistical and time-series models."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


class ForecastModel(str, Enum):
    """Available forecasting models."""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    SEASONAL = "seasonal"


class ForecastMetric(str, Enum):
    """Metrics to forecast."""
    CALL_VOLUME = "call_volume"
    CALL_DURATION = "call_duration"
    COST = "cost"
    AGENT_AVAILABILITY = "agent_availability"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    ERROR_RATE = "error_rate"


@dataclass
class DataPoint:
    """Time series data point."""
    timestamp: datetime
    value: float
    metadata: Optional[Dict] = None


@dataclass
class Forecast:
    """Forecast result."""
    metric: ForecastMetric
    model: ForecastModel
    timestamp: datetime
    horizon_days: int
    predictions: List[Tuple[datetime, float]]  # [(timestamp, value), ...]
    confidence_intervals: List[Tuple[float, float]]  # [(lower, upper), ...]
    trend: str  # "increasing", "decreasing", "stable"
    accuracy_score: float
    metadata: Dict = None


class ForecastingService:
    """Service for ML forecasting and predictive analytics."""

    def __init__(self):
        """Initialize forecasting service."""
        self.historical_data: Dict[str, List[DataPoint]] = {}
        self.forecasts: Dict[str, List[Forecast]] = {}
        self.model_cache: Dict[str, Any] = {}

    async def add_data_point(
        self,
        company_id: str,
        metric: ForecastMetric,
        value: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add data point for forecasting.
        
        Args:
            company_id: Company identifier
            metric: Metric type
            value: Data value
            timestamp: Data timestamp
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            timestamp = timestamp or datetime.utcnow()
            key = f"{company_id}:{metric.value}"

            if key not in self.historical_data:
                self.historical_data[key] = []

            point = DataPoint(timestamp, value, metadata)
            self.historical_data[key].append(point)

            # Keep last 365 days
            cutoff = datetime.utcnow() - timedelta(days=365)
            self.historical_data[key] = [
                p for p in self.historical_data[key]
                if p.timestamp >= cutoff
            ]

            return True
        except Exception as e:
            logger.error(f"Error adding data point: {e}")
            return False

    async def forecast(
        self,
        company_id: str,
        metric: ForecastMetric,
        horizon_days: int = 30,
        model: ForecastModel = ForecastModel.EXPONENTIAL_SMOOTHING
    ) -> Optional[Forecast]:
        """
        Generate forecast for metric.
        
        Args:
            company_id: Company identifier
            metric: Metric to forecast
            horizon_days: Forecast horizon (1-90 days)
            model: Forecasting model
            
        Returns:
            Forecast object or None
        """
        try:
            horizon_days = min(horizon_days, 90)
            key = f"{company_id}:{metric.value}"

            # Get historical data
            data = self.historical_data.get(key, [])
            if len(data) < 7:  # Need at least 7 days of data
                logger.warning(f"Insufficient data for {key}")
                return None

            # Sort by timestamp
            data = sorted(data, key=lambda x: x.timestamp)
            values = [p.value for p in data]

            # Generate predictions based on model
            if model == ForecastModel.EXPONENTIAL_SMOOTHING:
                predictions = self._exponential_smoothing(values, horizon_days)
            elif model == ForecastModel.MOVING_AVERAGE:
                predictions = self._moving_average(values, horizon_days)
            elif model == ForecastModel.LINEAR_REGRESSION:
                predictions = self._linear_regression(values, horizon_days)
            elif model == ForecastModel.SEASONAL:
                predictions = self._seasonal_forecast(values, horizon_days)
            elif model == ForecastModel.ARIMA:
                predictions = self._arima_forecast(values, horizon_days)
            else:
                predictions = self._exponential_smoothing(values, horizon_days)

            # Calculate confidence intervals
            confidence = self._calculate_confidence_intervals(values, predictions)

            # Determine trend
            recent = values[-7:]
            avg_recent = sum(recent) / len(recent)
            avg_prior = sum(values[:-7]) / len(values[:-7]) if len(values) > 7 else avg_recent
            
            if avg_recent > avg_prior * 1.1:
                trend = "increasing"
            elif avg_recent < avg_prior * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

            # Calculate accuracy
            accuracy = self._calculate_model_accuracy(values, model)

            # Build timestamp predictions
            last_timestamp = data[-1].timestamp
            timestamp_predictions = []
            for i, value in enumerate(predictions):
                pred_timestamp = last_timestamp + timedelta(days=i+1)
                timestamp_predictions.append((pred_timestamp, value))

            forecast = Forecast(
                metric=metric,
                model=model,
                timestamp=datetime.utcnow(),
                horizon_days=horizon_days,
                predictions=timestamp_predictions,
                confidence_intervals=confidence,
                trend=trend,
                accuracy_score=accuracy,
                metadata={
                    "data_points": len(data),
                    "last_value": values[-1],
                    "avg_value": sum(values) / len(values)
                }
            )

            # Cache forecast
            if company_id not in self.forecasts:
                self.forecasts[company_id] = []

            self.forecasts[company_id].append(forecast)

            logger.info(f"Generated {model.value} forecast for {key}")
            return forecast
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return None

    async def what_if_scenario(
        self,
        company_id: str,
        metric: ForecastMetric,
        adjustment_percent: float,
        horizon_days: int = 30
    ) -> Optional[Forecast]:
        """
        Generate what-if scenario forecast.
        
        Args:
            company_id: Company identifier
            metric: Metric to forecast
            adjustment_percent: Adjustment percentage (-100 to +100)
            horizon_days: Forecast horizon
            
        Returns:
            Adjusted forecast or None
        """
        try:
            # Get base forecast
            base_forecast = await self.forecast(
                company_id,
                metric,
                horizon_days,
                ForecastModel.EXPONENTIAL_SMOOTHING
            )

            if not base_forecast:
                return None

            # Adjust predictions
            multiplier = 1 + (adjustment_percent / 100)
            adjusted_predictions = [
                (ts, value * multiplier)
                for ts, value in base_forecast.predictions
            ]

            # Adjust confidence intervals
            adjusted_intervals = [
                (lower * multiplier, upper * multiplier)
                for lower, upper in base_forecast.confidence_intervals
            ]

            # Create what-if forecast
            forecast = Forecast(
                metric=metric,
                model=ForecastModel.EXPONENTIAL_SMOOTHING,
                timestamp=datetime.utcnow(),
                horizon_days=horizon_days,
                predictions=adjusted_predictions,
                confidence_intervals=adjusted_intervals,
                trend=base_forecast.trend,
                accuracy_score=base_forecast.accuracy_score,
                metadata={
                    **base_forecast.metadata,
                    "scenario": "what_if",
                    "adjustment_percent": adjustment_percent
                }
            )

            return forecast
        except Exception as e:
            logger.error(f"Error generating what-if scenario: {e}")
            return None

    async def detect_anomalies(
        self,
        company_id: str,
        metric: ForecastMetric,
        std_dev_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in time series data.
        
        Args:
            company_id: Company identifier
            metric: Metric to analyze
            std_dev_threshold: Standard deviation threshold
            
        Returns:
            List of detected anomalies
        """
        try:
            key = f"{company_id}:{metric.value}"
            data = self.historical_data.get(key, [])

            if len(data) < 7:
                return []

            values = [p.value for p in sorted(data, key=lambda x: x.timestamp)]

            # Calculate mean and std dev
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = math.sqrt(variance)

            # Detect anomalies
            anomalies = []
            for i, point in enumerate(sorted(data, key=lambda x: x.timestamp)):
                z_score = abs((point.value - mean) / std_dev) if std_dev > 0 else 0

                if z_score > std_dev_threshold:
                    anomalies.append({
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value,
                        "z_score": z_score,
                        "deviation_percent": ((point.value - mean) / mean * 100) if mean > 0 else 0,
                        "metadata": point.metadata
                    })

            logger.info(f"Detected {len(anomalies)} anomalies for {key}")
            return anomalies
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def get_recent_forecast(
        self,
        company_id: str,
        metric: ForecastMetric
    ) -> Optional[Forecast]:
        """Get most recent forecast for metric."""
        forecasts = self.forecasts.get(company_id, [])
        metric_forecasts = [f for f in forecasts if f.metric == metric]
        return metric_forecasts[-1] if metric_forecasts else None

    def _exponential_smoothing(self, values: List[float], horizon: int) -> List[float]:
        """Exponential smoothing forecast."""
        alpha = 0.3  # Smoothing parameter
        result = [values[0]]

        for i in range(1, len(values)):
            smoothed = alpha * values[i] + (1 - alpha) * result[-1]
            result.append(smoothed)

        # Project forward
        last = result[-1]
        forecast = []
        for _ in range(horizon):
            forecast.append(last)

        return forecast

    def _moving_average(self, values: List[float], horizon: int) -> List[float]:
        """Simple moving average forecast."""
        window = 7
        ma = sum(values[-window:]) / window

        return [ma] * horizon

    def _linear_regression(self, values: List[float], horizon: int) -> List[float]:
        """Simple linear regression forecast."""
        n = len(values)
        x_vals = list(range(n))
        y_vals = values

        # Calculate slope and intercept
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n

        numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Project forward
        forecast = []
        for i in range(horizon):
            pred = slope * (n + i) + intercept
            forecast.append(max(pred, 0))  # No negative values

        return forecast

    def _seasonal_forecast(self, values: List[float], horizon: int) -> List[float]:
        """Seasonal decomposition forecast."""
        # Simple seasonal pattern (7-day week)
        if len(values) < 14:
            return self._exponential_smoothing(values, horizon)

        seasonal_period = 7
        seasonal_avg = [0] * seasonal_period

        # Calculate seasonal averages
        for i in range(seasonal_period):
            period_values = [
                values[j] for j in range(i, len(values), seasonal_period)
            ]
            seasonal_avg[i] = sum(period_values) / len(period_values)

        # Project using seasonal pattern
        forecast = []
        for i in range(horizon):
            season_idx = i % seasonal_period
            forecast.append(seasonal_avg[season_idx])

        return forecast

    def _arima_forecast(self, values: List[float], horizon: int) -> List[float]:
        """ARIMA-like forecast (simplified)."""
        # Simplified ARIMA: use exponential smoothing with AR(1) component
        if len(values) < 2:
            return [values[0]] * horizon

        # AR(1) coefficient
        mean = sum(values) / len(values)
        numerator = sum((values[i] - mean) * (values[i-1] - mean) for i in range(1, len(values)))
        denominator = sum((values[i] - mean) ** 2 for i in range(len(values)-1))

        phi = numerator / denominator if denominator != 0 else 0.5

        # Forecast
        forecast = []
        last = values[-1]
        for _ in range(horizon):
            next_val = mean + phi * (last - mean)
            forecast.append(max(next_val, 0))
            last = next_val

        return forecast

    def _calculate_confidence_intervals(
        self,
        historical: List[float],
        predictions: List[float],
        confidence: float = 0.95
    ) -> List[Tuple[float, float]]:
        """Calculate confidence intervals for predictions."""
        # Simplified: use 20% margin for 95% confidence
        margin_percent = 0.20

        intervals = []
        for pred in predictions:
            margin = pred * margin_percent
            lower = max(pred - margin, 0)
            upper = pred + margin
            intervals.append((lower, upper))

        return intervals

    def _calculate_model_accuracy(self, values: List[float], model: ForecastModel) -> float:
        """Calculate model accuracy using cross-validation."""
        if len(values) < 14:
            return 0.75  # Default confidence for small datasets

        # Use last 7 days as test set
        train = values[:-7]
        test = values[-7:]

        # Generate forecast for test period
        if model == ForecastModel.EXPONENTIAL_SMOOTHING:
            pred = self._exponential_smoothing(train, 7)
        elif model == ForecastModel.MOVING_AVERAGE:
            pred = self._moving_average(train, 7)
        elif model == ForecastModel.LINEAR_REGRESSION:
            pred = self._linear_regression(train, 7)
        elif model == ForecastModel.SEASONAL:
            pred = self._seasonal_forecast(train, 7)
        else:
            pred = self._exponential_smoothing(train, 7)

        # Calculate MAPE (Mean Absolute Percentage Error)
        errors = []
        for actual, predicted in zip(test, pred):
            if actual != 0:
                error = abs((actual - predicted) / actual)
                errors.append(error)

        mape = sum(errors) / len(errors) if errors else 0
        accuracy = max(0, 1 - mape)  # Convert to 0-1 scale

        return accuracy


# Global instance
forecasting_service = ForecastingService()
