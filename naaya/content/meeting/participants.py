# Authors:
# Andrei Laza, Eau de Web

#Python imports

#Zope imports
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import change_permissions
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from persistent.list import PersistentList

#Naaya imports
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile
from naaya.content.meeting import MEETING_ROLE

class Participants(SimpleItem):
    security = ClassSecurityInfo()

    title = "Edit participants"

    def __init__(self, id):
        """ """
        self.id = id
        self.uids = PersistentList()

    def findUsers(self, search_param, search_term):
        """ """
        def userMatched(uid, cn):
            if search_param == 'uid':
                return search_term in uid
            if search_param == 'cn':
                return search_term in cn

        def schema_has_param(acl_folder, param):
            for item in acl_folder.getLDAPSchema():
                if item[0] == param:
                    return True
            return False

        auth_tool = self.getAuthenticationTool()
        ret = []

        for user in auth_tool.getUsers():
            uid = auth_tool.getUserAccount(user)
            cn = auth_tool.getUserFullName(user)
            info = 'Local user'
            
            if userMatched(uid, cn):
                ret.append({'uid': uid, 'cn': cn, 'info': info})

        for source in auth_tool.getSources():
            acl_folder = source.getUserFolder()
            if schema_has_param(acl_folder, search_param): 
                users = acl_folder.findUser(search_param=search_param, search_term=search_term)
                for user in users:
                    uid = user['uid']
                    cn = user['cn']
                    info = user['dn']
                    ret.append({'uid': uid, 'cn': cn, 'info': info})

        return ret

    def _add_user(self, uid):
        self.aq_parent.manage_setLocalRoles(uid, MEETING_ROLE)
        self.uids.append(uid)

    def addUsers(self, REQUEST):
        """ """
        if 'uid' in REQUEST.form:
            uid = REQUEST.form['uid']
            if type(uid) == type([]):
                for u in uid:
                    self._add_user(u)
            else:
                self._add_user(uid)
        return REQUEST.RESPONSE.redirect(self.absolute_url())

    def _remove_user(self, uid):
        self.aq_parent.manage_delLocalRoles([uid])
        self.uids.remove(uid)

    def removeUsers(self, REQUEST):
        """ """
        if 'uid' in REQUEST.form:
            uid = REQUEST.form['uid']
            if type(uid) == type([]):
                for u in uid:
                    self._remove_user(u)
            else:
                self._remove_user(uid)
        return REQUEST.RESPONSE.redirect(self.absolute_url())

    security.declareProtected(change_permissions, 'index_html')
    def index_html(self, REQUEST):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'meeting_participants')

NaayaPageTemplateFile('zpt/participants_index', globals(), 'meeting_participants')

