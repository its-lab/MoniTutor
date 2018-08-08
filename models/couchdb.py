from gluon.contrib.appconfig import AppConfig
from cloudant import CouchDB
app_conf = AppConfig(reload=False)
COUCHDB_DATABASE = app_conf.take("monitutor_env.couchdb_database")
COUCHDB_HOST = app_conf.take("monitutor_env.couchdb_host")
COUCHDB_USERNAME = app_conf.take("monitutor_env.couchdb_username")
COUCHDB_PASSWORD = app_conf.take("monitutor_env.couchdb_password")

class ResultDatabase():

    def __init__(self,
                 couchdb_host,
                 couchdb_database,
                 couchdb_username,
                 couchdb_password):
        self.couchdb = CouchDB(couchdb_username, couchdb_password, url=couchdb_host)
        self.couchdb_database = couchdb_database

    def _get_db_handle(self):
        self.couchdb.connect()
        return self.couchdb[self.couchdb_database]

    def _get_ddoc(self):
        couchdb_database = self._get_db_handle()
        return couchdb_database.get_design_document("results")

    def _get_result_history(self):
        result_ddoc = self._get_ddoc()
        return result_ddoc.get_view("check_result_history")

    def _get_results(self):
        result_ddoc = self._get_ddoc()
        return result_ddoc.get_view("check_results")

    def _get_host_status_history(self):
        result_ddoc = self._get_ddoc()
        return result_ddoc.get_view("host_status_history")

    def _get_host_status(self):
        result_ddoc = self._get_ddoc()
        return result_ddoc.get_view("host_status")

    def _get_severity(self):
        result_ddoc = self._get_ddoc()
        return result_ddoc.get_view("severity")

    def host_status(self, username=None, hostname=None):
        host_status_view = self._get_host_status()
        if username is None and hostname is None:
            host_status = host_status_view()
        elif hostname is None:
            host_status = host_status_view(startkey=[username], endkey=[username,{}])
        else:
            host_status = host_status_view(keys=[[username, hostname]])
        return host_status["rows"]

    def check_results(self, username=None, check_name=None):
        check_results_view = self._get_results()
        if username is None and check_name is None:
            check_results = check_results_view()
        elif check_name is None:
            check_results = check_results_view(startkey=[username], endkey=[username,{}])
        else:
            check_results = check_results_view(keys=[[username, check_name]])
        return check_results["rows"]

resultdb = ResultDatabase(COUCHDB_HOST, COUCHDB_DATABASE, COUCHDB_USERNAME, COUCHDB_PASSWORD)
