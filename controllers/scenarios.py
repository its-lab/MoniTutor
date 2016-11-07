import json

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
                        (tutordb.monitutor_targets.type_id == 1)).select()

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

                systems = tutordb((tutordb.monitutor_targets.check_id == checkdata[0].monitutor_checks.check_id) &
                                  (tutordb.monitutor_targets.system_id == tutordb.monitutor_systems.system_id) &
                                  (tutordb.monitutor_targets.type_id == tutordb.monitutor_types.type_id) &
                                  (tutordb.monitutor_types.name == system_type)
                                  ).select()
                if len(systems):
                    if attribute is None:
                        parameter = systems[0].monitutor_systems.hostname
                    if attribute == "ip4_address":
                        parameter = str(systems[0].monitutor_systems.hostname)
                    elif attribute == "ip6_address":
                        parameter = str(systems[0].monitutor_systems.ip6_address)
                    elif attribute == "hostname":
                        parameter = systems[0].monitutor_systems.hostname
                    else:
                        # in this case the attribute is a custom attribute
                        custom_attributes = tutordb((tutordb.monitutor_customvar_system.name == attribute) &
                                                   (tutordb.monitutor_customvar_system.system_id ==
                                                    systems[0].monitutor_systems.system_id)).select()
                        if len(custom_attributes):
                            parameter = custom_attributes[0].value
                        else:
                            # Fallback to hostname in case the attribute was not found
                            parameter = systems[0].monitutor_systems.hostname
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

