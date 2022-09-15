"""Get MBTA's predictions for a given station

API Documentation: https://api-v3.mbta.com/docs/swagger/index.html
Best Practices: https://www.mbta.com/developers/v3-api/best-practices

Currently this does not support an API key or header info.

Devices making requests without keys can make up to 20 requests per minute
without getting throttled.
"""
from datetime import datetime
import requests
from typing import Union, List
import zoneinfo

BASE_URL = 'https://api-v3.mbta.com/'
TIMEZONE_INFO = zoneinfo.ZoneInfo("America/New_York")
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

STATUS_STOP = 'STOPPED_AT'


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

    if distance_s < 0:
      # The vehicle has already left
      continue

    # Get associated vehicle and trip data
    vehicle = _get_matching_id(vehicles,
                               prediction['relationships']['vehicle']['data']['id'])
    trip = _get_matching_id(trips, prediction['relationships']['trip']['data']['id'])
    headsign = trip['attributes']['headsign']

    if prediction['attributes']['status']:
      # There's a status on the train
      display_str = prediction['attributes']['status']
    else:
      if distance_s > (20 * 60):
        # Per MBTA guidelines, cap at 20 min
        display_str = '20+ min'
      elif distance_s < 90 and vehicle['attributes']['current_status'] == STATUS_STOP:
        display_str = 'BRD'
      elif distance_s < 30:
        display_str = 'ARR'
      elif distance_s < 60:
        display_str = 'Approaching'
      else:
        display_str = f'{int(distance_s / 60 + 0.5):0.0f} min'

    parsed_predictions[direction].append(
      {'direction_name': direction_name,
       'display_str': display_str,
       'distance_s': distance_s,
       'headsign': headsign}
    )

  # Return the trips sorted by time
  for direction_list in parsed_predictions:
    list.sort(direction_list, key=lambda x: x['distance_s'])
  return parsed_predictions
