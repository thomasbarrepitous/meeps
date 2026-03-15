import time
from mwrogue.esports_client import EsportsClient
from mwclient.errors import APIError

from meeps.logger import leaguepedia_parser_logger as logger


class LeaguepediaSite:
    """A ghost loaded class that handles Leaguepedia connection and some caching.

    Full documentation: https://lol.fandom.com/Help:API_Documentation
    """

    def __init__(self, limit=500, max_retries=5, base_wait_time=5):
        self._site = None
        self.limit = limit
        self.max_retries = max_retries
        self.base_wait_time = base_wait_time

    @property
    def site(self):
        if not self._site:
            self._load_site()

        return self._site

    def _load_site(self):
        """Creates site class fields.

        Used for ghost loading the class during package import.
        """
        # If not, we create the self.client object as our way to interact with the wiki
        self._site = EsportsClient("lol")

    def query(self, **kwargs) -> list:
        """Issues a cargo query to leaguepedia.

        Params are usually:
            tables, join_on, fields, order_by, where

        Returns:
            List of rows from the query.
        """
        result = []

        # We check if we hit the API limit
        while len(result) % self.limit == 0:
            retry_count = 0

            while retry_count < self.max_retries:
                try:
                    result.extend(
                        self.site.cargo_client.query(
                            limit=self.limit, offset=len(result), **kwargs
                        )
                    )
                    break  # Success, exit retry loop

                except APIError as e:
                    if e.code == 'ratelimited' and retry_count < self.max_retries - 1:
                        wait_time = self.base_wait_time * (2 ** retry_count)
                        logger.warning(f"Rate limited by Leaguepedia API. Waiting {wait_time}s before retry {retry_count + 2}/{self.max_retries}...")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        # Either not a rate limit error, or we've exhausted retries
                        raise

            # If the cargoquery is empty, we stop the loop
            if not result:
                break

        return result


# Ghost loaded instance shared by all other classes
leaguepedia = LeaguepediaSite()
