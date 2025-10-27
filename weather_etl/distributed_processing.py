import dask.dataframe as dd
import pandas as pd
from dask.distributed import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from .extract import fetch_weather
from .monitoring import monitor_performance
import structlog

logger = structlog.get_logger()


class DistributedProcessor:
    def __init__(self):
        self.client = None

    def start_cluster(self):
        """Start Dask distributed cluster"""
        try:
            # Connect to existing cluster
            self.client = Client("localhost:8786")
        except:
            # Fallback to local cluster
            self.client = Client(processes=False, threads_per_worker=2, n_workers=4)
        logger.info("dask_cluster_started", scheduler=str(self.client.scheduler_info()))

    @monitor_performance
    def process_cities_parallel(self, cities: dict) -> pd.DataFrame:
        """Process multiple cities in parallel using Dask"""
        if not self.client:
            self.start_cluster()

        # Creatioj of delayed computations
        delayed_results = []
        for city, coords in cities.items():
            delayed_df = dd.from_delayed(
                self.client.submit(fetch_weather, coords["lat"], coords["lon"], city)
            )
            delayed_results.append(delayed_df)

        # Combining all results
        combined_df = dd.concat(delayed_results, ignore_index=True)
        return combined_df.compute()

    def close_cluster(self):
        """Close Dask cluster"""
        if self.client:
            self.client.close()


class AsyncProcessor:
    @staticmethod
    async def fetch_weather_async(session, lat, lon, city):
        """Async version of weather fetching"""
        import aiohttp
        from datetime import date, timedelta

        today = date.today()
        start_date = today - timedelta(days=5)

        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={today}"
            f"&hourly=temperature_2m,precipitation"
        )

        async with session.get(url) as response:
            data = await response.json()
            df = pd.DataFrame(data["hourly"])
            df["city"] = city
            return df

    @staticmethod
    async def process_cities_async(cities: dict) -> pd.DataFrame:
        """Process cities asynchronously"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            tasks = [
                AsyncProcessor.fetch_weather_async(
                    session, coords["lat"], coords["lon"], city
                )
                for city, coords in cities.items()
            ]

            results = await asyncio.gather(*tasks)
            return pd.concat(results, ignore_index=True)


distributed_processor = DistributedProcessor()
async_processor = AsyncProcessor()
