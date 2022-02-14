import boto3
import logging

logger = logging.getLogger(__name__)


def get_ips_from_instances(instance_ids, region):
    """Read a yaml file

    Args:
        instance_ids (list): list of instance-ids
        region (string): reegion name

    Returns:
        dict: dict where key=instance-id and value=ip-addr
    """

    ec2 = boto3.resource('ec2', region_name=region)
    ips = {}

    for instance_id in instance_ids:
        instance = ec2.Instance(instance_id)

        # TODO: figure out if need to get public ip of instance
        ip_address = instance.private_ip_address

        if ip_address:
            ips[instance_id] = ip_address
        else:
            ips[instance_id] = ''

        for id, ip in ips.items():
            if not ip:
                logger.info(f'{id} has no ip address!')
            else:
               logger.info(f'{id} has ip address: {ip}')

    return ips
