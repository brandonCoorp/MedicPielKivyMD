import json
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
import requests
from plyer import filechooser
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivymd.uix.bottomsheet import MDGridBottomSheet
from kivymd.uix.label import MDLabel

#import para detectar enfermedad
import numpy as np
from keras.utils import load_img, img_to_array
from keras.models import load_model
import os
from PIL import Image
from urllib.request import *
Window.size = (350, 600)
# CTRL + K, CTRL + C
#  CTRL +K, CTRL + U

class MainApp(MDApp):
    def build(self):
        global sm
        global urlApiLogin, cnn,urlApi, urlApiMedia
        urlApiLogin = "http://127.0.0.1:8000/api/login/"
        urlApi = "http://127.0.0.1:8000/api/"
        urlApiMedia = "http://127.0.0.1:8000/media/"
        
        modelo = './Modelo/modelo/modelo.h5'
        pesos = './Modelo/modelo/pesos.h5'
        print(os.getcwd())
        print("aqui esta")
        cnn = load_model(modelo)
        cnn.load_weights(pesos)
        sm = ScreenManager() 
        sm.add_widget( Builder.load_file('./screen/slapsh.kv'))
        sm.add_widget( Builder.load_file('./screen/login.kv'))  
        sm.add_widget( Builder.load_file('./screen/dash.kv')) 
        sm.add_widget( Builder.load_file('./screen/consulta.kv'))  
        sm.add_widget( Builder.load_file('./screen/diagnostico.kv'))  
        sm.add_widget( Builder.load_file('./screen/listarDiagnostico.kv'))  
        
       # sm.add_widget( Builder.load_file('./screen/consulta.kv'))  
          
        self.theme_cls.theme_style="Dark"
        self.theme_cls.primary_palette ="Teal"
        self.theme_cls.accent_palette = "Red"
        return sm
    
    def on_start(self):
        Clock.schedule_once(self.loginS, 30)
  
    def loginS(self, *args):
        sm.current = "login"
        self.closes()
    
    def regsitrarP(self):
        pass

#-------------------efectos


#-------------------------lpgin
    def logger(self, user, password):
        datos = {'email': user,'password': password}
        datosjs =json.dumps(datos)
        r = requests.post(urlApiLogin, data=datosjs)
        resp = json.loads(r.text)
        if(resp['detail'] == "logeado"):
           print("logeao")
           sm.current = "dashboard"
        else:
           print("error en los credenciales")
        #sm.current = "dashboard"
    

    def detectarEnfermedad(self):
        wo = sm.get_screen('consulta')
        print(os.getcwd())
        file = wo.camara1.source
        longitud, altura = 100, 100
        resp = "ninguno"
       # print(os.getcwd())

        x = load_img(file, target_size = (longitud, altura))
        x = img_to_array(x)
        x = np.expand_dims(x, axis=0)
        arreglo = cnn.predict(x)    # [ [1, 0, 0] ] -> 2D
        resultado = arreglo[0]      # [1, 0, 0]
        respuesta = np.argmax(resultado)    # 0 -> arr[0] tiene el valor más alto
        diagnostic = ""
        diagnostic = "Wow tu caso es dificil de predecir será mejor que te acerques a un hospital"
        print(respuesta)
        if respuesta == 0:
            print('Melanoma')
            diagnostic = "Tienes una Afeccion en tu Piel llamada :              Melanoma"
            resp= "Melanoma"
        elif respuesta == 1:
            #print('Carcinoma de células basales')
            diagnostic = "Wow tu caso es dificil de predecir será mejor que te acerques a un hospital"
            resp="ninguno"
        elif respuesta == 5:
            print('Nevus melanocíticos')
            diagnostic = "'Tienes una Afeccion en tu Piel llamada :             Nevus melanocíticos"
            resp= "Nevus melanocíticos"
        elif respuesta == 6:
            print('Lesion vascular de la piel')
            diagnostic = "Tienes una Afeccion en tu Piel llamada :             Lesion vascular de la piel"
            resp= "Lesion vascular de la piel"
        if(resp != "ninguno"):
            model ="enfermedadN/"
            model = model + resp
            paciente_id = 2 
            estado = 1
            resp = self.getapi(model)
            enfermedad = resp['enfermedad'][0]
            print(enfermedad['tratamiento'])
            imagen = load_img(file)
            print(imagen)
            print(file)
            print(resp)
            self.postApiconsulta3(file, 2,enfermedad['nombre'])

        wo = sm.get_screen('diagnostico')
        wo.diag.text = diagnostic
        wo.enfermedad.text = str(enfermedad['id'])
        wo.camara2.source =  'medicina.jpg'
        sm.current = "diagnostico"  

    def listarDiagnostico(self):
        model = "DiagnosticoUser/"
        paciente_id = 2
        resp=self.getapi(model, paciente_id)
        diagnosticos = resp['diagnosticos']
        print(diagnosticos[0])
        self.cargarTablaDiagnostico(diagnosticos)
       
        #wo.diag.text = resp
    def cargarTablaDiagnostico(self, diagnosticos):
        wo = sm.get_screen('listarDiagnostico')
        self.data_tables = MDDataTable(
            use_pagination=True,
            size_hint=(0.9, 0.9),
            pos_hint={"center_y": 0.5, "center_x": 0.5},
            background_color="#65275d",
          #  check=True,
            column_data=[
                        ("N.", dp(10)),
                        ("ND.", dp(20)),   
                        ("Resultado", dp(35)),
                        ("Fecha", dp(40), self.sort_on_signal),
                                        
            ],
            row_data=[],
            sorted_on="Schedule",
            sorted_order="ASC",
            elevation=2,
        )
       

       # last_num_row = int(self.data_tables.row_data[-1][0])
     #   self.data_tables.add_row((str(last_num_row + 1), "1", "2", "3"))
        cant = 1
        for n in diagnosticos:
            print(cant)
           # self.data_tables.add_row((str(cant), "1", "2", "3"))
            self.data_tables.row_data.append((cant, n['id'], n['resultado'], n['fecha']))
            cant = cant +1
            print(n['id'])
            self.data_tables.bind(on_row_press=self.on_row_press) 
        wo.listdiag.clear_widgets()
        wo.listdiag.add_widget(self.data_tables)

    def on_row_press(self, instance_table, instance_row):
        '''Called when a table row is clicked.'''
        print(instance_table, instance_row)
        try: 
            int(instance_row.text)
            print(True)
            model = "diagnostico/"
            resp= self.getapi(model,int(instance_row.text))
            diagnostico = resp['diagnostico']
            
            imagen = urlApiMedia + diagnostico['imagen']
            print(imagen)
            wo = sm.get_screen('diagnostico')
            try:
                wo.camara2.source =  'medicina.jpg'
                os.remove('pic.jpg')

            except OSError as e:
                print(f"Error:{ e.strerror}")
            urlretrieve(imagen,'pic.jpg')
            
           # img = Image.open('pic.jpg')

           
            wo.diag.text = diagnostico['resultado']
            wo.enfermedad.text = str(diagnostico['enfermedad_id_id'])
            wo.camara2.source =  'medicina.jpg'
            sm.current = "diagnostico"  
        except ValueError:
            print(False)

    def sort_on_signal(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][2]))

    def sort_on_schedule(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: sum(
                    [
                        int(l[1][-2].split(":")[0]) * 60,
                        int(l[1][-2].split(":")[1]),
                    ]
                ),
            )
        )

    def sort_on_team(self, data):
        return zip(*sorted(enumerate(data), key=lambda l: l[1][-1]))

    def descripcionDiagnostico(self, id):
        bottom_sheet_menu = MDGridBottomSheet()
        print(id)
        model = "enfermedad/"
        resp = self.getapi(model, int(id))
        enfermedad = resp['enfermedad']
        print(enfermedad['tratamiento'])
        data = {
            "Tratamiento": "",
            enfermedad['tratamiento']: "",
        }
        label = MDLabel(
                        text=enfermedad['tratamiento'],
                        halign= "center",
        )      
        #for item in data.items():
             
        bottom_sheet_menu.add_widget(label)
            # bottom_sheet_menu.add_item(
            #     item[0],
            #     lambda x, y=item[0]: self.llamar(y),
            # )
        bottom_sheet_menu.open()
    
    def llamar(self, *args):
        print("args")

#*****------------------------------------------------

# funciones API REST------------------------------------

    def getapi(self, model, id = 0):
        if(id>0):
             api = urlApi + model + str(id)
             print(api)
        else:
            api = urlApi + model
        
        r = requests.get(api)
        resp = json.loads(r.text)
       # print(resp)
        return resp
           #if(resp['detail'] == "logeado"):
            #    print("logeao")
           #  sm.current = "dashboard"
          #  else:
            #    print("error en los credenciales")
    def postapi(self, datos):
        datos = {'email': datos,'password': datos}
        datosjs =json.dumps(datos)
        r = requests.post(urlApiLogin, data=datosjs)
        resp = json.loads(r.text)
    
  

    def postApiconsulta3(self, imagen, id, enfermedad):   
        estado = 1 
        data = {
            'estado': estado,
            'paciente_id': id,
            'enfermedad': enfermedad         
        }
        r = requests.post("http://127.0.0.1:8000/api/crearconsulta/",
            files={'imagen': open(imagen, 'rb')},
            data=data,
            headers={"Authorization": "Token jfhgfgsdadhfghfgvgjhN"} #since I had to authenticate for the same
        )
        print (r.json())
    
#----------------------------------------------------
    def navegacion(self):
        #print("navegando")
        self.open('dashboard')
       # print("navegando")
        self.open('consulta')
       # print("navegando")
        self.open('diagnostico')
       # print("navegando")
        self.open('listarDiagnostico')
       # print("navegando")
        


    def volver(self):
        sm.current = "dashboard"
        self.closes()

    def consultaNav(self):
        self.closes()
        sm.current = "consulta"
        
    def consulta(self):
        self.closes()
        sm.current = "consulta"
        
    def listarDiagnostiosNav(self):  
        self.closes()
        self.listarDiagnostico()
        sm.current = "listarDiagnostico"
    


    def open(self, screen):
        wo = sm.get_screen(screen)
        wo.nav_drawers.set_state("open")
    def close(self, screen):
        wo = sm.get_screen(screen)
        wo.nav_drawers.set_state("close")
    def closes(self):
        self.close('dashboard')
        self.close('consulta')
        self.close('diagnostico')
        self.close('listarDiagnostico')
#---------------------------------------------------###
    def file_chooser1(self):
      #  self.prueba.text 
        print(self.selected1)
        filechooser.open_file(on_selection=self.selected1)

    def selected1(self, selection1, *args):
        print(selection1)
        print(selection1[0])
        wo = sm.get_screen('consulta')
        print(wo.prueba.text)
        if len(selection1)==0:
            print("vacio")
        else:
            wo.camara1.source = selection1[0]



MainApp().run()