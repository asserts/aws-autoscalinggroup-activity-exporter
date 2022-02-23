import logging
import click

from aws_autoscalinggroup_activity_exporter.app import run_app

click.disable_unicode_literals_warning = True


@click.command()
@click.option('--region', 'region', envvar='REGION',
              required=True, help='The AWS region.')
def cli(**kwargs):
    args = kwargs
    region = args['region']
    logger = logging.getLogger(__name__)
    logger.info(f'Starting AWS AutoscalingGroup Activity Exporter...')
    run_app(region, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    cli()
