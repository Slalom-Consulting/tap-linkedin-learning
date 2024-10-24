"""LinkedinLearning tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_linkedin_learning import streams


class TapLinkedinLearning(Tap):
    """LinkedinLearning tap class."""

    name = "tap-linkedin-learning"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "grant_type",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "url_base",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "access_token_url",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "query_string",
            th.StringType,
            required=True,
            description="The token to authenticate against the API service",
        ),
#        th.Property(
#            "start_date",
#            th.DateTimeType,
#            description="The earliest record date to sync",
#        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.LinkedinLearningStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            #streams.GroupsStream(self),
            streams.LearnerDetail(self),
        ]


if __name__ == "__main__":
    TapLinkedinLearning.cli()
