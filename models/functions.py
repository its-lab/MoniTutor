def update_progress(scenario_id):
    checks = tutordb((tutordb.monitutor_milestone_scenario.scenario_id == scenario_id) &
                     (tutordb.monitutor_milestone_scenario.milestone_id ==
                      tutordb.monitutor_milestones.milestone_id) &
                     (tutordb.monitutor_milestones.milestone_id ==
                      tutordb.monitutor_check_milestone.milestone_id) &
                     (tutordb.monitutor_check_milestone.check_id ==
                      tutordb.monitutor_checks.check_id) &
                     (tutordb.monitutor_check_milestone.flag_invis == '0') &
                     (tutordb.monitutor_milestone_scenario.hidden == '0')
                     ).select()


    for userinfo in tutordb((tutordb.scenario_user.scenario_id == scenario_id) &
                            (tutordb.auth_user.id == tutordb.scenario_user.user_id) &
                            ("initiated" == tutordb.scenario_user.status)
                            ).select():
        username = userinfo.auth_user.username
        successful = 0
        maximum = 0
        for check in checks:
            maximum +=1
            checkname = str(username) + "_" + str(check.monitutor_checks.name)
            if userinfo.scenario_user.initiation_time is not None:
                history = db(
                             (db.icinga_objects.object_id == db.icinga_statehistory.object_id) &
                             (db.icinga_objects.name2 == checkname) &
                             (db.icinga_statehistory.state == 0) &
                             (db.icinga_statehistory.state_time > userinfo.scenario_user.initiation_time)).select()
                if len(history):
                    successful += 1
            else:  # For those scenarios, initiated before there was a timestamp
                history = db(
                             (db.icinga_objects.object_id == db.icinga_statehistory.object_id) &
                             (db.icinga_objects.name2 == checkname) &
                             (db.icinga_statehistory.state == 0)).select()
                if len(history):
                    successful += 1
        if maximum:
            percent = (float(successful) / maximum) * 100
            tutordb((tutordb.scenario_user.user_id == userinfo.auth_user.id) &
                    (tutordb.scenario_user.scenario_id == scenario_id)).update(progress=percent)
    return True

