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

    scenarios = tutordb((tutordb.monitutor_scenarios.hidden == False) &
                        (tutordb.monitutor_scenarios.initiated == True)).select()
    return dict(scenarios=scenarios, user_id=user_id)


@auth.requires_login()
def init_scenario():
    """Triggers scenario initiation for a given senario-user tuple"""
    scenario_id = request.vars.scenarioid
    if auth.has_membership("admin"):
        username = request.vars.username
    else:
        username = session.auth.user.username

    new_task = initializer.queue_task('api_init_scenario', group_name="init", pargs=[username, scenario_id])

    user = tutordb(tutordb.auth_user.username == username).select()

    tutordb.scenario_user.update_or_insert((tutordb.scenario_user.scenario_id == scenario_id) &
                                           (tutordb.scenario_user.user_id == user[0].id),
                                            scenario_id=scenario_id,
                                            user_id=user[0].id,
                                            status="initiating")
    tutordb.commit()
    return json.dumps({"progress": 20, "newTask": new_task.id})


@auth.requires_login()
def delete_scenario():
    """Triggers scenario deletion for a given scenario-user tuple"""
    scenario_id = request.vars.scenarioId
    if auth.has_membership("admin"):
        user_id = request.vars.userId
    else:
        user_id = auth.user_id

    user = tutordb.auth_user[user_id]

    new_task = initializer.queue_task('drop_user_scenario', group_name="init", pargs=[user.username, scenario_id])

    tutordb.scenario_user.update_or_insert((tutordb.scenario_user.scenario_id == scenario_id) &
                                           (tutordb.scenario_user.user_id == user_id),
                                            scenario_id=scenario_id,
                                            user_id=user_id,
                                            status="")
    tutordb.commit()
    return json.dumps({"progress": 20, "newTask": new_task.id})


@auth.requires_login()
def update_task_status():
    """Asks the Web2py database for the status of a given task to display it as a progress bar"""
    error = "None"
    task_id = request.vars.taskId
    task_info = initializer.task_status(int(task_id), output=True)
    if task_info is not None:
        status = task_info.scheduler_task.status
    else:
        status = "UNKNOWN TaskID: " + task_id
        error  = "Couldn't find task"

    if status == "QUEUED":
        progress = 40
    elif status == "ASSIGNED":
        progress = 60
    elif status == "RUNNING":
        progress = 80
    elif status == "COMPLETED":
        progress = 100
    else:
        progress = 0
        error = "STATUS: "+status

    return json.dumps({"progress": progress, "error": error})


@auth.requires_login()
def queue_task():
    """Queues a check for the MoniTunnel application to execute"""
    scenario_id = request.vars.scenarioid
    check_milestone_id = request.vars.checkMilestoneId
    if auth.has_membership("admin"):
        username = request.vars.username
    else:
        username = session.auth.user.username

    prio = 20
    if auth.has_membership("admin"):
        prio = 50

    checks = tutordb((tutordb.monitutor_check_milestone.check_milestone_id == check_milestone_id) &
                            (tutordb.monitutor_checks.check_id == tutordb.monitutor_check_milestone.check_id)).select()
    tutordb_check = checks[0].monitutor_checks.name
    check_name = username + "_" + tutordb_check

    checkdata = tutordb((tutordb_check == tutordb.monitutor_checks.name) &
                        (tutordb.monitutor_checks.program_id == tutordb.monitutor_programs.program_id) &
                        (tutordb.monitutor_programs.interpreter_id == tutordb.monitutor_interpreters.interpreter_id) &
                        (tutordb.monitutor_checks.check_id == tutordb.monitutor_targets.check_id) &
                        (tutordb.monitutor_targets.system_id == tutordb.monitutor_systems.system_id) &
                        (tutordb.monitutor_targets.type_id == tutordb.monitutor_types.type_id) &
                        (tutordb.monitutor_types.name == "source")).select()

    if len(checkdata) is 1:
        parameters = checkdata[0].monitutor_checks.params
        parameters = parameters.split()
        parameterSnippets = []
        for parameter in parameters:
            if parameter[0] == "$":
                # parameter might look like: $DEST.community or $SOURCE.ip4_address
                system_type = parameter.split(".")
                attribute = None
                if len(system_type) is 2:
                    attribute = system_type[1].strip(".")
                system_type = system_type[0].strip("$").lower()
                system = tutordb((tutordb.monitutor_targets.check_id == checkdata[0].monitutor_checks.check_id) &
                                  (tutordb.monitutor_targets.system_id == tutordb.monitutor_systems.system_id) &
                                  (tutordb.monitutor_targets.type_id == tutordb.monitutor_types.type_id) &
                                  (tutordb.monitutor_types.name == system_type)
                                  ).select()
                if len(system):
                    system = system.first()
                    # check if the system was customized
                    user_system = tutordb((system.monitutor_targets.system_id ==
                                            tutordb.monitutor_user_system.system_id) &
                                            (username == tutordb.auth_user.username) &
                                            (tutordb.auth_user.id == tutordb.monitutor_user_system.user_id)).select()
                    if len(user_system):
                        user_system = user_system.first()
                        system.monitutor_systems.hostname = user_system.monitutor_user_system.hostname
                        system.monitutor_systems.ip4_address = user_system.monitutor_user_system.ip4_address
                        system.monitutor_systems.ip6_address = user_system.monitutor_user_system.ip6_address
                    if attribute is None:
                        parameter = system.monitutor_systems.hostname
                    if attribute == "ip4_address":
                        parameter = str(system.monitutor_systems.ip4_address)
                    elif attribute == "ip6_address":
                        parameter = str(system.monitutor_systems.ip6_address)
                    elif attribute == "hostname":
                        parameter = system.monitutor_systems.hostname
                    else:
                        # in this case the attribute is a custom attribute
                        custom_attributes = tutordb((tutordb.monitutor_customvar_system.name == attribute) &
                                                   (tutordb.monitutor_customvar_system.system_id ==
                                                    system.monitutor_systems.system_id)).select()
                        if len(custom_attributes):
                            parameter = custom_attributes.value
                        else:
                            # Fallback to hostname in case the attribute was not found
                            parameter = system.monitutor_systems.hostname
            parameterSnippets.append(parameter)
        parameters = " ".join(parameterSnippets)

        import datetime
        system_name = checkdata[0].monitutor_systems.hostname
        interpreter_path = checkdata[0].monitutor_interpreters.path
        program_name = checkdata[0].monitutor_programs.name
        new_task = tutordb.monitutor_check_tasks.insert(interpreter_path=interpreter_path,
                                             username=username,
                                             hostname=system_name,
                                             prio=prio,
                                             status="NEW",
                                             timestamp=datetime.datetime.now(),
                                             check_name=tutordb_check,
                                             parameters=parameters,
                                             program_name=program_name)

        return json.dumps(dict(newTask=new_task, checkName=check_name))
    return False



@auth.requires_login()
def update_task():
    """Queries Icinga-DB for service status when the scheduler task is finished"""
    task_id = request.vars.taskId

    if task_id is not None:
        task = tutordb.monitutor_check_tasks[task_id]
        status = task.status
    else:
        status = "DONE"

    if status == "DONE" or status == "ERROR":
        icinga_servicestatus = db((db.icinga_servicestatus.service_object_id == db.icinga_objects.object_id) &
                                  (db.icinga_objects.name1 == (task.username + "_" + task.hostname)) &
                                  (db.icinga_objects.name2 == (task.username + "_" + task.check_name))).select()

        current_state = icinga_servicestatus[0].icinga_servicestatus.current_state
        output = icinga_servicestatus[0].icinga_servicestatus.output
    else:
        current_state = 3
        output = "No result"

    return json.dumps(dict(currentState=current_state, output=output, status=status))


@auth.requires_login()
def update_host():
    """Queries Icinga-DB for the status of a given host"""
    hostid = request.vars.hostId[1:]  # Strip H character from ID
    host = db.icinga_hoststatus[hostid]
    return json.dumps(dict(output=host.output, state=host.current_state))



@auth.requires_login()
def view_milestones():
    """Displays each milestone and host for a given scenario-user tuple"""

    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        scenario_id = None
    if len(request.args) > 1:
        username = request.args(1, cast=str)
    else:
        username = None

    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    scenario = tutordb.monitutor_scenarios[scenario_id]
    scenario_info = {"description": scenario.description,
                     "display_name": scenario.display_name,
                     "scenario_id": scenario_id,
                     "goal": scenario.goal}

    milestones = tutordb((tutordb.monitutor_milestones.milestone_id ==
                          tutordb.monitutor_milestone_scenario.milestone_id) &
                         (tutordb.monitutor_milestone_scenario.scenario_id ==
                          scenario_id)).select(orderby=tutordb.monitutor_milestone_scenario.sequence_nr)

    scenario_info["milestones"] = milestones

    data = tutordb((tutordb.monitutor_scenario_data.scenario_id == scenario_id) &
                   (tutordb.monitutor_scenario_data.data_id == tutordb.monitutor_data.data_id)).select()
    if len(data):
        scenario_info["data"] = data

    hosts = db((db.icinga_hoststatus.host_object_id == db.icinga_customvariables.object_id) &
               (db.icinga_hosts.host_object_id == db.icinga_customvariables.object_id) &
               (db.icinga_customvariables.varname == "owner") &
               (db.icinga_customvariables.varvalue == username) &
               (db.icinga_objects.object_id == db.icinga_hoststatus.host_object_id) &
               (db.icinga_objects.is_active == "1")).select()

    checks = {}
    for milestone in milestones:
        check_milestone = tutordb((tutordb.monitutor_check_milestone.milestone_id ==
                                  milestone.monitutor_milestones.milestone_id) &
                                  (tutordb.monitutor_check_milestone.check_id ==
                                  tutordb.monitutor_checks.check_id) &
                                  (tutordb.monitutor_systems.system_id ==
                                   tutordb.monitutor_targets.system_id) &
                                  (tutordb.monitutor_checks.check_id ==
                                   tutordb.monitutor_targets.check_id)).select(orderby=
                                                                            tutordb.monitutor_check_milestone.sequence_nr)
        checks[milestone.monitutor_milestones.milestone_id] = check_milestone

    scenario_info["checks"] = checks
    user_s = tutordb((tutordb.scenario_user.user_id == tutordb.auth_user.id) &
                     (tutordb.auth_user.username == username) &
                     (tutordb.scenario_user.scenario_id == scenario_id)).select()

    return dict(scenarioinfo=scenario_info, username=username, hosts=hosts, args=request.args, user_s=user_s)


@auth.requires_login()
def edit_system():
    if auth.has_membership("admin") and len(request.args)>1:
        system_id = request.args(0, cast=int)
        user_id = request.args(1, cast=int)
    elif len(request.args) is 0:
        redirect(URL('default','index'))
    else:
        user_id = auth.user_id
        system_id = request.args(0, cast=str)
    system = tutordb((tutordb.monitutor_user_system.user_id == user_id)&
                     (tutordb.monitutor_user_system.system_id == system_id)).select()
    if len(system):
        system = system.first()
    else:
        system = tutordb.monitutor_systems[system_id]

    user_system_form = SQLFORM(tutordb.monitutor_user_system, fields=["hostname"])
    ipv4_field  = LABEL('Ipv4 Address: '), INPUT(_name='ipv4',
            value=system.ip4_address, requires=IS_IPV4())
    ipv6_field  = LABEL('Ipv6 Address: '), INPUT(_name='ipv6',
            value=system.ip6_address, requires=IS_IPV6())

    user_system_form.vars.hostname = system.hostname
    user_system_form[0].insert(-1, ipv4_field)
    user_system_form[0].insert(-1, ipv6_field)

    if user_system_form.validate():
        system = tutordb((tutordb.monitutor_user_system.user_id ==
            user_id)&
                (tutordb.monitutor_user_system.system_id ==
                    system_id)).select()
        if len(system):
            system = system.first()
            system.hostname = user_system_form.vars.hostname
            system.ip4_address = user_system_form.vars.ipv4
            system.ip6_address = user_system_form.vars.ipv6
            system.update_record()
        else:
            tutordb.monitutor_user_system.update_or_insert(
                    system_id = system_id,
                    user_id = user_id,
                    hostname = user_system_form.vars.hostname,
                    ip4_address = user_system_form.vars.ipv4,
                    ip6_address = user_system_form.vars.ipv6)
        redirect(URL(args=[system_id,user_id]))

    return dict(user_system_form=user_system_form)


@auth.requires_login()
def edit_systems():
    if auth.has_membership("admin") and len(request.args)>1:
        scenario_id = request.args(0, cast=int)
        user_id = request.args(1, cast=int)
    elif len(request.args) is 0:
        redirect(URL('default','index'))
    else:
        scenario_id = request.args(0, cast=int)
        user_id = auth.user_id

    if scenario_id > 0:
        scenario_systems = tutordb((tutordb.monitutor_milestone_scenario.scenario_id
                                == scenario_id)&
                               (tutordb.monitutor_checks.check_id ==
                                tutordb.monitutor_check_milestone.check_id)&
                               (tutordb.monitutor_targets.check_id ==
                                tutordb.monitutor_checks.check_id)&
                               (tutordb.monitutor_targets.check_id ==
                                   tutordb.monitutor_checks.check_id)&
                               (tutordb.monitutor_systems.system_id ==
                                   tutordb.monitutor_targets.system_id)).select(
                                           tutordb.monitutor_systems.display_name,
                                           tutordb.monitutor_systems.description,
                                           tutordb.monitutor_systems.system_id,
                                           distinct=True)
    else:
        scenario_systems = tutordb(
                               (tutordb.monitutor_systems.system_id ==
                                   tutordb.monitutor_targets.system_id)).select(
                                           tutordb.monitutor_systems.display_name,
                                           tutordb.monitutor_systems.description,
                                           tutordb.monitutor_systems.system_id,
                                           distinct=True)
    return dict(scenario_systems = scenario_systems, user_id = user_id)


@auth.requires_membership("admin")
def toggle_scenario_done():
    user_id = request.vars.userId
    scenario_id = request.vars.scenarioId
    scenario_user = tutordb((tutordb.scenario_user.user_id == user_id) &
                            (tutordb.scenario_user.scenario_id == scenario_id)).select().first()
    scenario_user["passed"] = not scenario_user["passed"]
    scenario_user.update_record()


def get_history():
    if auth.has_membership("admin"):
        user_id = request.vars.userId;
    else:
        user_id = auth.user_id
    scenario_id = request.vars.scenarioId
    object_id = request.vars.objectId
    user_scenario = tutordb((tutordb.scenario_user.scenario_id == scenario_id)&
            (tutordb.scenario_user.user_id == user_id)).select().first()
    history = db((db.icinga_statehistory.object_id == object_id)&
            (db.icinga_statehistory.state_time > user_scenario.initiation_time)).select(
                    db.icinga_statehistory.output,
                    db.icinga_statehistory.state,
                    orderby=~db.icinga_statehistory.state_time)
    return json.dumps({"history": history.as_list()})

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
    else:
        username = None
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    rabbit_mq_address = app_conf.take("monitutor_env.rabbit_mq_external_address")
    rabbit_mq_port = app_conf.take("monitutor_env.rabbit_mq_websocket_port")
    rabbit_mq_config = {"address": rabbit_mq_address, "port": rabbit_mq_port}
    scenario = tutordb.monitutor_scenarios[scenario_id]

    hosts = tutordb((scenario_id == tutordb.monitutor_milestones.milestone_id) &
                     (tutordb.monitutor_check_milestone.milestone_id ==
                         tutordb.monitutor_milestones.milestone_id) &
                     (tutordb.monitutor_check_milestone.check_id ==
                         tutordb.monitutor_checks.check_id) &
                     (tutordb.monitutor_systems.system_id ==
                         tutordb.monitutor_targets.system_id) &
                     (tutordb.monitutor_checks.check_id ==
                         tutordb.monitutor_targets.check_id)).select(
                                 tutordb.monitutor_systems.system_id,
                                 tutordb.monitutor_systems.display_name,
                                 tutordb.monitutor_systems.name,
                                 distinct=True)

    milestones = tutordb((tutordb.monitutor_milestones.milestone_id ==
                          tutordb.monitutor_milestone_scenario.milestone_id) &
                         (tutordb.monitutor_milestone_scenario.scenario_id ==
                          scenario_id)).select(orderby=tutordb.monitutor_milestone_scenario.sequence_nr)

    checks = dict()
    for milestone in milestones:
        check_milestone = tutordb((tutordb.monitutor_check_milestone.milestone_id ==
                                  milestone.monitutor_milestones.milestone_id) &
                                  (tutordb.monitutor_check_milestone.check_id ==
                                  tutordb.monitutor_checks.check_id) &
                                  (tutordb.monitutor_systems.system_id ==
                                   tutordb.monitutor_targets.system_id) &
                                  (tutordb.monitutor_checks.check_id ==
                                   tutordb.monitutor_targets.check_id)).select(orderby=
                                                                            tutordb.monitutor_check_milestone.sequence_nr)
        checks[milestone.monitutor_milestones.milestone_id] = check_milestone
    scenario_info = {"description": scenario.description,
                     "display_name": scenario.display_name,
                     "scenario_id": scenario_id,
                     "goal": scenario.goal,
                     "milestones": milestones,
                     "checks": checks,
                     "hosts": hosts,
                     "username": username}
    return dict(scenario_info=scenario_info, rabbit_mq_config=rabbit_mq_config)


@auth.requires_login()
def get_host_status():
    """Queries Icinga-DB for the status of a given host"""
    hostname = request.vars.hostName
    host  = db((db.icinga_hoststatus.host_object_id == db.icinga_objects.id) &
               (db.icinga_objects.name1 == hostname)) \
               .select(db.icinga_hoststatus.output, db.icinga_hoststatus.current_state) \
               .first()
    return json.dumps(dict(output=host.output, state=host.current_state, hostName=hostname))

@auth.requires_login()
def get_service_status():
    """Queries Icinga-DB for the status of a given service"""
    servicename = request.vars.checkName
    service = db((db.icinga_servicestatus.service_object_id == db.icinga_objects.id) &
                 (db.icinga_objects.name2 == servicename)) \
                 .select(db.icinga_servicestatus.output, db.icinga_servicestatus.current_state) \
                 .first()
    return json.dumps(dict(output=service.output, state=service.current_state, checkName=servicename))

@auth.requires_login()
def put_check():
    check_name = request.vars.taskName
    username = request.vars.userName
    if not auth.has_membership("admin") or username is None:
        username = session.auth.user.username
    check_host_program = tutordb((tutordb.monitutor_checks.name == check_name) &
        (tutordb.monitutor_targets.check_id == tutordb.monitutor_checks.check_id) &
        (tutordb.monitutor_targets.type_id == tutordb.monitutor_types.type_id) &
        (tutordb.monitutor_types.name == "source") &
        (tutordb.monitutor_targets.system_id == tutordb.monitutor_systems.system_id) &
        (tutordb.monitutor_checks.program_id == tutordb.monitutor_programs.program_id ) &
        (tutordb.monitutor_programs.interpreter_id == tutordb.monitutor_interpreters.interpreter_id)).select(
            tutordb.monitutor_checks.name,
            tutordb.monitutor_checks.params,
            tutordb.monitutor_checks.check_id,
            tutordb.monitutor_programs.name,
            tutordb.monitutor_interpreters.path,
            tutordb.monitutor_systems.name,
            cache=(cache.ram, 360)).first()
    check = { "name": check_host_program.monitutor_checks.name,
              "program": check_host_program.monitutor_programs.name,
              "params": __substitute_vars(check_host_program.monitutor_checks.params,
                                          check_host_program.monitutor_checks.check_id,
                                          username),
              "interpreter_path": check_host_program.monitutor_interpreters.path}
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
    system = tutordb((tutordb.monitutor_targets.check_id == check_id) &
                      (tutordb.monitutor_targets.system_id == tutordb.monitutor_systems.system_id) &
                      (tutordb.monitutor_targets.type_id == tutordb.monitutor_types.type_id) &
                      (tutordb.monitutor_types.name == system_type)
                      ).select(tutordb.monitutor_systems.ALL, cache=(cache.ram, 360), cacheable=True).first()
    # check if the system was customized
    user_system = tutordb((system.system_id ==
                           tutordb.monitutor_user_system.system_id) &
                          (username == tutordb.auth_user.username) &
                          (tutordb.auth_user.id == tutordb.monitutor_user_system.user_id)
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
        custom_attributes = tutordb((tutordb.monitutor_customvar_system.name == attribute) &
                                    (tutordb.monitutor_customvar_system.system_id ==
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
    queue_name =  session.auth.user.username+"-"+__generate_random_string(6)
    request_url = rabbit_mq_url + \
                 '/queues/%2F/' + \
                 queue_name
    answer = requests.put(request_url,
                 headers=headers,
                 auth=(rabbit_mq_user, rabbit_mq_password),
                 data=json.dumps(queue_args))
    if answer.status_code > 299:
        return json.dumps({"status": "ERROR creating queue"})

    data = {"routing_key": session.auth.user.username+".*"}
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
    return json.dumps(dict(results=results))
