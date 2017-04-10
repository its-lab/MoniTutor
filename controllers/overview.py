@auth.requires_login()
def view_scenarios():
    """Display available scenarios and the number of active students for each of them"""
    count = tutordb.monitutor_scenarios.scenario_id.count()
    if auth.has_membership("admin"):
        scenarios = tutordb(
                            (tutordb.monitutor_scenarios.initiated == True) &
                            (tutordb.monitutor_scenarios.scenario_id == tutordb.scenario_user.scenario_id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(tutordb.monitutor_scenarios.ALL,
                                     count,
                                     groupby=tutordb.monitutor_scenarios.scenario_id)
    else:
        scenarios = tutordb(
                            (tutordb.monitutor_scenarios.initiated == True) &
                            (tutordb.monitutor_scenarios.hidden == False) &
                            (tutordb.monitutor_scenarios.scenario_id == tutordb.scenario_user.scenario_id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(tutordb.monitutor_scenarios.ALL,
                                     count,
                                     groupby=tutordb.monitutor_scenarios.scenario_id)

    return dict(scenarios=scenarios)


@auth.requires_login()
def view_progress():
    """Display the name and progress for each student working on a given scenario"""
    if len(request.args) is 0:
        redirect(URL('default','index'))
    scenario_id = request.args(0, cast=int)
    if auth.has_membership("admin"):
        update_progress(scenario_id)
    user_scenario = tutordb((tutordb.scenario_user.scenario_id == scenario_id) &
                            (tutordb.scenario_user.user_id == tutordb.auth_user.id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(orderby=tutordb.scenario_user.progress)
    return dict(user_scenario=user_scenario, scenario_id=scenario_id)


@auth.requires_membership("admin")
def reveal_progress():
    """Display the name and progress for each student working on a given scenario on a reveal.js slide"""
    if len(request.args) is 0:
        redirect(URL('default','index'))
    scenario_id = request.args(0, cast=int)
    amount = 5
    only_successful = 1
    if len(request.args) > 1:
        amount = request.args(1, cast=int)
    if len(request.args) > 2:
        only_successful = 0

    if auth.has_membership("admin"):
        update_progress(scenario_id)
    user_scenairo = tutordb((tutordb.scenario_user.scenario_id == scenario_id) &
                            (tutordb.scenario_user.user_id == tutordb.auth_user.id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(orderby=tutordb.scenario_user.progress)
    reveal_autoscroll = 15
    return dict(user_scenario=user_scenairo, scenario_id=scenario_id, amount=amount, only_successful=only_successful, reveal_autoscroll=reveal_autoscroll)


@auth.requires_membership("admin")
def get_user_events():
    scenario_id = request.vars.scenarioId
    user_id = request.vars.userId
    amount = 5
    only_successful = request.vars.onlySuccessful
    if request.vars.amount != amount:
        amount = int(request.vars.amount)
    
    check_rows = tutordb((tutordb.monitutor_milestone_scenario.scenario_id == scenario_id) &
                         (tutordb.monitutor_milestones.milestone_id == 
                          tutordb.monitutor_milestone_scenario.milestone_id) &
                         (tutordb.monitutor_milestones.milestone_id ==
                          tutordb.monitutor_check_milestone.milestone_id) &
                         (tutordb.monitutor_checks.check_id ==
                          tutordb.monitutor_check_milestone.check_id)&
                         (tutordb.monitutor_milestone_scenario.hidden == False)&
                         (tutordb.monitutor_check_milestone.flag_invis== False)).select()
    
    user_row = tutordb.auth_user[user_id]
    username = user_row.username
    checks_by_name = {}
    for check in check_rows:
        check_name = username +"_"+ check.monitutor_checks.name
        checks_by_name[check_name] = check
    
    if only_successful == "true":
        service_hist = db((db.icinga_statehistory.object_id ==   db.icinga_objects.object_id) &
                      (db.icinga_objects.is_active == 1) &
                      (db.icinga_statehistory.state == 0) &
                      (db.icinga_statehistory.state != db.icinga_statehistory.last_state) &
                      (db.icinga_objects.name2.startswith(str(username)))).select(orderby=~db.icinga_statehistory.state_time,
                              limitby=(0,20))
    else:
        service_hist = db((db.icinga_statehistory.object_id ==   db.icinga_objects.object_id) &
                      (db.icinga_objects.is_active == 1) &
                      (db.icinga_statehistory.state != db.icinga_statehistory.last_state) &
                      (db.icinga_objects.name2.startswith(str(username)))).select(orderby=~db.icinga_statehistory.state_time,
                              limitby=(0,20))

    check_events = []
    i = 0
    for event in service_hist:
        if event.icinga_objects.name2 in checks_by_name:
            check_info = checks_by_name[event.icinga_objects.name2]
            check_events.append({
                "checkInfo": 
                {
                    "hint": check_info.monitutor_checks.hint,
                    "displayName": check_info.monitutor_checks.display_name,
                },
                "checkState":
                {
                    "state": event.icinga_statehistory.state,
                    "lastState": event.icinga_statehistory.last_state,
                    "time": str((datetime.datetime.now(event.icinga_statehistory.state_time.tzinfo)-event.icinga_statehistory.state_time).total_seconds()).split('.',2)[0],
                    "output": event.icinga_statehistory.output
                }
            })
            i = i+1
            if i >= amount:
                break

    return json.dumps(check_events)
