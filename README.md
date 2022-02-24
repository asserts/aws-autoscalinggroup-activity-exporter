AWS AutoScalingGroup Activity Exporter
=====

A Prometheus exporter for AWS [AutoScalingGroup Actvities](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-verify-scaling-activity.html)

## Helm Installation

```
helm repo add asserts https://asserts.github.io/helm-charts

helm upgrade --install aws-autoscalinggroup-activity-exporter asserts/aws-autoscalinggroup-activity-exporter -n <namespace> --set "region=<region>"
```

## Building and running

### Source
```
poetry shell
poetry install

cd aws_autoscalinggroup_activity_exporter

# See Configuration section for details
cp conf/example-config.yaml conf/config.yaml

aws-autoscaling-group-activity-exporter --region <region-name> --port <port>

OR

aws-autoscaling-group-activity-exporter --region us-west-2 --port 8080
```

View metrics with `curl localhost:8080/metrics`

### Docker

```
docker build -t aws-autoscalinggroup-activity-exporter:latest .

# no session token
docker run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -it -d -p 8080:8080 aws-autoscalinggroup-activity-exporter:latest

OR

# using a seesion token
docker run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -it -d -p 8080:8080 aws-autoscalinggroup-activity-exporter:latest

docker logs <container> -f
```

View metrics with `curl localhost:8080/metrics`

## Credentials and permissions

Currently `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` can be used to run locally or in docker.
Alternatively, if running on an EC2 instance or in EKS, the instance role can be used.

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
`AWS EC2 Console` -> `AutoScalingGroups` -> `<AutoScalingGroupName>` -> `Activity`

An example with common options:
```
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
