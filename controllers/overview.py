@auth.requires_login()
def view_scenarios():
    """Display available scenarios"""
    count = tutordb.monitutor_scenarios.scenario_id.count()
    if auth.has_membership("admin"):
        scenarios = tutordb().select(tutordb.monitutor_scenarios.ALL)
    else:
        scenarios = tutordb(tutordb.monitutor_scenarios.hidden == False).select()
    active_students = dict()
    for scenario in scenarios:
        active_students[scenario.name] = len(resultdb.active_students(scenario.name))
    return dict(scenarios=scenarios, active_students=active_students)

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
        student_progress[student] = {"successful_check_amount": resultdb.successful_checks_count(scenario.name, student)}
    passed_students = tutordb((tutordb.scenario_user.user_id == tutordb.auth_user.id)
                               &(tutordb.scenario_user.passed == True)).select()
    for student in passed_students:
        student_progress[student.auth_user.username]["passed"] = True

    return dict(student_progress=student_progress, check_amount=check_amount, scenario_id=scenario_id)
