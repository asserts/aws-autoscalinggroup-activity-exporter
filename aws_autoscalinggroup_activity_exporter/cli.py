import os
import sys
import logging
import click
import atexit
from more_click import host_option, port_option, with_gunicorn_option, workers_option, run_app

from aws_autoscalinggroup_activity_exporter.app import Scheduler, app

click.disable_unicode_literals_warning = True


@click.command()
@click.option('--region', 'region', envvar='REGION',
              required=True, help='The AWS region.')
@host_option
@port_option
@with_gunicorn_option
@workers_option
def web(region: str, host: str, port: int, with_gunicorn: bool, workers: int):
    logger = logging.getLogger(__name__)
    logger.info(f'Starting AWS AutoscalingGroup Activity Exporter...')

    conf_path = 'conf/config.yaml'
    if not os.path.exists(
               os.path.join(
                   os.path.dirname(__file__), conf_path
               )
            ):
        logger.error(f'File {conf_path} does not exist!')
        sys.exit(1)

    scheduler = Scheduler(region, conf_path)
    scheduler.add_jobs()
    scheduler.start_scheduler()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.scheduler.shutdown())
    run_app(app=app, host=host, port=port, with_gunicorn=with_gunicorn, workers=workers)


if __name__ == '__main__':
    web()
