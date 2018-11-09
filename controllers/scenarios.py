import json
import requests
import random
import string
import pika

@auth.requires_login()
def view_available_scenarios():
    """Displays available scenarios and their status for a given user"""
    if auth.has_membership("admin") and len(request.args):
        user_id = request.args(0, cast=str)
    else:
        user_id = auth.user_id
    if auth.has_membership("admin"):
        scenarios = db().select(db.monitutor_scenarios.ALL)
    else:
        scenarios = db(db.monitutor_scenarios.hidden == False).select()
    passed = dict()
    for scenario in scenarios:
        passed_rows = db((db.scenario_user.scenario_id==scenario.scenario_id)
                          &(user_id == db.scenario_user.user_id)).select()
        if passed_rows:
            passed[scenario.name] = passed_rows[0].passed
        else:
            passed[scenario.name] = False
    return dict(scenarios=scenarios, user_id=user_id, passed=passed)

@auth.requires_membership("admin")
def toggle_scenario_done():
    username = request.vars.username
    user_id = request.vars.userId
    if user_id is None and username is not None:
        user_id = db(db.auth_user.username == username).select().first().id
    scenario_id = request.vars.scenarioId
    scenario_user = db((db.scenario_user.user_id == user_id) &
                            (db.scenario_user.scenario_id == scenario_id)).select().first()
    if scenario_user is None:
        db.scenario_user.insert(scenario_id=scenario_id, user_id=user_id, passed=True)
    else:
        scenario_user["passed"] = not scenario_user["passed"]
        scenario_user.update_record()

@auth.requires_login()
def progress():
    """Displays progress and host for a given scenario-user tuple"""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        scenario_id = None
    if len(request.args) > 1:
        username = request.args(1, cast=str)
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    rabbit_mq_address = app_conf.take("monitutor_env.rabbit_mq_external_address")
    rabbit_mq_port = app_conf.take("monitutor_env.rabbit_mq_websocket_port")
    rabbit_mq_config = {"address": rabbit_mq_address, "port": rabbit_mq_port}
    scenario = db.monitutor_scenarios[scenario_id]

    hosts = db((scenario_id == db.monitutor_milestone_scenario.scenario_id) &
                     (db.monitutor_milestone_scenario.milestone_id ==
                         db.monitutor_milestones.milestone_id) &
                     (db.monitutor_check_milestone.milestone_id ==
                         db.monitutor_milestones.milestone_id) &
                     (db.monitutor_check_milestone.check_id ==
                         db.monitutor_checks.check_id) &
                     (db.monitutor_systems.system_id ==
                         db.monitutor_targets.system_id) &
                     (db.monitutor_checks.check_id ==
                         db.monitutor_targets.check_id)).select(
                                 db.monitutor_systems.system_id,
                                 db.monitutor_systems.display_name,
                                 db.monitutor_systems.name,
                                 distinct=True)

    milestones = db((db.monitutor_milestones.milestone_id ==
                          db.monitutor_milestone_scenario.milestone_id) &
                         (db.monitutor_milestone_scenario.scenario_id ==
                          scenario_id)).select(orderby=db.monitutor_milestone_scenario.sequence_nr)
    data = db((db.monitutor_data.data_id == db.monitutor_scenario_data.data_id) &
                    (db.monitutor_scenario_data.scenario_id == scenario_id)).select()
    checks = dict()
    for milestone in milestones:
        check_milestone = db((db.monitutor_check_milestone.milestone_id ==
                                  milestone.monitutor_milestones.milestone_id) &
                                  (db.monitutor_check_milestone.check_id ==
                                  db.monitutor_checks.check_id) &
                                  (db.monitutor_systems.system_id ==
                                   db.monitutor_targets.system_id) &
                                  (db.monitutor_targets.type_id == 1) & # 1 = source
                                  (db.monitutor_checks.check_id ==
                                   db.monitutor_targets.check_id)).select(orderby=
                                                                            db.monitutor_check_milestone.sequence_nr)
        checks[milestone.monitutor_milestones.milestone_id] = check_milestone
    scenario_info = {"description": scenario.description,
                     "display_name": scenario.display_name,
                     "scenario_id": scenario_id,
                     "scenario_name": scenario.name,
                     "goal": scenario.goal,
                     "milestones": milestones,
                     "checks": checks,
                     "hosts": hosts,
                     "username": username}
    return dict(scenario_info=scenario_info, rabbit_mq_config=rabbit_mq_config, data=data)

@auth.requires_login()
def get_host_status():
    """Get current status of a given host"""
    hostname = request.vars.hostName
    username = request.vars.userName
    if not auth.has_membership("admin"):
        username = session.auth.user.username
    host = resultdb.host_status(username=username, hostname=hostname)
    if host:
        hoststate = host[0]["value"]["severity"]
        output = host[0]["value"]["output"]
    else:
        hoststate = 3
        output = "Disconnected"
    return json.dumps(dict(output=output, state=hoststate, hostName=hostname))

@auth.requires_login()
def get_service_status():
    """Get status of a given service"""
    check_name = request.vars.checkName
    username = requset.vars.userName
    if not auth.has_membership("admin"):
        username = session.auth.user.username
    check_result = resultdb.check_results(username=username, check_name=check_name)
    if check_result:
        checkstate = check_result[0]["value"]["severity"]
        output = check_result[0]["value"]["output"]
    else:
        checkstate = 3
        output = "Unknown"
    return json.dumps(dict(output=output, state=checkstate, checkName=check_name))

@auth.requires_login()
def get_services_status():
    checknames = json.loads(request.vars.checkNames)
    username = request.vars.userName
    if not auth.has_membership("admin"):
        username = session.auth.user.username
    status = list()
    for row in resultdb.check_results(username=username, check_name=checknames):
        status.append(dict(output=row["value"]["output"],
                           state=row["value"]["severity"],
                           checkName=row["key"][1],
                           attachments=row["value"]["attachments"],
                           hostname=row["value"]["hostname"]))
    return json.dumps(status)

@auth.requires_login()
def get_successful_checks():
    scenario_name = request.vars.scenarioName
    username = request.vars.userName
    if not auth.has_membership("admin"):
        username = session.auth.user.username
    return json.dumps(resultdb.successful_checks(scenario_name, username))

@auth.requires_login()
def put_check():
    check_name = request.vars.taskName
    username = request.vars.userName
    scenario_name = request.vars.scenarioName
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    check_host_program = db((db.monitutor_checks.name == check_name) &
        (db.monitutor_targets.check_id == db.monitutor_checks.check_id) &
        (db.monitutor_targets.type_id == db.monitutor_types.type_id) &
        (db.monitutor_types.name == "source") &
        (db.monitutor_targets.system_id == db.monitutor_systems.system_id) &
        (db.monitutor_checks.program_id == db.monitutor_programs.program_id ) &
        (db.monitutor_programs.interpreter_id == db.monitutor_interpreters.interpreter_id)).select(
            db.monitutor_checks.name,
            db.monitutor_checks.params,
            db.monitutor_checks.check_id,
            db.monitutor_programs.name,
            db.monitutor_interpreters.path,
            db.monitutor_systems.name,
            cache=(cache.ram, 360)).first()
    check = db(db.monitutor_checks.check_id == check_host_program.monitutor_checks.check_id).select(
            cache=(cache.ram, 3600)).first()
    attachments = db(db.monitutor_attachments.check_id == check.check_id).select(cache=(cache.ram, 360))
    check = { "name": check.name,
              "program": check_host_program.monitutor_programs.name,
              "params": __substitute_vars(check.params,
                                          check.check_id,
                                          username),
              "interpreter_path": check_host_program.monitutor_interpreters.path,
              "scenario_name": scenario_name}
    if attachments:
        check["attachments"] = []
        for attachment in attachments:
            check_attachment = {"name": attachment.name, "producer": attachment.producer}
            if attachment.filter:
                check_attachment["filter"] = attachment.filter
            if attachment.requires_status:
                check_attachment["requires_status"] = attachment.requires_status
            check["attachments"].append(check_attachment)
    topic = username+"."+check_host_program.monitutor_systems.name
    rabbit_mq_host = app_conf.take("monitutor_env.rabbit_mq_host")
    rabbit_mq_user = app_conf.take("monitutor_env.rabbit_mq_user")
    rabbit_mq_password = app_conf.take("monitutor_env.rabbit_mq_password")
    task_exchange = app_conf.take("monitutor_env.rabbit_mq_task_exchange")
    credentials = pika.credentials.PlainCredentials(rabbit_mq_user, rabbit_mq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbit_mq_host,
            credentials=credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=task_exchange, exchange_type="topic")
    channel.queue_declare(queue=topic, durable=True)
    channel.queue_bind(queue=topic, exchange=task_exchange, routing_key=topic)
    channel.basic_publish(
        exchange=task_exchange,
        routing_key=topic,
        body=json.dumps(check))
    connection.close()
    return json.dumps(dict(status="OK"))

def __substitute_vars(parameters, check_id, username):
    parameters = parameters.split()
    parameterSnippets = []
    for parameter in parameters:
        if parameter[0] == "$":
            parameter = __get_variable_value(parameter, check_id, username)
        parameterSnippets.append(parameter)
    return " ".join(parameterSnippets)

def __get_variable_value(variable, check_id, username):
    system_type = variable.split(".")[0].lower()[1:]
    attribute = None
    if len(system_type) is 2:
        attribute = ''.join(variable.split("."))[1:]
    system = db((db.monitutor_targets.check_id == check_id) &
                      (db.monitutor_targets.system_id == db.monitutor_systems.system_id) &
                      (db.monitutor_targets.type_id == db.monitutor_types.type_id) &
                      (db.monitutor_types.name == system_type)
                      ).select(db.monitutor_systems.ALL, cache=(cache.ram, 360), cacheable=True).first()
    # check if the system was customized
    user_system = db((system.system_id ==
                           db.monitutor_user_system.system_id) &
                          (username == db.auth_user.username) &
                          (db.auth_user.id == db.monitutor_user_system.user_id)
                         ).select(cache=(cache.ram, 360), cacheable=True)
    if len(user_system):
        user_system = user_system.first()
        system.hostname = user_system.monitutor_user_system.hostname
        system.ip4_address = user_system.monitutor_user_system.ip4_address
        system.ip6_address = user_system.monitutor_user_system.ip6_address
    if attribute is None or attribute == "hostname":
        parameter = system.hostname
    if attribute == "ipv4_address":
        parameter = str(system.ip4_address)
    elif attribute == "ipv6_address":
        parameter = str(system.ip6_address)
    else:
        # in this case the attribute is a custom attribute
        custom_attributes = db((db.monitutor_customvar_system.name == attribute) &
                                    (db.monitutor_customvar_system.system_id ==
                                     system.system_id)
                                    ).select(cache=(cache.ram, 360), cacheable=True)
        if len(custom_attributes):
            parameter = custom_attributes.value
        else:
            # Fallback to hostname in case the attribute was not found
            parameter = system.hostname
    return parameter

def __generate_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))

@auth.requires_login()
def create_rabbit_user():
    username = request.vars.username
    if username is None or not auth.has_membership("admin"):
        username = session.auth.user.username
    scenario_name = request.vars.scenarioName
    rabbit_mq_host = app_conf.take("monitutor_env.rabbit_mq_host")
    rabbit_mq_management_port = app_conf.take("monitutor_env.rabbit_mq_management_port")
    rabbit_mq_user = app_conf.take("monitutor_env.rabbit_mq_user")
    rabbit_mq_password = app_conf.take("monitutor_env.rabbit_mq_password")
    result_exchange = app_conf.take("monitutor_env.rabbit_mq_result_exchange")
    tags = "monitutor-user"
    if auth.has_membership("admin"):
        tags += ", monitutor-admin"
    rabbit_mq_url = "http://"+rabbit_mq_host+":"+rabbit_mq_management_port+"/api"
    request_url = rabbit_mq_url+"/users/"+session.auth.user.username
    headers = {'Accpet': 'application/json'}
    password = __generate_random_string(24)
    data = {"password": password, "tags": tags}
    answer = requests.put(request_url,
                 headers=headers,
                 auth=(rabbit_mq_user, rabbit_mq_password),
                 data=json.dumps(data))
    if answer.status_code > 299:
        return json.dumps({"status": "ERROR setting password"})

    queue_args = {
                  "durable": True,
                  "auto-delete": False,
                  "exclusive": False,
                  "arguments": {
                    "x-message-ttl": 120000, # 2 min
                    "x-expires": 120000 # 2 min
                    }
                  }
    queue_name =  username+"-"+__generate_random_string(6)
    request_url = rabbit_mq_url + \
                 '/queues/%2F/' + \
                 queue_name
    answer = requests.put(request_url,
                 headers=headers,
                 auth=(rabbit_mq_user, rabbit_mq_password),
                 data=json.dumps(queue_args))
    if answer.status_code > 299:
        return json.dumps({"status": "ERROR creating queue"})

    data = {"routing_key": username+".*"}
    request_url = rabbit_mq_url+'/bindings/%2F/e/'+result_exchange+'/q/'+queue_name
    answer = requests.post(request_url,
                 headers=headers,
                 auth=(rabbit_mq_user, rabbit_mq_password),
                 data=json.dumps(data))
    if answer.status_code > 299:
        return json.dumps({"status": "ERROR creating bind"})

    data = {"configure": "^"+session.auth.user.username+"-.{6}$", "write": "^$", "read": "^"+session.auth.user.username+"-.{6}$"}
    if auth.has_membership("admin"):
        data["read"] = ".*"
    request_url = rabbit_mq_url+'/permissions/%2F/'+session.auth.user.username
    answer = requests.put(request_url,
                 headers=headers,
                 auth=(rabbit_mq_user, rabbit_mq_password),
                 data=json.dumps(data))
    if answer.status_code > 299:
        return json.dumps({"status": "ERROR setting permissions"})
    return json.dumps({"status": "OK", "password": password, "queue_name": queue_name, "queue_args": queue_args, "code": answer.status_code})

@auth.requires_login()
def poll_results():
    username = request.vars.userName
    queue_name = str(request.vars.queueName)
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    queue_name = username +"-"+ queue_name.split("-")[1]
    rabbit_mq_host = app_conf.take("monitutor_env.rabbit_mq_host")
    rabbit_mq_user = app_conf.take("monitutor_env.rabbit_mq_user")
    rabbit_mq_password = app_conf.take("monitutor_env.rabbit_mq_password")
    result_exchange = app_conf.take("monitutor_env.rabbit_mq_result_exchange")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbit_mq_host,
            credentials=pika.PlainCredentials(rabbit_mq_user, rabbit_mq_password)
            )
        )
    channel = connection.channel()
    results = []
    while True:
        method, header, result = channel.basic_get(queue=queue_name)
        if result == None:
            break
        else:
            results.append(result)
            channel.basic_ack(method.delivery_tag)
    connection.close()
    return json.dumps(dict(results=results))

@auth.requires_login()
def get_attachment():
    username = request.vars.userName
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    attachment = request.vars.attachment
    check = request.vars.check
    return json.dumps(dict(result=resultdb.get_attachment(username, check, attachment)))
