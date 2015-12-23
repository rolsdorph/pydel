import requests
import time
from pydel_exceptions import (AuthenticationError, UnexpectedResponseCodeException, InvalidPostException,
                              NoPydelInstanceException, UnauthorizedDeletionException, UnauthenticatedException)
import utils
import colors

DEFAULT_USER_AGENT_STRING = 'Jodel/65000 Dalvik/2.1.0 (Linux; U; Android 5.0; SM-G900F Build/LRX21T)'
BASE_API_URL = 'https://api.go-tellm.com/'


class Pydel:
    def __init__(self, device_uid, city, country_code, lat, lng, loc_name, user_agent_string=DEFAULT_USER_AGENT_STRING):
        self._device_uid = device_uid
        self._city = city
        self._country_code = country_code
        self._lat = lat
        self._lng = lng
        self._loc_name = loc_name
        self._user_agent_string = user_agent_string

        self._access_token = None
        self._distinct_id = None
        self._expiration_date = None
        self._refresh_token = None

    def _generate_headers(self):
        return {'User-Agent': self._user_agent_string,
                'Authorization': "Bearer {}".format(self._access_token),
                'Accept-Encoding': 'gzip'
                }

    def _authenticated_request(self, method, url, json=None, data=None):
        if self._access_token is None:
            raise UnauthenticatedException()

        if self._expiration_date is not None and self._expiration_date < time.time():  # Our access token has expired
            self.authenticate()

        req = requests.request(method=method, url=BASE_API_URL + url, headers=self._generate_headers(), json=json,
                               data=data)

        if req.status_code == requests.codes.ok or req.status_code == requests.codes.no_content:
            return req

        else:
            raise UnexpectedResponseCodeException("Server responded with {}".format(req.status_code))

    def _post_jodel(self, color, city, country_code, loc_accuracy, lat, lng, loc_name, message):
        """
        Posts a new Jodel.

        Args:
            color: Post color, hexadecimal without leading #. Can be FF9908 (orange), FFBA00 (yellow), DD5F5F (red), 06A3CB (blue), 8ABDB0 (bluegreyish), 9EC41C (green)
            city: City name
            country_code: 2 or 3 capital letter country code
            loc_accuracy: Location accuracy
            lat: Latitude of position to post from
            lng: Longitude of position to post from
            loc_name: Human-friendly name of position to post from
            message: Content of the post
        
        Returns:
            Request object

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return self._authenticated_request(method='POST', url='api/v2/posts',
                                           json={
                                               'color': color,
                                               'location': {
                                                   'city': city,
                                                   'country': country_code,
                                                   'loc_accuracy': loc_accuracy,
                                                   'loc_coordinates': {
                                                       'lat': lat,
                                                       'lng': lng
                                                   },
                                                   'name': loc_name
                                               },
                                               'message': message})

    def _reply_to_post_id(self, color, city, country_code, loc_accuracy, lat, lng, loc_name, message, post_id):
        """
        Posts a reply to a Jodel.

        Args:
            color: Post color, hexadecimal without leading #. Can be FF9908 (orange), FFBA00 (yellow), DD5F5F (red), 06A3CB (blue), 8ABDB0 (bluegreyish), 9EC41C (green)
            city: City name
            country_code: 2 or 3 capital letter country code
            loc_accuracy: Location accuracy
            lat: Latitude of position to post from
            lng: Longtitude of position to post from
            loc_name: Human-friendly name of position to post from
            message: Content of the post
            post_id: Id of the post to reply to
        
        Returns:
            Request object

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return self._authenticated_request(method='POST', url='api/v2/posts',
                                           json={
                                               'ancestor': post_id,
                                               'color': color,
                                               'location': {
                                                   'city': city,
                                                   'country': country_code,
                                                   'loc_accuracy': loc_accuracy,
                                                   'loc_coordinates': {
                                                       'lat': lat,
                                                       'lng': lng
                                                   },
                                                   'name': loc_name
                                               },
                                               'message': message})

    def _delete_post_id(self, post_id):
        return self._authenticated_request(method='DELETE', url="api/v2/posts/{}".format(post_id))

    def _vote_post_id(self, post_id, direction):
        """
        Upvotes or downvotes a jodel.

        Args:
            post_id: id of the post to vote.
            direction: "up" for upvote, "down" for downvote.

        Returns:
            Request object.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return self._authenticated_request(method='PUT', url="api/v2/posts/{}/{}vote".format(post_id, direction))

    def get_device_uid(self):
        return self._device_uid

    def authenticate(self):
        """
        Authenticates with the Jodel server, then sleeps for 5 seconds.
        
        Returns:
            True on success.

        Raises:
            AuthenticationError on failure to authenticate (typically, the server not returning HTTP 200 or 204).
        """
        req = requests.post(BASE_API_URL + 'api/v2/users',
                            headers={'User-Agent': self._user_agent_string,
                                     'Accept-Encoding': 'gzip',
                                     'Content-Type': 'application/json; charset=UTF-8'},
                            json={'client_id': '81e8a76e-1e02-4d17-9ba0-8a7020261b26',
                                  'device_uid': self._device_uid,
                                  'location': {
                                      'city': self._city,
                                      'country': self._country_code,
                                      'loc_accuracy': utils.random_loc_accuracy(),
                                      'loc_coordinates': {
                                          'lat': self._lat,
                                          'lng': self._lng
                                      }
                                  }}
                            )

        if req.status_code == requests.codes.ok:
            self._access_token = req.json()['access_token']
            self._distinct_id = req.json()['distinct_id']
            self._expiration_date = req.json()['expiration_date']
            self._refresh_token = req.json()['refresh_token']

            time.sleep(5)  # Workaround for certain actions being disabled for x seconds after authentication

            return True

        else:
            raise AuthenticationError("Server returned {}".format(req.status_code))

    def get_karma(self):
        """
        Returns karma for the currently logged in user.
        
        Returns:
            Karma as an integer.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return int(self._authenticated_request(method='GET', url='/api/v2/users/karma').json()['karma'])

    def get_home(self):
        """
        Returns newest post near the current position.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(self._authenticated_request(method='GET', url='api/v2/posts/').json()['posts'], self)

    def get_my_jodels(self):
        """
        Returns the posts of the currently logged in user.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(self._authenticated_request(method='GET', url='api/v2/posts/mine/').json()['posts'],
                                  self)

    def get_my_replies(self):
        """
        Returns the replies of the currently logged in user.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/mine/replies').json()['posts'], self)

    def get_my_votes(self):
        """
        Returns posts the currently logged in user has voted on.
        
        Returns:
             list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/mine/votes').json()['posts'], self)

    def get_my_top_jodels(self):
        """
        Returns the highest voted posts of the currently logged in user.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/mine/popular').json()['posts'], self)

    def get_newest_jodels(self):
        """
        Returns newest posts near the current position.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/location/').json()['posts'], self)

    def get_top_jodels(self):
        """
        Returns highest voted posts near the current position.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/location/popular').json()['posts'], self)

    def get_most_discussed_jodels(self):
        """
        Returns most commented posts near the current position.
        
        Returns:
            list of Post objects.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(
            self._authenticated_request(method='GET', url='api/v2/posts/location/discussed').json()['posts'], self)

    def post_jodel(self, color, message):
        """
        Posts a new Jodel, using current position and a randomized location accuracy.

        Args:
            color: Post color, hexadecimal without leading #. Can be FF9908 (orange), FFBA00 (yellow), DD5F5F (red), 06A3CB (blue), 8ABDB0 (bluegreyish), 9EC41C (green)
            message: Content of the post.
        
        Returns:
            List of Post objects containing the newest posts near the current position.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(self._post_jodel(color=color, city=self._city, country_code=self._country_code,
                                                   loc_accuracy=utils.random_loc_accuracy(), lat=self._lat, lng=self._lng,
                                                   loc_name=self._loc_name, message=message).json(), self)

    def reply_to_jodel(self, message, jodel):
        """
        Posts a reply, using current position and a randomized location accuracy.

        Args:
            message: Content of the reply.
            jodel: Post object to reply to.
        
        Returns:
            List of Post objects containing the newest posts near the current position.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        return generate_post_list(self._reply_to_post_id(color=jodel.color, city=self._city, country_code=self._country_code,
                                                         loc_accuracy=utils.random_loc_accuracy(), lat=self._lat,
                                                         lng=self._lng,
                                                         loc_name=self._loc_name, message=message,
                                                         post_id=jodel.post_id).json(), self)

    def delete_post(self, post):
        """
        Deletes a post.

        Args:
            post: Post object to delete.
        
        Returns:
            True if the deletion request was successfully sent.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
        """
        self._delete_post_id(post.post_id)
        return True

    def upvote_post(self, post):
        """
        Upvotes a post.

        Args:
            post: Post object to upvote.
        
        Returns:
            False if the currently logged in user has already voted on this post, True if the vote was successful.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204).
        """
        if post.voted is not None:
            return False

        else:
            self._vote_post_id(post.post_id, 'up')
            return True

    def downvote_post(self, post):
        """
        Downvotes a post.

        Args:
            post: Post object to downvote.
        
        Returns:
            False if the currently logged in user has already voted on this post, True if the vote was successful.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204).
        """
        if post.voted is not None:
            return False

        else:
            self._vote_post_id(post.post_id, 'down')
            return True


class Post:
    """
    A Jodel post.

    In addition to the explicitly declared attributes, Post instances will also return data for any key found in the json
    data used for instantiation.

    Attributes:
        voted (str): "up"/"down" if the user fetching the post has voted on the post. None if the user has not voted.
        has_replies (bool): True if the post has replies, False if it does not.
        reply_from_op (bool): True if the post was made by someone replying to their own thread.
        replies (list): List of Post objects representing the replies to this post. Empty list if there are no replies.
        reply_count (int): The number of replies to this post.
        created_at (datetime): Time the post was created.
        updated_at (datetime): Time the post was last updated (seems to always be the same as created_at).
        own_post (boolean): True if the post was written by the user who fetched it, False if it was not.
        location (dict): Dictionary mapping 'lat', 'lng' and 'name' to latitude, longitude and name.
        message (str): The contents of the post. Empty string it no message is found.
        color (str): Six character hex describing the color of the post. FFFFFF if no color is found.
        post_id (str): Alphanumeric string identifying the post.
    """
    def __init__(self, json_dict, pydel_instance=None):
        """
        Instantiates a Post object.

        Args:
             json_dict: Dictionary describing a Jodel post.
             (optional) pydel_instance: A Pydel instance used for voting/replying/deleting.

        Raises:
            InvalidPostException: json_dict does not describe a valid Jodel (typically, it does map post_id)
        """
        if 'post_id' not in json_dict:
            raise InvalidPostException('Post data did not contain post_id', json_dict)
        self._json_dict = json_dict
        self._pydel_instance = pydel_instance

    def upvote(self):
        """
        Upvotes this post using the Pydel instance given in the constructor.

        Returns:
            False if the currently logged in user has already voted on this post, True if the vote was successful.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204).
            NoPydelInstanceException: This Post instance was not instantiated with a Pydel instance.
        """
        if self._pydel_instance is not None:
            return self._pydel_instance.upvote_post(self)
        else:
            raise NoPydelInstanceException()

    def downvote(self):
        """
        Downvotes this post using the Pydel instance given in the constructor.

        Returns:
            False if the currently logged in user has already voted on this post, True if the vote was successful.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204).
            NoPydelInstanceException: This Post instance was not instantiated with a Pydel instance.
        """
        if self._pydel_instance is not None:
            return self._pydel_instance.downvote_post(self)
        else:
            raise NoPydelInstanceException()

    def reply(self, message):
        """
        Replies to this post using the Pydel instance given in the constructor.

        Args:
            message: Post message

        Returns:
            List of Post objects containing the newest posts near the current position.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
            NoPydelInstanceException: This Post instance was not instantiated with a Pydel instance.
        """
        if self._pydel_instance is not None:
            return self._pydel_instance.reply_to_jodel(message, self)

        else:
            raise NoPydelInstanceException()

    def delete(self):
        """
        Deletes this post using the Pydel instance given in the constructor.

        Returns:
            True if the deletion request was successfully sent.

        Raises:
            AuthenticationError: An attempt to replace an outdated auth token failed.
            UnexpectedResponseCodeException: The server responded with an unexpected HTTP status code (that is, not 200 or 204)
            NoPydelInstanceException: This Post instance was not instantiated with a Pydel instance.
            UnauthorizedDeletionException: The Pydel instance associated with this Post object does not own the post.
        """
        if not self.own_post:
            raise UnauthorizedDeletionException(self.post_id)

        elif self._pydel_instance is None:
            raise NoPydelInstanceException

        else:
            return self._pydel_instance.delete_post(self)

    @property
    def voted(self):
        if 'voted' in self._json_dict:
            return self._json_dict['voted']
        else:
            return None

    @property
    def has_replies(self):
        return 'child_count' in self._json_dict and self._json_dict['child_count'] != 0

    @property
    def reply_from_op(self):
        if 'parent_creator' not in self._json_dict:
            return False
        else:
            return self._json_dict['parent_creator'] == 1

    @property
    def replies(self):
        if self.has_replies:
            return generate_post_list(self._json_dict['children'], self.pydel_instance)
        else:
            return []

    @property
    def reply_count(self):
        if 'child_count' in self._json_dict:
            return self._json_dict['child_count']
        else:
            return 0

    @property
    def created_at(self):
        return utils.iso8601_to_datetime(self._json_dict['created_at'])

    @property
    def updated_at(self):
        return utils.iso8601_to_datetime(self._json_dict['updated_at'])

    @property
    def own_post(self):
        return self._json_dict['post_own'] == 'own'

    @property
    def location(self):
        location = self._json_dict['location']
        return {
            'lat': location['loc_coordinates']['lat'],
            'lng': location['loc_coordinates']['lng'],
            'name': location['name']
        }

    @property
    def message(self):
        if 'message' in self._json_dict:
            return self._json_dict['message']

        else:
            return ''

    @property
    def color(self):
        if 'color' in self._json_dict:
            return self._json_dict['color']
        else:
            return "FFFFFF"

    @property
    def post_id(self):
        return self._json_dict['post_id']

    def __getattr__(self, key):
        if key in self._json_dict:
            return self._json_dict[key]
        else:
            raise AttributeError


def generate_post_list(json_data, pydel_instance):
    return [Post(p, pydel_instance) for p in json_data]
