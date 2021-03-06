"""
   Copyright 2010 Daniel Graziotin <daniel.graziotin@acm.org>

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
"""
Wraps `Trip<http://dycapo.org/Protocol#Trip/>`_ objects in a
RESTful way. 
"""
import piston.handler
import piston.utils
import server.models
import server.utils
import server.common
import server.driver
import rest.utils
    
class TripHandler(piston.handler.BaseHandler):
    allowed_methods = ['GET','POST','PUT','DELETE']
    model = server.models.Trip
    fields = ('id','href', 'published', 'updated', 'expires', 
              ('author',('username','gender','href')), 
              'locations',
              ('modality',('kind','capacity','lic','color','make','vacancy','cost','year','model_name')),
              'preferences',
              'participations')
    
    """
"kind": "auto",
"capacity": 4,
"lic": "38238asd",
"color": "black",
"make": "Ford",
"vacancy": 4,
"cost": 0.0,
"year": 0,
"model_name": "Fiesta",


    """
    @classmethod
    def participations(cls,trip):
        participation = {}
        participation['href'] = trip.href + 'participations/'
        return participation
    
    @classmethod
    def locations(cls, trip):
        locations = trip.locations.all()
        return locations

    def read(self, request, id=None):
        if not id:
            trips = server.models.Trip.objects.filter(active=True)
            return trips
        else:
            try:
                trip = server.models.Trip.objects.get(id=id)
                return trip
            except server.models.Trip.DoesNotExist:
                return piston.utils.rc.NOT_FOUND

    def create(self, request, id=None):
        data = request.data
        author = rest.utils.get_rest_user(request)


        source = server.models.Location()
        dict_source = rest.utils.get_location_from_array(data['locations'],"orig")
        dict_source = rest.utils.clean_ids(dict_source)
        source = rest.utils.populate_object_from_dictionary(source, dict_source)

        destination = server.models.Location()
        dict_destination = rest.utils.get_location_from_array(data['locations'],"dest")
        dict_destination = rest.utils.clean_ids(dict_destination)
        destination = rest.utils.populate_object_from_dictionary(destination, dict_destination)

        modality = server.models.Modality()
        dict_modality = rest.utils.clean_ids(data['modality'])

        modality = rest.utils.populate_object_from_dictionary(modality, dict_modality)
        modality.vacancy = data['modality']['vacancy']
        modality.person = author

        preferences = server.models.Preferences()
        dict_preferences = rest.utils.clean_ids(data['preferences'])
        preferences = rest.utils.populate_object_from_dictionary(preferences, dict_preferences)

        trip = server.models.Trip()
        dict_trip = rest.utils.clean_ids(data)
        trip = rest.utils.populate_object_from_dictionary(trip, dict_trip)


        result = server.driver.insertTrip(trip, author, source, destination, modality, preferences)
        if result.code == server.models.Response.CREATED:
            id = result.value.id
            trip = server.models.Trip.objects.get(id=id)
            trip.href = rest.utils.get_href(request, 'trip_handler', [trip.id])
            trip.preferences.href = rest.utils.get_href(request, 'preferences_handler',[trip.id,])
            trip.modality.href = rest.utils.get_href(request, 'modality_handler',[trip.id,])
            trip.preferences.save()
            trip.modality.save()

            locations = trip.locations.all()
            [item.__setattr__('href',rest.utils.get_href(request,'location_handler',[trip.id])) for item in locations]
            [item.save() for item in locations]
            trip.save()
            participation = server.models.Participation.objects.get(author=trip.author, trip=trip,
                                         role='driver')
            participation.href = rest.utils.get_href(request, 'participation_handler',[trip.id,trip.author.username])
            participation.save()
            if trip.active:
                server.driver.startTrip(trip, author)
            return trip
        return result.to_xmlrpc() #rest.utils.extract_result_from_response(result)

    def update(self, request, id=None):
        current_user = rest.utils.get_rest_user(request)
        data = request.data
        try:
            trip = server.models.Trip.objects.get(id=id)
            if trip.author.id != current_user.id:
                return piston.utils.rc.FORBIDDEN
            if trip.active and not data['active']:
                result = server.driver.finishTrip(trip, current_user)
            elif not trip.active and data['active']:
                result = server.driver.startTrip(trip, current_user)
            else:
                return piston.utils.rc.FORBIDDEN
            return rest.utils.extract_result_from_response(result)
        except server.models.Trip.DoesNotExist:
            return piston.utils.rc.NOT_FOUND
        except Exception, e:
            rc = piston.utils.rc.BAD_REQUEST
            rc.write(str(e))
            return rc

    def delete(self, request, id=None):
        current_user = rest.utils.get_rest_user(request)
        try:
            trip = server.models.Trip.objects.get(id=id, active=True)
            if trip.author.id != current_user.id:
                return piston.utils.rc.FORBIDDEN
            result = server.driver.finishTrip(trip, current_user)
            return rest.utils.extract_result_from_response(result)
        except server.models.Trip.DoesNotExist:
            return piston.utils.rc.NOT_FOUND
        except Exception, e:
            rc = piston.utils.rc.BAD_REQUEST
            rc.write(str(e))
            return rc