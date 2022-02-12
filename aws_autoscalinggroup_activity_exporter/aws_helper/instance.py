import boto3


# Given a list of instance ids, will return a map of IDs to IPs
def get_ips_from_instances(instance_ids):
    # TODO: generalize region
    ec2 = boto3.resource('ec2', region_name='us-west-2')
    ips = {}

    for instance_id in instance_ids:
        instance = ec2.Instance(instance_id)

        # TODO: figure out if need to get public ip of instance
        # ip_address = instance.private_ip_address
        ip_address = instance.private_ip_address

        if ip_address:
            ips[instance_id] = ip_address
        else:
            ips[instance_id] = ''

        for id, ip in ips.items():
            if not ip:
                print(f'{id} has no ip address!')
            # else:
            #    print(f'{id} has ip address: {ip}')

    return ips
