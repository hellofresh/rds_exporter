#!/usr/bin/env python


import os
import boto3
import yaml
import subprocess


AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'live')

client = boto3.client('rds', region_name=AWS_REGION)

def get_db_instances(page_size=20):
    marker = ""
    pool = []
    while True:
        for instance in pool:
            yield instance

        if marker is None:
            break
        result = client.describe_db_instances(MaxRecords=page_size,
                                              Marker=marker)
        marker = result.get("Marker")
        pool = result.get("DBInstances")


def get_rds_tags(instance_arn):
    response = client.list_tags_for_resource(
        ResourceName=instance_arn
    )
    return { tag['Key']: tag['Value'] for tag in response['TagList'] }


def is_applicable(instance):
    instance_name = instance['DBInstanceIdentifier']
    instance_arn = instance['DBInstanceArn']
    instance_tags = get_rds_tags(instance_arn)
    instance_enhanced_monitoring_interval = instance.get('MonitoringInterval', 0)
    instance_environment_tag = instance_tags.get('Environment', '')
    return instance_enhanced_monitoring_interval > 0 and (instance_name.lower().endswith(ENVIRONMENT.lower()) or instance_environment_tag.lower() == ENVIRONMENT.lower())


if __name__ == "__main__":
    em_enabled_instances = {'instances': []}

    for instance in get_db_instances():
        if is_applicable(instance):
            instance_name = instance['DBInstanceIdentifier']
            instance = {'instance': instance_name, 'region': AWS_REGION}
            em_enabled_instances['instances'].append(instance)

    with open('/rds_exporter/config.yml', 'w') as yaml_file:
        yaml.dump(em_enabled_instances, yaml_file, default_flow_style=False)

    rds_exporter = '/rds_exporter/rds_exporter \
                --config.file=/rds_exporter/config.yml'

    subprocess.run(rds_exporter, shell=True)
