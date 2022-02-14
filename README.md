AWS AutoScalingGroup Activity Exporter
=====

A Prometheus exporter for AWS [AutoScalingGroup Actvities](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-verify-scaling-activity.html)

## Building and running

```
poetry shell
poetry install

cd aws-autoscalinggroup-activity-exporter

# See Configuration section for details
cp conf/example-config.yaml conf/config.yaml

python app.py
```

View metrics with `curl localhost:8080/metrics`


## Credentials and permissions

This Exporter uses

## Configuration
The configuration is in YAML and must be stored in conf/config.yaml.
An example can be found in conf/example-config.yaml

If tags are not specified, then all AutoScalingGroups in the
region will gathered and metrics published for.

Custom causes can be added as well. Examples are given, but
if there is a cause pattern you wish to capture, then you
just need to add it with the cause label you wish to assign it.

Using the following example, if a cause with pattern:

'Spot Instance interruption notice' is detected, then it will publish a metric
like so:

```
aws_autoscalinggroup_activity{instance_id="i-06b1e395e5596d7cf",name="myASG",reason="interrupt"} 1.0
```

Causes for your AutoScalingGroup instances scaling up/down can be viewed in the
AWS EC2 Console -> AutoScalingGroups -> <AutoScalingGroupName> -> Activity

An example with common options:
```
# AWS region to run in
region: "us-west-2"
# autoscaling groups to discover by tag
tags:
  - key: "kubernetes.io/cluster/my-cluster"
    value: "owned"
  - key: "eks:nodegroup-name"
    value: "my-spot-nodegroup"
# autoscaling group activity causes
causes:
  - pattern: ".*Spot Instance interruption notice.*"
    reason: "interrupt"
  - pattern: ".*EC2 instance rebalance recommendation.*"
    reason: "rebalance"
  - pattern: ".*user request.*"
    reason: "user_request"
```
