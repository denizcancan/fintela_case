import time
import datetime
import logging
import pandas as pd
from tefas import Crawler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TefasCrawler:

    def __init__(
        self,
    ):
        """Initialize the TefasCrawler with database settings"""
        self.crawler = Crawler()

    def save_to_db(self, data):
        # TODO: Implement this
        raise NotImplementedError("Not implemented")

    def fetch_historical_data(self, start_date, end_date=None, chunk_size=7):
        """
        Fetch historical data in chunks

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format, defaults to today
            chunk_size: Days per fetch, max 7 days
        """
        if end_date is None:
            end_date = datetime.date.today()
        else:
            if isinstance(end_date, str):
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        # Ensure we're not trying to get future data
        today = datetime.date.today()
        if end_date > today:
            error_message = "End date cannot be in the future"
            logger.error(error_message)
            raise ValueError(error_message)

        if start_date > end_date:
            error_message = "Start date cannot be after end date"
            logger.error(error_message)
            raise ValueError(error_message)

        # Calculate the number of days to fetch
        total_days = (end_date - start_date).days + 1

        logger.info(
            f"Fetching data from {start_date} to {end_date} ({total_days} days)"
        )

        # Create date ranges
        current_date = start_date
        all_data = []

        try:
            while current_date <= end_date:
                # Calculate chunk end date (not exceeding end_date)
                chunk_end = min(
                    current_date + datetime.timedelta(days=chunk_size - 1), end_date
                )

                logger.info(f"Processing from {current_date} to {chunk_end}")

                # Fetch data for the current chunk
                try:
                    data = self.crawler.fetch(
                        start=current_date.strftime("%Y-%m-%d"),
                        end=chunk_end.strftime("%Y-%m-%d"),
                    )

                    if not data.empty:
                        all_data.append(data)
                    else:
                        logger.warning(
                            f"No data returned for {current_date} to {chunk_end}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error fetching data for {current_date} to {chunk_end}: {e}"
                    )

                # Move to the next chunk
                current_date = chunk_end + datetime.timedelta(days=1)

                # Sleep to avoid overloading the server
                time.sleep(1)
            # Replace line 100:
            if len(all_data) > 0:
                return pd.concat(all_data)
            else:
                logger.warning("No data fetched from TEFAS, returning empty DataFrame")
                return pd.DataFrame()  # Return empty DataFrame instead of crashing

        except Exception as e:
            logger.error(f"Error during historical data collection: {e}")
            raise e
