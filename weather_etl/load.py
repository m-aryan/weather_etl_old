import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from .database import engine, WeatherData, DataLineage
from .security import security_manager
import structlog

logger = structlog.get_logger()
Session = sessionmaker(bind=engine)


def save_to_csv(df, filename="data/weather_data.csv"):
    # Save data to csv with encryption for sensitive data
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Anonymize coordinates for privacy
    if "lat" in df.columns and "lon" in df.columns:
        df["lat"] = df["lat"].apply(
            lambda x: security_manager.anonymize_location(x, 0)[0]
        )
        df["lon"] = df["lon"].apply(
            lambda x: security_manager.anonymize_location(0, x)[1]
        )

    df.to_csv(filename, index=False)
    logger.info("data_saved_csv", filename=filename, records=len(df))


def save_to_database(df):
    # Save data to database
    session = Session()
    try:
        for _, row in df.iterrows():
            weather_record = WeatherData(
                city=row["city"],
                timestamp=row["timestamp"],
                temperature_c=row["temperature_C"],
                precip_mm=row["precip_mm"],
                data_source="open_meteo_api",
                processed_at=datetime.utcnow(),
            )
            session.add(weather_record)

        # Add data lineage record
        lineage = DataLineage(
            source_table="api_raw",
            target_table="weather_data",
            transformation="extract_transform_load",
            processed_at=datetime.utcnow(),
        )
        session.add(lineage)

        session.commit()
        logger.info("data_saved_database", records=len(df))

    except Exception as e:
        session.rollback()
        logger.error("database_save_failed", error=str(e))
        raise
    finally:
        session.close()
