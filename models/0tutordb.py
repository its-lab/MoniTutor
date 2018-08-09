from gluon.contrib.appconfig import AppConfig
import uuid
app_conf = AppConfig(reload=True)
DATABASE_NAME = app_conf.take("monitutor_env.database_name")
DATABASE_USER = app_conf.take("monitutor_env.database_user")
DATABASE_PASSWORD = app_conf.take("monitutor_env.database_password")
DATABASE_HOST = app_conf.take("monitutor_env.database_host")
tutordb = DAL("postgres://" + DATABASE_USER + ":" + DATABASE_PASSWORD + "@" + DATABASE_HOST + "/" + DATABASE_NAME)

from gluon.tools import Auth

auth = Auth(tutordb)

auth.settings.extra_fields['auth_user']= [
        Field('hmac_secret', length=512, default=lambda:str(uuid.uuid4()).replace("-","")[:16]),
        Field('image', type='upload', uploadfield='image_data'),
        Field('image_data', type='blob')
        ]

auth.define_tables(username=True)

if not tutordb.auth_group[1]:
    tutordb.auth_group.insert(role="admin")

tutordb.define_table('monitutor_scenarios',
    Field('scenario_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='text', required=True),
    Field('goal', type='text'),
    Field('hidden', type='boolean', default=True),
    Field('initiated', type='boolean', default=True))

tutordb.define_table('monitutor_data',
    Field('data_id', type='id'),
    Field('data', type='upload', required=True, uploadfield='data_data'),
    Field('data_data', type='blob'),
    Field('description', type='text'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True))

tutordb.define_table('monitutor_scenario_data',
    Field('scenario_data_id', type='id'),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('data_id', 'reference monitutor_data', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_data, '%(name)s')))

tutordb.define_table('monitutor_milestones',
    Field('milestone_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='string'))

tutordb.define_table('monitutor_milestone_scenario',
    Field('milestone_scenario_id', type='id'),
    Field('milestone_id', 'reference monitutor_milestones', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_milestones, '%(name)s')),
    Field('scenario_id', 'reference monitutor_scenarios', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_scenarios, '%(name)s')),
    Field('sequence_nr', type='integer'),
    Field('dependency', 'reference monitutor_milestone_scenario',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_scenarios, '%(name)s')),
    Field('hidden', type="boolean", default=False))

tutordb.define_table('monitutor_interpreters',
    Field('interpreter_id', type='id'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('path', type='string', required=True))

tutordb.define_table('monitutor_programs',
    Field('program_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('code', type='text', required=True, requires=IS_LENGTH(655360)),
    Field('interpreter_id', 'reference monitutor_interpreters', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_interpreters, '%(name)s')))

tutordb.define_table('monitutor_checks',
    Field('check_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type='string', required=True, requires=[IS_ALPHANUMERIC(), IS_NOT_IN_DB(tutordb,"monitutor_checks.name")]),
    Field('display_name', type='string', required=True),
    Field('params', type='string'),
    Field('program_id', 'reference monitutor_programs', required=True, 
          requires=IS_IN_DB(tutordb, tutordb.monitutor_programs, '%(name)s')),
    Field('hint', type="text"))

tutordb.define_table('monitutor_check_milestone',
    Field('check_milestone_id', type='id'),
    Field('check_id', 'reference monitutor_checks', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_checks, '%(name)s')),
    Field('milestone_id', 'reference monitutor_milestones', required=True,
          requires=IS_IN_DB(tutordb, tutordb.monitutor_milestones, '%(name)s')),
    Field('flag_invis', type='integer', default=0),
    Field('sequence_nr', type='integer'))

tutordb.define_table('monitutor_systems',
    Field('system_id', type='id'),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('hostname', type='string', required=True),
    Field('ip4_address', type='blob'),
    Field('ip6_address', type='blob'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='string'))

tutordb.define_table('monitutor_types',
    Field('type_id', type='id'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True))

if not tutordb(tutordb.monitutor_types.name == "source").select():
    tutordb.monitutor_types.insert(name="source", display_name="Source")
    tutordb.monitutor_types.insert(name="dest", display_name="Destination")

tutordb.define_table('monitutor_targets',
    Field('target_id', type='id'),
    Field('system_id', 'reference monitutor_systems',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_systems, '%(name)s')),
    Field('check_id', 'reference monitutor_checks',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_checks, '%(name)s')),
    Field('type_id', 'reference monitutor_types',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_types, '%(name)s')))

tutordb.define_table('scenario_user',
    Field('scenario_user_id', type="id"),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('user_id', 'reference auth_user', required=True),
    Field('passed', type="boolean", required=False, default=False))

tutordb.define_table('monitutor_check_tasks',
    Field('check_tasks_id', type="id"),
    Field('interpreter_path', type="string"),
    Field('username', type="string"),
    Field('hostname', type="string"),
    Field('prio', type="integer"),
    Field('status', type="string"),
    Field('timestamp', type="datetime"),
    Field('check_name', type="string"),
    Field('parameters', type="string"),
    Field('program_name', type="string"))

tutordb.define_table('monitutor_customvars',
    Field('customvar_id', type="id", required=True),
    Field('uuid', length=64, default=lambda:str(uuid.uuid4())),
    Field('name', type="string", required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type="string", required=True),
    Field('value', type="string"))

tutordb.define_table('monitutor_customvar_system', tutordb.monitutor_customvars,
    Field('system_id', 'reference monitutor_systems',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_systems, '%(name)s')))

tutordb.define_table('monitutor_user_system',
    Field('user_system_id', type="id"),
    Field('system_id', 'reference monitutor_systems',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_systems, '%(name)s')),
    Field('user_id', 'reference auth_user'),
    Field('hostname', type='string'),
    Field('ip4_address', type='blob'),
    Field('ip6_address', type='blob'))

tutordb.define_table('monitutor_customvar_user_system', tutordb.monitutor_customvars,
    Field('system_id', 'reference monitutor_user_system',
          requires=IS_IN_DB(tutordb, tutordb.monitutor_user_system, '%(name)s')))
