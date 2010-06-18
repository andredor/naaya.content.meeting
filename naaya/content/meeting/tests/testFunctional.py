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

from unittest import TestSuite, makeSuite

from Products.Naaya.tests.NaayaFunctionalTestCase import NaayaFunctionalTestCase

class NyMeetingCreateTestCase(NaayaFunctionalTestCase):
    """ CreateTestCase for NyMeeting object """

    def afterSetUp(self):
        self.portal.manage_install_pluggableitem('Naaya Meeting')
        from Products.Naaya.NyFolder import addNyFolder
        addNyFolder(self.portal, 'myfolder', contributor='contributor', submitted=1)
        self.portal.myfolder.approveThis()
        self.portal.myfolder.folder_meta_types.append('Naaya Meeting')
        import transaction; transaction.commit()

    def beforeTearDown(self):
        self.portal.manage_delObjects(['myfolder'])
        self.portal.manage_uninstall_pluggableitem('Naaya Meeting')
        import transaction; transaction.commit()

    def test_add(self):
        self.browser_do_login('contributor', 'contributor')
        self.browser.go('http://localhost/portal/myfolder/meeting_add_html')
        self.assertTrue('<h1>Submit Meeting</h1>' in self.browser.get_html())

        form = self.browser.get_form('frmAdd')
        expected_controls = set(['title:utf8:ustring', 'location:utf8:ustring',
            'releasedate', 'start_date', 'end_date',
            'agenda_url:utf8:ustring', 'minutes_url:utf8:ustring',
            'contact_person:utf8:ustring', 'contact_email:utf8:ustring'])
        found_controls = set(c.name for c in form.controls)
        self.assertTrue(expected_controls <= found_controls, 
            'Missing form controls: %s' % repr(expected_controls - found_controls))

        self.browser.clicked(form, self.browser.get_form_field(form, 'title'))
        form['title:utf8:ustring'] = 'MyMeeting'
        form['location:utf8:ustring'] = 'Kogens Nytorv 6, 1050 Copenhagen K, Denmark'
        form['releasedate'] = '16/06/2010'
        form['start_date'] = '20/06/2010'
        form['end_date'] = '25/06/2010'
        form['contact_person:utf8:ustring'] = 'My Name'
        form['contact_email:utf8:ustring'] = 'my.email@my.domain'
        self.browser.submit()
        self.assertTrue('The administrator will analyze your request and you will be notified about the result shortly.' in self.browser.get_html())
        self.assertTrue(hasattr(self.portal.myfolder, 'mymeeting'))

        self.portal.myfolder.mymeeting.approveThis()
        self.browser.go('http://localhost/portal/myfolder/mymeeting')
        html = self.browser.get_html()
        self.assertTrue('MyMeeting' in html)
        self.assertTrue('[20/06/2010 - 25/06/2010]' in html)
        self.assertTrue('My Name' in html)
        self.assertTrue('mailto:my.email@my.domain' in html)
        self.assertTrue('http://localhost/portal/myfolder/mymeeting/get_ics' in html)
        self.assertTrue('16/06/2010' in html)
        self.assertTrue('contributor' in html)
        self.assertTrue('Kogens Nytorv 6, 1050 Copenhagen K, Denmark' in html)

        self.browser_do_logout()

    def test_add_error(self):
        self.browser_do_login('contributor', 'contributor')
        self.browser.go('http://localhost/portal/myfolder/meeting_add_html')
        form = self.browser.get_form('frmAdd')
        self.browser.clicked(form, self.browser.get_form_field(form, 'title'))
        # enter no values in the fields
        self.browser.submit()
        self.assertTrue('The form contains errors' in self.browser.get_html())
        self.assertTrue('Value required for' in self.browser.get_html())

        self.browser_do_logout()

    def test_manage_add(self):
        self.browser_do_login('admin', '')
        self.browser.go('http://localhost/portal/myfolder/manage_addProduct/Naaya/manage_addNyMeeting')
        self.assertTrue('Add Naaya Meeting' in self.browser.get_html())

        form = self.browser.get_form('frmAdd')
        expected_controls = set(['title:utf8:ustring', 'location:utf8:ustring',
            'releasedate', 'start_date', 'end_date',
            'agenda_url:utf8:ustring', 'minutes_url:utf8:ustring',
            'contact_person:utf8:ustring', 'contact_email:utf8:ustring'])
        found_controls = set(c.name for c in form.controls)
        self.assertTrue(expected_controls <= found_controls, 
            'Missing form controls: %s' % repr(expected_controls - found_controls))

        self.browser.clicked(form, self.browser.get_form_field(form, 'title'))
        form['title:utf8:ustring'] = 'MyMeeting2'
        form['location:utf8:ustring'] = 'Kogens Nytorv 6, 1050 Copenhagen K, Denmark'
        form['releasedate'] = '16/06/2010'
        form['start_date'] = '20/06/2010'
        form['end_date'] = '25/06/2010'
        form['contact_person:utf8:ustring'] = 'My Name'
        form['contact_email:utf8:ustring'] = 'my.email@my.domain'
        self.browser.submit()
        self.assertTrue(hasattr(self.portal.myfolder, 'mymeeting2'))

        self.browser.go('http://localhost/portal/myfolder/mymeeting2')
        html = self.browser.get_html()
        self.assertTrue('MyMeeting2' in html)
        self.assertTrue('[20/06/2010 - 25/06/2010]' in html)
        self.assertTrue('My Name' in html)
        self.assertTrue('mailto:my.email@my.domain' in html)
        self.assertTrue('http://localhost/portal/myfolder/mymeeting2/get_ics' in html)
        self.assertTrue('16/06/2010' in html)
        self.assertTrue('admin' in html)
        self.assertTrue('Kogens Nytorv 6, 1050 Copenhagen K, Denmark' in html)

        self.browser_do_logout()


class NyMeetingEditingTestCase(NaayaFunctionalTestCase):
    """ EditingTestCase for NyMeeting object """

    def afterSetUp(self):
        self.portal.manage_install_pluggableitem('Naaya Meeting')
        from naaya.content.meeting.meeting_item import addNyMeeting
        addNyMeeting(self.portal.info, 'mymeeting', contributor='contributor', submitted=1,
            title='MyMeeting', location='Kogens Nytorv 6, 1050 Copenhagen K, Denmark',
            releasedate='16/06/2010', start_date='20/06/2010', end_date='25/06/2010',
            contact_person='My Name', contact_email='my.email@my.domain')
        addNyMeeting(self.portal.info, 'mymeeting2', contributor='contributor', submitted=1,
            title='MyMeeting', location='Kogens Nytorv 6, 1050 Copenhagen K, Denmark',
            releasedate='16/06/2010', start_date='20/06/2010', end_date='25/06/2010',
            contact_person='My Name', contact_email='my.email@my.domain')
        self.portal.info.mymeeting.approveThis()
        self.portal.info.mymeeting2.approveThis()
        import transaction; transaction.commit()

    def beforeTearDown(self):
        self.portal.info.manage_delObjects(['mymeeting', 'mymeeting2'])
        self.portal.manage_uninstall_pluggableitem('Naaya Meeting')
        import transaction; transaction.commit()

    def test_edit(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting'))
        
        self.browser_do_login('admin', '')
        self.browser.go('http://localhost/portal/info/mymeeting/edit_html')
        self.assertTrue('<h1>Edit Meeting</h1>' in self.browser.get_html())

        form = self.browser.get_form('frmEdit')
        self.assertEqual(form['title:utf8:ustring'], 'MyMeeting')
        self.assertEqual(form['location:utf8:ustring'], 'Kogens Nytorv 6, 1050 Copenhagen K, Denmark')
        self.assertEqual(form['releasedate'], '16/06/2010')
        self.assertEqual(form['start_date'], '20/06/2010')
        self.assertEqual(form['end_date'], '25/06/2010')
        self.assertEqual(form['contact_person:utf8:ustring'], 'My Name')
        self.assertEqual(form['contact_email:utf8:ustring'], 'my.email@my.domain')

        self.browser.clicked(form, self.browser.get_form_field(form, 'title'))
        form['title:utf8:ustring'] = 'MyEditedMeeting'
        form['location:utf8:ustring'] = 'Kogens Nytorv 8, 1050 Copenhagen K, Denmark'
        form['releasedate'] = '17/06/2010'
        form['start_date'] = '21/06/2010'
        form['end_date'] = '26/06/2010'
        form['contact_person:utf8:ustring'] = 'My Edited Name'
        form['contact_email:utf8:ustring'] = 'my.edited.email@my.domain'
        self.browser.submit()
        self.browser.go('http://localhost/portal/info/mymeeting')
        html = self.browser.get_html()
        self.assertTrue('MyEditedMeeting' in html)
        self.assertTrue('[21/06/2010 - 26/06/2010]' in html)
        self.assertTrue('My Edited Name' in html)
        self.assertTrue('mailto:my.edited.email@my.domain' in html)
        self.assertTrue('http://localhost/portal/info/mymeeting/get_ics' in html)
        self.assertTrue('17/06/2010' in html)
        self.assertTrue('contributor' in html)
        self.assertTrue('Kogens Nytorv 8, 1050 Copenhagen K, Denmark' in html)

        self.browser_do_logout()

    def test_edit_error(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting'))
        
        self.browser_do_login('admin', '')
        self.browser.go('http://localhost/portal/info/mymeeting/edit_html')
        form = self.browser.get_form('frmEdit')
        self.browser.clicked(form, self.browser.get_form_field(form, 'title:utf8:ustring'))
        form['title:utf8:ustring'] = ''
        self.browser.submit()
        html = self.browser.get_html()
        self.assertTrue('The form contains errors' in html)
        self.assertTrue('Value required for "Title"' in html)

        self.browser_do_logout()

    def test_manage_edit(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting2'))
        
        self.browser_do_login('admin', '')
        self.browser.go('http://localhost/portal/info/mymeeting2/manage_edit_html')
        self.assertTrue('Naaya Meeting' in self.browser.get_html())

        form = self.browser.get_form('frmEdit')
        self.assertEqual(form['title:utf8:ustring'], 'MyMeeting')
        self.assertEqual(form['location:utf8:ustring'], 'Kogens Nytorv 6, 1050 Copenhagen K, Denmark')
        self.assertEqual(form['releasedate'], '16/06/2010')
        self.assertEqual(form['start_date'], '20/06/2010')
        self.assertEqual(form['end_date'], '25/06/2010')
        self.assertEqual(form['contact_person:utf8:ustring'], 'My Name')
        self.assertEqual(form['contact_email:utf8:ustring'], 'my.email@my.domain')

        self.browser.clicked(form, self.browser.get_form_field(form, 'title'))
        form['title:utf8:ustring'] = 'MyEditedMeeting'
        form['location:utf8:ustring'] = 'Kogens Nytorv 8, 1050 Copenhagen K, Denmark'
        form['releasedate'] = '17/06/2010'
        form['start_date'] = '21/06/2010'
        form['end_date'] = '26/06/2010'
        form['contact_person:utf8:ustring'] = 'My Edited Name'
        form['contact_email:utf8:ustring'] = 'my.edited.email@my.domain'
        self.browser.submit()
        self.browser.go('http://localhost/portal/info/mymeeting2')
        html = self.browser.get_html()
        self.assertTrue('MyEditedMeeting' in html)
        self.assertTrue('[21/06/2010 - 26/06/2010]' in html)
        self.assertTrue('My Edited Name' in html)
        self.assertTrue('mailto:my.edited.email@my.domain' in html)
        self.assertTrue('http://localhost/portal/info/mymeeting2/get_ics' in html)
        self.assertTrue('17/06/2010' in html)
        self.assertTrue('contributor' in html)
        self.assertTrue('Kogens Nytorv 8, 1050 Copenhagen K, Denmark' in html)

        self.browser_do_logout()


class NyMeetingFunctionalTestCase(NaayaFunctionalTestCase):
    """ FunctionalTestCase for NyMeeting object """

    def afterSetUp(self):
        self.portal.manage_install_pluggableitem('Naaya Meeting')
        from naaya.content.meeting.meeting_item import addNyMeeting
        addNyMeeting(self.portal.info, 'mymeeting', contributor='contributor', submitted=1,
            title='MyMeeting', location='Kogens Nytorv 6, 1050 Copenhagen K, Denmark',
            releasedate='16/06/2010', start_date='20/06/2010', end_date='25/06/2010',
            contact_person='My Name', contact_email='my.email@my.domain')
        self.portal.info.mymeeting.approveThis()
        self.portal.recatalogNyObject(self.portal.info.mymeeting)
        import transaction; transaction.commit()

    def beforeTearDown(self):
        self.portal.info.manage_delObjects(['mymeeting'])
        self.portal.manage_uninstall_pluggableitem('Naaya Meeting')
        import transaction; transaction.commit()

    def test_index(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting'))

        self.browser.go('http://localhost/portal/info/mymeeting')
        html = self.browser.get_html()
        self.assertTrue('MyMeeting' in html)
        self.assertTrue('[20/06/2010 - 25/06/2010]' in html)
        self.assertTrue('My Name' in html)
        self.assertTrue('mailto:my.email@my.domain' in html)
        self.assertTrue('http://localhost/portal/info/mymeeting/get_ics' in html)
        self.assertTrue('16/06/2010' in html)
        self.assertTrue('contributor' in html)
        self.assertTrue('Kogens Nytorv 6, 1050 Copenhagen K, Denmark' in html)

    def test_feed(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting'))

        self.browser.go('http://localhost/portal/portal_syndication/latestuploads_rdf')
        html = self.browser.get_html()
        self.assertTrue('MyMeeting' in html)
        self.assertTrue('http://localhost/portal/info/mymeeting' in html)
        self.assertTrue('Kogens Nytorv 6, 1050 Copenhagen K, Denmark' in html)
        self.assertTrue('My Name' in html)


    def test_search_for_new_participants(self):
        self.assertTrue(hasattr(self.portal.info, 'mymeeting'))

        self.browser_do_login('admin', '')
        self.browser.go('http://localhost/portal/info/mymeeting')
        self.assertTrue('http://localhost/portal/info/mymeeting/edit_participants' in self.browser.get_html())

        self.browser.go('http://localhost/portal/info/mymeeting/edit_participants')
        form = self.browser.get_form('formSearchUsers')
        expected_controls = set(['search_param', 'search_term:utf8:ustring', 'search_user'])
        found_controls = set(c.name for c in form.controls)
        self.assertTrue(expected_controls <= found_controls,
            'Missing form controls: %s' % repr(expected_controls - found_controls))

        self.browser.clicked(form, self.browser.get_form_field(form, 'search_term:utf8:ustring'))
        form['search_term:utf8:ustring'] = 'contributor'
        self.browser.submit()

        form = self.browser.get_form('formAddUsers')
        expected_controls = set(['uid', 'add_users'])
        found_controls = set(c.name for c in form.controls)
        self.assertTrue(expected_controls <= found_controls,
            'Missing form controls: %s' % repr(expected_controls - found_controls))

        self.browser_do_logout()

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(NyMeetingCreateTestCase))
    suite.addTest(makeSuite(NyMeetingEditingTestCase))
    suite.addTest(makeSuite(NyMeetingFunctionalTestCase))
    return suite

