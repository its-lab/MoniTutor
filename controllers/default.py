# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################
@auth.requires_login()
def index():
    return dict()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    form = auth()
    return dict(form=form)


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, tutordb)

@cache.action()
def export():
    """
    allows downloading of uploaded files
    http://..../[app]/default/export/[filename]
    """
    return response.download(request, None)



def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@auth.requires_login()
def edit_user():
    if auth.has_membership("admin") and len(request.args):
        user_id = request.args(0, cast=int)
    else:
        user_id = auth.user_id

    edit_user_form = SQLFORM(db.auth_user, user_id, upload=URL('download'))
    if edit_user_form.process().accepted:
        response.flash = 'form accepted'
    elif edit_user_form.errors:
        response.flash = 'form has errors'
    return dict(edit_user_form = edit_user_form)

