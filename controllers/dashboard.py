from time import strptime
import datetime

@auth.requires_membership('admin')
def view_dashboard():
    usernumber = db(db.auth_user.id >0).count()
    return dict(usernumber=usernumber)

@auth.requires_membership('admin')
def view_users():
    users = db(db.auth_user.id >0).select()
    user_scenario = db(db.auth_user.id == db.scenario_user.user_id).select()
    admin_user = db((db.auth_group.role == 'admin') &
                         (db.auth_membership.group_id == db.auth_group.id) &
                         (db.auth_user.id == db.auth_membership.user_id)).select()
    last_action = {}
    last_login = {}
    for user in users:
        last_action_row = db(db.auth_event.user_id == user.id).select(orderby=~db.auth_event.time_stamp).first()
        last_login_row = db((db.auth_event.user_id == user.id)&
                                 (db.auth_event.description.contains("Logged-in"))).select(orderby=~tutordb.auth_event.time_stamp).first()
        if last_login_row is not None:
            last_login_row.time_stamp = str(datetime.datetime.now()-last_login_row.time_stamp).split('.',2)[0]
            last_action_row.time_stamp = str(datetime.datetime.now()-last_action_row.time_stamp).split('.',2)[0]
            last_action[user.id] = last_action_row
            last_login[user.id] = last_login_row
        else:
            last_action[user.id] = "NONE"
            last_login[user.id] = "NONE"
    admin_ids = []
    for user in admin_user:
        admin_ids.append(user.auth_user.id)
    return dict(users=users, user_scenario=user_scenario, admin_ids=admin_ids, last_action=last_action, last_login=last_login)

@auth.requires_membership('admin')
def view_user():
    if len(request.args):
        user_id = request.args(0, cast=int)
    else:
        redirect(URL())
        user_id = None
    user = db.auth_user[user_id]

    last_action = None
    last_login = None
    event_history = db(db.auth_event.user_id == user_id).select(orderby=~db.auth_event.time_stamp)
    last_action_row = event_history.first()
    last_login_row = db((db.auth_event.user_id == user_id)&
                             (db.auth_event.description.contains("Logged-in"))).select(orderby=~db.auth_event.time_stamp).first()

    if last_login_row is not None:
        last_login_row.time_stamp = str(datetime.datetime.now()-last_login_row.time_stamp).split('.',2)[0]
        last_action_row.time_stamp = str(datetime.datetime.now()-last_action_row.time_stamp).split('.',2)[0]

        last_action = last_action_row
        last_login = last_login_row
    else:
        last_action = "NONE"
        last_login = "NONE"
    is_admin = auth.has_membership(user_id=user_id, role='admin')
    return dict(user=user, is_admin=is_admin,  last_action=last_action, last_login=last_login)

@auth.requires_membership('admin')
def view_history():
    if len(request.args):
        user_id = request.args(0, cast=int)
    else:
        redirect(URL())
        user_id = None
    grid = SQLFORM.grid(db.auth_event.user_id==user_id,
                        deletable=False,
                        editable=False,
                        create=False,
                        user_signature=False,
                        orderby=~db.auth_event.time_stamp,
                        details=False,
                        links_in_grid=False,
                        paginate=15,
                        args=request.args[:1])
    return dict(grid=grid)
