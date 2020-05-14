#!/usr/bin/python -Btt
import sys  # For simplicity, we'll read config file from 1st CLI param sys.argv[1]
import json
import logging
import requests
import msal
from lambda_support import decrypt

""" If the key is not encrypted , then we can remove the decrypt function """ 


default_file = "/configs/azure-config.json"
default_ep="https://graph.microsoft.com/v1.0/"

def get_token(jsonfile=default_file):

    config = json.load(open(jsonfile))
    client_id = decrypt(config["encrypted_client"])
    tenant = decrypt(config["encrypted_tenant"])
    secret = decrypt(config["encrypted_secret"])
    authority = config["authority"] + tenant

    # Create a preferably long-lived app instance which maintains a token cache.
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=secret)
    result = None
    
    result = app.acquire_token_silent(config["scope"], account=None)
    
    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])
    if "access_token" in result:
        token = result['access_token']
        return token
    
    return False


def get_all_users(token):
    endpoint = endpoint + "users"
    graph_data = get_graph_data(token, endpoint)
    if graph_data:
        userlist = [item["userPrincipalName"] for item in graph_data["value"]]
    return userlist


def get_user_object(token, name):
    endpoint = "https://graph.microsoft.com/v1.0/users"
    graph_data = get_graph_data(token, endpoint)
    if graph_data:
        for item in graph_data["value"]:
            if item["displayName"] == name:
                return item
    else:
        return None

def get_group_object(token, name):
    endpoint = "https://graph.microsoft.com/v1.0/groups"
    graph_data = get_graph_data(token, endpoint)
    if graph_data:
        for item in graph_data["value"]:
            if item["displayName"] == name:
                return item
    else:
        return None

def base_url():
    return "https://graph.microsoft.com/v1.0/"


def create_azure_user(token, json_file):
    json_obj = json.load(open(json_file))
    endpoint = base_url() + "users"
    result = post_request(token, endpoint, json_obj)
    return result


def create_azure_group(token, json_file):
    json_obj = json.load(open(json_file))
    endpoint = base_url() + "groups"
    result = post_request(token, endpoint, json_obj)
    return result


def add_azure_user_to_group(token, user, group):
    pass_dict = {}
    dir_url = "directoryObjects/{}"
    group_url = "groups/{}/members/$ref"
    user_obj = get_user_object(token, user)
    group_obj = get_group_object(token, group)
    group_endpoint = base_url() + group_url.format(group_obj["id"])
    pass_dict["@odata.id"] = base_url() + dir_url.format(user_obj["id"])
    result = post_request(token, group_endpoint, pass_dict)
    return result


def remove_azure_user_from_group(token, user, group):
    url = "groups/{}/members/{}/$ref"
    user_obj = get_user_object(token, user)
    group_obj = get_group_object(token, group)
    endpoint = base_url() + url.format(group_obj["id"], user_obj["id"])
    response = delete_request(token, endpoint)
    return response


def delete_azure_user(token, user):
    url = "users/{}"
    user_obj = get_user_object(token, user)
    endpoint = base_url() + url.format(user_obj["id"])
    response = delete_request(token, endpoint)
    return response


def delete_azure_group(token, group):
    url = "groups/{}"
    group_obj = get_group_object(token, group)
    endpoint = base_url() + url.format(group_obj["id"])
    response = delete_request(token, endpoint)
    return response

def post_request(token, endpoint, json_obj):
    try:
        headers = {'Authorization': 'Bearer ' + token}
        headers['Content-type'] = 'application/json'
        graph_data = requests.post(endpoint, json=json_obj, headers=headers)
    except Exception as e:
        graph_data = False
    return graph_data


def get_graph_data(token, endpoint):
    try:
        graph_data = requests.get(endpoint, headers={'Authorization': 'Bearer ' + token},).json()
    except Exception as e:
        print("Error in obtaining the graph object for {}".format(endpoint))
        sys.exit(1)
    return graph_data


def delete_request(token, endpoint):
    try:
        response = requests.delete(endpoint, headers={'Authorization': 'Bearer ' + token},)
    except Exception as e:
        print("Error in the following delete request: {}".format(endpoint))
        sys.exit(1)
    return response



def get_aws_groups(token):
    endpoint = default_ep + "groups"
    graph_data = get_graph_data(token, endpoint)
    if graph_data:
        grouplist = [item["displayName"] for item in graph_data["value"] if item["displayName"].startswith("aws")]
    return grouplist


def get_group_members(token, group):
    url = "groups?$filter=displayName+eq+{})".format(group)

    endpoint = default_ep + url 
    graph_data = get_graph_data(token, endpoint)
    return graph_data

