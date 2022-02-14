import boto3
import os
import re
import sys
import calendar
import time
import datetime
import logging
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge
from flask_apscheduler import APScheduler

from serialize.yamlhandler import read_yaml_file
from logger.log import setup_custom_logger
from aws_helper.autoscalinggroup import get_group_instances
from aws_helper.instance import get_ips_from_instances

setup_custom_logger(__name__, 'info')
logger = logging.getLogger(__name__)

logger.info('starting')
SECONDS_MIN = 60
SECONDS_HOUR = 60 * 60

app = Flask(__name__)
metrics = PrometheusMetrics(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

info = metrics.info('app_info', 'Application info', version='0.1.0')
activity_metric = Gauge(
    'aws_autoscalinggroup_activity',
    'AWS AutoscalingGroup Activity Information',
    ['name', 'instance_id', 'reason']
)

@app.route('/health', methods=['GET'])
def health():
    """Get server health
    Returns:
        str: 'OK'
    """

    return 'OK', 200


@scheduler.task('interval', seconds=15)
def publish_version():
    """Publish version by setting prometheus
       info metric with version label.

    Returns:
        None
    """
    info.set(1)


@scheduler.task('interval', minutes=1)
def publish_activities():
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

    client = boto3.client('autoscaling', region_name=conf['region'])
    groups = client.describe_auto_scaling_groups(
        Filters=_get_filters(conf)
    )['AutoScalingGroups']

    possible_causes = conf['causes']

    for group in groups:
        name = group.get('AutoScalingGroupName')
        # instances = get_group_instances(client, name)
        # instance_ip_map = get_ips_from_instances(instances)
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
                    start = calendar.timegm(activity.get('StartTime').utctimetuple())
                    now = int(time.mktime(datetime.datetime.now().timetuple()))
                    delta = now - start

                    publish = delta < 12 * SECONDS_HOUR
                    active = delta < 10 * SECONDS_MIN

                    if publish:
                        if description:
                            d_match = re.match('(Terminating|Launching) EC2 instance: (.+).*', description)
                            if d_match:
                                instance_id = d_match.group(2)
                                if not instance_id:
                                    logger.info(f'Could not determine instance-id from description: {description}')

                                cause = activity.get('Cause')
                                if cause:
                                    # possible causes configured in conf/config.yaml
                                    for pc in possible_causes:
                                        c_match = re.match(pc['pattern'], cause)
                                        if c_match:
                                            # TODO: do we need the instance ip? If an instance is gone, so is the ip
                                            #       BUT it might be nice to have it if it's available during termination
                                            #       If funcitonality to detect Instance Launches is desired, could help
                                            #       but need to remember that the instance might not have an ip assigned
                                            #       until some time after launch.
                                            # instance_ip = instance_ip_map.get(instance_id)
                                            # if not instance_ip:
                                            #     instance_ip = ""

                                            value = 0
                                            if active:
                                                value = 1

                                            activity_metric.labels(
                                                name=name,
                                                # instance_ip=instance_ip,
                                                instance_id=instance_id,
                                                reason=pc['reason']
                                            ).set(value)


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


if __name__ == "__main__":
    publish_activities()
    app.run(host='0.0.0.0', port=8080)
    pass
