from time import strptime
@auth.requires_membership('admin')
def view_dashboard():
    usernumber = tutordb(tutordb.auth_user.id >0).count()
    return dict(usernumber=usernumber)

@auth.requires_membership('admin')
def view_users():
    users = tutordb(tutordb.auth_user.id >0).select()
    user_scenario = tutordb(tutordb.auth_user.id == tutordb.scenario_user.user_id).select()
    admin_user = tutordb((tutordb.auth_group.role == 'admin') &
                          (tutordb.auth_membership.group_id == tutordb.auth_group.id) &
                          (tutordb.auth_user.id == tutordb.auth_membership.user_id)).select()
    last_action = {}
    last_login = {}
    for user in users:
        last_action_row = tutordb(tutordb.auth_event.user_id == user.id).select(orderby=~tutordb.auth_event.time_stamp).first()
        last_login_row = tutordb((tutordb.auth_event.user_id == user.id)&
                                 (tutordb.auth_event.description.contains("Logged-in"))).select(orderby=~tutordb.auth_event.time_stamp).first()
        
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
    user = tutordb.auth_user[user_id]

    last_action = None
    last_login = None 
    event_history = tutordb(tutordb.auth_event.user_id == user_id).select(orderby=~tutordb.auth_event.time_stamp)
    last_action_row = event_history.first()
    last_login_row = tutordb((tutordb.auth_event.user_id == user_id)&
                             (tutordb.auth_event.description.contains("Logged-in"))).select(orderby=~tutordb.auth_event.time_stamp).first()
    
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
    grid = SQLFORM.grid(tutordb.auth_event.user_id==user_id,
                        deletable=False, 
                        editable=False, 
                        create=False, 
                        user_signature=False,
                        orderby=~tutordb.auth_event.time_stamp,
                        details=False,
                        links_in_grid=False,
                        paginate=15,
                        args=request.args[:1])
    return dict(grid=grid)
