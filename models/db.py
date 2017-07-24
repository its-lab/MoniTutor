from gluon.contrib.appconfig import AppConfig
app_conf = AppConfig(reload=False)
DATABASE_NAME = app_conf.take("monitutor_env.database_name")
DATABASE_USER = app_conf.take("monitutor_env.database_user")
DATABASE_PASSWORD = app_conf.take("monitutor_env.database_password")
DATABASE_HOST = app_conf.take("monitutor_env.database_host")
ICINGA2_DATABASE_NAME = app_conf.take("monitutor_env.icinga2_database_name")
db = DAL("postgres://" + DATABASE_USER + ":" + DATABASE_PASSWORD + "@" + DATABASE_HOST + "/" + ICINGA2_DATABASE_NAME, migrate_enabled=False, lazy_tables=False)

db.define_table('icinga_hosts', 
    Field('host_id', type='id'), 
    Field('alias'), 
    Field('display_name'), 
    Field('address'), 
    Field('address6'),
    Field('host_object_id', 'reference icinga_objects'))

db.define_table('icinga_hoststatus',
    Field('hoststatus_id', type='id'),
    Field('host_object_id', 'reference icinga_objects'),
    Field('status_update_time'),
    Field('output'),
    Field('long_output'),
    Field('perfdata'),
    Field('current_state'),
    Field('last_check'),
    Field('next_check'))
                
db.define_table('icinga_objects',
    Field('object_id', type='id'),
    Field('instance_id'),
    Field('objecttype_id'),
    Field('name1'),
    Field('name2'),
    Field('is_active'))

db.define_table('icinga_services',
    Field('service_id', type='id'),
    Field('instance_id'),
    Field('config_type'),
    Field('host_object_id', 'reference icinga_objects'),
    Field('service_object_id', 'reference icinga_objects'), 
    Field('display_name'), 
    Field('check_command_object_id'),
    Field('check_command_args'),
    Field('check_interval'),
    Field('retry_interval'),
    Field('max_check_attempts'),
    Field('notes'))


db.define_table('icinga_servicestatus',
    Field('servicestatus_id',type='id'),
    Field('instance_id'),
    Field('service_object_id', 'reference icinga_objects'),
    Field('status_update_time'),
    Field('output'),
    Field('long_output'),
    Field('perfdata'),
    Field('current_state'),
    Field('has_been_checked'),
    Field('last_check'),
    Field('next_check') )               

db.define_table('icinga_customvariables',
    Field('customvariable_id', type='id'),
    Field('instance_id'),
    Field('object_id', 'reference icinga_objects'),
    Field('config_type'),
    Field('has_been_modified'),
    Field('varname'),
    Field('varvalue'),
    Field('is_json') )

db.define_table('icinga_statehistory',
    Field('statehistory_id',type='id'),
    Field('state_time', 'datetime'),
    Field('object_id', 'reference icinga_objects'),
    Field('state'),
    Field('state_type'),
    Field('last_state'),
    Field('output'),
    Field('long_output'),
    Field('state_change'))

                
