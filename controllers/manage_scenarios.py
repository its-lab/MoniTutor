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
def add_existing_check():
    """Allows associating an existing check to a new milestone."""
    if len(request.args):
        milestone_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
    check_form = SQLFORM.factory(
        Field('name',
              type='string',
              requires=[IS_ALPHANUMERIC(),
                        IS_NOT_IN_DB(db,"monitutor_checks.name")]),
        Field('check', 'reference monitutor_checks',
              requires=IS_IN_DB(db, db.monitutor_checks, '%(name)s')))
    if check_form.accepts(request, session):
        check = db.monitutor.checks[check_form.vars.check]
        db.monitutor_checks.insert(name=check_form.vars.name,
                                   milestone_id=milestone_id,
                                   display_name=check.display_name,
                                   params=check.params,
                                   program_id=check.program_id,
                                   source_id=check.source_id,
                                   dest_id=check.dest_id,
                                   hint=check.hint)
    return dict(form=check_form)


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
    milestone_id = request.args(0, cast=int)
    check_milestone_id = request.args(1, cast=int)
    scenario_id = request.args(2, cast=int)
    del db.monitutor_check_milestone[check_milestone_id]

    if scenario_id:
        redirect(URL('manage_scenarios', 'view_milestone.html', args=[milestone_id, scenario_id]))


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
    db(db.monitutor_milestone_scenario.scenario_id == scenario_id).delete()
    db(db.monitutor_scenario_data.scenario_id == scenario_id).delete()
    db(db.scenario_user.scenario_id == scenario_id).delete()
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
    scenario = {}
    scenario["name"] = scenario_table.name
    scenario["uuid"] = scenario_table.uuid
    scenario["display_name"] = scenario_table.display_name
    scenario["description"] = scenario_table.description
    scenario["goal"] = scenario_table.goal
    scenario["hidden"] = True
    milestone_refs = []
    milestone_ref_table = db(db.monitutor_milestone_scenario.scenario_id == scenario_id).select()
    for milestone_ref_row in milestone_ref_table:
        milestone_ref = dict()
        milestone_ref["hidden"] = milestone_ref_row.hidden
        milestone_ref["sequence_nr"] = milestone_ref_row.sequence_nr
        milestone_ref["dependency"] = milestone_ref_row.dependency
        milestone_row = db.monitutor_milestones[milestone_ref_row.milestone_id]
        milestone = dict()
        milestone["name"] = milestone_row.name
        milestone["uuid"] = milestone_row.uuid
        milestone["display_name"] = milestone_row.display_name
        milestone["description"] = milestone_row.description
        check_refs = []
        check_ref_table = db(db.monitutor_check_milestone.milestone_id == milestone_ref_row.milestone_id).select()
        for check_ref_row in check_ref_table:
            check_ref = dict()
            check_ref["flag_invis"] = check_ref_row.flag_invis
            check_ref["sequence_nr"] = check_ref_row.sequence_nr
            check_row = db.monitutor_checks[check_ref_row.check_id]
            check = dict()
            check["name"] = check_row.name
            check["uuid"] = check_row.uuid
            check["display_name"] = check_row.display_name
            check["params"] = check_row.params
            check["hint"] = check_row.hint
            targets = []
            target_table = db(db.monitutor_targets.check_id == check_row.check_id).select()
            for target_row in target_table:
                target = dict()
                type_row = db.monitutor_types[target_row.type_id]
                target["type"] = {"name": type_row.name, "display_name": type_row.display_name}
                system = dict()
                system_row = db.monitutor_systems[target_row.system_id]
                system["name"] = system_row.name
                system["uuid"] = system_row.uuid
                system["display_name"] = system_row.display_name
                system["hostname"] = system_row.hostname
                system["description"] = system_row.description
                customvars = []
                customvar_table = db(db.monitutor_customvar_system.system_id == system_row.system_id).select()
                for customvar_row in customvar_table:
                    customvar = {
                        "name": customvar_row.name,
                        "uuid": customvar_row.uuid,
                        "display_name": customvar_row.display_name,
                        "value": customvar_row.value,
                        }
                    customvars.append(customvar)
                system["customvars"] = customvars
                target["system"] = system
                targets.append(target)
            check["targets"] = targets
            program_row = db.monitutor_programs[check_row.program_id]
            program = dict()
            program["name"] = program_row.name
            program["uuid"] = program_row.uuid
            program["display_name"] = program_row.display_name
            program["code"] = program_row.code
            interpreter_row = db.monitutor_interpreters[program_row.interpreter_id]
            program["interpreter"] = {
                "name": interpreter_row.name,
                "display_name": interpreter_row.display_name,
                "path": interpreter_row.path
                }
            check["program"] = program
            check_ref["check"] = check
            check_refs.append(check_ref)
        milestone["check_refs"] = check_refs
        milestone_ref["milestone"] = milestone
        milestone_refs.append(milestone_ref)
    scenario["milestone_refs"] = milestone_refs
    return json.dumps(scenario)

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
                program_ids[existing_program.name] = existing_program_id
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
