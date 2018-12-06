import json

@auth.requires_membership('admin')
def view_scenarios():
    """Displays all Scenarios and global scenario information"""
    scenarios = db(db.monitutor_scenarios).select()
    new_scenario_form = SQLFORM(db.monitutor_scenarios)
    if new_scenario_form.accepts(request, session):
        session.flash = 'Record inserted.'
        redirect(URL("manage_scenarios", "view_scenarios"))
    return dict(scenarios=scenarios, new_scenario_form=new_scenario_form)

@auth.requires_membership('admin')
def edit_scenario():
    """Displays a form to edit a given scenario"""
    scenario_id = request.args(0) or redirect(URL('index'))
    edit_scenario_form = SQLFORM(db.monitutor_scenarios,
                                 db.monitutor_scenarios(scenario_id))
    if edit_scenario_form.accepts(request, session):
        session.flash = 'Scenario updated'
        edit_scenario_form.process()
        return dict(form=SQLFORM(db.monitutor_scenarios, db.monitutor_scenarios(scenario_id)))
    return dict(form=edit_scenario_form)

@auth.requires_membership('admin')
def hide_scenario():
    """Sets the value of a given Scenarios hidden field to True"""
    scenario_id = request.vars.scenarioId
    db(db.monitutor_scenarios.scenario_id == scenario_id).update(hidden=True)
    return json.dumps({"scenarioId": scenario_id})

@auth.requires_membership('admin')
def show_scenario():
    """Sets the value of a given Scenarios hidden field to False"""
    scenario_id = request.vars.scenarioId
    db(db.monitutor_scenarios.scenario_id == scenario_id).update(hidden=False)
    return json.dumps({"scenarioId": scenario_id})

@auth.requires_membership('admin')
def view_scenario():
    """Displays an overview over the scenario, its attached data and the associated milestones."""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        redirect(URL('manage_scenarios', 'view_scenarios'))
    scenario_data_query = (db.monitutor_scenarios.scenario_id == scenario_id)
    scenario = db.monitutor_scenarios[scenario_id]
    data = db((db.monitutor_data.data_id == db.monitutor_scenario_data.data_id) &
              (db.monitutor_scenario_data.scenario_id == scenario_id)).select()
    milestones = db(db.monitutor_milestones.scenario_id == scenario_id).select(
                    orderby=db.monitutor_milestones.order)
    return dict(scenario=scenario, data=data, milestones=milestones)

@auth.requires_membership('admin')
def view_milestone():
    """Overview over a given milestone, displaying associated checks and milestone information."""
    if len(request.args) == 1:
        milestone_id = request.args(0, cast=int)
    else:
        redirect(URL('manage_scenarios', 'view_scenarios'))
    milestone = db.monitutor_milestones[milestone_id]
    scenario = db.monitutor_scenarios[milestone.scenario_id]
    checks = __db_get_checks(milestone_id = milestone_id)
    check_details = dict()
    for check in checks:
        check_details[check.check_id] = __db_get_check(check.check_id)
    return dict(milestone=milestone,
                checks=checks,
                check_details=check_details,
                scenario_id=scenario.scenario_id,
                milestone_id=milestone_id,
                scenario=scenario)

@auth.requires_membership('admin')
def add_check():
    """Adds a check to a given milestone"""
    if len(request.args):
        milestone_id = request.args(0, cast=int)
    else:
        redirect(URL('default', 'index'))
        milestone_id = None
    add_check_form = SQLFORM(db.monitutor_checks)
    add_check_form.vars.milestone_id = milestone_id
    if add_check_form.accepts(request, session):
        response.flash = "Form accepted. Added check"
    add_check_form.vars.order = 0
    add_check_form.vars.uuid = str(uuid.uuid4())
    return dict(form=add_check_form)

@auth.requires_membership('admin')
def edit_milestone_form():
    """Displays a form to edit a given milestone"""
    if len(request.args):
        milestone_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        milestone_id = None
    milestone_form = SQLFORM(db.monitutor_milestones,
                   db.monitutor_milestones(milestone_id))
    if milestone_form.accepts(request, session):
        response.flash = "Form accepted"
    return dict(milestone_form=milestone_form)

@auth.requires_membership('admin')
def remove_check():
    """Deletes the reference between the check and the milestone"""
    check_id = request.args(0, cast=int)
    milestone_id = db.monitutor_checks[check_id].milestone_id
    del db.monitutor_checks[check_id]
    redirect(URL('manage_scenarios', 'view_milestone.html', args=[milestone_id]))

@auth.requires_membership('admin')
def hide_check():
    """Hides a check so it is only visible to administrators"""
    milestone_id = request.args(0, cast=int)
    check_milestone_id = request.args(1, cast=int)
    invis = request.args(2, cast=int)
    scenario_id = request.args(3, cast=int)
    db.monitutor_check_milestone[check_milestone_id] = dict(flag_invis=invis)

    if scenario_id:
        redirect(URL('manage_scenarios', 'view_milestone.html', args=[milestone_id, scenario_id]))


@auth.requires_membership('admin')
def lower_check():
    """Lowers the check prio to change the order of checks within a milestone"""
    milestone_id = request.args(0, cast=int)
    check_milestone_id = request.args(1, cast=int)
    lower = request.args(2, cast=int)
    scenario_id = request.args(3, cast=int)

    row = db.monitutor_check_milestone[check_milestone_id]
    sequence = row.sequence_nr
    if lower == 1:
        db.monitutor_check_milestone[check_milestone_id] = dict(sequence_nr=sequence-1)
    else:
        db.monitutor_check_milestone[check_milestone_id] = dict(sequence_nr=sequence+1)

    if scenario_id:
        redirect(URL('manage_scenarios', 'view_milestone.html', args=[milestone_id, scenario_id]))


@auth.requires_membership('admin')
def remove_milestone():
    """Removes the reference between a given scenario and a milestone"""
    milestone_scenario_id = request.args(0, cast=int)
    scenario_id = request.args(1, cast=int)
    del db.monitutor_milestone_scenario[milestone_scenario_id]
    if scenario_id:
        redirect(URL('manage_scenarios', 'view_scenario.html', args=[scenario_id]))


@auth.requires_membership('admin')
def hide_milestone():
    """Hides a milestone so it can only be seen by an administrator"""
    milestone_id = request.args(0, cast=int)
    hidden = request.args(1, cast=int)
    db.monitutor_milestones[milestone_id] = dict(hidden=hidden)
    if scenario_id:
        redirect(URL('manage_scenarios', 'view_scenario.html',
                     args=[db.monitutor_milestones[milestone_id].scenario_id]))

@auth.requires_membership('admin')
def lower_milestone():
    """Lowers the milestone milestone prio to change order"""
    milestone_id = request.args(0, cast=int)
    lower = request.args(1, cast=int)
    scenario_id = db.monitutor_milestones[milestone_id].scenario_id

    milestone = db.monitutor_milestones[milestone_id]
    order = milestone.order
    if lower == 1:
        db.monitutor_milestones[milestone_id] = dict(order=order-1)
    else:
        db.monitutor_milestones[milestone_id] = dict(order=order+1)
    if scenario_id:
        redirect(URL('manage_scenario', 'view_scenario.html', args=[scenario_id]))

@auth.requires_membership('admin')
def delete_milestone():
    milestone_id = request.vars.milestoneId
    milestonerefs = db(db.monitutor_check_milestone.milestone_id == milestone_id)
    milestone = db(db.monitutor_milestones.milestone_id == milestone_id)
    milestonerefs.delete()
    milestone.delete()
    return json.dumps({milestone_id: True})

@auth.requires_membership('admin')
def delete_check():
    check_id = request.vars.checkId
    check = db(db.monitutor_checks.check_id == check_id)
    targets = db(db.monitutor_targets.check_id == check_id)
    targets.delete()
    check.delete()
    return json.dumps({check_id: True})

@auth.requires_membership('admin')
def add_milestone():
    """Displays form to add milestone to a given scenario"""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        scenario_id = None
    new_milestone_form = SQLFORM(db.monitutor_milestones)
    if new_milestone_form.accepts(request, session):
        session.flash = 'Milestone inserted.'
    new_milestone_form.vars.order = 0
    new_milestone_form.vars.uuid = str(uuid.uuid4())
    new_milestone_form.vars.scenario_id = scenario_id
    return dict(new_milestone_form=new_milestone_form)

@auth.requires_membership('admin')
def edit_check():
    """Displays forms to show and alter all information of a given check"""
    if len(request.args):
        check_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
    check = db.monitutor_checks[check_id]
    milestone_id = check.milestone_id
    scenario_id = db.monitutor_milestones[milestone_id].scenario_id
    attachment_form = SQLFORM(db.monitutor_attachments,
        showid=False,
        formstyle="divs",
        fields=["name", "producer","filter", "requires_status"])
    attachment_form.vars.check_id = check_id
    form = SQLFORM(db.monitutor_checks,
                   check_id,
                   showid=False,
                   formstyle="divs",
                   fields=["name", "display_name", "program_id","params", "hint", "source_id", "dest_id"])
    form.vars.milestone_id = milestone_id
    if form.accepts(request, session):
        __db_get_check(check_id, reset_cache=True)
        response.flash = 'form accepted'
    if attachment_form.accepts(request, session):
        response.flash = 'form accepted'
        __db_get_attachments(check_id, reset_cache=True)
    return dict(form=form, attachment_form=attachment_form, checkid=check_id, milestone_id=milestone_id, scenario_id=scenario_id)

@auth.requires_membership('admin')
def view_attachment():
    """Displays all information of a target"""
    if len(request.args):
        check_id = request.args(0, cast=int)
    else:
        check_id = None
    attachments = db((db.monitutor_checks.check_id == db.monitutor_attachments.check_id) &
                          (db.monitutor_checks.check_id == check_id)).select()
    return dict(attachments=attachments)

@auth.requires_membership('admin')
def edit_attachment():
    if len(request.args):
        attachment_id = request.args(0, cast=int)
    else:
        attachment_id = None
    form = SQLFORM(db.monitutor_attachments,
        attachment_id,
        showid=False,
        formstyle="divs",
        fields=["name", "producer","filter", "requires_status"])
    if form.accepts(request, session):
        response.flash = 'form accepted'
        __db_get_attachments(db.monitutor_attachments[attachment_id].check_id, reset_cache=True)
    return dict(form=form)

@auth.requires_membership("admin")
def delete_attachment():
    """Removes a system from a check by deleting the target"""
    attachment_id = request.vars.attachmentId
    check_id = db.monitutor_attachments[attachment_id].check_id
    db(db.monitutor_attachments.attachment_id == attachment_id).delete()
    __db_get_attachments(check_id, reset_cache=True)
    return json.dumps(dict(attachment_id=attachment_id))

@auth.requires_membership("admin")
def delete_scenario():
    """Deletes a given Scenario and all its references"""
    scenario_id = request.vars.scenarioId
    db(db.monitutor_scenarios.scenario_id == scenario_id).delete()
    return json.dumps(dict(scenario_id=scenario_id))

@auth.requires_membership("admin")
def get_scenario():
    """Returns a json dict that exports a given scenario"""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        scenario_id = 0
        redirect(URL("default","index"))
    scenario_table = db.monitutor_scenarios[scenario_id]
    programs = set()
    systems = set()
    export = {"programs": [], "scenarios": [], "systems": []}

    scenario = dict()
    scenario["name"] = scenario_table.name
    scenario["uuid"] = scenario_table.uuid
    if scenario_table.uuid == "":
        scenario["uuid"] = str(uuid.uuid4())
    scenario["description"] = scenario_table.description
    scenario["goal"] = scenario_table.goal
    scenario["hidden"] = True
    scenario["milestones"] = []
    milestones_table = db(db.monitutor_milestones.scenario_id == scenario_id).select()
    for milestone_row in milestones_table:
        milestone = dict()
        milestone["hidden"] = milestone_row.hidden
        milestone["order"] = milestone_row.order
        milestone["name"] = milestone_row.name
        milestone["uuid"] = milestone_row.uuid
        milestone["description"] = milestone_row.description
        milestone["checks"] = []
        checks_table = db(db.monitutor_checks.milestone_id == milestone_row.milestone_id).select()
        for check_row in checks_table:
            check = dict()
            check["hidden"] = check_row.hidden
            check["order"] = check_row.order
            check["name"] = check_row.name
            check["uuid"] = check_row.uuid
            check["display_name"] = check_row.display_name
            check["params"] = check_row.params
            check["hint"] = check_row.hint
            check["source"] = db.monitutor_systems[check_row.source_id].name
            systems.add(check["source"])
            check["dest"] = db.monitutor_systems[check_row.dest_id].name
            systems.add(check["dest"])
            check["program"] = db.monitutor_programs[check_row.program_id].name
            programs.add(check["program"])
            check["attachments"] = []
            attachment_table = db(db.monitutor_attachments.check_id == check_row.check_id).select()
            for attachment_row in attachment_table:
                attachment = dict()
                attachment["name"] = attachment_row.name
                attachment["uuid"] = attachment_row.uuid
                attachment["filter"] = attachment_row.filter
                attachment["producer"] = attachment_row.producer
                attachment["requires_status"] = attachment_row.requires_status
                check["attachments"].append(attachment)
            milestone["checks"].append(check)
        scenario["milestones"].append(milestone)
    export["scenarios"].append(scenario)
    for system_name in systems:
        system_row = db(db.monitutor_systems.name == system_name).select().first()
        system = dict()
        system["name"] = system_name
        system["display_name"] = system_row.display_name
        system["description"] = system_row.description
        system["uuid"] = system_row.uuid
        system["customvars"] = []
        for customvar_row in db(db.monitutor_customvars.system_id == system_row.system_id).select():
            customvar = dict()
            customvar["name"] = customvar_row.name
            customvar["uuid"] = customvar_row.uuid
            customvar["display_name"] = customvar_row.display_name
            customvar["value"] = customvar_row.value
            system["customvars"].append(customvar)
        export["systems"].append(system)
    for program_name in programs:
        program_row = db(db.monitutor_programs.name == program_name).select().first()
        program = dict()
        program["name"] = program_name
        program["display_name"] = program_row.display_name
        program["code"] = program_row.code
        program["uuid"] = program_row.uuid
        program["interpreter_path"] = db.monitutor_interpreters[program_row.interpreter_id].path
        program["interpreter_name"] = db.monitutor_interpreters[program_row.interpreter_id].name
        export["programs"].append(program)
    return json.dumps(export)

@auth.requires_membership("admin")
def upload_scenario():
    form2 = FORM( INPUT(_type="file", _name="scenariofile",
                        _form="form2", requires=IS_NOT_EMPTY(error_message='Select a .json file')),
                  INPUT(_type="submit", _form="form2"), _id="form2")
    if form2.accepts(request, session):
        data = json.loads(form2.vars.scenariofile.value)

        program_ids = dict()
        for program in data["programs"]:
            interpreter = db(db.monitutor_interpreters.name == program["interpreter_name"]).select()
            if len(interpreter):
                interpreter_id = interpreter.first().interpreter_id
            else:
                interpreter_id = db.monitutor_interpreters.insert(
                    name=program["interpreter_name"],
                    path= program["interpreter_path"])
            existing_program = db(db.monitutor_programs.name == program["name"]).select()
            if(len(existing_program)):
                existing_program = existing_program.first()
                existing_program.name = program["name"]
                existing_program.display_name = program["display_name"]
                existing_program.code = program["code"]
                existing_program.interpreter_id = interpreter_id
                existing_program.update_record()
                program_ids[existing_program.name] = existing_program.program_id
            else:
                program_id = db.monitutor_programs.insert(
                    name=program["name"],
                    display_name = program["display_name"],
                    code = program["code"],
                    interpreter_id = interpreter_id
                    )
                program_ids[program["name"]] = program_id

        system_ids = dict()
        for system in data["systems"]:
            existing_system = db(db.monitutor_systems.name == system["name"]).select()
            if(len(existing_system)):
                existing_system = existing_system.first()
                existing_system.display_name = system["display_name"]
                existing_system.description = system["description"]
                existing_system.update_record()
                system_id = existing_system.system_id
                system_ids[system["name"]] = system_id
            else:
                system_id = db.monitutor_systems.insert(
                    name=system["name"],
                    description = system["description"],
                    display_name = system["display_name"]
                    )
                system_ids[system["name"]] = system_id

            for customvar in system["customvars"]:
                existing_customvars=db(db.monitutor_customvars.uuid==customvar["uuid"]).select()
                if len(existing_customvars):
                    existing_customvars = existing_customvars.first()
                    existing_customvars.name = customvar["name"]
                    existing_customvars.display_name = customvar["display_name"]
                    existing_customvars.value = customvar["value"]
                    existing_customvars.update_record()
                else:
                    db.monitutor_customvars.insert(
                        name = customvar["name"],
                        display_name = customvar["display_name"],
                        value = customvar["value"],
                        system_id = system_id,
                        uuid = customvar["uuid"])

        for scenario in data["scenarios"]:
            existing_scenario = db(db.monitutor_scenarios.uuid == scenario["uuid"]).select()
            if(len(existing_scenario)):
                existing_scenario = existing_scenario.first()
                existing_scenario.name = scenario["name"]
                existing_scenario.goal = scenario["goal"]
                existing_scenario.description = scenario["description"]
                existing_scenario.hidden = True
                existing_scenario.update_record()
                scenario_id = existing_scenario.scenario_id
            else:
                scenario_id = db.monitutor_scenarios.insert(name=scenario["name"],
                    goal=scenario["goal"],
                    description=scenario["description"],
                    uuid=scenario["uuid"],
                    hidden=True)
            for milestone in scenario["milestones"]:
                existing_milestone = db(db.monitutor_milestones.uuid == milestone["uuid"]).select()
                if(len(existing_milestone)):
                    existing_milestone = existing_milestone.first()
                    existing_milestone.name = milestone["name"]
                    existing_milestone.description = milestone["description"]
                    existing_milestone.order = milestone["order"]
                    existing_milestone.hidden = milestone["hidden"]
                    existing_milestone.update_record()
                    milestone_id = existing_milestone.milestone_id
                else:
                    milestone_id = db.monitutor_milestones.insert(
                        name=milestone["name"],
                        description = milestone["description"],
                        order = milestone["order"],
                        hidden = milestone["hidden"],
                        uuid = milestone["uuid"],
                        scenario_id = scenario_id
                        )
                for check in milestone["checks"]:
                    program_id = program_ids[check["program"]]
                    source_id = system_ids[check["source"]]
                    dest_id = system_ids[check["dest"]]
                    existing_check = db(db.monitutor_checks.uuid == check["uuid"]).select()
                    if len(existing_check):
                        existing_check = existing_check.first()
                        existing_check.name = check["name"]
                        existing_check.display_name = check["display_name"]
                        existing_check.hint = check["hint"]
                        existing_check.hidden = check["hidden"]
                        existing_check.order = check["order"]
                        existing_check.params = check["params"]
                        existing_check.program_id = program_id
                        existing_check.source_id = source_id
                        existing_check.dest_id = dest_id
                        existing_check.update_record()
                        check_id = existing_check.check_id
                    else:
                        check_id = db.monitutor_checks.insert(
                            name = check["name"],
                            display_name = check["display_name"],
                            hint = check["hint"],
                            params = check["params"],
                            program_id = program_id,
                            dest_id = dest_id,
                            source_id = source_id,
                            hidden = check["hidden"],
                            order = check["order"],
                            milestone_id = milestone_id,
                            uuid = check["uuid"])
                    for attachment in check["attachments"]:
                        existing_attachment = db(db.monitutor_attachments.uuid == attachment["uuid"]).select()
                        if len(existing_attachment):
                            existing_attachment = existing_attachment.first()
                            existing_attachment.name = attachment["name"]
                            existing_attachment.producer = attachment["producer"]
                            existing_attachment.filter = attachment["filter"]
                            existing_attachment.requires_status = attachment["requires_status"]
                        else:
                             db.monitutor_attachments.insert(
                                name = attachment["name"],
                                producer = attachment["producer"],
                                filter = attachment["filter"],
                                requires_status = attachment["requires_status"],
                                uuid = attachment["uuid"],
                                check_id = check_id)
        redirect(URL('manage_scenarios',"view_scenarios"))
    return dict(form2=form2)
