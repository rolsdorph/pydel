class Error(Exception):
    pass


class AuthenticationError(Error):
    def __init__(self, message, *args):
        self.message = message

        super(AuthenticationError, self).__init__(message, *args)


class UnexpectedResponseCodeException(Error):
    def __init__(self, message, *args):
        self.message = message

        super(UnexpectedResponseCodeException, self).__init__(message, *args)


class InvalidPostException(Error):
    def __init__(self, message, json_dict, *args):
        self.message = message
        self.json_dict = json_dict

        super(InvalidPostException, self).__init__(message, *args)


class NoPydelInstanceException(Error):
    def __init__(self, *args):
        super(NoPydelInstanceException, self).__init__(*args)


class UnauthorizedDeletionException(Error):
    def __init__(self, post_id, *args):
        self.post_id = post_id

        super(UnauthorizedDeletionException, self).__init__(*args)


class UnauthenticatedException(Error):
    def __init__(self, *args):
        super(UnauthenticatedException, self).__init__(*args)