import pandas as pd
import great_expectations as gx
from great_expectations.core import ExpectationSuite
import structlog
from .monitoring import data_quality_score

logger = structlog.get_logger()

class DataQualityValidator:
    def __init__(self):
        self.context = gx.get_context()
    
    def create_weather_expectations(self) -> ExpectationSuite:
        """Create data quality expectations for weather data"""
        suite = self.context.add_expectation_suite("weather_data_suite")
        
        # Temp validations
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="temperature_c", min_value=-50, max_value=60
            )
        )
        
        # Precipitation validatons
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeNonNull(column="precip_mm")
        )
        
        # City validations
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="city", 
                value_set=["New York", "Los Angeles", "Chicago", "Houston", "Miami", 
                          "Seattle", "Denver", "Las Vegas", "Orlando", "Atlanta", 
                          "Boston", "San Francisco"]
            )
        )
        
        return suite
    
    def validate_data(self, df: pd.DataFrame) -> dict:
        """Validate dataframe against expectations"""
        try:
            suite = self.create_weather_expectations()
            validator = self.context.get_validator(
                batch_request=gx.core.batch.RuntimeBatchRequest(
                    datasource_name="pandas_datasource",
                    data_connector_name="runtime_data_connector",
                    data_asset_name="weather_data",
                    runtime_parameters={"batch_data": df},
                    batch_identifiers={"default_identifier_name": "weather_batch"}
                ),
                expectation_suite=suite
            )
            
            results = validator.validate()
            success_rate = results.statistics["successful_expectations"] / results.statistics["evaluated_expectations"]
            
            # Update monitoring metrics
            data_quality_score.set(success_rate)
            
            logger.info("data_quality_check", 
                       success_rate=success_rate,
                       total_expectations=results.statistics["evaluated_expectations"],
                       successful=results.statistics["successful_expectations"])
            
            return {
                "success": results.success,
                "success_rate": success_rate,
                "results": results
            }
        except Exception as e:
            logger.error("data_quality_validation_failed", error=str(e))
            return {"success": False, "error": str(e)}

data_validator = DataQualityValidator()