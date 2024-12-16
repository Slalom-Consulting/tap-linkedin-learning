"""REST client handling, including LinkedinLearningStream base class."""

from __future__ import annotations

import typing as t
from functools import cached_property
from importlib import resources
from urllib.parse import parse_qsl

from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.helpers._state import write_replication_key_signpost
from singer_sdk.pagination import BaseHATEOASPaginator  # noqa: TCH002
from singer_sdk.streams import RESTStream
from singer_sdk import metrics
from datetime import datetime
from tap_linkedin_learning.auth import LinkedinLearningAuthenticator

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Auth, Context

# TODO: Delete this is if not using json files for schema definition

class MyPaginator(BaseHATEOASPaginator):
    def __init__(self,start_time):
        self.start_time = start_time
        self.current_url = None
        super().__init__()

    def get_next_start_time(self, start_time):
        end_time = datetime.now().timestamp() * 1000
        if end_time < start_time:
            return None
        else:
            self.start_time += 604800000

            return self.start_time

    def get_next_url(self, response):
        data = response.json()
        paging_data = data['paging']['links']
        next_url = None
        for item in paging_data:
            if item['rel'] == 'next':
                next_url = item['href']
        if next_url:
            return next_url
        else:
            return None

    def get_next(self,response):
        next_url = self.get_next_url(response)
        if next_url == None:
            new_start = self.get_next_start_time(self.start_time)
            if new_start == None:
                return None
            else:
                return new_start 
        else:
            self.current_url = next_url
            return next_url
        

        #return data['paging']['links'][0]['href']

class LinkedinLearningStream(RESTStream):
    """LinkedinLearning stream class."""

    # Update this value if necessary or override `parse_response`.
    records_jsonpath = "$[elements][*]"

    # @property
    # def start_time(self) -> str:
    #     return self.config.get("start_time")


    # Update this value if necessary or override `get_new_paginator`.
    #next_page_token_jsonpath = "$.next_page"  # noqa: S105

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # TODO: hardcode a value here, or retrieve it from self.config
        return self.config.get("url_base")

    @cached_property
    def authenticator(self) -> Auth:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return LinkedinLearningAuthenticator.create_for_stream(self)

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_new_paginator(self, start_time) -> BaseHATEOASPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide: https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        return MyPaginator(start_time) 

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ANN401
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict = {}
        
        #pull the params from the config
        if 'query_string' in self.config:
            query_string = self.config.get('query_string')
        else:
            query_string = None


        params.update(parse_qsl(query_string))
        if next_page_token:
            self.logger.info(f'next page token: {datetime.utcfromtimestamp(next_page_token/1000.0)}')
        replicationkey = self.get_starting_replication_key_value(context)
        if replicationkey:
            self.logger.info(f'replicationkey: {datetime.utcfromtimestamp(replicationkey/1000.0)}')

        if next_page_token:
            params['startedAt'] = next_page_token
        else:
            if replicationkey:
                params['startedAt'] = replicationkey
        self.logger.info(f'PARAMS:{params}')
        return params

    def get_start_time(self, context):
        if 'query_string' in self.config:
            query_string = self.config.get('query_string')
        else:
            query_string = None

        params = {}
        params.update(parse_qsl(query_string))
        replicationkey = self.get_starting_replication_key_value(context)

        if replicationkey:
            if replicationkey > int(params['startedAt']):
                start_time = replicationkey
        else:
            start_time = int(params['startedAt'])

        return start_time

    def request_records(self, context: Context | None) -> t.Iterable[dict]:
        """Request records from REST endpoint(s), returning response records.

        If pagination is detected, pages will be recursed automatically.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            An item for every record in the response.
        """
        paginator = self.get_new_paginator(self.get_start_time(context))
        decorated_request = self.request_decorator(self._request)
        pages = 0

        with metrics.http_request_counter(self.name, self.path) as request_counter:
            request_counter.context = context

            while not paginator.finished:
                prepared_request = self.prepare_request(
                    context,
                    next_page_token=paginator.current_value,
                )
                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)
                records = iter(self.parse_response(resp))
                try:
                    first_record = next(records)
                except StopIteration:
                    self.logger.info(
                        "Pagination stopped after %d pages because no records were "
                        "found in the last response",
                        pages,
                    )
                    break
                yield first_record
                yield from records
                pages += 1

                paginator.advance(resp)

    def prepare_request_payload(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ARG002, ANN401
    ) -> dict | None:
        """Prepare the data payload for the REST API request.

        By default, no payload will be sent (return None).

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary with the JSON body for a POST requests.
        """
        # TODO: Delete this method if no payload is required. (Most REST APIs.)
        return None

    def parse_response(self, response: requests.Response) -> t.Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        # TODO: Parse response body and return a set of records.
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def post_process(
        self,
        row: dict,
        context: Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        """As needed, append or transform raw data to match expected structure.

        Args:
            row: An individual record from the stream.
            context: The stream context.

        Returns:
            The updated record dictionary, or ``None`` to skip the record.
        """
        # TODO: Delete this method if not needed.
        return row
