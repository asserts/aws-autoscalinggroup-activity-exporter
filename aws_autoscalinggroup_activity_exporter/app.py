import boto3
import os
import re
import sys
import calendar
import time
import datetime
import logging
import atexit
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge
from apscheduler.schedulers.background import BackgroundScheduler

from aws_autoscalinggroup_activity_exporter.serialize.yamlhandler import read_yaml_file
from aws_autoscalinggroup_activity_exporter.logger.log import setup_custom_logger

setup_custom_logger(__name__, 'info')
logger = logging.getLogger(__name__)

SECONDS_MIN = 60
SECONDS_HOUR = 60 * 60

app = Flask(__name__)
metrics = PrometheusMetrics(app)

info = metrics.info('app_info', 'Application info', version='0.1.0')
activity_metric = Gauge(
    'aws_autoscalinggroup_activity',
    'AWS AutoscalingGroup Activity Information',
    ['name', 'instance_id', 'reason']
)


class Scheduler():
    """Scheduler wrapper to add and run scheduled jobs."""

    def __init__(self, region):
        self.region = region
        self.scheduler = BackgroundScheduler()

    def add_jobs(self):
        """Add jobs to the BackgroundScheduler"""

        self.scheduler.add_job(func=publish_version, trigger="interval", seconds=15)
        self.scheduler.add_job(func=publish_activities, trigger='interval', seconds=60, args=(self.region,))

    def start_scheduler(self):
        """Start the BackgroundScheduler"""

        self.scheduler.start()

def publish_version():
    """Publish version by setting prometheus
       info metric with version label.

    Returns:
        None
    """
    info.set(1)


def publish_activities(region):
    """Publish AutoScalingGroup Activities into
       Prometheus metrics.

    This function runs on a 1 minute interval and will:
        1. Get the AutoScalingGroups configured to be discovered
           by the 'tags' configuration in conf/config.yaml. Defaults to
           all the groups in the region.
        2. Iterate over the Activity for the groups and identify
           activity causes by their configured patterns in conf/config.yaml.
        3. Publish a meaningful metric with the autoscalinggroup name,
           instance-id, and cause for instance launch/termination.

    Returns:
        None
    """

    global activity_metric

    conf_path = 'conf/config.yaml'
    if not os.path.exists(conf_path):
        logger.error(f'File {conf_path} does not exist!')
        sys.exit(1)
    else:
        conf = read_yaml_file(
            os.path.join(os.path.dirname(__file__), conf_path)
        )

    client = boto3.client('autoscaling', region_name=region)
    groups = client.describe_auto_scaling_groups(
        Filters=_get_filters(conf)
    )
    ['AutoScalingGroups']

    try:
        possible_causes = conf['causes']
    except TypeError:
        logger.error('No causes configured in config.yaml')
        sys.exit(1)

    for group in groups:
        name = group.get('AutoScalingGroupName')

        if name:
            response = client.describe_scaling_activities(
                AutoScalingGroupName=name,
                IncludeDeletedGroups=False,
                MaxRecords=100
            )
            activities = response.get('Activities')
            if activities:
                for activity in activities:
                    description = activity.get('Description')

                    # get activity start time and compare with current time
                    # of launching/terminating instances
                    #
                    # if launched/terminated within the last 10 minutes, will
                    # be published as active (value=1)
                    #
                    # if launched/terminated within the last 12 hours, will be
                    # published as inactive (value=0)
                    #
                    # if activity greater than 12 hours ago, ignore (don't publish)
                    delta = _calculate_delta(activity.get('StartTime'))
                    publish = delta < 12 * SECONDS_HOUR
                    active = delta < 10 * SECONDS_MIN

                    if publish:
                        if description:
                            d_match = re.match('.*(Launching|Terminating).* EC2 instance: (.+).*', description)
                            if d_match:
                                instance_id = d_match.group(2)
                                if not instance_id:
                                    logger.warn(f'Could not determine instance-id from description: {description}')

                                cause = activity.get('Cause')
                                if cause:
                                    # possible causes configured in conf/config.yaml
                                    for pc in possible_causes:
                                        c_match = re.match(pc['pattern'], cause)
                                        if c_match:
                                            value = 0
                                            if active:
                                                value = 1

                                            activity_metric.labels(
                                                name=name,
                                                instance_id=instance_id,
                                                reason=pc['reason']
                                            ).set(value)


def run_app(region, host, port):
    scheduler = Scheduler(region)
    scheduler.add_jobs()
    scheduler.start_scheduler()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.scheduler.shutdown())
    app.run(host, port)


@app.route('/health', methods=['GET'])
def health():
    """Get server health
    Returns:
        str: 'OK'
    """

    return 'OK', 200


def _calculate_delta(start_time):
    """Calculate delta from start_time
       normalizing to UTC. UTC works here since
       we only care about the difference.

    Args:
        client (Session): AWS boto3 client
        name (string): AutoScalingGroup Name

    Returns:
        int: difference between now and the start time
    """

    start = calendar.timegm(start_time.utctimetuple())
    now = int(time.mktime(datetime.datetime.now().timetuple()))
    delta = now - start

    return delta


def _get_filters(conf):
    """Get and construct AWS Tag Filters

    Args:
        conf (dict): yaml dict with tag configuraiton

    Returns:
        list: list of filters for AWS API consumption
    """

    filters = []

    tags = conf.get('tags')
    if tags:
        for tag in tags:
            filters.append(
                {
                    'Name': f'''tag:{tag['key']}''',
                    'Values': [
                        tag['value']
                    ]
                }
            )

    return filters
