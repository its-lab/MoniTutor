@auth.requires_membership("admin")
def view_scenarios():
    """Display available scenarios"""
    count = db.monitutor_scenarios.scenario_id.count()
    if auth.has_membership("admin"):
        scenarios = db().select(db.monitutor_scenarios.ALL)
    else:
        scenarios = db(db.monitutor_scenarios.hidden == False).select()
    active_students = dict()
    for scenario in scenarios:
        active_students[scenario.name] = len(resultdb.active_students(scenario.name))
    return dict(scenarios=scenarios, active_students=active_students)

@auth.requires_membership("admin")
def view_progress():
    """Display the name and progress for each student working on a given scenario"""
    if len(request.args) is 0:
        redirect(URL('default','index'))
    scenario_id = request.args(0, cast=int)
    scenario = db.monitutor_scenarios[scenario_id]
    active_students = resultdb.active_students(scenario.name)
    checks = __db_get_visible_checks(scenario_id)
    check_amount = len(checks)
    student_progress = dict()
    for student in active_students:
        student_progress[student] = {
            "successful_check_amount": resultdb.successful_checks_count(
                scenario.name, student)
            }
    passed_students = db((db.scenario_user.user_id == db.auth_user.id)
                               &(db.scenario_user.passed == True)).select()
    for student in passed_students:
        if student.auth_user.username not in student_progress:
            student_progress[student.auth_user.username] = {"successful_check_amount": 0}
        student_progress[student.auth_user.username]["passed"] = True
    return dict(student_progress=student_progress, check_amount=check_amount, scenario_id=scenario_id)
