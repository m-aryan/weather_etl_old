import time
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps

# Metrics
api_requests = Counter('weather_api_requests_total', 'Total API requests', ['endpoint', 'method'])
processing_time = Histogram('weather_processing_seconds', 'Time spent processing')
data_quality_score = Gauge('weather_data_quality_score', 'Data quality score')
pipeline_errors = Counter('weather_pipeline_errors_total', 'Pipeline errors', ['stage'])

logger = structlog.get_logger()

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed successfully", duration=time.time() - start_time)
            return result
        except Exception as e:
            pipeline_errors.labels(stage=func.__name__).inc()
            logger.error(f"{func.__name__} failed", error=str(e))
            raise
        finally:
            processing_time.observe(time.time() - start_time)
    return wrapper

def start_metrics_server(port=8001):
    start_http_server(port)
    logger.info(f"Metrics server started on port {port}")

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            raise e