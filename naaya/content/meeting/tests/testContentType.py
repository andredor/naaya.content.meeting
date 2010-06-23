# Authors:
# Alin Voinea, Eau de Web
# Andrei Laza, Eau de Web

from unittest import TestSuite, makeSuite
from naaya.content.meeting.meeting import addNyMeeting as addNaayaContent
from naaya.content.meeting.meeting import NyMeeting as NaayaContent
from Products.Naaya.tests import NaayaTestCase

class NaayaContentTestCase(NaayaTestCase.NaayaTestCase):
    """ TestCase for NaayaContent object
    """
    def afterSetUp(self):
        self.doc_name_en = 'mycontent_en'
        self.doc_name_fr = "mycontent_fr"
        self.doc_meta_type = NaayaContent.meta_type
        self.doc_start_date = '16/06/2010'
        self.login()
        
    def beforeTearDown(self):
        del self.doc_name_en
        del self.doc_name_fr
        del self.doc_meta_type
        del self.doc_start_date
        self.logout()

    def test_main(self):
        """ Add, Find, Edit and Delete Naaya Contact """
        #add Naaya Content
        addNaayaContent(self._portal().info, title=self.doc_name_en, lang='en', start_date=self.doc_start_date, contact_email='email@email.com')
        addNaayaContent(self._portal().info, title=self.doc_name_fr, lang='fr', start_date=self.doc_start_date, contact_email='email@email.com')
        
        meta = self._portal().getCatalogedObjectsCheckView(meta_type=[self.doc_meta_type,])
        
        #Get added content
        for x in meta:
            if x.getLocalProperty('title', 'en') == self.doc_name_en:
                meta = x
            if x.getLocalProperty('title', 'fr') == self.doc_name_fr:
                meta_fr = x
        
        self.assertEqual(meta.getLocalProperty('title', 'en'), self.doc_name_en)
        self.assertEqual(meta_fr.getLocalProperty('title', 'fr'), self.doc_name_fr)
        
        #Change content title
        title_en = self.doc_name_en + '_edited'
        title_fr = self.doc_name_fr + 'edited'
        meta.saveProperties(title=title_en, lang='en', start_date=self.doc_start_date, contact_email='email@email.com')
        meta_fr.saveProperties(title=title_fr, lang='fr', start_date=self.doc_start_date, contact_email='email@email.com')
        
        self.assertEqual(meta.getLocalProperty('title', 'en'), title_en)
        self.assertEqual(meta_fr.getLocalProperty('title', 'fr'), title_fr)
        
        #delete NyNews
        self._portal().info.manage_delObjects([meta.id])
        self._portal().info.manage_delObjects([meta_fr.id])
        
        meta = self._portal().getCatalogedObjectsCheckView(meta_type=[self.doc_meta_type,])
        
        self.assertEqual(meta, [])

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(NaayaContentTestCase))
    return suite
