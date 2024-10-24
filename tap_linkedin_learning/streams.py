"""Stream type classes for tap-linkedin-learning."""

from __future__ import annotations

import typing as t
from importlib import resources

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_linkedin_learning.client import LinkedinLearningStream


class LearnerDetail(LinkedinLearningStream):
    """Define custom stream."""

    name = "LearnerDetail"
    #path = "v2/learningActivityReports?aggregationCriteria.primary=INDIVIDUAL&aggregationCriteria.secondary=CONTENT&q=criteria&start=0&count=500&contentSource=LINKEDIN_LEARNING&assetType=COURSE&startedAt=1702699900247&timeOffset.duration=14&timeOffset.unit=DAY"
    path = "v2/learningActivityReports"
    primary_keys: t.ClassVar[list[str]] = ["profileUrn","contentUrn"]
    replication_key = "latestDataAt"
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    # schema_filepath = SCHEMAS_DIR / "users.json"  # noqa: ERA001
    schema = th.PropertiesList(
        th.Property("latestDataAt", th.IntegerType),
        th.Property("learnerDetails",
                    th.ObjectType(
                    th.Property("name", th.StringType),
                    th.Property("enterpriseGroups", th.ArrayType(th.StringType), default = "None"),
                    th.Property("entity",
                                th.ObjectType(
                                th.Property("profileUrn",th.StringType)
                    )),
                    th.Property("email", th.StringType),
                    th.Property("customAttributes",
                                th.ObjectType(
                                th.Property("Market", th.ArrayType(th.StringType), default = "None"),
                                th.Property("Employee_ID", th.ArrayType(th.StringType), default = "None"),
                                th.Property("Department", th.ArrayType(th.StringType), default = "None"),
                                )
                    ),
                    th.Property("uniqueUserId", th.StringType)
                                )
                    ),
        th.Property("activities",
                    th.ArrayType(
                    th.ObjectType(
                    th.Property("engagementType", th.StringType),
                    th.Property("lastEngagedAt", th.IntegerType),
                    th.Property("firstEngagedAt", th.IntegerType),
                    th.Property("assetType", th.StringType),
                    th.Property("engagementMetricQualifier", th.StringType),
                    th.Property("engagementValue", th.IntegerType)
                    ))),
        th.Property("contentDetails",
                    th.ObjectType(
                    th.Property("contentProviderName", th.StringType),
                    th.Property("name", th.StringType),
                    th.Property("contentUrn", th.StringType),
                    th.Property("locale",
                                th.ObjectType(
                                th.Property("country", th.StringType),
                                th.Property("language", th.StringType)
                                            )
                                )
                                )
                    )
    ).to_dict()


class GroupsStream(LinkedinLearningStream):
    """Define custom stream."""

    name = "groups"
    path = "/groups"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = "modified"
    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("id", th.StringType),
        th.Property("modified", th.DateTimeType),
    ).to_dict()
