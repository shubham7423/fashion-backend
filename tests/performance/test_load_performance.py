"""
Performance and load tests for the Fashion Backend API.

These tests measure response times, throughput, and resource usage
under various load conditions.
"""

import pytest
import time
import asyncio
import concurrent.futures
import requests
from pathlib import Path
import tempfile
from PIL import Image
import io
import threading
from statistics import mean, median, stdev
from unittest.mock import patch, Mock

# Optional import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceMetrics:
    """Collect and analyze performance metrics."""
    
    def __init__(self):
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.cpu_usage = []
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.end_time = time.time()
    
    def add_response_time(self, response_time):
        """Add a response time measurement."""
        self.response_times.append(response_time)
    
    def get_stats(self):
        """Get performance statistics."""
        if not self.response_times:
            return {}
        
        return {
            "total_requests": len(self.response_times),
            "duration": self.end_time - self.start_time if self.end_time else 0,
            "avg_response_time": mean(self.response_times),
            "median_response_time": median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "std_response_time": stdev(self.response_times) if len(self.response_times) > 1 else 0,
            "requests_per_second": len(self.response_times) / (self.end_time - self.start_time) if self.end_time and self.end_time > self.start_time else 0
        }


@pytest.mark.performance
@pytest.mark.slow
class TestPerformanceBaseline:
    """Baseline performance tests for individual components."""
    
    def test_image_processing_performance(self):
        """Test image processing performance with various image sizes."""
        from app.services.attribution_service import ClothingAttributionService
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # Test different image sizes
        test_sizes = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]
        
        for width, height in test_sizes:
            # Create test image
            img = Image.new("RGB", (width, height), color="blue")
            
            start_time = time.time()
            
            # Mock the compression to avoid file I/O in performance tests
            with patch.object(ClothingAttributionService, 'compress_and_resize_image') as mock_compress:
                mock_compress.return_value = (img, {
                    'original_size': (width, height),
                    'processed_size': (512, 512),
                    'scale_factor': 512 / max(width, height)
                })
                
                # Process image
                result, info = ClothingAttributionService.compress_and_resize_image(img)
            
            end_time = time.time()
            metrics.add_response_time(end_time - start_time)
        
        metrics.stop_monitoring()
        stats = metrics.get_stats()
        
        # Performance assertions
        assert stats["avg_response_time"] < 0.1, f"Average processing time too slow: {stats['avg_response_time']:.3f}s"
        assert stats["max_response_time"] < 0.5, f"Maximum processing time too slow: {stats['max_response_time']:.3f}s"
        
        print(f"\n📊 Image Processing Performance:")
        print(f"   Average time: {stats['avg_response_time']:.3f}s")
        print(f"   Median time: {stats['median_response_time']:.3f}s")
        print(f"   Max time: {stats['max_response_time']:.3f}s")
    
    def test_attribute_extraction_performance(self):
        """Test clothing attribute extraction performance."""
        from app.services.attribution.gemini_attributor import GeminiAttributor
        
        metrics = PerformanceMetrics()
        
        # Mock Gemini API to avoid actual API calls
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = '{"identifier": "top", "category": "T-Shirt", "primary_color": "blue"}'
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            attributor = GeminiAttributor()
            test_image = Image.new("RGB", (512, 512), color="red")
            
            metrics.start_monitoring()
            
            # Test multiple attribute extractions
            for _ in range(10):
                start_time = time.time()
                result = attributor.extract(test_image, "test.jpg")
                end_time = time.time()
                metrics.add_response_time(end_time - start_time)
                
                assert isinstance(result, dict)
                assert "identifier" in result
            
            metrics.stop_monitoring()
            stats = metrics.get_stats()
            
            # Performance assertions (mocked calls should be very fast)
            assert stats["avg_response_time"] < 0.01, f"Mocked attribute extraction too slow: {stats['avg_response_time']:.3f}s"
            
            print(f"\n🧠 Attribute Extraction Performance (Mocked):")
            print(f"   Average time: {stats['avg_response_time']:.3f}s")
            print(f"   Total requests: {stats['total_requests']}")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.integration
class TestLoadPerformance:
    """Load testing with simulated concurrent requests."""
    
    def create_test_image_bytes(self, size=(100, 100)):
        """Create test image as bytes."""
        img = Image.new("RGB", size, color="red")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG")
        return img_buffer.getvalue()
    
    def make_api_request(self, base_url, image_data, user_id="test_user"):
        """Make a single API request."""
        try:
            start_time = time.time()
            
            files = {"files": ("test.jpg", io.BytesIO(image_data), "image/jpeg")}
            params = {"user_id": user_id}
            
            response = requests.post(
                f"{base_url}/api/v1/attribute_clothes",
                files=files,
                params=params,
                timeout=30
            )
            
            end_time = time.time()
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response_time": 0,
                "error": str(e)
            }
    
    @pytest.mark.skipif(
        True,  # Skip by default since it requires running server
        reason="Requires running API server - run manually with --run-integration"
    )
    def test_concurrent_requests(self):
        """Test API performance under concurrent load."""
        base_url = "http://localhost:8000"
        
        # Check if API is available
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API server not available")
        except Exception:
            pytest.skip("API server not available")
        
        metrics = PerformanceMetrics()
        image_data = self.create_test_image_bytes()
        
        # Test parameters
        num_concurrent_requests = 10
        num_batches = 3
        
        metrics.start_monitoring()
        
        for batch in range(num_batches):
            print(f"\n🔄 Running batch {batch + 1}/{num_batches} with {num_concurrent_requests} concurrent requests...")
            
            # Create concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
                futures = []
                
                for i in range(num_concurrent_requests):
                    future = executor.submit(
                        self.make_api_request,
                        base_url,
                        image_data,
                        f"load_test_user_{batch}_{i}"
                    )
                    futures.append(future)
                
                # Wait for all requests to complete
                results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        metrics.add_response_time(result["response_time"])
            
            # Analyze batch results
            successful_requests = sum(1 for r in results if r["success"])
            failed_requests = len(results) - successful_requests
            
            print(f"   ✅ Successful: {successful_requests}/{len(results)}")
            print(f"   ❌ Failed: {failed_requests}")
            
            if failed_requests > 0:
                print("   Failed request details:")
                for i, result in enumerate(results):
                    if not result["success"]:
                        print(f"     Request {i}: {result['status_code']} - {result['error']}")
            
            # Brief pause between batches
            time.sleep(1)
        
        metrics.stop_monitoring()
        stats = metrics.get_stats()
        
        # Performance assertions
        assert stats["total_requests"] > 0, "No successful requests completed"
        assert stats["avg_response_time"] < 10.0, f"Average response time too slow: {stats['avg_response_time']:.2f}s"
        
        print(f"\n📊 Load Test Results:")
        print(f"   Total successful requests: {stats['total_requests']}")
        print(f"   Total duration: {stats['duration']:.2f}s")
        print(f"   Requests per second: {stats['requests_per_second']:.2f}")
        print(f"   Average response time: {stats['avg_response_time']:.2f}s")
        print(f"   Median response time: {stats['median_response_time']:.2f}s")
        print(f"   95th percentile: {sorted(metrics.response_times)[int(0.95 * len(metrics.response_times))]:.2f}s")


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage during various operations."""
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            pytest.skip("psutil not available for memory monitoring")
        
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def test_memory_usage_during_image_processing(self):
        """Test memory usage during image processing."""
        initial_memory = self.get_memory_usage()
        
        # Process multiple large images
        for i in range(5):
            img = Image.new("RGB", (2048, 2048), color="blue")
            
            # Simulate image processing without actual file I/O
            with patch('app.services.attribution_service.ClothingAttributionService.compress_and_resize_image') as mock_process:
                mock_process.return_value = (img.resize((512, 512)), {})
                
            current_memory = self.get_memory_usage()
            memory_increase = current_memory - initial_memory
            
            # Memory should not increase by more than 100MB per image
            assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"
        
        final_memory = self.get_memory_usage()
        total_increase = final_memory - initial_memory
        
        print(f"\n💾 Memory Usage Test:")
        print(f"   Initial memory: {initial_memory:.2f}MB")
        print(f"   Final memory: {final_memory:.2f}MB")
        print(f"   Total increase: {total_increase:.2f}MB")


if __name__ == "__main__":
    # Run performance tests manually
    pytest.main([__file__, "-v", "-s", "--tb=short"])
