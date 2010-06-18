# The contents of this file are subject to the Mozilla Public
# License Version 1.1 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS
# IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
# implied. See the License for the specific language governing
# rights and limitations under the License.
#
# The Initial Owner of the Original Code is European Environment
# Agency (EEA).  Portions created by Finsiel Romania and Eau de Web are
# Copyright (C) European Environment Agency.  All
# Rights Reserved.
#
# Authors:
#
# Andrei Laza, Eau de Web

#Python imports
from copy import deepcopy
import os
import sys
import datetime

import vobject

#Zope imports
from Globals import InitializeClass
from App.ImageFile import ImageFile
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens, view
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Acquisition import Implicit
from zope.event import notify
from naaya.content.base.events import NyContentObjectAddEvent
from naaya.content.base.events import NyContentObjectEditEvent
from zope.interface import implements

#Product imports
from Products.Naaya.NyFolder import NyFolder
from Products.NaayaBase.NyContentType import NyContentType, NY_CONTENT_BASE_SCHEMA
from naaya.content.base.constants import *
from Products.NaayaBase.constants import *
from Products.NaayaBase.NyItem import NyItem
from Products.NaayaBase.NyAttributes import NyAttributes
from Products.NaayaBase.NyValidation import NyValidation
from Products.NaayaBase.NyCheckControl import NyCheckControl
from Products.NaayaBase.NyContentType import NyContentData
from Products.NaayaCore.managers.utils import make_id
from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile
from naaya.core.zope2util import DT2dt
from interfaces import INyMeeting
from NyParticipants import NyParticipants

#module constants
DEFAULT_SCHEMA = {
    'location':         dict(sortorder=100, widget_type='String',   label='Meeting location', localized=True),
    'start_date':       dict(sortorder=130, widget_type='Date',     label='Start date', data_type='date', required=True),
    'end_date':         dict(sortorder=140, widget_type='Date',     label='End date', data_type='date'),
    'agenda_url':       dict(sortorder=210, widget_type='String',   label='Agenda URL'),
    'minutes_url':      dict(sortorder=210, widget_type='String',   label='Minutes URL'),
    'contact_person':   dict(sortorder=210, widget_type='String',   label='Contact person'),
    'contact_email':    dict(sortorder=210, widget_type='String',   label='Contact email'),
}
DEFAULT_SCHEMA.update(NY_CONTENT_BASE_SCHEMA)

# this dictionary is updated at the end of the module
config = {
        'product': 'NaayaContent',
        'module': 'meeting_item',
        'package_path': os.path.abspath(os.path.dirname(__file__)),
        'meta_type': 'Naaya Meeting',
        'label': 'Meeting',
        'permission': 'Naaya - Add Naaya Meeting objects',
        'forms': ['meeting_add', 'meeting_edit', 'meeting_index'],
        'add_form': 'meeting_add_html',
        'description': 'This is Naaya Meeting type.',
        'default_schema': DEFAULT_SCHEMA,
        'schema_name': 'NyMeeting',
        '_module': sys.modules[__name__],
        'additional_style': None,
        'icon': os.path.join(os.path.dirname(__file__), 'www', 'meeting.gif'),
        '_misc': {
                'NyMeeting.gif': ImageFile('www/meeting.gif', globals()),
                'NyMeeting_marked.gif': ImageFile('www/meeting_marked.gif', globals()),
            },
    }

def meeting_add_html(self, REQUEST=None, RESPONSE=None):
    """ """
    from Products.NaayaBase.NyContentType import get_schema_helper_for_metatype
    form_helper = get_schema_helper_for_metatype(self, config['meta_type'])
    return self.getFormsTool().getContent({'here': self, 'kind': config['meta_type'], 'action': 'addNyMeeting', 'form_helper': form_helper}, 'meeting_add')

def _create_NyMeeting_object(parent, id, contributor):
    id = make_id(parent, id=id, prefix='meeting')
    ob = NyMeeting(id, contributor)
    parent.gl_add_languages(ob)
    parent._setObject(id, ob)
    ob = parent._getOb(id)
    ob.after_setObject()
    return ob

def addNyMeeting(self, id='', REQUEST=None, contributor=None, **kwargs):
    """
    Create an Meeting type of object.
    """
    if REQUEST is not None:
        schema_raw_data = dict(REQUEST.form)
    else:
        schema_raw_data = kwargs
    _lang = schema_raw_data.pop('_lang', schema_raw_data.pop('lang', None))
    _releasedate = self.process_releasedate(schema_raw_data.pop('releasedate', ''))
    schema_raw_data.setdefault('resourceurl', '')
    schema_raw_data.setdefault('source', '')
    _contact_word = schema_raw_data.get('contact_word', '')

    id = make_id(self, id=id, title=schema_raw_data.get('title', ''), prefix='meeting')
    if contributor is None: contributor = self.REQUEST.AUTHENTICATED_USER.getUserName()

    ob = _create_NyMeeting_object(self, id, contributor)

    form_errors = ob.process_submitted_form(schema_raw_data, _lang, _override_releasedate=_releasedate)

    #check Captcha/reCaptcha
    if not self.checkPermissionSkipCaptcha():
        captcha_validator = self.validateCaptcha(_contact_word, REQUEST)
        if captcha_validator:
            form_errors['captcha'] = captcha_validator

    if form_errors:
        if REQUEST is None:
            raise ValueError(form_errors.popitem()[1]) # pick a random error
        else:
            import transaction; transaction.abort() # because we already called _crete_NyZzz_object
            ob._prepare_error_response(REQUEST, form_errors, schema_raw_data)
            REQUEST.RESPONSE.redirect('%s/meeting_add_html' % self.absolute_url())
            return

    if self.glCheckPermissionPublishObjects():
        approved, approved_by = 1, self.REQUEST.AUTHENTICATED_USER.getUserName()
    else:
        approved, approved_by = 0, None
    ob.approveThis(approved, approved_by)
    ob.submitThis()

    if ob.discussion: ob.open_for_comments()
    self.recatalogNyObject(ob)
    notify(NyContentObjectAddEvent(ob, contributor, schema_raw_data))
    #log post date
    auth_tool = self.getAuthenticationTool()
    auth_tool.changeLastPost(contributor)
    #redirect if case
    if REQUEST is not None:
        l_referer = REQUEST['HTTP_REFERER'].split('/')[-1]
        if l_referer == 'meeting_manage_add' or l_referer.find('meeting_manage_add') != -1:
            return self.manage_main(self, REQUEST, update_menu=1)
        elif l_referer == 'meeting_add_html':
            self.setSession('referer', self.absolute_url())
            return ob.object_submitted_message(REQUEST)
            REQUEST.RESPONSE.redirect('%s/messages_html' % self.absolute_url())

    return ob.getId()

def importNyMeeting(self, param, id, attrs, content, properties, discussion, objects):
    #this method is called during the import process
    try: param = abs(int(param))
    except: param = 0
    if param == 3:
        #just try to delete the object
        try: self.manage_delObjects([id])
        except: pass
    else:
        ob = self._getOb(id, None)
        if param in [0, 1] or (param==2 and ob is None):
            if param == 1:
                #delete the object if exists
                try: self.manage_delObjects([id])
                except: pass

            ob = _create_NyMeeting_object(self, id, self.utEmptyToNone(attrs['contributor'].encode('utf-8')))
            ob.sortorder = attrs['sortorder'].encode('utf-8')
            ob.discussion = abs(int(attrs['discussion'].encode('utf-8')))
            ob.start_date = self.utConvertDateTimeObjToString(self.utGetDate(attrs['start_date'].encode('utf-8')))
            ob.end_date = self.utConvertDateTimeObjToString(self.utGetDate(attrs['end_date'].encode('utf-8')))
            ob.agenda_url = attrs['agenda_url'].encode('utf-8')
            ob.minutes_url = attrs['minutes_url'].encode('utf-8')
            ob.contact_person = attrs['contact_person'].encode('utf-8')
            ob.contact_email = attrs['contact_email'].encode('utf-8')

            for property, langs in properties.items():
                [ ob._setLocalPropValue(property, lang, langs[lang]) for lang in langs if langs[lang]!='' ]
            ob.approveThis(approved=abs(int(attrs['approved'].encode('utf-8'))),
                approved_by=self.utEmptyToNone(attrs['approved_by'].encode('utf-8')))
            if attrs['releasedate'].encode('utf-8') != '':
                ob.setReleaseDate(attrs['releasedate'].encode('utf-8'))
            ob.import_comments(discussion)
            self.recatalogNyObject(ob)

class meeting_item(Implicit, NyContentData):
    """ """

class NyMeeting(meeting_item, NyFolder, NyAttributes, NyItem, NyCheckControl, NyContentType):
    """ """

    implements(INyMeeting)

    meta_type = config['meta_type']
    meta_label = config['label']
    icon = 'misc_/NaayaContent/NyMeeting.gif'
    icon_marked = 'misc_/NaayaContent/NyMeeting_marked.gif'

    def manage_options(self):
        """ """
        l_options = ()
        l_options += ({'label': 'Properties', 'action': 'manage_edit_html'},)
        l_options += meeting_item.manage_options
        l_options += ({'label': 'View', 'action': 'index_html'},) + NyItem.manage_options
        return l_options

    security = ClassSecurityInfo()

    edit_participants = NyParticipants('edit_participants')

    def __init__(self, id, contributor):
        """ """
        self.id = id
        meeting_item.__init__(self)
        NyCheckControl.__dict__['__init__'](self)
        NyItem.__dict__['__init__'](self)
        self.contributor = contributor

    security.declarePrivate('objectkeywords')
    def objectkeywords(self, lang):
        return u' '.join([self._objectkeywords(lang), self.getLocalProperty('location', lang)])

    security.declarePrivate('export_this_tag_custom')
    def export_this_tag_custom(self):
        return 'start_date="%s" end_date="%s" agenda_url="%s" minutes_url="%s" contact_person="%s" contact_email="%s"' % \
            (
                self.utXmlEncode(self.utNoneToEmpty(self.start_date)),
                self.utXmlEncode(self.utNoneToEmpty(self.end_date)),
                self.utXmlEncode(self.agenda_url),
                self.utXmlEncode(self.minutes_url),
                self.utXmlEncode(self.contact_person),
                self.utXmlEncode(self.contact_email),
            )

    security.declarePrivate('export_this_body_custom')
    def export_this_body_custom(self):
        r = []
        ra = r.append
        for l in self.gl_get_languages():
            ra('<location lang="%s"><![CDATA[%s]]></location>' % (l, self.utToUtf8(self.getLocalProperty('location', l))))
        return ''.join(r)

    security.declarePrivate('syndicateThis')
    def syndicateThis(self, lang=None):
        l_site = self.getSite()
        if lang is None: lang = self.gl_get_selected_language()
        r = []
        ra = r.append
        ra(self.syndicateThisHeader())
        ra(self.syndicateThisCommon(lang))
        ra('<dc:type>Meeting</dc:type>')
        ra('<dc:format>text</dc:format>')
        ra('<dc:source>%s</dc:source>' % self.utXmlEncode(l_site.getLocalProperty('publisher', lang)))
        ra('<dc:creator>%s</dc:creator>' % self.utXmlEncode(l_site.getLocalProperty('creator', lang)))
        ra('<dc:publisher>%s</dc:publisher>' % self.utXmlEncode(l_site.getLocalProperty('publisher', lang)))
        ra('<ev:startdate>%s</ev:startdate>' % self.utShowFullDateTimeHTML(self.start_date))
        ra('<ev:enddate>%s</ev:enddate>' % self.utShowFullDateTimeHTML(self.end_date))
        ra('<ev:location>%s</ev:location>' % self.utXmlEncode(self.getLocalProperty('location', lang)))
        ra('<ev:organizer>%s</ev:organizer>' % self.utXmlEncode(self.contact_person))
        ra('<ev:type>Meeting</ev:type>')
        ra(self.syndicateThisFooter())
        return ''.join(r)

    #zmi actions
    security.declareProtected(view_management_screens, 'manageProperties')
    def manageProperties(self, REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG

        if REQUEST is not None:
            schema_raw_data = dict(REQUEST.form)
        else:
            schema_raw_data = kwargs
        _lang = schema_raw_data.pop('_lang', schema_raw_data.pop('lang', None))
        _releasedate = self.process_releasedate(schema_raw_data.pop('releasedate', ''), self.releasedate)
        _approved = int(bool(schema_raw_data.pop('approved', False)))

        form_errors = self.process_submitted_form(schema_raw_data, _lang, _override_releasedate=_releasedate)
        if form_errors:
            raise ValueError(form_errors.popitem()[1]) # pick a random error

        if _approved != self.approved:
            if _approved == 0: _approved_by = None
            else: _approved_by = self.REQUEST.AUTHENTICATED_USER.getUserName()
            self.approveThis(_approved, _approved_by)

        self._p_changed = 1
        if self.discussion: self.open_for_comments()
        else: self.close_for_comments()
        self.recatalogNyObject(self)
        if REQUEST: REQUEST.RESPONSE.redirect('manage_edit_html?save=ok')

    #site actions
    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'saveProperties')
    def saveProperties(self, REQUEST=None, **kwargs):
        """ """
        if not self.checkPermissionEditObject():
            raise EXCEPTION_NOTAUTHORIZED, EXCEPTION_NOTAUTHORIZED_MSG

        obj = self

        if REQUEST is not None:
            schema_raw_data = dict(REQUEST.form)
        else:
            schema_raw_data = kwargs
        _lang = schema_raw_data.pop('_lang', schema_raw_data.pop('lang', None))
        _releasedate = self.process_releasedate(schema_raw_data.pop('releasedate', ''), obj.releasedate)

        form_errors = self.process_submitted_form(schema_raw_data, _lang, _override_releasedate=_releasedate)

        if not form_errors:
            if self.discussion: self.open_for_comments()
            else: self.close_for_comments()
            self._p_changed = 1
            self.recatalogNyObject(self)
            #log date
            contributor = self.REQUEST.AUTHENTICATED_USER.getUserName()
            auth_tool = self.getAuthenticationTool()
            auth_tool.changeLastPost(contributor)
            notify(NyContentObjectEditEvent(self, contributor))
            if REQUEST:
                self.setSessionInfoTrans(MESSAGE_SAVEDCHANGES, date=self.utGetTodayDate())
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), _lang))
        else:
            if REQUEST is not None:
                self._prepare_error_response(REQUEST, form_errors, schema_raw_data)
                REQUEST.RESPONSE.redirect('%s/edit_html?lang=%s' % (self.absolute_url(), _lang))
            else:
                raise ValueError(form_errors.popitem()[1]) # pick a random error

    #zmi pages
    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/meeting_manage_edit', globals())

    #site pages
    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST=None, RESPONSE=None):
        """ """
        if self.publicinterface:
            l_index = self._getOb('index', None)
            if l_index is not None: return l_index()
        return self.getFormsTool().getContent({'here': self}, 'meeting_index')

    security.declareProtected(PERMISSION_EDIT_OBJECTS, 'edit_html')
    def edit_html(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'meeting_edit')

    security.declareProtected(view, 'menusubmissions')
    def menusubmissions(self, REQUEST=None, RESPONSE=None):
        """ """
        return self.getFormsTool().getContent({'here': self}, 'meeting_menusubmissions')

    def get_ics(self, REQUEST, RESPONSE):
        """ Export this meeting as 'ics' """

        cal = vobject.iCalendar()
        cal.add('prodid').value = '-//European Environment Agency//Naaya//EN'
        cal.add('method').value = 'PUBLISH'
        cal.add('vevent')

        cal.vevent.add('uid').value = self.absolute_url() + '/get_ics'
        cal.vevent.add('url').value = self.absolute_url()
        cal.vevent.add('summary').value = self.title_or_id()
        cal.vevent.add('transp').value = 'OPAQUE'

        modif_time = DT2dt(self.bobobase_modification_time())
        cal.vevent.add('dtstamp').value = modif_time

        cal.vevent.add('dtstart').value = DT2dt(self.start_date).date()
        cal.vevent.add('dtend').value = (DT2dt(self.end_date).date() +
                                         datetime.timedelta(days=1))

        loc = []
        if self.location:
            loc.append(self.location)

        if loc:
            cal.vevent.add('location').value = ', '.join(loc)

        ics_data = cal.serialize()

        #RESPONSE.setHeader('Content-Type', 'text/plain')
        RESPONSE.setHeader('Content-Type', 'text/calendar')
        RESPONSE.setHeader('Content-Disposition',
                           'attachment;filename=%s.ics' % self.getId())
        RESPONSE.write(ics_data)

InitializeClass(NyMeeting)

manage_addNyMeeting_html = PageTemplateFile('zpt/meeting_manage_add', globals())
manage_addNyMeeting_html.kind = config['meta_type']
manage_addNyMeeting_html.action = 'addNyMeeting'

#Custom page templates
NaayaPageTemplateFile('zpt/meeting_menusubmissions', globals(), 'meeting_menusubmissions')

config.update({
    'constructors': (manage_addNyMeeting_html, addNyMeeting),
    'folder_constructors': [
            # NyFolder.manage_addNyMeeting_html = manage_addNyMeeting_html
            ('manage_addNyMeeting', manage_addNyMeeting_html),
            ('meeting_add_html', meeting_add_html),
            ('addNyMeeting', addNyMeeting),
            ('import_meeting_item', importNyMeeting),
        ],
    'add_method': addNyMeeting,
    'validation': issubclass(NyMeeting, NyValidation),
    '_class': NyMeeting,
})

def get_config():
    return config

