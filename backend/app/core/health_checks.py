"""
Health Check System

This module provides comprehensive health checks for:
- Database connectivity
- Redis connectivity
- External API connectivity
- System resources (CPU, memory)
- Application status
"""

import logging
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import redis
import requests
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class DatabaseHealthCheck:
    """Database connectivity and performance health check."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.name = "database"
    
    async def check(self) -> HealthCheckResult:
        """Perform database health check."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            result = self.db_session.execute(text("SELECT 1"))
            result.fetchone()
            
            # Test query performance
            start_query = time.time()
            result = self.db_session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            query_duration = (time.time() - start_query) * 1000
            
            duration = (time.time() - start_time) * 1000
            
            if query_duration < 100:  # Less than 100ms
                status = HealthStatus.HEALTHY
                message = "Database connection healthy"
            elif query_duration < 500:  # Less than 500ms
                status = HealthStatus.DEGRADED
                message = "Database performance degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Database performance poor"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "query_duration_ms": round(query_duration, 2),
                    "connection_pool_size": self.db_session.bind.pool.size(),
                    "connection_pool_checked_in": self.db_session.bind.pool.checkedin(),
                    "connection_pool_checked_out": self.db_session.bind.pool.checkedout(),
                },
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2)
            )
            
        except SQLAlchemyError as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed",
                details={},
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2),
                error=str(e)
            )

class RedisHealthCheck:
    """Redis connectivity and performance health check."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.name = "redis"
    
    async def check(self) -> HealthCheckResult:
        """Perform Redis health check."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            self.redis_client.ping()
            
            # Test write/read performance
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"
            
            start_write = time.time()
            self.redis_client.setex(test_key, 60, test_value)
            write_duration = (time.time() - start_write) * 1000
            
            start_read = time.time()
            retrieved_value = self.redis_client.get(test_key)
            read_duration = (time.time() - start_read) * 1000
            
            # Clean up test key
            self.redis_client.delete(test_key)
            
            duration = (time.time() - start_time) * 1000
            
            # Determine status based on performance
            if write_duration < 10 and read_duration < 10:
                status = HealthStatus.HEALTHY
                message = "Redis connection healthy"
            elif write_duration < 50 and read_duration < 50:
                status = HealthStatus.DEGRADED
                message = "Redis performance degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Redis performance poor"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "write_duration_ms": round(write_duration, 2),
                    "read_duration_ms": round(read_duration, 2),
                    "connected_clients": self.redis_client.info("clients")["connected_clients"],
                },
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2)
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Redis connection failed",
                details={},
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2),
                error=str(e)
            )

class ExternalAPIHealthCheck:
    """External API connectivity health check."""
    
    def __init__(self, name: str, url: str, timeout: int = 10, headers: Optional[Dict[str, str]] = None):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.headers = headers or {}
    
    async def check(self) -> HealthCheckResult:
        """Perform external API health check."""
        start_time = time.time()
        
        try:
            response = requests.get(
                self.url,
                timeout=self.timeout,
                headers=self.headers
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = f"{self.name} API accessible"
            elif response.status_code < 500:
                status = HealthStatus.DEGRADED
                message = f"{self.name} API responding with status {response.status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{self.name} API error: {response.status_code}"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "status_code": response.status_code,
                    "response_time_ms": round(duration, 2),
                    "url": self.url,
                },
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2)
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"{self.name} API health check failed: {e}")
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"{self.name} API connection failed",
                details={"url": self.url},
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2),
                error=str(e)
            )

class SystemResourceHealthCheck:
    """System resource monitoring health check."""
    
    def __init__(self):
        self.name = "system_resources"
    
    async def check(self) -> HealthCheckResult:
        """Perform system resource health check."""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            duration = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            if cpu_percent < 80 and memory_percent < 80 and disk_percent < 80:
                status = HealthStatus.HEALTHY
                message = "System resources healthy"
            elif cpu_percent < 90 and memory_percent < 90 and disk_percent < 90:
                status = HealthStatus.DEGRADED
                message = "System resources under pressure"
            else:
                status = HealthStatus.UNHEALTHY
                message = "System resources critical"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory_percent, 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk_percent, 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                },
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2)
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"System resource health check failed: {e}")
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="System resource check failed",
                details={},
                timestamp=datetime.utcnow(),
                duration_ms=round(duration, 2),
                error=str(e)
            )

class HealthCheckRegistry:
    """Registry for managing health checks."""
    
    def __init__(self):
        self.checks: List[Any] = []
        self.last_check_time: Optional[datetime] = None
        self.cache_duration = timedelta(seconds=30)  # Cache results for 30 seconds
        self.cached_results: Optional[List[HealthCheckResult]] = None
    
    def register_check(self, check: Any):
        """Register a health check."""
        self.checks.append(check)
        logger.info(f"Registered health check: {check.name}")
    
    async def run_all_checks(self, force_refresh: bool = False) -> List[HealthCheckResult]:
        """Run all registered health checks."""
        # Return cached results if available and not expired
        if (not force_refresh and 
            self.cached_results and 
            self.last_check_time and 
            datetime.utcnow() - self.last_check_time < self.cache_duration):
            return self.cached_results
        
        # Run all checks concurrently
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Health check {self.checks[i].name} failed with exception: {result}")
                processed_results.append(HealthCheckResult(
                    name=self.checks[i].name,
                    status=HealthStatus.UNKNOWN,
                    message="Health check failed with exception",
                    details={},
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        # Cache results
        self.cached_results = processed_results
        self.last_check_time = datetime.utcnow()
        
        return processed_results
    
    def get_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall health status from individual check results."""
        if not results:
            return HealthStatus.UNKNOWN
        
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for result in results:
            status_counts[result.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_summary(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Get a summary of health check results."""
        overall_status = self.get_overall_status(results)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "total_checks": len(results),
            "healthy_checks": len([r for r in results if r.status == HealthStatus.HEALTHY]),
            "degraded_checks": len([r for r in results if r.status == HealthStatus.DEGRADED]),
            "unhealthy_checks": len([r for r in results if r.status == HealthStatus.UNHEALTHY]),
            "unknown_checks": len([r for r in results if r.status == HealthStatus.UNKNOWN]),
            "overall_duration_ms": sum(r.duration_ms for r in results),
        }
