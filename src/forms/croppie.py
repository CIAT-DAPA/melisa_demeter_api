import requests
import uuid
import os
class Croppie:

    def __init__(self, token=None, url=None):
        self.token = token if token is not None else os.getenv("CROPPIE_TOKEN")
        self.url = url

    def post_data(self, region_id, variety_id, plot_area, altitude):
        if not self.url:
            raise ValueError("URL not provided")

        farm_id = str(uuid.uuid4())
        farm_code = "PRN-" + str(uuid.uuid4())[:6] 
        plot_id = str(uuid.uuid4())
        external_user_id = str(uuid.uuid4())

        endpoint = f"/regions/{region_id}/farm-plots"  # Construir el endpoint con region_id
        full_url = f"{self.url}{endpoint}"

        data_to_post = {
            "farm_id": farm_id,
            "farm_code": farm_code,
            "plot_id": plot_id,
            "external_user_id": external_user_id,
            "plot_area": plot_area,
            "altitude": altitude,
            "geometry": {
                "type": "Point",
                "coordinates": [-76.3538, 3.5126]
            },
            "region_id": region_id,
            "variety_id": variety_id
        }

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        response = requests.post(full_url, json=data_to_post, headers=headers)

        return response.json()
    
    def post_image(self, image_path_full):
        if not self.url:
            raise ValueError("URL not provided")

        headers = {"Authorization": f"Bearer {self.token}"}

        image_filename = os.path.basename(image_path_full)

        files = {'images[]': (image_filename, open(image_path_full, 'rb'), 'image/jpeg')}

        endpoint = f"/files/images"  # Construir el endpoint de imagenes
        full_url = f"{self.url}{endpoint}"

        response = requests.post(full_url, headers=headers, files=files)

        return response.json()

    def post_plant_data(self, plants_count, coffee_plants,plat_form_id):
        if not self.url:
            raise ValueError("URL not provided")

        external_user_id = str(uuid.uuid4())
        external_session_id = str(uuid.uuid4())
        previous_yield = 0
        endpoint = f"/yield/coffee?farmPlotId={plat_form_id}"  # Construir el endpoint con region_id
        full_url = f"{self.url}{endpoint}"
        data_to_post = {
            "plot_plants_count": plants_count,
            "previous_yield": previous_yield,
            "coffee_plants": coffee_plants, # se debe agregar los datos de las plantas de café
            "external_user_id": external_user_id,
            "external_session_id": external_session_id
        }
        print(f' la data a postear es: {data_to_post}')
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        response = requests.post(full_url, json=data_to_post, headers=headers)

        return response.json()
    
    def get_coffee_yield_estimate(self, parameter_value):
        if not self.url:
            raise ValueError("URL not provided")

        endpoint = f"/yield/coffee/{parameter_value}"
        full_url = f"{self.url}{endpoint}"

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(full_url, headers=headers)

        return response.json()


