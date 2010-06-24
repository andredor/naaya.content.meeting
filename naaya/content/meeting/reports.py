# Authors:
# Andrei Laza, Eau de Web

#Python imports
try:
    import json
except ImportError:
    import simplejson as json

#Zope imports
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view

#Naaya imports
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile

#naaya.content.meeting improts
import meeting as meeting_module

class MeetingReports(SimpleItem):
    """ """
    security = ClassSecurityInfo()

    title = "Meeting Reports"

    def __init__(self, id):
        """ """
        self.id = id

    def _get_info_tool(self, meeting_obs):
        if len(meeting_obs) > 0:
            return meeting_obs[0].participants

    def jstree_participants(self):
        """ """
        jstree, participants = [], {}
        site = self.getSite()
        meeting_config = meeting_module.get_config()
        meeting_obs = site.getCatalogedObjectsCheckView(meta_type=meeting_config['meta_type'], approved=1)
        info_tool = self._get_info_tool(meeting_obs)

        for meeting_ob in meeting_obs:
            for uid in meeting_ob.participants.uids:
                if uid not in participants:
                    participants[uid] = []
                participants[uid].append(meeting_ob)

        for uid, meetings_part in participants.iteritems():
            meeting_nodes = []
            for meeting_ob in meetings_part:
                title = meeting_ob.title_or_id()
                icon = meeting_ob.icon
                href = meeting_ob.absolute_url()
                meeting_nodes.append({'data':
                                            {'title': title,
                                             'icon': icon,
                                             'attributes':
                                                     {'href': href}
                                    }})

            name = info_tool.getUserFullName(uid)
            icon = 'images/report_icons/participant.gif'
            user_node = {'data':
                                {'title': name,
                                 'icon': icon,
                                 'attributes':
                                    {'href': ''}
                                },
                            'children': meeting_nodes}
            email = info_tool.getUserEmail(uid)
            if email is not None:
                href = 'mailto:' + email
                user_node['data']['attributes'] = {'href': href}
            jstree.append(user_node)

        return json.dumps(jstree)

    def jstree_organisations(self):
        """ """
        jstree, organisations = [], {}
        site = self.getSite()
        meeting_config = meeting_module.get_config()
        meeting_obs = site.getCatalogedObjectsCheckView(meta_type=meeting_config['meta_type'], approved=1)
        info_tool = self._get_info_tool(meeting_obs)

        for meeting in meeting_obs:
            for uid in meeting.participants.uids:
                organisation = info_tool.getUserOrganisation(uid)
                if organisation not in organisations:
                    organisations[organisation] = {}
                if uid not in organisations[organisation]:
                    organisations[organisation][uid] = []
                organisations[organisation][uid].append(meeting)

        for organisation, values in organisations.iteritems():
            user_nodes = []
            for uid, meetings in values.iteritems():
                meeting_nodes = []
                for meeting in meetings:
                    title = meeting.title_or_id()
                    icon = meeting.icon
                    href = meeting.absolute_url()
                    meeting_nodes.append({'data':
                                                {'title': title,
                                                 'icon': icon,
                                                 'attributes':
                                                         {'href': href}
                                        }})
                name = info_tool.getUserFullName(uid)
                icon = 'images/report_icons/participant.gif'
                user_node = {'data':
                                    {'title': name,
                                     'icon': icon,
                                     'attributes':
                                        {'href': ''}
                                    },
                                'children': meeting_nodes}
                email = info_tool.getUserEmail(uid)
                if email is not None:
                    href = 'mailto:' + email
                    user_node['data']['attributes'] = {'href': href}
                user_nodes.append(user_node)
            
            jstree.append({'data':
                                {'title': organisation,
                                'icon': 'images/report_icons/organisation.gif',},
                            'children': user_nodes
                        })
        return json.dumps(jstree)
 
    security.declareProtected(view, 'report_meeting_participants')
    def report_meeting_participants(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'report_meeting_participants')

    security.declareProtected(view, 'report_meeting_organisations')
    def report_meeting_organisations(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'report_meeting_organisations')

#Custom page templates
NaayaPageTemplateFile('zpt/report_meeting_participants', globals(), 'report_meeting_participants')
NaayaPageTemplateFile('zpt/report_meeting_organisations', globals(), 'report_meeting_organisations')

