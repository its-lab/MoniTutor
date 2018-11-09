from os import path
import json

@auth.requires_membership('admin')
def add_data():
    """Displays a form to upload Data"""
    add_data_form = SQLFORM(db.monitutor_data)
    if add_data_form.process().accepted:
        session.flash = 'Record inserted.'
        redirect(URL())
    return dict(add_data_form=add_data_form)

@auth.requires_membership('admin')
def view_data():
    """Displays available data"""
    available_data = db(db.monitutor_data).select()
    return dict(available_data=available_data)

@auth.requires_membership('admin')
def delete_data():
    data_id = request.vars.dataId
    db(db.monitutor_scenario_data.data_id == data_id).delete()
    db(db.monitutor_data.data_id == data_id).delete()
    return json.dumps(dict(data_id=data_id))

@auth.requires_membership('admin')
def attach_data():
    """Form, to add or remove data from or to a scenario"""
    if len(request.args):
        scenario_id = request.args(0, cast=int)
    else:
        redirect(URL(''))

    scenario_query = (db.monitutor_scenarios.scenario_id == scenario_id)
    scenario = db(scenario_query).select()

    available_data = db().select(
        db.monitutor_scenario_data.ALL, db.monitutor_data.ALL,
        left=db.monitutor_data.on(
            db.monitutor_data.data_id == db.monitutor_scenario_data.data_id)
    )
    assigned = db((db.monitutor_scenario_data.data_id == db.monitutor_data.data_id)
                        & (db.monitutor_scenario_data.scenario_id == scenario_id)).select(
                        db.monitutor_data.ALL, db.monitutor_scenario_data.ALL)

    inputlist = DIV()
    already_assigned = []
    for row in assigned:
        inputfield = DIV(
                DIV(
                    SPAN(
                            INPUT(_type='checkbox', _name="remove", _value=row.monitutor_scenario_data.scenario_data_id, _checked=True)
                    , _class="input-group-addon"),
                    DIV(
                        str(row.monitutor_data.name)
                        , _class="form-control")
                , _class="input-group")
            , _class="col-lg-4", _style="margin-bottom: 5px")
        inputlist += inputfield
        already_assigned.append(row.monitutor_data.data_id)

    for row in db(db.monitutor_data).select():
        if row.data_id not in already_assigned:
            inputfield=DIV(
                    DIV(
                        SPAN(
                            INPUT(_type='checkbox', _name="add",  _value=row.data_id,)
                        , _class="input-group-addon"),
                        DIV(
                            str(row.name)
                            , _class="form-control")
                    , _class="input-group")
                , _class="col-lg-4", _style="margin-bottom: 5px")
            inputlist += inputfield

    form = FORM(
        FIELDSET(
            inputlist
        ),BR(),BR(),
        INPUT( _type='submit'),
        _action="#"
    )
    ids_to_be_removed = None
    remove = []
    if form.accepts(request, session):
        response.flash = "form accepted"
        ids_to_be_removed = db((db.monitutor_scenario_data.scenario_data_id != None) & (db.monitutor_scenario_data.scenario_id == scenario_id) ).select(
        db.monitutor_scenario_data.ALL, db.monitutor_data.ALL,
        left=db.monitutor_scenario_data.on(
            db.monitutor_data.data_id == db.monitutor_scenario_data.data_id)
        )
        if form.vars.add is None:
            form.vars.add = []
        if form.vars.remove is None:
            form.vars.remove = []
        for row in ids_to_be_removed:
            if str(row.monitutor_scenario_data.scenario_data_id) not in form.vars.remove:
                # Delete relation
                del db.monitutor_scenario_data[row.monitutor_scenario_data.scenario_data_id]
        for newentry in form.vars.add:
            # Add relation
            db.monitutor_scenario_data.insert(scenario_id=scenario_id, data_id=long(newentry))
        redirect(URL(args=scenario_id))
    return dict(available_data=available_data, form=form, scenario=scenario, ids_to_be_removed=remove)


@auth.requires_membership('admin')
def view_components():
    """Displays an overview over all configured components and possible issues"""
    data = db(db.monitutor_data).select()
    interpreter = db(db.monitutor_interpreters).select()
    programs = db(db.monitutor_programs).select(orderby=db.monitutor_programs.id)
    unused_programs = db(db.monitutor_checks.check_id == None).select(
        db.monitutor_programs.ALL,
        db.monitutor_checks.ALL,
        left=db.monitutor_checks.on(db.monitutor_checks.program_id == db.monitutor_programs.program_id)
    )
    broken_files = {}
    for file in data:
        if not path.isfile("./applications/MoniTutor/uploads/" + file.data):
            broken_files[file.id] = file
    return dict(data=data, interpreter=interpreter, programs=programs, unused_programs=unused_programs, broken_files=broken_files)


@auth.requires_membership('admin')
def add_interp():
    """Form to add an interpreter"""
    form2=SQLFORM(db.monitutor_interpreters)
    if form2.process().accepted:
        session.flash = 'Record inserted.'
        redirect(URL())
    return dict(form2=form2)

@auth.requires_membership('admin')
def view_interp():
    """Displays all configured interpreters"""
    interpreters = db(db.monitutor_interpreters).select()
    return dict(interpreters=interpreters)

@auth.requires_membership('admin')
def view_systems():
    """Displays all configured Systems"""
    systems = db(db.monitutor_systems).select()
    system_customvars = {}
    for system in systems:
        customvars = db(db.monitutor_customvars.system_id == system.system_id).select()
        if len(customvars):
            var_list = []
            for customvar in customvars:
                var_list.append(customvar)
            system_customvars[str(system.id)] = var_list
    return dict(systems=systems, system_customvars=system_customvars)

@auth.requires_membership('admin')
def view_system():
    """Displays a specific  Systems"""
    if len(request.args):
        system_id = request.args(0, cast=int)
    else:
        redirect(URL('default','index'))
        system_id = None
    system = db.monitutor_systems[system_id]
    system_customvars = db(db.monitutor_customvars.system_id == system_id).select()
    return dict(system=system, system_customvars=system_customvars)

@auth.requires_membership("admin")
def edit_system():
    """From to edit the configuration of a given system"""
    if len(request.args):
        system_id = request.args(0, cast=int)
    else:
        redirect(URL(''))
        system_id = None
    system = db.monitutor_systems[system_id]
    form = SQLFORM(db.monitutor_systems, system, deletable=True)
    if form.accepts(request, session):
        response.flash = 'form accepted'
    return dict(form=form)

@auth.requires_membership("admin")
def edit_customvar():
    """Returns a form to edit a customvar"""
    if len(request.args):
        customvar_id = request.args(0, cast=int)
    else:
        customvar_id = None
    customvar = db.monitutor_customvars[customvar_id]
    form = SQLFORM(db.monitutor_customvars, customvar, deletable=True)
    if form.accepts(request, session):
        response.flash = 'form accepted'
    return dict(form=form)

@auth.requires_membership('admin')
def view_programs():
    """Displays all available programs"""
    programs = db(db.monitutor_programs).select(orderby=db.monitutor_programs.id)
    return dict(programs=programs)

@auth.requires_membership('admin')
def view_program():
    """Displays all information of a given program"""
    if len(request.args):
        program_id = request.args(0, cast=int)
    else:
        redirect(URL('index'))
        program_id = None
    program = db.monitutor_programs[program_id]
    form = FORM(
        XML('<b>Edit code:</b>'), BR(),
        DIV(
            SPAN( XML(''),
            _class="input-group-addon", _id="basic-addon"),
            TEXTAREA(program.code,
                     _name="code",
                     _class="form-control"
                     ),
            _class="input-group"), BR(),
        INPUT(_type='submit'),
        _id="form"
    )
    if form.accepts(request, session):
        response.flash = "form accepted"
        db(db.monitutor_programs.program_id == program_id).validate_and_update(
                code=form.vars.code
            )
        redirect(URL(args=[program_id]))
    return dict(program=program, form=form)


@auth.requires_membership('admin')
def add_program():
    """Adds a program to the program table"""
    form = SQLFORM(db.monitutor_programs)
    interpreters = db(db.monitutor_interpreters).select()
    if form.process().accepted:
        session.flash = 'Record inserted.'
        redirect(URL())
    elif form.errors:
        session.flash = 'There was an error.'
    return dict(form=form, interpreters=interpreters)


@auth.requires_membership('admin')
def add_system():
    """Form to add a system to the system table"""
    systems = db(db.monitutor_systems).select()
    form = SQLFORM(db.monitutor_systems)
    if form.accepts(request, session):
        response.flash = 'form accepted'
    return dict(systems=systems, form=form)


@auth.requires_membership("admin")
def add_customvar():
    """Form to add a custom variable to a System"""
    if len(request.args):
        system_id = request.args(0, cast=int)
    else:
        redirect(URL('default', 'index'))
        system_id = None
    customvar_form = SQLFORM(db.monitutor_customvars)
    customvar_form.vars.system_id = system_id
    if customvar_form.accepts(request, session):
        response.flash = 'form accepted'
    return dict(customvar_form=customvar_form)

@auth.requires_membership('admin')
def delete_system():
    system_id = request.vars.systemId
    db(db.monitutor_systems.system_id == system_id).delete()
    return json.dumps(dict(system_id=system_id))
