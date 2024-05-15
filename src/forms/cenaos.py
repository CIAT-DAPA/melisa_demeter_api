import gspread
from google.oauth2.service_account import Credentials

class GoogleSheetManager:
    def __init__(self, spreadsheet_name, sheet_name, credentials_file):
        self.spreadsheet_name = spreadsheet_name
        self.sheet_name = sheet_name
        self.credentials_file = credentials_file
        self.gc = self.authenticate()

    def authenticate(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
        return gspread.authorize(credentials)

    def open_sheet(self):
        return self.gc.open(self.spreadsheet_name).worksheet(self.sheet_name)

    def write_headers(self, headers):
        sheet = self.open_sheet()
        sheet.update('A1:C1', [headers])

    def write_data(self, data):
        sheet = self.open_sheet()
        for row_data in data:
            sheet.append_row(row_data)

    def get_available_sheets(self):
        spreadsheet = self.gc.open(self.spreadsheet_name)
        return [sheet.title for sheet in spreadsheet.worksheets()]