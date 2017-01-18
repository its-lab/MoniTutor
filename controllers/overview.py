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
    user_scenairo = tutordb((tutordb.scenario_user.scenario_id == scenario_id) &
                            (tutordb.scenario_user.user_id == tutordb.auth_user.id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(orderby=tutordb.scenario_user.progress)
    return dict(user_scenairo=user_scenairo, scenario_id=scenario_id)


@auth.requires_membership("admin")
def reveal_progress():
    """Display the name and progress for each student working on a given scenario on a reveal.js slide"""
    if len(request.args) is 0:
        redirect(URL('default','index'))
    scenario_id = request.args(0, cast=int)
    if auth.has_membership("admin"):
        update_progress(scenario_id)
    user_scenairo = tutordb((tutordb.scenario_user.scenario_id == scenario_id) &
                            (tutordb.scenario_user.user_id == tutordb.auth_user.id) &
                            (tutordb.scenario_user.status == "initiated")
                            ).select(orderby=tutordb.scenario_user.progress)
    return dict(user_scenario=user_scenairo, scenario_id=scenario_id)

