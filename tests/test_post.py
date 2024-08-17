import unittest
import random
import sys
import csv
import requests
import json

from api import delete_table

sys.path.append('./')

data_path = 'data/data.csv'
api_url = 'http://localhost:8000/'

def decomment(csvfile):
    for row in csvfile:
        raw = row.split('#')[0].strip()
        if raw: yield raw



class TestApi(unittest.TestCase):
    def test_post(self):

        with open(data_path, 'r') as file:
            reader = csv.reader(decomment(file))
            data = []
            for row in reader:
                data.append(row)

        self.assertEqual(len(data), 11)

        
        with open(data_path, 'rb') as file:
            file_content = file.read()
            response = requests.post(api_url + 'transactions', files={'file': (data_path, file_content, 'text/csv')})
            # print(response)

    def test_get(self):
        response = requests.get(api_url + 'report')
        json_data = response.json()
        # print(response.text, tuple(json_data), json_data)
        # print('gross_revenue' in json_data)
        self.assertEqual('gross_revenue' in json_data, True)
        self.assertEqual('net_revenue' in json_data, True)
        self.assertEqual('expenses' in json_data, True)
        