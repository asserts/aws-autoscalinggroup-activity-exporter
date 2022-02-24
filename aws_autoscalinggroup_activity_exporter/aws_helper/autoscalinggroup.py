import logging

logger = logging.getLogger(__name__)


def get_group_instances(client, name):
    """Read a yaml file

    Args:
        client (Session): AWS boto3 client
        name (string): AutoScalingGroup Name

    Returns:
        list: list of instance-ids from an AutoScalingGroup
    """

    instances = []
    group = client.describe_auto_scaling_groups(AutoScalingGroupNames=[name])

    if group:
        asgs = group['AutoScalingGroups']
        if len(asgs) > 0:
            instance_data = asgs[0]['Instances']
            for item in instance_data:
                instances.append(item['InstanceId'])
        else:
            logger.info(f'No autoscaling group {name}. Asg does not exist while ami does.')

    return instances
