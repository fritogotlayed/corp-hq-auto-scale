"""The main entry point of the application"""

import datetime
import logging
import os
import signal
import time

from corp_hq_auto_scale import db
from corp_hq_auto_scale import log

import docker

import pika
from pika.adapters.blocking_connection import BlockingChannel

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

STATE = {'running': True}


def main():
    log.setup(LOG)
    rabbit_channel = get_rabbit_channel()
    docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock', timeout=10)
    signal.signal(signal.SIGINT, _ctrl_c_handle)

    last_run = None
    last_shrink = datetime.datetime.utcnow()
    last_expand = datetime.datetime.utcnow()
    last_cleanup = datetime.datetime.utcnow()
    last_message_count = -1

    poll_seconds = 0
    expand_seconds = 5
    shrink_seconds = 60
    cleanup_seconds = 30

    LOG.info('Starting to watch queue')
    while STATE['running']:
        now = datetime.datetime.utcnow()
        if last_run is None or (now - last_run).total_seconds() > poll_seconds:
            last_run = datetime.datetime.utcnow()
            message_count = get_queue_length(rabbit_channel)

            if last_message_count != message_count:
                LOG.debug('Messages: ' + str(message_count))
                last_message_count = message_count

            runner_count = docker_runner_count(docker_client)
            desired_count = get_scale_configuration(message_count)

            if runner_count < desired_count and (now - last_expand).total_seconds() > expand_seconds:
                docker_start_runner(docker_client, desired_count - runner_count)

            if desired_count < runner_count and (now - last_shrink).total_seconds() > shrink_seconds:
                last_shrink = now
                gracefully_stop_runner(rabbit_channel, runner_count - desired_count)

            if (now - last_cleanup).total_seconds() > cleanup_seconds:
                cleanup_dead_containers(docker_client)

            time.sleep(1)


def get_rabbit_channel() -> BlockingChannel:
    settings_col = db.get_collection('corp-hq', 'settings')

    # Get the rabbit settings
    rabbit_settings = settings_col.find_one({
        'key': 'rabbitConnection',
        'environment': os.environ.get('CORP_HQ_ENVIRONMENT', 'local')})

    # Connect to rabbit
    instance = rabbit_settings['value']['hosts'][0]['address']
    LOG.debug('Connecting to Rabbit Instance: %s', instance)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            instance,
            credentials=pika.PlainCredentials(
                rabbit_settings['value']['username'],
                rabbit_settings['value']['password']
            ))
    )
    return connection.channel()


def get_scale_configuration(message_count: int) -> int:
    count = message_count / 10 + 1
    return 0 if message_count == 0 else int(count)


def get_queue_length(channel: BlockingChannel) -> int:
    # If the queue does not exist it will be created. If it does
    # exist then we can query the message count from it.
    queue = channel.queue_declare(
        queue="jobs",
        durable=True,
        exclusive=False,
        auto_delete=False
    )

    return queue.method.message_count


def _ctrl_c_handle(*_):
    LOG.info('Gracefully shutting down...')
    STATE['running'] = False


def docker_stuff(client: docker.DockerClient):
    client.containers.list()
    containers = client.containers.list(all=True, filters={'ancestor': 'fritogotlayed/corp-hq-runner'})
    print('{:<20} {:<30} {}'.format('CONTAINER ID', 'NAME', 'STATUS'))
    for container in containers:
        print('{:<20} {:<30} {}'.format(
            container.short_id,
            container.name,
            container.status))

    print('')
    print('Removing exited containers')
    for container in containers:
        if container.status in ['exited', 'created']:
            print('{:<20} {}'.format(container.short_id, container.name))
            container.remove()


def docker_start_runner(client: docker.DockerClient, count: int = 1):
    container_ids = []
    for _ in range(count):
        container = client.containers.run(
            'fritogotlayed/corp-hq-runner',
            detach=True,
            network='corp-hq_default',
            environment={
                'MONGO_CONNECTION': 'mongodb://mongodb:27017/corp-hq',
                'CORP_HQ_ENVIRONMENT': 'localDocker'
            }
        )
        container_ids.append(container.short_id)

    LOG.info('Started %s new container(s). %s', count, ','.join(container_ids))


def docker_runner_count(client: docker.DockerClient) -> int:
    containers = client.containers.list(all=True, filters={'ancestor': 'fritogotlayed/corp-hq-runner'})
    running_containers = []

    for container in containers:
        if container.status in ['running']:
            running_containers.append(container)

    return len(running_containers)


def gracefully_stop_runner(channel: BlockingChannel, count: int):
    runners = db.get_collection('corp-hq', 'runners')
    all_runners = list(runners.find())
    for i in range(count):
        runner = all_runners[i]
        channel.basic_publish(
            exchange='',
            routing_key=runner['name'],
            body=''
        )
        LOG.info('Request for runner "%s" to stop sent.', runner['name'])


def cleanup_dead_containers(client: docker.DockerClient):
    containers = client.containers.list(all=True, filters={'ancestor': 'fritogotlayed/corp-hq-runner'})
    container_ids = []

    for container in containers:
        if container.status in ['exited', 'created']:
            container_ids.append(container.short_id)
            container.remove()
        elif container.status != 'running':
            LOG.warning('Unhandled container status: ' + container.status)

    count = len(container_ids)
    if count > 0:
        LOG.info('Removed %s dead containers: %s', len(container_ids), ','.join(container_ids))


if __name__ == '__main__':
    main()
