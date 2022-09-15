from datetime import datetime, timezone, timedelta
import requests
from typing import Union, List
import zoneinfo

BASE_URL = 'https://api-v3.mbta.com/'
TIMEZONE_INFO = zoneinfo.ZoneInfo("America/New_York")
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


def _get_matching_id(items: List[dict], search_id) -> Union[dict, None]:
  """Given a list of JSONs, return the one with an 'ID' field that matches"""
  for item in items:
    if item['id'] == search_id:
      return item
  return None


def get_predictions_for_stop(stop_id: str, route_id: str, num_predicts: int) -> tuple:
  """Given an MBTA place, return predicted vehicles that meet the qualifications

  Args:
    stop_id: place to query
    route_id: the line the vehicle you are looking for is on
    num_predicts: the number of predicitons for each direction to return
  Returns:
    ([list of num_predicts predictions for dir=0), [... for dir=1])
    predictions are dicts with the following fields:
    {direction_name: direction name from the route,
     distance_s: vehicle distance in seconds
     display_str: string to display for vehicle
     headsign: vehicle headsign
    }
  """
  query_url = (f'{BASE_URL}predictions?'
               f'include=route,trip,vehicle&'
               f'filter[stop]={stop_id}&sort=departure_time')

  query_data = requests.get(query_url).json()

  predictions = query_data['data']

  routes = [item for item in query_data['included'] if item['type'] == 'route']
  trips = [item for item in query_data['included'] if item['type'] == 'trip']
  vehicles = [item for item in query_data['included'] if item['type'] == 'vehicle']

  route = _get_matching_id(routes, route_id)
  if route is None:
    return ()

  # Pull out the next num_predicts predictions for each direction:
  parsed_predictions = ([], [])
  for prediction in predictions:
    if prediction['relationships']['route']['data']['id'] != route_id:
      # Ignore if for a different route
      continue
    if prediction['attributes']['departure_time'] is None:
      # Ignore if there's no departure time, this means the vehicle isn't stopping
      continue
    direction = int(prediction['attributes']['direction_id'])
    if len(parsed_predictions[direction]) >= num_predicts:
      continue

    direction = int(prediction['attributes']['direction_id'])
    direction_name = route['attributes']['direction_names'][direction]

    arrival_time = datetime.strptime(
      prediction['attributes']['arrival_time'], TIME_FORMAT)
    departure_time = datetime.strptime(
      prediction['attributes']['departure_time'], TIME_FORMAT)
    distance_s = arrival_time - datetime.now(TIMEZONE_INFO)
    distance_s = distance_s.seconds

    if prediction['attributes']['status']:
      # Deal with this
      display_str = prediction['attributes']['status']
    else:
      display_str = f'{int(distance_s / 60 + 0.5):0.0f} min'

    vehicle = _get_matching_id(vehicles,
                               prediction['relationships']['vehicle']['data']['id'])
    trip = _get_matching_id(trips, prediction['relationships']['trip']['data']['id'])
    headsign = trip['attributes']['headsign']

    parsed_predictions[direction].append(
      {'direction_name': direction_name,
       'display_str:': display_str,
       'distance_s': distance_s,
       'headsign': headsign}
    )
  return parsed_predictions
