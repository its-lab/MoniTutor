def __connect_to_rabbit_mq():
    rabbit_mq_host = app_conf.take("monitutor_env.rabbit_mq_host")
    rabbit_mq_user = app_conf.take("monitutor_env.rabbit_mq_user")
    rabbit_mq_password = app_conf.take("monitutor_env.rabbit_mq_password")
    credentials = pika.credentials.PlainCredentials(rabbit_mq_user, rabbit_mq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbit_mq_host,
            credentials=credentials))
    return connection

def __rabbit_mq_publish_message(exchange, routing_key, message, queue=None):
    connection = __connect_to_rabbit_mq()
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type="topic")
    if queue:
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message))
    connection.close()

def __rabbit_mq_publish_task(routing_key, task):
    task_exchange = app_conf.take("monitutor_env.rabbit_mq_task_exchange")
    __rabbit_mq_publish_message(task_exchange,
                                queue=routing_key,
                                routing_key=routing_key,
                                message=task)

def __rabbit_mq_publish_system_message(routing_key, message):
    __rabbit_mq_publish_message("system_events",
                                routing_key=routing_key,
                                message=message)



