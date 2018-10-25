import json

@auth.requires_membership('admin')
def view_scenarios():
    """Displays all Scenarios and global scenario information"""
    scenarios = db(db.monitutor_scenarios).select()
    new_scenario_form = SQLFORM(db.monitutor_scenarios)
    new_scenario_form.vars.hidden = True
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
    scenario = db(scenario_data_query).select(
        db.monitutor_scenarios.ALL,
        db.monitutor_scenario_data.ALL,
        left = db.monitutor_scenario_data.on(
            db.monitutor_scenarios.scenario_id == db.monitutor_scenario_data.scenario_id))
    data = db((db.monitutor_data.data_id == db.monitutor_scenario_data.data_id) &
              (db.monitutor_scenario_data.scenario_id == scenario_id)).select()
    milestones = db((db.monitutor_milestones.scenario_id == scenario_id).select(
        orderby=db.monitutor_milestone_scenario.sequence_nr)
    return dict(scenario=scenario, data=data, milestones=milestones)

@auth.requires_membership('admin')
def view_milestone():
    """Overview over a given milestone, displaying associated checks and milestone information."""
    if len(request.args) > 1:
        milestone_id = request.args(0, cast=int)
        scenario_id = request.args(1, cast=int)
    else:
        redirect(URL('manage_scenarios', 'view_scenarios'))
    scenario = db.monitutor_scenarios[scenario_id]
    milestone = db.monitutor_milestones[milestone_id]
    checks = __db_get_checks(milestone_id = milestone_id)
    return dict(milestone=milestone,
                checks=checks,
                scenarioid=scenario_id,
                milestoneid=milestone_id,
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
    add_check_form.vars.hidden = False
    if add_check_form.accepts(request, session):
        response.flash = "Form accepted. Added check "+form.vars.diplay_name+"."
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
    if check_form.validates(request, session):
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
    current_milestone = db.monitutor_milestones[milestone_id]
    form = FORM(
        DIV(
            SPAN( XML('<b>Name</b>'), _class="input-group-addon", _id="basic-addon"),
            INPUT(_name="name",
                  _class="form-control",
                  requires=IS_NOT_EMPTY(),
                  _value=current_milestone.name),
            _class="input-group"), BR(),
        DIV(
            SPAN(XML('<b>Display Name</b>'), _class="input-group-addon", _id="basic-addon"),
            INPUT(_name="display_name",
                  _class="form-control",
                  requires=IS_NOT_EMPTY(),
                  _value=current_milestone.display_name),
            _class="input-group"), BR(),
        XML('<b>Description:</b>'), BR(),
        DIV(
            SPAN( XML(''),
            _class="input-group-addon", _id="basic-addon"),
            TEXTAREA(current_milestone.description,
                     _name="description",
                     _class="form-control"
                     ),
            _class="input-group"), BR(),
        INPUT(_type='submit'),
        _id="form"
    )
    if form.accepts(request, session):
        response.flash = "form accepted"
        db(db.monitutor_milestones.milestone_id == milestone_id).validate_and_update(name=form.vars.name,
                                            display_name=form.vars.display_name,
                                            description=form.vars.description)

    return dict(addscenario_form=form)


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
    milestone_scenario_id = request.args(0, cast=int)
    invis = request.args(1, cast=int)
    scenario_id = request.args(2, cast=int)
    db.monitutor_milestone_scenario[milestone_scenario_id] = dict(hidden=invis)
    if scenario_id:
        redirect(URL('manage_scenario', 'view_scenario.html', args=[scenario_id]))


@auth.requires_membership('admin')
def lower_milestone():
    """Lowers the milestone milestone prio to change order"""
    milestone_scenario_id = request.args(0, cast=int)
    lower = request.args(1, cast=int)
    scenario_id = request.args(2, cast=int)

    row = db.monitutor_milestone_scenario[milestone_scenario_id]
    sequence = row.sequence_nr
    if lower == 1:
        db.monitutor_milestone_scenario[milestone_scenario_id] = dict(sequence_nr=sequence-1)
    else:
        db.monitutor_milestone_scenario[milestone_scenario_id] = dict(sequence_nr=sequence+1)
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
        redirect(URL('default','index'))

    scenario_milestone = db((db.monitutor_milestone_scenario.milestone_id ==
                                  db.monitutor_milestones.milestone_id) &
                                 (db.monitutor_milestone_scenario.scenario_id == scenario_id)).select()

    options = OPTION("No dependency", _value=None, _selected="selected")
    for row in scenario_milestone:
        options += OPTION(XML(row.monitutor_milestones.display_name),
                          _value=row.monitutor_milestone_scenario.milestone_scenario_id)
    form = FORM(
        DIV(
          SPAN( XML('<b>Name</b>'), _class="input-group-addon", _id="basic-addon"),
          INPUT( _name="name", _class="form-control", requires=IS_NOT_EMPTY()), _class="input-group" ),BR(),
        DIV(
          SPAN( XML('<b>Display Name</b>'), _class="input-group-addon", _id="basic-addon"),
          INPUT( _name="display_name", _class="form-control", requires=IS_NOT_EMPTY()),  _class="input-group"),BR(),
        XML('<b>Description:</b>'),BR(),
        DIV(
          SPAN( XML(''), _class="input-group-addon", _id="basic-addon"),
          TEXTAREA(_name="description", _form='form',  _class="form-control"), _class="input-group"),BR(),
        INPUT(_type='submit'),
        _id="form"
    )

    if form.accepts(request, session):
        response.flash = "form accepted"
        newid = db.monitutor_milestones.insert(name=form.vars.name,
                                            display_name=form.vars.display_name,
                                            description=form.vars.description)
        if scenario_id is not None:
            if form.vars.dependency is None:
                db.monitutor_milestone_scenario.insert(milestone_id=long(newid),
                                                        scenario_id=long(scenario_id),
                                                        sequence_nr=int(0))
            else:
                db.monitutor_milestone_scenario.insert(milestone_id=long(newid),
                                                        scenario_id=long(scenario_id),
                                                        sequence_nr=int(0),
                                                        dependency=form.vars.dependency)
    return dict(addscenario_form=form)


@auth.requires_membership('admin')
def add_milestone_ref():
    """Adds an existing Milestone to the scenario by adding a reference"""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        scenario_id = None
    milestones = db(db.monitutor_milestones).select()
    input_list = DIV()
    for milestone in milestones:
        input_field = DIV(
                DIV(
                    SPAN(
                            INPUT(_type='radio', _name="add", _value=milestone.milestone_id)
                    , _class="input-group-addon"),
                    DIV(
                        str(milestone.display_name[:33])
                        , _class="form-control")
                , _class="input-group")
            , _class="col-lg-4", _style="margin-bottom: 5px")
        input_list += input_field
    form = FORM(
        FIELDSET(
            input_list
        ), BR(),
        INPUT(_type='submit'),
        _action="#"
    )
    if form.accepts(request, session):
        response.flash = 'form accepted'
        db.monitutor_milestone_scenario.insert(milestone_id=form.vars.add,
                                    scenario_id=scenario_id,
                                    hidden=False,
                                    sequence_nr=0)
    return dict(form=form)


@auth.requires_membership('admin')
def edit_check():
    """Displays forms to show and alter all information of a given check"""
    if len(request.args):
        check_id = request.args(0, cast=int)
        if len(request.args) > 2:
            scenario_id = request.args(1, cast=int)
            milestone_id = request.args(2, cast=int)
        else:
            scenario_id = None
            milestone_id = None
    else:
        redirect(URL('default','index'))
        check_id = None
        scenario_id = None
        milestone_id = None

    attachment_form = SQLFORM(db.monitutor_attachments,
        showid=False,
        formstyle="divs",
        fields=["name", "producer","filter", "requires_status"])
    attachment_form.vars.check_id = check_id
    form = SQLFORM(db.monitutor_checks,
                   check_id,
                   showid=False,
                   formstyle="divs",
                   fields=["name", "display_name", "program_id","params", "hint"])
    if form.accepts(request, session):
        db(db.monitutor_checks.check_id == check_id).select(cache=(cache.ram, -1))
        response.flash = 'form accepted'
    if attachment_form.accepts(request, session):
        response.flash = 'form accepted'
        db(db.monitutor_attachments.check_id == check_id).select(cache=(cache.ram, -1))
    return dict(form=form, attachment_form=attachment_form, checkid=check_id, milestone_id=milestone_id, scenario_id=scenario_id)


@auth.requires_membership('admin')
def add_target():
    """Displays information and a form to alter a checks target references"""
    if len(request.args):
        check_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        check_id = None
    targets = db((db.monitutor_checks.check_id == db.monitutor_targets.check_id) &
                      (db.monitutor_targets.check_id == check_id) &
                      (db.monitutor_targets.type_id == db.monitutor_types.type_id) &
                      (db.monitutor_targets.system_id == db.monitutor_systems.system_id)).select()
    check = db(db.monitutor_checks.check_id == check_id).select()
    type_options = OPTION(" ")
    types = db(db.monitutor_types).select()
    for type in types:
        type_options += OPTION(XML(type.display_name),
                          _value=type.type_id)
    sys_option = OPTION(" ")
    syss = db(db.monitutor_systems).select()
    for sys in syss:
        sys_option += OPTION(XML(sys.display_name),
                          _value=sys.system_id)
    new_target = FORM(
        DIV(
            XML('<b>System:</b>'),
            SELECT((sys_option), _name="system", _form="newtarget", _class="form-control", requires=IS_NOT_EMPTY()), _class="input_group"), BR(),
        DIV(
            XML('<b>Type:</b>'),
            SELECT((type_options), _name="type", _form="newtarget", _class="form-control", requires=IS_NOT_EMPTY()), _class="input_group"), BR(),
        INPUT(_type='submit'),
        _id="newtarget"
    )
    if new_target.accepts(request, session):
        validate_db = db((db.monitutor_targets.check_id == check_id) &
                              (db.monitutor_targets.system_id == new_target.vars.system) &
                              (db.monitutor_targets.type_id == new_target.vars.type)
                              ).select()
        if len(validate_db):
            response.flash = "duplicate entry!"
        else:
            db.monitutor_targets.insert(
                                    check_id=check_id,
                                    system_id=new_target.vars.system,
                                    type_id=new_target.vars.type,
                                    )
            response.flash = "Entry inserted!"
            redirect(URL(args=check_id))
    return dict(targets=targets, check=check, newtarget=new_target)


@auth.requires_membership('admin')
def view_target():
    """Displays all information of a target"""
    if len(request.args):
        check_id = request.args(0, cast=int)
    else:
        check_id = None
    targets = db((db.monitutor_checks.check_id == db.monitutor_targets.check_id) &
                      (db.monitutor_targets.check_id == check_id) &
                      (db.monitutor_targets.type_id == db.monitutor_types.type_id) &
                      (db.monitutor_targets.system_id == db.monitutor_systems.system_id)).select()
    return dict(targets=targets)


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
    return dict(form=form)

@auth.requires_membership("admin")
def delete_attachment():
    """Removes a system from a check by deleting the target"""
    attachment_id = request.vars.attachmentId
    db(db.monitutor_attachments.attachment_id == attachment_id).delete()
    return json.dumps(dict(attachment_id=attachment_id))

@auth.requires_membership("admin")
def delete_target():
    """Removes a system from a check by deleting the target"""
    target_id = request.vars.targetId
    db(db.monitutor_targets.target_id == target_id).delete()
    return json.dumps(dict(target_id=target_id))


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
        scenario = json.loads(form2.vars.scenariofile.value)
        existing_scenario = db(db.monitutor_scenarios.uuid == scenario["uuid"]).select()
        if(len(existing_scenario)):
            existing_scenario = existing_scenario.first()
            existing_scenario.name = scenario["name"]
            existing_scenario.display_name = scenario["display_name"]
            existing_scenario.goal = scenario["goal"]
            existing_scenario.description = scenario["description"]
            existing_scenario.hidden = True
            existing_scenario.update_record()
            scenario_id = existing_scenario.scenario_id
        else:
            scenario_id = db.monitutor_scenarios.insert(name=scenario["name"],
                                                      display_name=scenario["display_name"],
                                                      goal=scenario["goal"],
                                                      description=scenario["description"],
                                                      uuid=scenario["uuid"],
                                                      hidden=True)
        for milestone_ref in scenario["milestone_refs"]:
            milestone = milestone_ref["milestone"]
            existing_milestone = db(db.monitutor_milestones.uuid == milestone["uuid"]).select()
            if(len(existing_milestone)):
                existing_milestone = existing_milestone.first()
                existing_milestone.name = milestone["name"]
                existing_milestone.description = milestone["description"]
                existing_milestone.display_name = milestone["display_name"]
                existing_milestone.update_record()
                milestone_id = existing_milestone.milestone_id
            else:
                milestone_id = db.monitutor_milestones.insert(name=milestone["name"],
                                                                   description = milestone["description"],
                                                                   display_name = milestone["display_name"],
                                                                   uuid = milestone["uuid"])
            if len(db((db.monitutor_milestone_scenario.milestone_id == milestone_id)&
                           (db.monitutor_milestone_scenario.scenario_id == scenario_id)).select()) < 1:
                db.monitutor_milestone_scenario.insert(milestone_id=milestone_id,
                                                            scenario_id=scenario_id,
                                                            sequence_nr=milestone_ref["sequence_nr"],
                                                            dependency=milestone_ref["dependency"],
                                                            hidden=milestone_ref["hidden"])
            for check_ref in milestone["check_refs"]:
                check = check_ref["check"]
                program = check["program"]
                interpreter = program["interpreter"]
                db.monitutor_interpreters.update_or_insert(name=interpreter["name"],
                                               display_name=interpreter["display_name"],
                                               path=interpreter["path"])
                interpreter_id = db.monitutor_interpreters(name=interpreter["name"]).interpreter_id
                existing_program = db(db.monitutor_programs.uuid == program["uuid"]).select()
                if(len(existing_program)):
                    existing_program = existing_program.first()
                    existing_program.code = program["code"]
                    existing_program.display_name = program["display_name"]
                    existing_program.interpreter_id = interpreter_id
                    existing_program.name = program["name"]
                    existing_program.update_record()
                    program_id = existing_program.program_id
                else:
                    program_id = db.monitutor_programs.insert(name = program["name"],
                                                                   display_name = program["display_name"],
                                                                   code = program["code"],
                                                                   interpreter_id = interpreter_id,
                                                                   uuid = program["uuid"])
                existing_check = db(db.monitutor_checks.uuid == check["uuid"]).select()
                if len(existing_check):
                    existing_check = existing_check.first()
                    existing_check.name = check["name"]
                    existing_check.display_name = check["display_name"]
                    existing_check.hint = check["hint"]
                    existing_check.params = check["params"]
                    existing_check.program_id = program_id
                    existing_check.update_record()
                    check_id = existing_check.check_id
                else:
                    check_id = db.monitutor_checks.insert(name = check["name"],
                                                               display_name = check["display_name"],
                                                               hint = check["hint"],
                                                               params = check["params"],
                                                               program_id = program_id,
                                                               uuid = check["uuid"])
                for target in check["targets"]:
                    system = target["system"]
                    type_var = target["type"]
                    existing_system = db(db.monitutor_systems.uuid == system["uuid"]).select()
                    if len(existing_system):
                        existing_system = existing_system.first()
                        existing_system.name = system["name"]
                        existing_system.display_name = system["display_name"]
                        existing_system.hostname = system["hostname"]
                        existing_system.description = system["description"]
                        existing_system.update_record()
                        system_id = existing_system.system_id
                    else:
                        system_id = db.monitutor_systems.insert(name = system["name"],
                                                                      display_name = system["display_name"],
                                                                      hostname = system["hostname"],
                                                                      description = system["description"],
                                                                      uuid = system["uuid"])
                    db.monitutor_types.update_or_insert(name=type_var["name"],
                                                             display_name=type_var["display_name"])
                    type_id = db(db.monitutor_types.name ==
                            type_var["name"]).select().first().type_id
                    if len(db((db.monitutor_targets.type_id == type_id) &
                                   (db.monitutor_targets.check_id == check_id) &
                                   (db.monitutor_targets.system_id == system_id)).select()) < 1:
                        db.monitutor_targets.insert(type_id = type_id,
                                                         system_id = system_id,
                                                         check_id = check_id)
                    for customvar in system["customvars"]:
                        existing_customvars=db(db.monitutor_customvar_system.uuid==customvar["uuid"]).select()
                        if len(existing_customvars):
                            existing_customvars = existing_customvars.first()
                            existing_customvars.name = customvar["name"]
                            existing_customvars.display_name = customvar["display_name"]
                            existing_customvars.value = customvar["value"]
                            existing_customvars.system_id = system_id
                            existing_customvars.update_record()
                        else:
                            db.monitutor_customvar_system.insert(name = customvar["name"],
                                                                      display_name = customvar["display_name"],
                                                                      value = customvar["value"],
                                                                      system_id = system_id,
                                                                      uuid = customvar["uuid"])
                    if len(db((db.monitutor_targets.system_id == system_id)&
                           (db.monitutor_targets.check_id == check_id)&
                           (db.monitutor_targets.type_id ==
                               type_id)).select())<1:
                        db.monitutor_targets.insert(system_id = system_id,
                                                         check_id = check_id,
                                                         type_id = type_id)
                if len(db((db.monitutor_check_milestone.milestone_id == milestone_id) &
                               (db.monitutor_check_milestone.check_id == check_id)).select()) < 1:
                    db.monitutor_check_milestone.insert(check_id = check_id,
                                                             milestone_id = milestone_id,
                                                             flag_invis = check_ref["flag_invis"],
                                                             sequence_nr = check_ref["sequence_nr"])
        redirect(URL('manage_scenarios',"view_scenarios"))
    return dict(form2=form2)
