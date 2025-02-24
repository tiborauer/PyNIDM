
from pathlib import Path
import pytest
import pandas as pd
import json
import os
import urllib
import re
from  nidm.experiment.Utils import map_variables_to_terms
import tempfile
from os.path import join
from nidm.core import Constants
from uuid import UUID





@pytest.fixture(scope="module", autouse="True")
def setup():
    global DATA, REPROSCHEMA_JSON_MAP, BIDS_SIDECAR

    temp = { 'participant_id': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109'],
             'age': [18, 25, 30,19 ,35 ,20 ,27 ,29 ,38 ,27],
             'sex': ['m', 'm', 'f', 'm', 'f', 'f', 'f', 'f', 'm','m'] }

    DATA = pd.DataFrame(temp)

    REPROSCHEMA_JSON_MAP = json.loads(
        '''
        {
            "DD(source='participants.tsv', variable='participant_id')": {
                "label": "participant_id",
                "description": "subject/participant identifier",
                "source_variable": "participant_id",
                "responseOptions": {
                    "valueType": "http://www.w3.org/2001/XMLSchema#string"
                },
                "isAbout": [
                    {
                        "@id": "https://ndar.nih.gov/api/datadictionary/v2/dataelement/src_subject_id",
                        "label": "src_subject_id"
                    }
                ]
            },
            "DD(source='participants.tsv', variable='age')": {
                "responseOptions": {
                    "unitCode": "years",
                    "minValue": "0",
                    "maxValue": "100",
                    "valueType": "http://www.w3.org/2001/XMLSchema#integer"
                },
                "label": "age",
                "description": "age of participant",
                "source_variable": "age",
                "associatedWith": "NIDM",
                "isAbout": [
                    {
                        "@id": "http://uri.interlex.org/ilx_0100400",
                        "label": "Age"
                    }
                ]
            },
            "DD(source='participants.tsv', variable='sex')": {
                "responseOptions": {
                    "minValue": "NA",
                    "maxValue": "NA",
                    "unitCode": "NA",
                    "valueType": "http://www.w3.org/2001/XMLSchema#complexType",
                    "choices": {
                        "Male": "m",
                        "Female": "f"
                    }
                },
                "label": "sex",
                "description": "biological sex of participant",
                "source_variable": "sex",
                "associatedWith": "NIDM",
                "isAbout": [
                    {
                        "@id": "http://uri.interlex.org/ilx_0738439",
                        "label": "SEX"
                    }
                ]
            }
        }''')

    BIDS_SIDECAR = json.loads(
        '''
        {
            "age": {
                "label": "age",
                "description": "age of participant",
                "source_variable": "age",
                "associatedWith": "NIDM",
                "isAbout": [
                    {
                        "@id": "http://uri.interlex.org/ilx_0100400",
                        "label": "Age"
                    }
                ],
                "valueType": "http://www.w3.org/2001/XMLSchema#integer",
                "minValue": "10",
                "maxValue": "100"
            },
            "sex": {
                "minValue": "NA",
                "maxValue": "NA",
                "unitCode": "NA",
                "valueType": "http://www.w3.org/2001/XMLSchema#complexType",
                "levels": {
                    "Male": "m",
                    "Female": "f"
                },
                "label": "sex",
                "description": "biological sex of participant",
                "source_variable": "sex",
                "associatedWith": "NIDM",
                "isAbout": [
                    {
                        "@id": "http://uri.interlex.org/ilx_0738439",
                        "label": "SEX"
                    }
                ]
            }
        }
        
        ''')


def test_map_vars_to_terms_BIDS():
    '''
    This function will test the Utils.py "map_vars_to_terms" function with a BIDS-formatted
    JSON sidecar file
    '''


    global DATA, BIDS_SIDECAR

    column_to_terms, cde = map_variables_to_terms(df=DATA,json_source=BIDS_SIDECAR,
                directory=tempfile.gettempdir(),assessment_name="test",bids=True)

    # check whether JSON mapping structure returned from map_variables_to_terms matches the
    # reproshema structure
    assert "DD(source='test', variable='age')" in column_to_terms.keys()
    assert "DD(source='test', variable='sex')" in column_to_terms.keys()
    assert "isAbout" in column_to_terms["DD(source='test', variable='age')"].keys()
    assert "http://uri.interlex.org/ilx_0100400" == column_to_terms["DD(source='test', variable='age')"] \
            ['isAbout'][0]['@id']
    assert "http://uri.interlex.org/ilx_0738439" == column_to_terms["DD(source='test', variable='sex')"] \
                ['isAbout'][0]['@id']
    assert "responseOptions" in column_to_terms["DD(source='test', variable='sex')"].keys()
    assert "choices" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions'].keys()
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']

    # now check the JSON sidecar file created by map_variables_to_terms which should match BIDS format
    with open(join(tempfile.gettempdir(),"nidm_annotations.json")) as fp:
        bids_sidecar = json.load(fp)

    assert "age" in bids_sidecar.keys()
    assert "sex" in bids_sidecar.keys()
    assert "isAbout" in bids_sidecar["age"].keys()
    assert "http://uri.interlex.org/ilx_0100400" == bids_sidecar["age"] \
        ['isAbout'][0]['@id']
    assert "http://uri.interlex.org/ilx_0738439" == bids_sidecar["sex"] \
        ['isAbout'][0]['@id']
    assert "levels" in bids_sidecar["sex"].keys()
    assert "Male" in bids_sidecar["sex"]['levels'].keys()
    assert "m" == bids_sidecar["sex"]['levels']['Male']
    assert "Male" in bids_sidecar["sex"]['levels'].keys()
    assert "m" == bids_sidecar["sex"]['levels']['Male']

    # check the CDE dataelement graph for correct information
    query = '''
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        select distinct ?uuid ?DataElements ?property ?value
            where {

                ?uuid a/rdfs:subClassOf* nidm:DataElement ;
                    ?property ?value .

        }'''
    qres=cde.query(query)

    results=[]
    for row in qres:
        results.append(list(row))

    assert len(results) == 20


def test_map_vars_to_terms_reproschema():
    '''
    This function will test the Utils.py "map_vars_to_terms" function with a reproschema-formatted
    JSON sidecar file
    '''

    global DATA, REPROSCHEMA_JSON_MAP

    column_to_terms, cde = map_variables_to_terms(df=DATA, json_source=REPROSCHEMA_JSON_MAP,
                                                  directory=tempfile.gettempdir(), assessment_name="test")

    # check whether JSON mapping structure returned from map_variables_to_terms matches the
    # reproshema structure
    assert "DD(source='test', variable='age')" in column_to_terms.keys()
    assert "DD(source='test', variable='sex')" in column_to_terms.keys()
    assert "isAbout" in column_to_terms["DD(source='test', variable='age')"].keys()
    assert "http://uri.interlex.org/ilx_0100400" == column_to_terms["DD(source='test', variable='age')"] \
        ['isAbout'][0]['@id']
    assert "http://uri.interlex.org/ilx_0738439" == column_to_terms["DD(source='test', variable='sex')"] \
        ['isAbout'][0]['@id']
    assert "responseOptions" in column_to_terms["DD(source='test', variable='sex')"].keys()
    assert "choices" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions'].keys()
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']

    # now check the JSON mapping file created by map_variables_to_terms which should match Reproschema format
    with open(join(tempfile.gettempdir(), "nidm_annotations.json")) as fp:
        reproschema_json = json.load(fp)

    assert "DD(source='test', variable='age')" in column_to_terms.keys()
    assert "DD(source='test', variable='sex')" in column_to_terms.keys()
    assert "isAbout" in column_to_terms["DD(source='test', variable='age')"].keys()
    assert "http://uri.interlex.org/ilx_0100400" == column_to_terms["DD(source='test', variable='age')"] \
        ['isAbout'][0]['@id']
    assert "http://uri.interlex.org/ilx_0738439" == column_to_terms["DD(source='test', variable='sex')"] \
        ['isAbout'][0]['@id']
    assert "responseOptions" in column_to_terms["DD(source='test', variable='sex')"].keys()
    assert "choices" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions'].keys()
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']
    assert "Male" in column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices'].keys()
    assert "m" == column_to_terms["DD(source='test', variable='sex')"]['responseOptions']['choices']['Male']

    # check the CDE dataelement graph for correct information
    query = '''
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        select distinct ?uuid ?DataElements ?property ?value
            where {

                ?uuid a/rdfs:subClassOf* nidm:DataElement ;
                    ?property ?value .

        }'''
    qres = cde.query(query)

    results = []
    for row in qres:
        results.append(list(row))

    assert len(results) == 20


    

