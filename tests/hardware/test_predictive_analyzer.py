"""Tests for predictive resource allocation and power management."""
import unittest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta
from proxmox_nli.core.monitoring.predictive_analyzer import PredictiveAnalyzer
from proxmox_nli.core.monitoring.resource_analyzer import ResourceAnalyzer

class TestPredictiveAnalyzer(unittest.TestCase):
    """Test cases for PredictiveAnalyzer."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_api = Mock()
        self.resource_analyzer = ResourceAnalyzer(self.mock_api)
        self.analyzer = PredictiveAnalyzer(self.resource_analyzer)
        
    def test_predict_resource_needs(self):
        """Test resource needs prediction."""
        # Mock historical data
        mock_history = {
            'success': True,
            'metrics': {
                'cpu': {
                    'values': [20.0, 25.0, 30.0, 35.0, 40.0] * 5,  # Increasing trend
                    'average': 30.0,
                    'peak': 40.0
                },
                'memory': {
                    'values': [50.0, 48.0, 52.0, 49.0, 51.0] * 5,  # Stable trend
                    'average': 50.0,
                    'peak': 52.0
                }
            }
        }
        
        with patch.object(self.resource_analyzer, 'analyze_vm_resources', return_value=mock_history):
            result = self.analyzer.predict_resource_needs('100')
            
            self.assertTrue(result['success'])
            self.assertIn('predictions', result)
            self.assertIn('cpu', result['predictions'])
            self.assertIn('memory', result['predictions'])
            
            # Verify CPU predictions
            cpu_pred = result['predictions']['cpu']
            self.assertEqual(cpu_pred['trend'], 'increasing')
            self.assertEqual(len(cpu_pred['next_24h']), 24)
            
            # Verify memory predictions
            mem_pred = result['predictions']['memory']
            self.assertEqual(mem_pred['trend'], 'stable')
            self.assertEqual(len(mem_pred['next_24h']), 24)
            
            # Verify recommendations
            self.assertGreater(len(result['recommendations']), 0)
            
    def test_analyze_power_efficiency(self):
        """Test power efficiency analysis."""
        # Mock cluster efficiency data
        mock_efficiency = {
            'success': True,
            'metrics': {
                'cpu_usage': 0.15,  # 15% CPU usage - below idle threshold
                'memory_usage': 0.25,  # 25% memory usage - below idle threshold
                'active_nodes': 3
            }
        }
        
        with patch.object(self.resource_analyzer, 'get_cluster_efficiency', return_value=mock_efficiency):
            result = self.analyzer.analyze_power_efficiency()
            
            self.assertTrue(result['success'])
            self.assertIn('metrics', result)
            self.assertIn('recommendations', result)
            
            # Verify metrics
            metrics = result['metrics']
            self.assertIn('cpu_efficiency', metrics)
            self.assertIn('memory_efficiency', metrics)
            self.assertIn('power_saving_potential', metrics)
            
            # Should have consolidation recommendation due to low usage
            recommendations = result['recommendations']
            self.assertTrue(any(r['type'] == 'consolidation' for r in recommendations))
            self.assertTrue(any(r['type'] == 'power_cpu' for r in recommendations))
            
    def test_trend_analysis(self):
        """Test trend analysis function."""
        # Test increasing trend
        increasing_data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.assertEqual(self.analyzer._analyze_trend(increasing_data), 'increasing')
        
        # Test decreasing trend
        decreasing_data = [60.0, 50.0, 40.0, 30.0, 20.0, 10.0]
        self.assertEqual(self.analyzer._analyze_trend(decreasing_data), 'decreasing')
        
        # Test stable trend
        stable_data = [30.0, 31.0, 29.0, 30.5, 29.8, 30.2]
        self.assertEqual(self.analyzer._analyze_trend(stable_data), 'stable')
        
    def test_power_saving_potential(self):
        """Test power saving potential calculation."""
        # Test low utilization case
        potential = self.analyzer._calculate_power_saving_potential(0.2, 0.3)  # 20% CPU, 30% memory
        self.assertGreater(potential, 0)
        
        # Test high utilization case
        potential = self.analyzer._calculate_power_saving_potential(0.8, 0.7)  # 80% CPU, 70% memory
        self.assertEqual(potential, 0.0)
        
    def test_prepare_time_series(self):
        """Test time series data preparation."""
        # Test with values list
        data = {'values': [1.0, 2.0, 3.0]}
        prepared = self.analyzer._prepare_time_series(data)
        self.assertIsInstance(prepared, np.ndarray)
        self.assertEqual(prepared.shape[1], 1)
        
        # Test with averaged data
        data = {'average': 50.0}
        prepared = self.analyzer._prepare_time_series(data)
        self.assertIsInstance(prepared, np.ndarray)
        self.assertEqual(len(prepared), 24)  # Should create 24 points
        
    def test_find_peak_time(self):
        """Test peak time identification."""
        data = [10, 20, 50, 30, 40]  # Peak at index 2
        peak_time = self.analyzer._find_peak_time(data)
        self.assertEqual(peak_time, 2)
        
if __name__ == '__main__':
    unittest.main()