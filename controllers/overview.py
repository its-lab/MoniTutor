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
    scenario = tutordb.monitutor_scenarios[scenario_id]
    active_students = resultdb.active_students(scenario.name)
    checks = tutordb((tutordb.monitutor_milestone_scenario.scenario_id == scenario_id) &
                     (tutordb.monitutor_milestone_scenario.milestone_id ==
                      tutordb.monitutor_milestones.milestone_id) &
                     (tutordb.monitutor_milestones.milestone_id ==
                      tutordb.monitutor_check_milestone.milestone_id) &
                     (tutordb.monitutor_check_milestone.check_id ==
                      tutordb.monitutor_checks.check_id) &
                     (tutordb.monitutor_check_milestone.flag_invis == False) &
                     (tutordb.monitutor_milestone_scenario.hidden == False)
                     ).select()
    check_amount = len(checks)
    student_progress = dict()
    for student in active_students:
        student_progress[student] = resultdb.successful_checks_count(scenario.name, student)
    return dict(student_progress=student_progress, check_amount=check_amount, scenario_id=scenario_id)
