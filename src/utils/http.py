import requests

from src.config import Config


def get(url, headers=None, params=None):
    response = requests.get(url, headers=headers, params=params, timeout=Config.TIMEOUT)
    response.raise_for_status()
    return response.json()


def post(url, headers=None, data=None):
    response = requests.post(url, headers=headers, json=data, timeout=Config.TIMEOUT)
    response.raise_for_status()
    return response.json()


def put(url, headers=None, data=None):
    response = requests.put(url, headers=headers, json=data, timeout=Config.TIMEOUT)
    response.raise_for_status()
    return response.json()


def delete(url, headers=None):
    response = requests.delete(url, headers=headers, timeout=Config.TIMEOUT)
    response.raise_for_status()
    return response.status_code
