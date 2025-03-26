"""
Predictive resource allocation and power management module.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from .resource_analyzer import ResourceAnalyzer

logger = logging.getLogger(__name__)

class PredictiveAnalyzer:
    """Analyzes resource usage patterns and predicts future requirements."""
    
    def __init__(self, resource_analyzer: ResourceAnalyzer):
        """Initialize the predictive analyzer.
        
        Args:
            resource_analyzer: ResourceAnalyzer instance for historical data
        """
        self.resource_analyzer = resource_analyzer
        self.scaler = StandardScaler()
        self.models = {}
        self.power_thresholds = {
            'cpu_idle': 0.2,  # CPU usage below 20% indicates potential power saving
            'memory_idle': 0.3,  # Memory usage below 30% indicates potential power saving
            'consolidation_threshold': 0.4  # Overall usage below 40% suggests consolidation
        }
        
    def predict_resource_needs(self, vm_id: str, hours_ahead: int = 24) -> Dict:
        """Predict future resource requirements for a VM.
        
        Args:
            vm_id: VM identifier
            hours_ahead: Number of hours to predict ahead
            
        Returns:
            Dict with predicted resource requirements
        """
        try:
            # Get historical data for the past week
            history = self.resource_analyzer.analyze_vm_resources(vm_id, days=7)
            if not history.get('success'):
                return {"success": False, "message": "Failed to get historical data"}
            
            metrics = history['metrics']
            predictions = {}
            
            # Predict CPU usage
            if 'cpu' in metrics:
                cpu_data = self._prepare_time_series(metrics['cpu'])
                cpu_prediction = self._train_and_predict('cpu_' + vm_id, cpu_data, hours_ahead)
                predictions['cpu'] = {
                    'next_24h': cpu_prediction,
                    'trend': self._analyze_trend(cpu_prediction),
                    'peak_time': self._find_peak_time(cpu_prediction)
                }
            
            # Predict memory usage
            if 'memory' in metrics:
                memory_data = self._prepare_time_series(metrics['memory'])
                memory_prediction = self._train_and_predict('memory_' + vm_id, memory_data, hours_ahead)
                predictions['memory'] = {
                    'next_24h': memory_prediction,
                    'trend': self._analyze_trend(memory_prediction),
                    'peak_time': self._find_peak_time(memory_prediction)
                }
            
            return {
                "success": True,
                "predictions": predictions,
                "recommendations": self._generate_predictive_recommendations(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error predicting resource needs: {str(e)}")
            return {"success": False, "message": str(e)}
            
    def analyze_power_efficiency(self, node_id: str = None) -> Dict:
        """Analyze power efficiency and generate recommendations.
        
        Args:
            node_id: Optional node identifier. If None, analyzes all nodes.
            
        Returns:
            Dict with power efficiency analysis and recommendations
        """
        try:
            # Get cluster efficiency metrics
            efficiency = self.resource_analyzer.get_cluster_efficiency()
            if not efficiency.get('success'):
                return {"success": False, "message": "Failed to get cluster efficiency"}
            
            metrics = efficiency['metrics']
            recommendations = []
            
            # Analyze CPU efficiency
            cpu_usage = metrics.get('cpu_usage', 0)
            if cpu_usage < self.power_thresholds['cpu_idle']:
                recommendations.append({
                    'type': 'power_cpu',
                    'severity': 'medium',
                    'message': f'Low CPU utilization ({cpu_usage:.1f}%). Consider power-saving measures.',
                    'actions': [
                        'Enable CPU frequency scaling',
                        'Consolidate VMs to fewer nodes',
                        'Put idle nodes into standby'
                    ],
                    'savings': 'Reduced power consumption and cooling requirements'
                })
            
            # Analyze memory efficiency
            memory_usage = metrics.get('memory_usage', 0)
            if memory_usage < self.power_thresholds['memory_idle']:
                recommendations.append({
                    'type': 'power_memory',
                    'severity': 'medium',
                    'message': f'Low memory utilization ({memory_usage:.1f}%). Consider optimization.',
                    'actions': [
                        'Reduce memory allocation to over-provisioned VMs',
                        'Enable memory ballooning',
                        'Consider VM consolidation'
                    ],
                    'savings': 'Lower power consumption and improved memory utilization'
                })
            
            # Check if consolidation is possible
            if cpu_usage < self.power_thresholds['consolidation_threshold'] and \
               memory_usage < self.power_thresholds['consolidation_threshold']:
                recommendations.append({
                    'type': 'consolidation',
                    'severity': 'high',
                    'message': 'Low overall resource utilization. Node consolidation recommended.',
                    'actions': [
                        'Identify VMs for migration',
                        'Plan consolidation schedule',
                        'Consider putting unused nodes in standby'
                    ],
                    'savings': 'Significant power savings through better resource utilization'
                })
            
            return {
                "success": True,
                "metrics": {
                    "cpu_efficiency": cpu_usage,
                    "memory_efficiency": memory_usage,
                    "power_saving_potential": self._calculate_power_saving_potential(cpu_usage, memory_usage)
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing power efficiency: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _prepare_time_series(self, metric_data: Dict) -> np.ndarray:
        """Prepare time series data for prediction."""
        values = []
        if 'values' in metric_data:
            values = metric_data['values']
        elif isinstance(metric_data, dict):
            # Handle averaged data
            values = [metric_data.get('average', 0)] * 24  # Use average as baseline
        
        return np.array(values).reshape(-1, 1)
        
    def _train_and_predict(self, model_key: str, data: np.ndarray, hours_ahead: int) -> List[float]:
        """Train model and generate predictions."""
        if len(data) < 24:  # Need at least 24 hours of data
            return [float(data[0])] * hours_ahead
            
        # Prepare training data
        X = np.arange(len(data)).reshape(-1, 1)
        y = data.ravel()
        
        # Scale data
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Generate future time points
        future_X = np.arange(len(data), len(data) + hours_ahead).reshape(-1, 1)
        future_X_scaled = self.scaler.transform(future_X)
        
        # Make predictions
        predictions = model.predict(future_X_scaled)
        
        # Store model for future use
        self.models[model_key] = {
            'model': model,
            'scaler': self.scaler,
            'last_trained': datetime.now()
        }
        
        return predictions.tolist()
        
    def _analyze_trend(self, predictions: List[float]) -> str:
        """Analyze trend in predictions."""
        if len(predictions) < 2:
            return 'stable'
            
        start_avg = sum(predictions[:6]) / 6  # Average of first 6 hours
        end_avg = sum(predictions[-6:]) / 6   # Average of last 6 hours
        
        diff = end_avg - start_avg
        if abs(diff) < 0.1 * start_avg:  # Less than 10% change
            return 'stable'
        return 'increasing' if diff > 0 else 'decreasing'
        
    def _find_peak_time(self, predictions: List[float]) -> int:
        """Find hour with peak predicted usage."""
        return predictions.index(max(predictions))
        
    def _calculate_power_saving_potential(self, cpu_usage: float, memory_usage: float) -> float:
        """Calculate potential power savings percentage."""
        # Simple model: assume linear relationship between resource usage and power
        avg_usage = (cpu_usage + memory_usage) / 2
        if avg_usage < self.power_thresholds['consolidation_threshold']:
            return (self.power_thresholds['consolidation_threshold'] - avg_usage) * 100
        return 0.0
        
    def _generate_predictive_recommendations(self, predictions: Dict) -> List[Dict]:
        """Generate recommendations based on predictions."""
        recommendations = []
        
        # Analyze CPU predictions
        if 'cpu' in predictions:
            cpu_pred = predictions['cpu']
            if cpu_pred['trend'] == 'increasing':
                recommendations.append({
                    'type': 'predictive_cpu',
                    'severity': 'high',
                    'message': 'CPU usage trending upward. Plan for increased demand.',
                    'actions': [
                        'Schedule CPU allocation increase',
                        'Monitor application performance',
                        'Review scaling policies'
                    ],
                    'timeframe': 'Next 24 hours'
                })
            
            # Add peak time recommendation if significant
            peak_hour = cpu_pred['peak_time']
            if max(cpu_pred['next_24h']) > 80:
                recommendations.append({
                    'type': 'predictive_cpu_peak',
                    'severity': 'medium',
                    'message': f'High CPU usage predicted at hour {peak_hour}',
                    'actions': [
                        'Schedule resource-intensive tasks around peak',
                        'Consider temporary CPU boost during peak'
                    ],
                    'timeframe': f'Hour {peak_hour}'
                })
        
        # Analyze memory predictions
        if 'memory' in predictions:
            mem_pred = predictions['memory']
            if mem_pred['trend'] == 'increasing':
                recommendations.append({
                    'type': 'predictive_memory',
                    'severity': 'high',
                    'message': 'Memory usage trending upward. Plan for increased demand.',
                    'actions': [
                        'Schedule memory allocation increase',
                        'Monitor swap usage',
                        'Review memory-intensive processes'
                    ],
                    'timeframe': 'Next 24 hours'
                })
            
            # Add peak time recommendation if significant
            peak_hour = mem_pred['peak_time']
            if max(mem_pred['next_24h']) > 85:
                recommendations.append({
                    'type': 'predictive_memory_peak',
                    'severity': 'medium',
                    'message': f'High memory usage predicted at hour {peak_hour}',
                    'actions': [
                        'Schedule memory-intensive tasks around peak',
                        'Consider temporary memory boost during peak'
                    ],
                    'timeframe': f'Hour {peak_hour}'
                })
        
        return recommendations