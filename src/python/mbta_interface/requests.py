import requests

import mbta

BASE_URL = 'https://api-v3.mbta.com/'


def flatten_json(nested_json, exclude=None):
  """Flatten json object with nested keys into a single level.
      Args:
          nested_json: A nested json object.
          exclude: Keys to exclude from output.
      Returns:
          The flattened json object if successful, None otherwise.
  """
  out = {}
  exclude = [''] if exclude is None else exclude

  def flatten(item, name='', exclude=exclude):
    if isinstance(item, dict):
      for key in item:
        if key not in exclude:
          flatten(item[key], name + key + '_')
    else:
      out[name[:-1]] = item

  flatten(nested_json)
  return out


def predicted_vehicle_to_str(vehicle: dict) -> str:
  """Convert a vehicle prediction JSON to text"""

  return

def get_predictions_for_place(place: str) -> list:
  """Given an MBTA place, return predicted vehicles that meet the qualifications

  Args:
    place: place to query
  Returns:
    list of predicted vehicles
  """
  query_url = (f'{BASE_URL}predictions?'
               f'include=route&filter[stop]={place}&sort=departure_time')

  query_data = requests.get(query_url).json()

  routes = query_data['included']
  routes_lookup = {route for route in routes}


