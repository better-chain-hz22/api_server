import pandas as pd
import json
from datetime import datetime


class MigrosAPI:
    def __init__(self):
        self.orders_data = None
        self.order_enrichment_data = None
        self.ship_tracks_data = None
        self.ports_data = None
        self.risks_data = None
        self.ports_with_risk_cache = set()
        self._load_data_to_memory()
        self._enrich_risk_data()

    def _load_data_to_memory(self):
        print('Loading dataset to memory')
        self.orders_df = pd.read_csv('data/gis_opex_international_bestellu.csv', delimiter=';')
        self.order_enrichment_data = pd.read_csv('data/gis_opex_international_raw.csv', delimiter=';')
        self.ship_tracks_data = pd.read_csv('data/shiptrac.csv', index_col=0)
        self.ports_data = pd.read_csv('data/ports.csv', delimiter=';')
        with open('data/known_risks.json', 'r') as fp:
            self.risks_data = json.load(fp)

    def _enrich_risk_data(self):
        for risk in self.risks_data:
            port_name = risk['portName']
            port_info = self.ports_data[self.ports_data['portname'] == port_name]
            if len(port_info) > 0:
                port_info = self.ports_data[self.ports_data['portname'] == port_name].iloc[0]
                if str(port_info['code']) != 'nan':
                    risk['portCode'] = port_info['code']
                    self.ports_with_risk_cache.add(risk['portCode'])

        self.risks_data = list(filter(lambda o: 'portCode' in o, self.risks_data))

    def _get_order_information(self, order_id):
        order_information = self.order_enrichment_data[
            self.order_enrichment_data['bestellnummer'] == order_id].drop_duplicates()
        return order_information if len(order_information) > 0 else None

    def _get_risks_for_steps(self, relevant_in_route_points):
        risks_for_steps = []
        for index, route_point in relevant_in_route_points.iterrows():
            for risk in self.risks_data:
                if risk['portCode'] == route_point['destination']:
                    start_window = datetime.strptime(risk['start'], '%d.%m.%Y %H:%M')
                    end_window = datetime.strptime(risk['end'], '%d.%m.%Y %H:%M')
                    eta = datetime.strptime(route_point['eta'], '%d.%m.%Y %H:%M')
                    if start_window <= eta <= end_window:
                        risks_for_steps.append(json.loads(route_point.to_json()))
        return risks_for_steps

    def _get_ship_route_risk_information(self, ship_id):
        ship_tracks_for_ship_id = \
            self.ship_tracks_data[self.ship_tracks_data['imo_number'] == ship_id]
        relevant_in_route_points = ship_tracks_for_ship_id[
            ship_tracks_for_ship_id['destination'].isin(self.ports_with_risk_cache)]
        return self._get_risks_for_steps(relevant_in_route_points)

    def get_risks_for_order_id(self, order_id):
        order_information = self._get_order_information(order_id)
        ship_risks = {}
        for index, order_info in order_information.iterrows():
            ship_id = order_info['imo_nr']
            container = order_info['container']
            ship_risks[ship_id] = {
                "risks": self._get_ship_route_risk_information(ship_id),
                "container": container
            }
        result = {
            "order_info": json.loads(order_information.to_json(orient='records')),
            "ship_risks": ship_risks
        }
        return result







