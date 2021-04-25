# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from googleapiclient.discovery import build
import google.oauth2.credentials
import re

logger = logging.getLogger(__name__)

def get_google_spreadsheets(access_token):
    credentials = google.oauth2.credentials.Credentials(access_token)
    service = build('sheets', 'v4', credentials=credentials)
    sheets = service.spreadsheets()
    return sheets

class Spreadsheet(models.Model):
    _name = 'terralab.spreadsheet'
    _inherit = ['mail.thread']
    _description = 'TerraLab Spreadsheet'

    name = fields.Char(track_visibility='onchange')
    spreadsheet_url = fields.Char(track_visibility='onchange')
    spreadsheet_id = fields.Char(track_visibility='onchange')
    test_types = fields.One2many('terralab.testtype', 'spreadsheet', 'Test Types', track_visibility='onchange') # Test Types attached to this spreadsheet

    def write(self, values):
        new_url = values.get('spreadsheet_url', None)
        if new_url:
            # Extract spreadsheet ID
            m = re.match(r'.*/([^/]+)/edit.*', new_url)
            logger.info('Matches: %s' % (m))
            if m:
                values['spreadsheet_id'] = m.group(1)
        super(Spreadsheet, self).write(values)
        logger.info('Writing Spreadsheet %s' % (values))
        return True

    def calculate_result(self, test_type, submitted_test_variables):
        access_token = self.env['google.drive.config'].get_access_token(scope='https://spreadsheets.google.com/feeds')
        spreadsheets = get_google_spreadsheets(access_token)
        logger.info('Calculating spreadsheet %s test result with submitted variables: %s' % (self.spreadsheet_id, submitted_test_variables))
        # Set input variables
        # XXX - Could we combine these to a single update() call?
        for submitted_test_variable in submitted_test_variables:
            logger.info('Setting input variable %s=%s' % (submitted_test_variable.test_variable.spreadsheet_input_ref, submitted_test_variable.value))
            update_result = spreadsheets.values().update(spreadsheetId=self.spreadsheet_id, range=submitted_test_variable.test_variable.spreadsheet_input_ref, valueInputOption='USER_ENTERED', body={'values':[[submitted_test_variable.value]]}).execute()
            logger.info('Update result: %s' % (update_result))
        # Retrieve result variable
        result = spreadsheets.values().get(spreadsheetId=self.spreadsheet_id, range=test_type.terralab_spreadsheet_result_ref).execute()
        values = result.get('values', [])
        logger.info('RESULT VALUES: %s' % (values))
        return values[0][0]
