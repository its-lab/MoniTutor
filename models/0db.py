from gluon.contrib.appconfig import AppConfig
import uuid
app_conf = AppConfig(reload=True)
DATABASE_NAME = app_conf.take("monitutor_env.database_name")
DATABASE_USER = app_conf.take("monitutor_env.database_user")
DATABASE_PASSWORD = app_conf.take("monitutor_env.database_password")
DATABASE_HOST = app_conf.take("monitutor_env.database_host")
db = DAL("postgres://" + DATABASE_USER + ":" + DATABASE_PASSWORD + "@" + DATABASE_HOST + "/" + DATABASE_NAME)

from gluon.tools import Auth

auth = Auth(db)

auth.settings.extra_fields['auth_user']= [
        Field('hmac_secret', length=512, default=lambda:str(uuid.uuid4()).replace("-","")[:16]),
        Field('image', type='upload')
        ]

auth.define_tables(username=True)

if not db.auth_group[1]:
    db.auth_group.insert(role="admin")

db.define_table('monitutor_scenarios',
    Field('scenario_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True),
    Field('description', type='text', required=True),
    Field('goal', type='text'),
    Field('hidden', type='boolean', default=True))

db.define_table('monitutor_data',
    Field('data_id', type='id'),
    Field('data', type='upload', required=True),
    Field('description', type='text'),
    Field('name', type='string', required=True))

db.define_table('monitutor_scenario_data',
    Field('scenario_data_id', type='id'),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('data_id', 'reference monitutor_data', required=True,
          requires=IS_IN_DB(db, db.monitutor_data, '%(name)s')))

db.define_table('monitutor_milestones',
    Field('milestone_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True),
    Field('description', type='string'),
    Field('order', type='integer'),
    Field('hidden', type='boolean', default=False),
    Field('scenario_id', 'reference monitutor_scenarios', required=True,
          requires=IS_IN_DB(db, db.monitutor_scenarios, '%(name)s')))

db.define_table('monitutor_interpreters',
    Field('interpreter_id', type='id'),
    Field('name', type='string', required=True),
    Field('path', type='string', required=True))

db.define_table('monitutor_programs',
    Field('program_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('code', type='text', required=True, requires=IS_LENGTH(655360)),
    Field('interpreter_id', 'reference monitutor_interpreters', required=True,
          requires=IS_IN_DB(db, db.monitutor_interpreters, '%(name)s')))

db.define_table('monitutor_systems',
    Field('system_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='string'))

db.define_table('monitutor_checks',
    Field('check_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=[IS_ALPHANUMERIC(), IS_NOT_IN_DB(db,"monitutor_checks.name")]),
    Field('display_name', type='string', required=True),
    Field('params', type='string'),
    Field('hidden', type='boolean', default=False),
    Field('order', type='integer'),
    Field('program_id', 'reference monitutor_programs', required=True,
          requires=IS_IN_DB(db, db.monitutor_programs, '%(name)s')),
    Field('source_id', 'reference monitutor_systems', required=True,
          requires=IS_IN_DB(db, db.monitutor_systems, '%(name)s')),
    Field('dest_id', 'reference monitutor_systems',
          requires=IS_IN_DB(db, db.monitutor_systems, '%(name)s')),
    Field('milestone_id', 'reference monitutor_milestones', required=True,
          requires=IS_IN_DB(db, db.monitutor_milestones, '%(name)s')),
    Field('hint', type="text"))

db.define_table('monitutor_attachments',
    Field('attachment_id', type='id'),
    Field('name', type='string', required=True),
    Field('producer', type='text', required=True),
    Field('filter', type='text'),
    Field('requires_status', type='integer'),
    Field('check_id', 'reference monitutor_checks', required=True,
          requires=IS_IN_DB(db, db.monitutor_checks, '%(name)s')))

db.define_table('scenario_user',
    Field('scenario_user_id', type="id"),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('user_id', 'reference auth_user', required=True),
    Field('passed', type="boolean", required=False, default=False))

db.define_table('monitutor_customvars',
    Field('customvar_id', type="id", required=True),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type="string", required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type="string", required=True),
    Field('value', type="string"),
    Field('system_id', 'reference monitutor_systems',
          requires=IS_IN_DB(db, db.monitutor_systems, '%(name)s')))

db.define_table('monitutor_user_customvars', db.monitutor_customvars,
    Field('user_id', 'reference auth_user', required=True))

def __db_get_checks(scenario_id):
    checks = db((db.monitutor_scenarios.scenario_id == scenario_id) &
                (db.monitutor_milestones.scenario_id ==
                 db.monitutor_scenarios.scenario_id) &
                (db.monitutor_checks.milestone_id ==
                 db.monitutor_milestones.milestone_id)).select()
    return checks

def __db_get_visible_checks(scenario_id):
    checks = db((db.monitutor_scenarios.scenario_id == scenario_id) &
                (db.monitutor_milestones.scenario_id ==
                 db.monitutor_scenarios.scenario_id) &
                (db.monitutor_checks.milestone_id ==
                 db.monitutor_milestones.milestone_id) &
                (db.monitutor_milestones.hidden == False) &
                (db.monitutor_checks.hidden == False)).select()
    return checks

