def get_group_instances(client, name):
    instances = []
    group = client.describe_auto_scaling_groups(AutoScalingGroupNames=[name])

    if group:
        asgs = group['AutoScalingGroups']
        if len(asgs) > 0:
            instance_data = asgs[0]['Instances']
            for item in instance_data:
                instances.append(item['InstanceId'])
        else:
            print(f'No autoscaling group {name}. Asg does not exist while ami does.')

    return instances