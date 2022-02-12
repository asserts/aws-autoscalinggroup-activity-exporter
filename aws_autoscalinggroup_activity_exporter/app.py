import boto3
import re
import calendar
import time
import datetime
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge
from flask_apscheduler import APScheduler

from serialize.yamlhandler import read_yaml_file
from aws_helper.autoscalinggroup import get_group_instances
from aws_helper.instance import get_ips_from_instances

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
    ['name', 'instance_ip', 'instance_id', 'reason']
)


@scheduler.task('interval', seconds=15)
def publish_version():
    info.set(1)


@scheduler.task('interval', minutes=1)
def collect_activities():
    global activity_metric
    client = boto3.client('autoscaling', region_name='us-west-2')
    groups = client.describe_auto_scaling_groups()['AutoScalingGroups']

    conf = read_yaml_file('../conf/config.yaml')
    possible_causes = conf['causes']

    for group in groups:
        name = group.get('AutoScalingGroupName')
        instances = get_group_instances(client, name)
        instance_ip_map = get_ips_from_instances(instances)
        if name:
            # TODO: figure out the number of records to look at
            response = client.describe_scaling_activities(
                AutoScalingGroupName=name,
                IncludeDeletedGroups=True,
                MaxRecords=20
            )
            activities = response.get('Activities')
            if activities:
                for activity in activities:
                    description = activity.get('Description')

                    start = calendar.timegm(activity.get('StartTime').utctimetuple())
                    now = int(time.mktime(datetime.datetime.now().timetuple()))
                    delta = now - start

                    # TODO: Decide when to:
                    #       1. publish metric with value=1, this means recent activity (10 min window)
                    #       2. publish metric with value=0, this means not recent (> 10 min window)
                    #       3. Stop publishing Activity (e.g.: 1 day)

                    publish = delta < 24 * SECONDS_HOUR
                    active = delta < 10 * SECONDS_MIN

                    if publish:
                        if description:
                            # TODO: track 'Launching EC2 Instances'???
                            d_match = re.match('Terminating EC2 instance: (.+).*', description)
                            if d_match:
                                instance_id = d_match.group(1)
                                if not instance_id:
                                    instance_id = ""
                                # TODO: should we try to get the instance-id from the cause in case this fails??
                                cause = activity.get('Cause')
                                if cause:
                                    for pc in possible_causes:
                                        c_match = re.match(pc['pattern'], cause)
                                        if c_match:
                                            # TODO: do we need the instance ip? If an instance is gone, so is the ip
                                            #       BUT it might be nice to have it if it's available during termination
                                            #       If funcitonality to detect Instance Launches is desired, could help
                                            #       but need to remember that the instance might not have an ip assigned
                                            #       until some time after launch.
                                            instance_ip = instance_ip_map.get(instance_id)
                                            if not instance_ip:
                                                instance_ip = ""

                                            value = 0
                                            if active:
                                                value = 1

                                            activity_metric.labels(
                                                name=name,
                                                instance_ip=instance_ip,
                                                instance_id=instance_id,
                                                reason=pc['reason']
                                            ).set(value)


if __name__ == "__main__":
    collect_activities()
    app.run(host='0.0.0.0', port=8080)
    pass
