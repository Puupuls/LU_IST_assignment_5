import json
from datetime import datetime
import flask
import requests
from flask import render_template, request
import csv

app = flask.Flask(__name__)
app.debug = True
data_folder = 'data'

# URL_BUILDING_DATA = 'https://data.gov.lv/dati/lv/api/3/action/datastore_search?resource_id=3bc2f8d1-3c59-40ca-bde3-891c4347a651&limit=500000000'
URL_BUILDING_DATA = 'https://data.gov.lv/dati/dataset/7458769e-9b13-4309-9d1a-8e827b51a67b/resource/3bc2f8d1-3c59-40ca-bde3-891c4347a651/download/eku-energosertifikati-{0}.csv'
URL_CERTIFICATE_DATA = 'https://data.gov.lv/dati/dataset/4b57f72e-5de7-4dfd-8301-b843e22693e4/resource/a8d90166-3938-4126-ab02-fe4381bd2288/download/sertificetie-neatkarigie-eksperti-{0}.csv'


def get_latest_data():
    today = datetime.now().strftime('%d.%m.%Y')
    try:
        with open(f'{data_folder}/buildings_{today}.json') as f:
            building_data = json.load(f)
        with open(f'{data_folder}/certificates_{today}.json') as f:
            certificate_data = json.load(f)
    except FileNotFoundError:
        response = requests.get(URL_BUILDING_DATA.format(today))
        reader = csv.DictReader(response.content.decode("utf-8").replace("﻿", "").splitlines())
        building_data = [row for row in reader]
        with open(f'{data_folder}/buildings_{today}.json', 'w') as f:
            json.dump(building_data, f, ensure_ascii=False)

        response = requests.get(URL_CERTIFICATE_DATA.format(today))
        reader = csv.DictReader(response.content.decode("utf-8").replace("﻿", "").splitlines())
        certificate_data = [row for row in reader]
        with open(f'{data_folder}/certificates_{today}.json', 'w') as f:
            json.dump(certificate_data, f, ensure_ascii=False)
    return building_data, certificate_data


@app.route('/')
def hello_world():
    return render_template(
        'index.html'
    )


@app.route('/autocomplete')
def autocomplete():
    search = request.args.get('term')
    results = []
    building_data, certificate_data = get_latest_data()
    seen_results = []
    for row in building_data:
        if row['Objekta adreses'].lower().startswith(search.lower()) or \
                row["Ēkas energosertifikāta numurs"].lower().startswith(search.lower()):
            if row['Objekta adreses kods'] not in seen_results:
                results.append({
                    'label': row['Objekta adreses'],
                    'value': row['Objekta adreses'],
                    'type': 'building'
                })
                seen_results.append(row['Objekta adreses kods'])
    for row in certificate_data:
        if row["Vārds"].lower().startswith(search.lower()) or \
                row["Uzvārds"].lower().startswith(search.lower()) or \
                (row["Vārds"] + " " + row["Uzvārds"]).lower().startswith(search.lower()) or \
                row["Sertifikāta numurs"].lower().startswith(search.lower()):
            if row["Vārds"] + " " + row["Uzvārds"] not in seen_results:
                results.append({
                    'label': f'{row["Vārds"]} {row["Uzvārds"]}',
                    'value': row["Vārds"] + " " + row["Uzvārds"],
                    'type': 'certificate'
                })
                if row["Sertifikāta numurs"].lower().startswith(search.lower()):
                    results[-1]['label'] += f' ({row["Sertifikāta numurs"]})'
                seen_results.append(row["Vārds"] + " " + row["Uzvārds"])

    return json.dumps(sorted(results, key=lambda x: x["label"]), ensure_ascii=False)


@app.route('/result', methods=['POST'])
def search_result():
    search = request.form.get('search')
    building_data, certificate_data = get_latest_data()
    results = []
    for row in building_data:
        row['type'] = 'building'
        if row['Objekta adreses'].lower().startswith(search.lower()) or \
                row["Ēkas energosertifikāta numurs"].lower().startswith(search.lower()):
            results.append(row)
            results[-1]['Izdošanas datums'] = row['Izdošanas datums'].split('T')[0]
            results[-1]['Derīguma termiņš'] = row['Derīguma termiņš'].split('T')[0]
        if row["Eksperta vārds"].lower().startswith(search.lower()) or \
                row["Eksperta uzvārds"].lower().startswith(search.lower()) or \
                (row["Eksperta vārds"] + " " + row["Eksperta uzvārds"]).lower().startswith(search.lower()):
            results.append(row)
            results[-1]['Izdošanas datums'] = row['Izdošanas datums'].split('T')[0]
            results[-1]['Derīguma termiņš'] = row['Derīguma termiņš'].split('T')[0]
    for row in certificate_data:
        if row["Vārds"].lower().startswith(search.lower()) or \
                row["Uzvārds"].lower().startswith(search.lower()) or \
                (row["Vārds"] + " " + row["Uzvārds"]).lower().startswith(search.lower()) or \
                row["Sertifikāta numurs"].lower().startswith(search.lower()):
            row['type'] = 'certificate'
            results.append(row)
    return json.dumps(results, ensure_ascii=False)


if __name__ == '__main__':
    app.run(debug=True)
