from gluon.contrib.appconfig import AppConfig
app_conf = AppConfig(reload=True)
DATABASE_NAME = app_conf.take("monitutor_env.database_name")
DATABASE_USER = app_conf.take("monitutor_env.database_user")
DATABASE_PASSWORD = app_conf.take("monitutor_env.database_password")
tutordb = DAL("postgres://" + DATABASE_USER + ":" + DATABASE_PASSWORD + "@localhost/" + DATABASE_NAME)

from gluon.tools import Auth

auth = Auth(tutordb)

auth.define_tables(username=True)


tutordb.define_table('monitutor_scenarios',
    Field('scenario_id', type='id'),
    Field('name', type='string', requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='text', required=True),
    Field('goal', type='text'),
    Field('hidden', type='boolean', default=True),
    Field('initiated', type='boolean', default=True))

tutordb.define_table('monitutor_data',
    Field('data_id', type='id'),
    Field('data', type='upload', required=True),
    Field('description', type='text'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True))

tutordb.define_table('monitutor_scenario_data',
    Field('scenario_data_id', type='id'),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('data_id', 'reference monitutor_data', required=True))

tutordb.define_table('monitutor_milestones',
    Field('milestone_id', type='id'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('description', type='string'))

tutordb.define_table('monitutor_milestone_scenario',
    Field('milestone_scenario_id', type='id'),
    Field('milestone_id', 'reference monitutor_milestones', required=True),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('sequence_nr', type='integer'),
    Field('dependency', 'reference monitutor_milestone_scenario'),
    Field('hidden', type="boolean", default=False))

tutordb.define_table('monitutor_interpreters',
    Field('interpreter_id', type='id'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('path', type='string', required=True))

tutordb.define_table('monitutor_programs',
    Field('program_id', type='id'),
    Field('name', type='string', required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type='string', required=True),
    Field('code', type='text', required=True, requires=IS_LENGTH(655360)),
    Field('interpreter_id', 'reference monitutor_interpreters', required=True))

tutordb.define_table('monitutor_checks',
    Field('check_id', type='id'),
    Field('name', type='string', required=True, requires=[IS_ALPHANUMERIC(), IS_NOT_IN_DB(tutordb,"monitutor_checks.name")]),
    Field('display_name', type='string', required=True),
    Field('params', type='string'),
    Field('program_id', 'reference monitutor_programs', required=True),
    Field('hint', type="text"))

tutordb.define_table('monitutor_check_milestone',
    Field('check_milestone_id', type='id'),
    Field('check_id', 'reference monitutor_checks', required=True),
    Field('milestone_id', 'reference monitutor_milestones', required=True),
    Field('flag_invis', type='integer', default=0),
    Field('sequence_nr', type='integer'))

tutordb.define_table('monitutor_systems',
    Field('system_id', type='id'),
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

tutordb.define_table('monitutor_targets',
    Field('target_id', type='id'),
    Field('system_id', 'reference monitutor_systems'),
    Field('check_id', 'reference monitutor_checks'),
    Field('type_id', 'reference monitutor_types'))

tutordb.define_table('scenario_user',
    Field('scenario_user_id', type="id"),
    Field('scenario_id', 'reference monitutor_scenarios', required=True),
    Field('user_id', 'reference auth_user', required=True),
    Field('status', type='string', required=True),
    Field('progress', type="integer", requires=IS_INT_IN_RANGE(minimum=0, maximum=100), default="0"),
    Field('initiation_time', type="datetime", required=False))

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
    Field('name', type="string", required=True, requires=IS_ALPHANUMERIC()),
    Field('display_name', type="string", required=True),
    Field('value', type="string"))

tutordb.define_table('monitutor_customvar_system', tutordb.monitutor_customvars,
    Field('system_id', 'reference monitutor_systems'))

tutordb.define_table('monitutor_user_system',
    Field('user_system_id', type="id"),
    Field('system_id', 'reference monitutor_systems'),
    Field('user_id', 'reference auth_user'),
    Field('hostname', type='string'),
    Field('ip4_address', type='blob'),
    Field('ip6_address', type='blob'))

tutordb.define_table('monitutor_customvar_user_system', tutordb.monitutor_customvars,
    Field('system_id', 'reference monitutor_user_system'))