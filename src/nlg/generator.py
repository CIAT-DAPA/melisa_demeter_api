import pandas as pd
from nlg.reply import ReplyKindEnum,ReplyErrorEnum,ReplyGeographicEnum,ReplyCultivarsEnum,ReplyHistoricalEnum,ReplyForecastEnum,ReplyFormEnum,ReplyFormCroppieEnum
from nlg.reply_system import ReplySystem

class Generator():


    # Method that return an answer for the users
    # (NER[]) answers: List of answers
    @staticmethod
    def print(answers):
        decimals = 0
        sys_answers = []

        for a in answers:
            #print(a[0])
            msg = []
            slots = None
            # Commands
            if isinstance(a.type, ReplyKindEnum):
                if a.type == ReplyKindEnum.HI:
                    msg.append("Hola, ¿cómo puedo ayudarte?")
                elif a.type == ReplyKindEnum.HELP:
                    msg.append("Puedes preguntarme sobre información histórica de clima, también sobre predicción de clima y producción de cultivos")
                    msg.append("Si quieres saber que localidades hay disponibles podrías preguntar algo como: Municipios disponibles")
                    msg.append("Si quieres saber sobre que cultivos hay disponibles, podrías intentar algo como: ¿Qué cultivos hay disponibles?")
                    msg.append("Si quieres saber sobre como será el clima para la próxima temporada, podrías intentar algo como: ¿Cuál es el pronóstico climático para Palmira?")
                    msg.append("Si quieres saber sobre como será el rendimiento de algún cultivo, podrías intentar algo como: ¿Cuál es la predicción de rendimiento para maíz en Cerete?")
                    msg.append("Tranquil@, pregunta como quieras, Yo estoy para ayudarte")
                elif a.type == ReplyKindEnum.BYE:
                    msg.append("Chao :)")
                elif a.type == ReplyKindEnum.THANKS:
                    msg.append("Con mucho gusto")
                elif a.type == ReplyKindEnum.NEW_USER:
                    msg.append("Hola, soy Melisa, un bot que provee información climática y agroclimática")
                    msg.append("Si no sabes como iniciar enviame el mensaje: ayuda")
                elif a.type == ReplyKindEnum.WAIT:
                    msg.append("Estoy procesando tu solicitud")
            # Geographic answers
            elif (isinstance(a.type, ReplyGeographicEnum)):
                if(a.type == ReplyGeographicEnum.STATE):
                    msg.append("Los departamentos disponibles son: " + ', '.join(a.values))
                elif(a.type == ReplyGeographicEnum.MUNICIPALITIES_STATE):
                    msg.append("Los municipios para el departamento " + a.tag + " disponibles son: " + ', '.join(a.values))
                elif(a.type == ReplyGeographicEnum.WS_MUNICIPALITY):
                    msg.append("Las estaciones climáticas para el municipio " + a.tag + " disponibles son: " + ', '.join(a.values))
                elif(a.type == ReplyGeographicEnum.WEATHER_STATION):
                    msg.append("En el municipio " + a.tag + " están las estaciones: " +  ', '.join(a.values))
            # Cultivars answers
            elif (isinstance(a.type, ReplyCultivarsEnum)):
                if(a.type == ReplyCultivarsEnum.CROP_MULTIPLE):
                    #msg.append("Los cultivos disponibles son: " + ', '.join(a.values))
                    msg.append("Los cultivos disponibles son: " + 'Arroz y Maíz')
                elif(a.type == ReplyCultivarsEnum.CROP_CULTIVAR):
                    msg.append("Las variedades para el cultivo " + a.tag + " disponibles son: " + ', '.join(a.values))
                elif(a.type == ReplyCultivarsEnum.CULTIVARS_MULTIPLE):
                    msg.append("Las variedades similares a " + a.tag + " disponibles son: " + ', '.join(a.values))
            # Historical answers
            elif (isinstance(a.type, ReplyHistoricalEnum)):
                # Climatology answers
                if(a.type == ReplyHistoricalEnum.CLIMATOLOGY):
                    # Get ws ids
                    ws_id = a.values.loc[:,"ws_id"].unique()
                    for ws in ws_id:
                        # Filter by ws_id
                        cl_ws = a.values.loc[a.values["ws_id"] == ws,:]
                        m = "Para la estación " + cl_ws.iloc[0]["ws_name"] + ", la climatología es: "
                        # Get measures
                        #msg.append(m)
                        cl_var = cl_ws.loc[:,"measure"].unique().tolist()
                        # Remove climatology for terciles
                        if "prec_ter_1" in cl_var:
                            cl_var.remove("prec_ter_1")
                        if "prec_ter_2" in cl_var:
                            cl_var.remove("prec_ter_2")
                        for v in cl_var:
                            #m = ""
                            m_name = Generator.get_climate_measure(v) + " (" + Generator.get_climate_unit(v) + ") "
                            m = m + m_name + ": "
                            cl_measure = cl_ws.loc[cl_ws["measure"] == v,:]
                            # List according to measure
                            for me in cl_measure.itertuples(index=True, name='Pandas') :
                                m = m + Generator.get_month(getattr(me, "month")) + " " + str(int(getattr(me, "value"))) + ", "
                            #msg.append(m[:-2])
                            m = m[:-2] + ". "
                        msg.append(m)
            # Forecast answer
            elif (isinstance(a.type, ReplyForecastEnum)):
                # Climate answers
                if(a.type == ReplyForecastEnum.CLIMATE):
                    # Get ws ids
                    ws_id = a.values.loc[:,"ws_id"].unique()
                    for ws in ws_id:
                        # Filter by ws_id
                        cl_ws = a.values.loc[a.values["ws_id"] == ws,:]
                        m = "Para la estación " + cl_ws.iloc[0]["ws_name"] + ", la predicción climática es: "
                        #msg.append(m)
                        #print(cl_ws.head())
                        for w in cl_ws.itertuples(index=True, name='Pandas') :
                            m = m + "para el trimestre "
                            m = m + Generator.get_month(getattr(w, "month")-1) + "-" + Generator.get_month(getattr(w, "month")) + "-" + Generator.get_month(getattr(w, "month")+1) + ": " 
                            m = m + "por encima de lo normal = " + str(round(getattr(w, "upper") * 100.0,decimals)) + "%, "
                            m = m + "por dentro de lo normal = " + str(round(getattr(w, "normal") * 100.0,decimals)) + "%, "
                            m = m +"por debajo de lo normal = " + str(round(getattr(w, "lower") * 100.0,decimals)) + "% "
                            #msg.append(m)
                        msg.append(m)
                # yield answers
                elif a.type == ReplyForecastEnum.YIELD_PERFORMANCE:
                    # Get ws ids
                    ws_id = a.values.loc[:,"ws_id"].unique()
                    for ws in ws_id:
                        # Filter by ws_id
                        cp_ws = a.values.loc[a.values["ws_id"] == ws,:]
                        crops = cp_ws["cp_name"].unique()
                        for cp in crops:
                            m = "Para la estación " + cp_ws.iloc[0]["ws_name"] + ", encontramos que el cultivo " + cp + " presenta las siguientes variedades con mejor rendimiento potencial: "
                            #msg.append(m)
                            cu_ws = cp_ws.loc[cp_ws["cp_name"] == cp,:]
                            cultivars = cu_ws["cu_name"].unique()
                            for cu in cultivars:
                                cp_cu_data = cu_ws.loc[cu_ws["cu_name"] == cu,:]
                                m = m + cu + ": "
                                for ccd in cp_cu_data.itertuples(index=True, name='Pandas'):
                                    m = m + "sembrando en " + str(getattr(ccd, "start"))[:-10] + ", tipo de suelo " + getattr(ccd, "so_name") + " "
                                    m = m + "puedes obtener en promedio: " + str(round(getattr(ccd, "avg"),decimals)) + " kg/ha, "
                                    m = m + "variando entre máx. " + str(round(getattr(ccd, "max"),decimals)) + " kg/ha "
                                    m = m + "y mín. " + str(round(getattr(ccd, "min"),decimals)) + " kg/ha. "
                                #msg.append(m)
                            msg.append(m)
                # yield answers
                elif a.type == ReplyForecastEnum.YIELD_DATE:
                    # Get ws ids
                    ws_id = a.values.loc[:,"ws_id"].unique()
                    for ws in ws_id:
                        # Filter by ws_id
                        cp_ws = a.values.loc[a.values["ws_id"] == ws,:]
                        crops = cp_ws["cp_name"].unique()
                        for cp in crops:
                            m = "Para la estación " + cp_ws.iloc[0]["ws_name"] + ", encontramos que las mejores fechas de siembra para el cultivo " + cp + " son: "
                            #msg.append(m)
                            for ccd in cp_ws.itertuples(index=True, name='Pandas'):
                                m = m + "la variedad " + getattr(ccd, "cu_name") + ", en un suelo " +  getattr(ccd, "so_name") + " "
                                m = m + "y sembrando en " + str(getattr(ccd, "start"))[:-10] + " "
                                m = m + " puedes obtener en promedio: " + str(round(getattr(ccd, "avg"),decimals)) + " kg/ha. "
                            msg.append(m)
            # Message Form
            elif (isinstance(a.type, ReplyFormEnum)):
                if(a.type == ReplyFormEnum.RECEIVED_OK):
                    msg.append("Recibido")
                elif(a.type == ReplyFormEnum.RECEIVED_ERROR):
                    msg.append("Error al registrar")
                elif(a.type == ReplyFormEnum.QUESTION):
                    msg.append(a.values)
                    slots = a.tag
                elif(a.type == ReplyFormEnum.RECEIVED_DATA_SHEET):
                    msg.append("Proceso Finalizado con exito")
            elif (isinstance(a.type, ReplyFormCroppieEnum)):
                if(a.type == ReplyFormCroppieEnum.FINISHED_ESTIMATION):
                    msg.append("El rendimiento estimado es: " + str(int(a.values['estimated_yield_total'])) + " El Rendimento estimado en cafe pergamino es: " +str(int(a.values['estimated_yield_parch']))+ " y su estimado en cafe verde es: " +str(int(a.values['estimated_yield_green']))+" Datos expresados en Kilogramos por hectarea (Kg/Ha)")
                elif(a.type == ReplyFormEnum.FAILED_ESTIMATION):
                    msg.append("Error al registrar")

            # Message error
            elif (isinstance(a.type, ReplyErrorEnum)):
                # Missing geographic
                if(a.type == ReplyErrorEnum.MISSING_LOCALITIES):
                    msg.append("Lo sentimos, no encontramos una localidad en su solicitud. Por favor ingresa el nombre de la localidad")
                # Locality not found
                elif(a.type == ReplyErrorEnum.LOCALITY_NOT_FOUND):
                    msg.append("Lo sentimos, actualmente no tenemos la localidad: " + a.tag + " disponible en la base de datos")
                # Locality not found
                elif(a.type == ReplyErrorEnum.ERROR_ACLIMATE):
                    msg.append("Lo sentimos, su consulta no pudo ser procesada. No se logró conectar con el servicio de AClimate")
                elif(a.type == ReplyErrorEnum.ERROR_ACLIMATE_CLIMATOLOGY):
                    msg.append("Lo sentimos, no hay información de climatología para la localidad de: " + a.tag + " en AClimate")
                elif(a.type == ReplyErrorEnum.ERROR_ACLIMATE_FORECAST_CLIMATE):
                    msg.append("Lo sentimos, no hay información de predicción climática para la localidad de: " + a.tag + " en AClimate")
                elif(a.type == ReplyErrorEnum.ERROR_ACLIMATE_FORECAST_YIELD):
                    msg.append("Lo sentimos, no hay información de pronóstico de cultivo de para la localidad de: " + a.tag + " en AClimate")
                elif(a.type == ReplyErrorEnum.QUESTION_NOT_FORMAT):
                    msg.append(a.values)

            sys_answers.append(ReplySystem(a.type,msg,slots))

        return sys_answers

    # Method that return the description of measure
    # (string) var: Name of measure
    @staticmethod
    def get_climate_measure(var):
        a = 'precipitación'
        if(var == "sol_rad"):
            a = "radiación solar"
        elif (var == "t_max"):
            a = "temperatura máxima"
        elif (var == "t_min"):
            a = "temperatura mínima"
        return a

    #
    @staticmethod
    def get_climate_unit(var):
        a = 'mm'
        if(var == "sol_rad"):
            a = "cal/cm²d"
        elif (var == "t_max"):
            a = "°C"
        elif (var == "t_min"):
            a = "°C"
        return a

    # Method that return the month name
    # (int) id: Id of month
    @staticmethod
    def get_month(id):
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        id_month = (int(id)-1) % 12
        #print(id_month)
        return months[id_month]