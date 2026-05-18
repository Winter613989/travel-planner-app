from tools.accommodations.apis import Accommodations
from tools.flights.apis import Flights
from tools.restaurants.apis import Restaurants
from tools.googleDistanceMatrix.apis import GoogleDistanceMatrix
import pandas as pd

hotel = Accommodations()
flight = Flights()
flight.load_db()
restaurant = Restaurants()
distanceMatrix = GoogleDistanceMatrix()


def estimate_budget(data, mode):
    """
    Estimate the budget based on the mode (lowest, highest, average) for flight, hotel, or restaurant data.
    """
    if mode == "lowest":
        return min(data)
    elif mode == "highest":
        return max(data)
    elif mode == "average":
        # filter the nan values
        data = [x for x in data if str(x) != 'nan']
        return sum(data) / len(data)
    

def budget_calc(org, dest, days, date:list , people_number=None, local_constraint = None):
    """
    Calculate the estimated budget for all three modes: lowest, highest, average.
    grain: city, state
    """
    if days == 3:
        grain = "city"
    elif days in [5,7]:
        grain = "state"

    if grain not in ["city", "state"]:
        raise ValueError("grain must be one of city, state")
    
    # Multipliers based on days
    multipliers = {
        3: {"flight": 2, "hotel": 3, "restaurant": 9},
        5: {"flight": 3, "hotel": 5, "restaurant": 15},
        7: {"flight": 4, "hotel": 7, "restaurant": 21}
    }
    
    if grain == "city":
        hotel_data = hotel.run(dest)
        restaurant_data = restaurant.run(dest)
        flight_data = flight.data[(flight.data["DestCityName"] == dest) & (flight.data["OriginCityName"] == org)]


    elif grain == "state":
        city_set = open('../database/background/citySet_with_states.txt').read().strip().split('\n')
        
        all_hotel_data = []
        all_restaurant_data = []
        all_flight_data = []
        
        for city in city_set:
            if dest == city.split('\t')[1]:
                candidate_city = city.split('\t')[0]
                
                # Fetch data for the current city
                current_hotel_data = hotel.run(candidate_city)
                current_restaurant_data = restaurant.run(candidate_city)
                current_flight_data = flight.data[(flight.data["DestCityName"] == candidate_city) & (flight.data["OriginCityName"] == org)]
                
                # Append the dataframes to the lists
                all_hotel_data.append(current_hotel_data)
                all_restaurant_data.append(current_restaurant_data)
                all_flight_data.append(current_flight_data)
        
        # Use concat to combine all dataframes in the lists
        hotel_data = pd.concat(all_hotel_data, axis=0)
        restaurant_data = pd.concat(all_restaurant_data, axis=0)
        flight_data = pd.concat(all_flight_data, axis=0)
        # flight_data should be in the range of supported date
        flight_data = flight_data[flight_data['FlightDate'].isin(date)]

    if people_number:
        hotel_data = hotel_data[hotel_data['maximum occupancy'] >= people_number]

    if local_constraint:

        if local_constraint['transportation'] == 'no self-driving':
            if grain == "city":
                if len(flight_data[flight_data['FlightDate'] == date[0]]) < 2:
                    raise ValueError("No flight data available for the given constraints.")
            elif grain == "state":
                if len(flight_data[flight_data['FlightDate'] == date[0]]) < 10:
                    raise ValueError("No flight data available for the given constraints.")
                    
    # Calculate budget ranges
    flight_prices = list(flight_data['Price'])
    hotel_prices = list(hotel_data['price'])
    restaurant_prices = list(restaurant_data['average_cost'])

    budgets = {
        "lowest": 0,
        "highest": 0,
        "average": 0
    }
    
    for mode in ["lowest", "highest", "average"]:
        flight_budget = estimate_budget(flight_prices, mode) * multipliers[days]["flight"]
        hotel_budget = estimate_budget(hotel_prices, mode) * multipliers[days]["hotel"]
        restaurant_budget = estimate_budget(restaurant_prices, mode) * multipliers[days]["restaurant"]
        
        budgets[mode] = round(flight_budget + hotel_budget + restaurant_budget, 2)
    
    return budgets