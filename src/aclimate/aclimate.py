import pandas as pd
from aclimate.catalog import Catalog
from aclimate.forecast import ForecastData
from aclimate.historical import HistoricalData
from nlg.reply import Reply, ReplyGeographicEnum, ReplyErrorEnum, ReplyCultivarsEnum, ReplyHistoricalEnum, ReplyForecastEnum

class AClimate:

    def __init__(self, url, countries):
        self.url_base = url
        self.countries = countries
        self.headers = {'Content-Type': 'application/json'}
        self.catalog = Catalog(url, self.headers)
        self.forecast = ForecastData(url, self.headers)
        self.historical_data = HistoricalData(url, self.headers)

    # Method that search geographic places
    # (str) locality: List of entities found in the message user
    def geographic(self, locality):
        answer = []
        data = self.catalog.get_Geographic(self.countries)
        # Check if could connect with aclimate
        if data is None:
            answer.append(Reply(ReplyErrorEnum.ERROR_ACLIMATE))
        else:
            # This section adds the list of localities
            l = locality
            e_data = data.loc[data["state_name"].str.contains(l.lower(), case = False), :]
            # Check if the message has state name in order to send the municipalities
            if(e_data.shape[0] > 0):
                answer.append(Reply(ReplyGeographicEnum.MUNICIPALITIES_STATE, e_data.loc[:,"municipality_name"].unique(), l))
            else:
                e_data = data.loc[data["municipality_name"].str.contains(l.lower(), case = False),: ]
                # Check if message has municipality name in order to send weather stations
                if(e_data.shape[0] > 0):
                    answer.append(Reply(ReplyGeographicEnum.WS_MUNICIPALITY, e_data.loc[:,"ws_name"].unique(),l))
                else:
                    e_data = data.loc[data["ws_name"].str.contains(l.lower(), case = False),: ]
                    # Check if message has weather station name in order to send the ws found
                    if(e_data.shape[0] > 0):
                        answer.append(Reply(ReplyGeographicEnum.WEATHER_STATION, e_data.loc[:,"ws_name"].unique(),l))
        return answer

    # Method that search cultivars available
    # (str) crop: crop to filter
    # (str) cultivar: cultivar to filter
    def cultivars(self, crop = None, cultivar = None):
        answer = []
        data = self.catalog.get_Cultivars()
        if data is None:
            answer.append(Reply(ReplyErrorEnum.ERROR_ACLIMATE))
        else:
            # Entities weren't found
            if not crop and not cultivar:
                answer.append(Reply(ReplyCultivarsEnum.CROP_MULTIPLE, data.loc[:,"cp_name"].unique()))
            # Entities were found
            elif crop:
                e_data = data.loc[data["cp_name"].str.contains(crop.lower(), case=False), :]
                answer.append(Reply(ReplyCultivarsEnum.CROP_CULTIVAR, e_data.loc[:,"cu_name"].unique(), crop))
            elif cultivar:
                e_data = data.loc[data["cu_name"].str.contains(cultivar.lower(), case=False),: ]
                answer.append(Reply(ReplyCultivarsEnum.CULTIVARS_MULTIPLE, e_data.loc[:,"cu_name"].unique(), cultivar))
        return answer

    # Method that search climatology
    # (dataframe) entities: List of entities found in the message user
    def historical_climatology(self, locality, measure = None, date = None):
        answer = []
        # Entities were found
        # Get the localities
        geographic = self.catalog.get_Geographic(self.countries)
        if geographic is None:
            answer.append(Reply(ReplyErrorEnum.ERROR_ACLIMATE))
        else:
            ws_data = pd.DataFrame()
            # This loop figure out all localtities through: states, municipalities and ws, which are into the message
            ws_data = self.get_ws(locality, geographic)
            # Check if the ws were found
            if ws_data.shape[0] > 0:
                ws_id = ws_data["ws_id"].unique()
                ws = ','.join(ws_id)
                # Ask for the historical data
                climatology = self.historical_data.get_Climatology(ws)
                if climatology is None:
                    answer.append(Reply(type = ReplyErrorEnum.ERROR_ACLIMATE_CLIMATOLOGY, tag = locality))
                else:
                    df = pd.merge(climatology, geographic, on='ws_id', how='inner')
                    # Filter by measure
                    if measure:
                        dft = pd.DataFrame()
                        dft = dft.append(df.loc[df["measure"] == self.get_measure_from_entities(measure),:], ignore_index=True)
                        if(dft.shape[0] > 0):
                            df = dft
                    # Filter by months
                    if date:
                        m_n = self.get_month_from_entities(date)
                        if(len(m_n) >= 0):
                            m_n = m_n + 1
                            df = df.loc[df["month"].isin(m_n),:]
                    # Add all answers
                    answer.append(Reply(ReplyHistoricalEnum.CLIMATOLOGY, df, locality))
            else:
                answer.append(Reply(ReplyErrorEnum.LOCALITY_NOT_FOUND,tag = locality))
        return answer

    # Method that search climate forecast
    # (dataframe) entities: List of entities found in the message user
    def forecast_climate(self, locality):
        answer = []
        # Entities were found
        #if (len(entities) > 0):
        # Get the localities
        geographic = self.catalog.get_Geographic(self.countries)
        if geographic is None:
            answer.append(Reply(ReplyErrorEnum.ERROR_ACLIMATE))
        else:
            ws_data = pd.DataFrame()
            # This loop figure out all localtities through: states, municipalities and ws, which are into the message
            ws_data = self.get_ws(locality, geographic)

            # Check if the ws were found
            if(ws_data.shape[0] > 0):
                ws_id = ws_data["ws_id"].unique()
                ws = ','.join(ws_id)
                # Ask for the forecast data
                forecast = self.forecast.get_Climate(ws)
                if forecast is None:
                    answer.append(Reply(type = ReplyErrorEnum.ERROR_ACLIMATE_FORECAST_CLIMATE, tag = locality))
                else:
                    df = pd.merge(forecast, geographic, on='ws_id', how='inner')
                    answer.append(Reply(ReplyForecastEnum.CLIMATE, df))
            else:
                answer.append(Reply(ReplyErrorEnum.LOCALITY_NOT_FOUND,tag=locality))
        return answer

    # Method that search yield forecast
    # (dataframe) entities: List of entities found in the message user
    def forecast_yield(self, entities, best_date = False):
        answer = []        
        # Entities were found
        #if (len(entities) > 0):            
        # Get the localities
        geographic = self.catalog.get_Geographic(self.countries)
        cultivars = self.catalog.get_Cultivars()
        soils = self.catalog.get_Soils()
        if geographic is None or cultivars is None or soils is None:
            answer.append(NER(Error.ERROR_ACLIMATE))
        else:
            ws_data = pd.DataFrame()
            # Try to search if locality was reconigzed
            if "locality" in entities.keys():                
                # This loop figure out all localtities through: states, municipalities and ws, which are into the message
                l = entities["locality"]
                ws_data = self.get_ws(l, geographic)
            
                # Check if the ws were found
                if(ws_data.shape[0] > 0):
                    ws_id = ws_data["ws_id"].unique()
                    ws = ','.join(ws_id)
                    # Ask for the forecast data
                    forecast = self.forecast.get_Yield(ws)
                    if forecast is None:
                        answer.append(NER(type = Error.ERROR_ACLIMATE_FORECAST_YIELD, tag = l))
                    else:
                        df = pd.merge(forecast, geographic, on='ws_id', how='inner')
                        df = pd.merge(df, cultivars, on='cu_id', how='inner')
                        df = pd.merge(df, soils, on='so_id', how='inner')
                        # Filtering by cultivar
                        filter_cultivar = False
                        if "cultivar" in entities.keys():
                            cu = entities["cultivar"] 
                            dft = df.loc[df["cu_name"].str.contains(cu.lower(), case = False) ,:]
                            if(dft.shape[0] > 0):
                                df = dft
                                filter_cultivar = True
                        # Filter by crop if couldn't filter by cultivar
                        if(filter_cultivar == False and "crop" in entities.keys()):
                            cp = entities["crop"]
                            dft = df.loc[df["cp_name"].str.contains(cp.lower(), case = False) ,:]
                            if(dft.shape[0] > 0):
                                df = dft
                        # Filter by measure
                        df = df.loc[df["measure"].isin(["yield_14", "yield_0"]),:]
                        # Top five by crop 
                        crops = df["cp_name"].unique().tolist()
                        for c in crops:
                            amount = 5
                            type_answer = Forecast.YIELD_PERFORMANCE
                            dft = pd.DataFrame()
                            if best_date:
                                amount = 1
                                type_answer = Forecast.YIELD_DATE
                                stations = df["ws_id"].unique().tolist()
                                for s in stations:
                                    d_local = df.loc[df["cp_name"] == str(c) ,:]
                                    d_local = d_local.loc[ d_local["ws_id"] == str(s),:]
                                    dft = dft.append(d_local.nlargest(amount,"avg"), ignore_index = True)    
                            else:
                                dft = df.loc[df["cp_name"] == c,:].nlargest(amount,"avg")
                            answer.append(NER(type_answer, dft))
                else:
                    answer.append(NER(Error.LOCALITY_NOT_FOUND,None,l))        
            else:
                answer.append(NER(Error.MISSING_GEOGRAPHIC))
        #else:
            #answer.append(NER(Error.MISSING_ENTITIES))
        return answer

    # Method that returns the measure according to aclimate platform depending of request
    # (string) value: Value to search
    def get_measure_from_entities(self, value):
        ms = 'prec'
        if('sol' in value.lower() or 'rad' in value.lower()):
            ms = 'sol_rad'
        elif ('temp' in value.lower() or 'tmp' in value.lower()):
            if('mín' in value.lower() or 'min' in value.lower() or 'mn' in value.lower()):
                ms = 't_min'
            else:
                ms = 't_max'
        return ms

    # Method that return the index of a month
    # (string) value: Name of month
    def get_month_from_entities(self, value):
        mo = -1
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        mo = [i for i, e in months if  e in value.lower()]
        return mo

    # Method that search ws names and ids into geographic data
    # (string) name: Name of the weather station
    # (dataframe) geographic: List of all geographic
    def get_ws(self, name, geographic):
        # Search by weather station, muncipality and state names
        names = name.split("_")
        ws_data = pd.DataFrame()
        for n in names:
            ws = geographic.loc[ (geographic["ws_name"].str.contains(n.lower(), case = False) | geographic["state_name"].str.contains(n.lower(), case = False) | geographic["municipality_name"].str.contains(n.lower(), case = False)), ["ws_id","ws_name"]]
            if ws.shape[0] > 0:
                ws_data = ws_data.append(ws, ignore_index=True)
        return ws_data


