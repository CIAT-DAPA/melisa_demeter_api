import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

class GoogleSheetManager:
    def __init__(self, spreadsheet_name, credentials_file):
        self.spreadsheet_name = spreadsheet_name
        self.credentials_file = credentials_file
        self.gc = self.authenticate()
        if self.gc is not None:
            print("GoogleSheetManager instance initialized successfully")

    def authenticate(self):
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            gc = gspread.authorize(credentials)
            return gc
        except Exception as e:
            print(f"Failed to initialize GoogleSheetManager instance: {e}")
            return None

    def open_sheet(self, sheet_name):
        return self.gc.open(self.spreadsheet_name).worksheet(sheet_name)

    def write_headers(self, sheet_name, headers):
        sheet = self.open_sheet(sheet_name)
        sheet.update('A1', [headers])  

    def write_data(self, sheet_name, data):
        sheet = self.open_sheet(sheet_name)
        for row_data in data:
            
            if isinstance(row_data[0], str) and len(row_data[0]) == 10 and row_data[0][4] == '-' and row_data[0][7] == '-':
                row_data[0] = datetime.strptime(row_data[0], "%Y-%m-%d").date()

            
            row_data = [float(item) if isinstance(item, str) and item.replace('.', '', 1).isdigit() else item for item in row_data]
            
            sheet.append_row(row_data)

    def get_available_sheets(self):
        print("Getting available sheets...")
        spreadsheet = self.gc.open(self.spreadsheet_name)
        return [sheet.title for sheet in spreadsheet.worksheets()]

    def sum_precipitation_for_date(self, sheet_name, date):
        sheet = self.open_sheet(sheet_name)
        records = sheet.get_all_records()
        print(f"The records are: {records}")
        hours = ["06:00", "12:00", "18:00", "00:00"]
        hours_found = {hour: False for hour in hours}

        print("Comparing date:", date)  

        for record in records:
            if record['Fecha']: 
                record_date, record_time = record['Fecha'].split()
                record_time = record_time.strip()  
                
                if record_date == date:
                    print("record matched date")  
                    if record_time in hours and record['variable'] == 'Prep':
                        hours_found[record_time] = True
                    else:
                        print("record time not in hours or variable not Prep")  
            else:
                print("field Fecha is empty in the record!")  

        print("Horas encontradas:", hours_found)

        missing_hours = [hour for hour, found in hours_found.items() if not found]
        print("Horas faltantes:", missing_hours)

        if missing_hours:
            print(f"missins values of precipitation for the folowing dates in the date {date}: {', '.join(missing_hours)}")

        return missing_hours


    def calculate_min_max_avg_temp(self, sheet_name, date):
        sheet = self.open_sheet(sheet_name)
        records = sheet.get_all_records()
        hours = ["06:00", "12:00", "18:00", "00:00"]
        hours_found = {hour: False for hour in hours}

        for record in records:
            if record['Fecha']: 
                record_date, record_time = record['Fecha'].split()
                record_time = record_time.strip()
                if record_date == date and record_time in hours and record['variable'] == 'Temp':
                    hours_found[record_time] = True
            else:
                print("field Fecha is empty in the record!")

        missing_hours = [hour for hour, found in hours_found.items() if not found]

        if missing_hours:
            print(f" missins values of temperature for the folowing dates in the date  {date}: {', '.join(missing_hours)}")

        return missing_hours


    def write_data_dinamic(self, sheet_name, data):
        sheet = self.open_sheet(sheet_name)
        for row_data in data:
            row_data = [float(item) if isinstance(item, str) and item.replace('.', '', 1).isdigit() else item for item in row_data]
            sheet.append_row(row_data)
        
        fila_datos = len(sheet.col_values(1))  

       
        column_total_prep = 6  
        column_avg_temp = 11 

        try:
            sheet.update_cell(fila_datos, column_total_prep, f'=SUM(B{fila_datos}:E{fila_datos})')
            sheet.update_cell(fila_datos, column_avg_temp, f'=(MIN(G{fila_datos}:J{fila_datos}) + MAX(G{fila_datos}:J{fila_datos})) / 2')
        except gspread.exceptions.APIError as e:
            print("Error updating the field", e.response.text)
























