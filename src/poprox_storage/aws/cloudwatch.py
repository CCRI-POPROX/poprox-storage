from collections import defaultdict
from datetime import datetime
from typing import List

import boto3
from botocore import exceptions

from poprox_storage.aws.exceptions import PoproxAwsUtilitiesException


class Cloudwatch:
    def __init__(self, session: boto3.Session):
        self.__session = session
        self.cloudwatch_client = self.__session.client("cloudwatch")

    def list_metrics(self, namespace):
        response = self.cloudwatch_client.list_metrics(
            Namespace=namespace,
        )
        return response

    def get_metric_daily_count(
        self, namespace: str, metrics: str | List[str], start_time: datetime, end_time: datetime
    ) -> dict[datetime, dict[str, int]]:
        """Gets values of metrics. FOR NOW this function only computes daily counts return value is a dictionary from
        datetime objects to dicitonaries of metric values for that day, if a day has no metric values it will not be
        returned"""
        if isinstance(metrics, str):  # if they enter one metric treat it as a list
            metrics = [metrics]

        # TODO: timezones...

        # clamp to date (since we're doing daily counts anyways)
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

        metric_ids = {"m" + str(i): metric for i, metric in enumerate(metrics)}

        metric_queries = [
            {
                "Id": metric_id,
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric,
                        "Dimensions": [],  # this works for the custom onboarding metrics at least.
                    },
                    "Period": 60 * 60 * 24,  # daily
                    "Stat": "SampleCount",
                },
                "ReturnData": True,
            }
            for metric_id, metric in metric_ids.items()
        ]

        data_results = []
        next_token = None
        while True:
            try:
                if next_token is not None:
                    response = self.cloudwatch_client.get_metric_data(
                        MetricDataQueries=metric_queries,
                        StartTime=start_time,
                        EndTime=end_time,
                        ScanBy="TimestampAscending",
                        NextToken=next_token,
                    )
                else:
                    response = self.cloudwatch_client.get_metric_data(
                        MetricDataQueries=metric_queries,
                        StartTime=start_time,
                        EndTime=end_time,
                        ScanBy="TimestampAscending",
                    )
            except exceptions.ClientError as e:
                msg = f"Error getting metric values for metrics {metrics}: {e}"
                raise PoproxAwsUtilitiesException(msg) from e
            data_results.extend(response.get("MetricDataResults", []))
            next_token = response.get("NextToken")
            if next_token is None:
                # I wish python had do-while loops.
                break
        results = defaultdict(dict)
        for data_result in data_results:
            metric_name = metric_ids[data_result.get("Id")]
            dates = data_result.get("Timestamps", [])
            values = data_result.get("Values", [])
            num = min(len(dates), len(values))
            for i in range(num):
                date = dates[i]
                val = values[i]
                results[date][metric_name] = val

        # fill in with defaults
        for result in results.values():
            for metric in metrics:
                if metric not in result:
                    result[metric] = 0
        return results
