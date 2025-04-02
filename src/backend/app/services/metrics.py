from prometheus_client import Counter, Gauge, Histogram, Info, REGISTRY, generate_latest
import time

http_requests_total = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds', 
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'active_requests', 
    'Number of active requests'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds', 
    'Database query duration in seconds',
    ['operation', 'collection']
)

app_info = Info('app_info', 'Application information')

def init_app_info(app_version: str, app_name: str):
    """Initialize application info metrics"""
    app_info.info({
        'version': app_version,
        'name': app_name
    })

class MetricsService:
    @staticmethod
    def get_metrics() -> bytes:
        """Generate the latest metrics in Prometheus format"""
        return generate_latest(REGISTRY)
    
    @staticmethod
    def track_request_start(method: str, endpoint: str):
        """Track the start of an HTTP request"""
        active_requests.inc()
        return time.time()
    
    @staticmethod
    def track_request_end(start_time: float, method: str, endpoint: str, status_code: int):
        """Track the end of an HTTP request"""
        active_requests.dec()
        duration = time.time() - start_time
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def track_db_operation(operation: str, collection: str, duration: float):
        """Track a database operation"""
        db_query_duration_seconds.labels(operation=operation, collection=collection).observe(duration)
