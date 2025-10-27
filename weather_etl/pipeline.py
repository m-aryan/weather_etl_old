import pandas as pd
import asyncio
from datetime import datetime
from weather_etl.extract import fetch_weather
from weather_etl.transform import transform_data
from weather_etl.load import save_to_csv, save_to_database
from weather_etl.distributed_processing import distributed_processor, async_processor
from weather_etl.data_quality import data_validator
from weather_etl.monitoring import monitor_performance, start_metrics_server
from weather_etl.security import security_manager
import structlog

logger = structlog.get_logger()

CITIES = {
    "New York": {"lat": 40.71, "lon": -74.01},
    "Los Angeles": {"lat": 34.05, "lon": -118.24},
    "Chicago": {"lat": 41.88, "lon": -87.63},
    "Houston": {"lat": 29.76, "lon": -95.37},
    "Miami": {"lat": 25.77, "lon": -80.19},
    "Seattle": {"lat": 47.61, "lon": -122.33},
    "Denver": {"lat": 39.74, "lon": -104.99},
    "Las Vegas": {"lat": 36.17, "lon": -115.14},
    "Orlando": {"lat": 28.54, "lon": -81.38},
    "Atlanta": {"lat": 33.75, "lon": -84.39},
    "Boston": {"lat": 42.36, "lon": -71.06},
    "San Francisco": {"lat": 37.77, "lon": -122.42},
}

@monitor_performance
def run_etl(cities_filter=None, use_distributed=False):
    """Enhanced ETL pipeline with monitoring and data quality"""
    cities = {k: v for k, v in CITIES.items() if not cities_filter or k in cities_filter}
    
    logger.info("etl_pipeline_started", cities=list(cities.keys()), distributed=use_distributed)
    
    # Audit logging
    security_manager.audit_log("etl_start", "system", "weather_pipeline")
    
    try:
        if use_distributed:
            combined_data = distributed_processor.process_cities_parallel(cities)
        else:
            all_data = []
            for city, coords in cities.items():
                lat, lon = coords["lat"], coords["lon"]
                df = fetch_weather(lat, lon, city)
                df = transform_data(df)
                all_data.append(df)
            combined_data = pd.concat(all_data, ignore_index=True)
        
        # Data quality validation
        quality_results = data_validator.validate_data(combined_data)
        if not quality_results["success"]:
            logger.warning("data_quality_issues", results=quality_results)
        
        # Save to multiple destinations
        save_to_csv(combined_data, "data/weather_data.csv")
        save_to_database(combined_data)
        
        logger.info("etl_pipeline_completed", records_processed=len(combined_data))
        
    except Exception as e:
        logger.error("etl_pipeline_failed", error=str(e))
        raise
    finally:
        security_manager.audit_log("etl_end", "system", "weather_pipeline")

async def run_etl_async(job_id: str, cities_filter=None):
    """Async version of ETL pipeline"""
    cities = {k: v for k, v in CITIES.items() if not cities_filter or k in cities_filter}
    
    logger.info("async_etl_started", job_id=job_id, cities=list(cities.keys()))
    
    try:
        combined_data = await async_processor.process_cities_async(cities)
        combined_data = transform_data(combined_data)
        
        # Data quality validation
        quality_results = data_validator.validate_data(combined_data)
        
        save_to_csv(combined_data, f"data/weather_data_{job_id}.csv")
        save_to_database(combined_data)
        
        logger.info("async_etl_completed", job_id=job_id, records=len(combined_data))
        
    except Exception as e:
        logger.error("async_etl_failed", job_id=job_id, error=str(e))
        raise

def main():
    # Main entry point with monitoring
    start_metrics_server()
    run_etl(use_distributed=True)
