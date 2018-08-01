from gluon.contrib.appconfig import AppConfig
from cloudant import CouchDB
app_conf = AppConfig(reload=False)
COUCHDB_DATABASE = app_conf.take("monitutor_env.couchdb_database")
COUCHDB_HOST = app_conf.take("monitutor_env.couchdb_host")
COUCHDB_USERNAME = app_conf.take("monitutor_env.couchdb_username")
COUCHDB_PASSWORD = app_conf.take("monitutor_env.couchdb_password")

couchdb = CouchDB(COUCHDB_USERNAME, COUCHDB_PASSWORD, url=COUCHDB_HOST)

def _get_db_handle():
    couchdb.connect()
    return couchdb[COUCHDB_DATABASE]

def _get_ddoc():
    couchdb.connect()
    couchdb_database = couchdb[COUCHDB_DATABASE]
    return couchdb_database.get_design_document("results")

