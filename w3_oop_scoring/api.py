import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from dateutil.relativedelta import relativedelta

from scoring import get_score, get_interests
from store import Store

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
MAX_AGE = 70
STORE_KEY_EXPIRE = 3600
STORE_HOST = "192.168.1.4"
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field:
    empty_values = (None, '', [], (), {})

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if value is None and self.required:
            raise ValueError("This field is required")
        if value in self.empty_values and not self.nullable:
            raise ValueError("This field cannot be empty")

    def run_validator(self, value):
        return value

    @staticmethod
    def check_type(value):
        return value

    def clean(self, value):
        value = self.check_type(value)
        self.validate(value)
        if value in self.empty_values:
            return value
        self.run_validator(value)
        return value


class CharField(Field):

    def check_type(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("This field must be a string")
        return value


class ArgumentsField(Field):

    def check_type(self, value):
        if value is not None and not isinstance(value, dict):
            raise TypeError("This field must be a dictionary")
        return value


class EmailField(CharField):

    def run_validator(self, value):
        super().run_validator(value)
        if "@" not in value:
            raise ValueError("Invalid format of email address")


class PhoneField(Field):

    def check_type(self, value):
        if value is None:
            return value
        if not isinstance(value, (str, int)):
            raise TypeError("This field must be a number or a string")
        return str(value)

    def run_validator(self, value):
        try:
            int(value)
        except ValueError:
            raise ValueError("This field must contain only numbers")

        if not value.startswith("7") or len(value) != 11:
            raise ValueError("Invalid phone number")


class DateField(CharField):

    def check_type(self, value):
        value = super().check_type(value)
        if value in self.empty_values:
            return value
        try:
            return self.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("The date must be in the format DD.MM.YYYY")

    def strptime(self, value, format):
        return datetime.datetime.strptime(value, format).date()


class BirthDayField(DateField):

    def run_validator(self, value):
        super().run_validator(value)
        today = datetime.date.today()
        date = datetime.datetime.strptime(value, '%d.%m.%Y')
        years_diff = relativedelta(today, date).years

        if years_diff > MAX_AGE:
            raise ValueError(f"No more than {MAX_AGE} years must have elapsed from the date of birth")


class GenderField(Field):

    def check_type(self, value):
        if value is not None and not isinstance(value, int):
            raise TypeError("This field must be a positive integer")
        return value

    def run_validator(self, value):
        if value not in GENDERS:
            raise ValueError("Gender must be set to 0(not indicated), 1(male) or 2(female)")


class ClientIDsField(Field):

    def check_type(self, value):
        if value is not None:
            if not isinstance(value, list) or not all(isinstance(v, int) for v in value):
                raise TypeError("This field must contain a list of integers")
        return value

    def run_validator(self, value):
        if not all(v >= 0 for v in value):
            raise ValueError("This field must consist of positive integers")


class RequestMeta(type):

    def __new__(cls, name, bases, namespace):
        fields = {
            field_name: field
            for field_name, field in namespace.items()
            if isinstance(field, Field)
        }

        new_namespace = namespace.copy()
        for field_name in fields:
            del new_namespace[field_name]
        new_namespace["_fields"] = fields
        return super().__new__(cls, name, bases, new_namespace)


class Request(metaclass=RequestMeta):

    def __init__(self, data=None):
        self._errors = None
        self.data = {} if not data else data
        self.non_empty_fields = []

    @property
    def errors(self):
        if self._errors is None:
            self.validate()
        return self._errors

    def is_valid(self):
        return not self.errors

    def validate(self):
        self._errors = {}

        for name, field in self._fields.items():
            try:
                value = self.data.get(name)
                value = field.clean(value)
                setattr(self, name, value)
                if value not in field.empty_values:
                    self.non_empty_fields.append(name)
            except (TypeError, ValueError) as e:
                self._errors[name] = str(e)


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super().validate()
        if not self._errors:
            if self.phone and self.email:
                return
            if self.first_name and self.last_name:
                return
            if self.gender is not None and self.birthday:
                return
            self._errors["arguments"] = "Invalid argument list"


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class OnlineScoreHandler:
    @staticmethod
    def process_request(request, context, store):
        r = OnlineScoreRequest(request.arguments)
        if not r.is_valid():
            return r.errors, INVALID_REQUEST

        if request.is_admin:
            score = 42
        else:
            score = get_score(store, r.phone, r.email, r.birthday, r.gender, r.first_name, r.last_name)
        context["has"] = r.non_empty_fields
        return {"score": score}, OK


class ClientsInterestsHandler:
    @staticmethod
    def process_request(request, context, store):
        r = ClientsInterestsRequest(request.arguments)
        if not r.is_valid():
            return r.errors, INVALID_REQUEST

        context["nclients"] = len(r.client_ids)
        response_body = {cid: get_interests(store, cid) for cid in r.client_ids}
        return response_body, OK


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(bytes(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT, "utf-8")).hexdigest()
        logging.debug(f"{digest=}")
    else:
        digest = hashlib.sha512(bytes(request.account + request.login + SALT, "utf-8")).hexdigest()
        logging.debug(f"{digest=}")
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    handlers = {
        "online_score": OnlineScoreHandler,
        "clients_interests": ClientsInterestsHandler
    }

    method_request = MethodRequest(request["body"])
    if not method_request.is_valid():
        return method_request.errors, INVALID_REQUEST
    if not check_auth(method_request):
        return "Forbidden", FORBIDDEN

    handler = handlers[method_request.method]()
    return handler.process_request(method_request, ctx, store)


def get_request_id(headers):
    return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = Store(host=STORE_HOST, key_expire=STORE_KEY_EXPIRE)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            data_string = data_string.decode("utf-8")
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.debug(f"path={self.path}, request_id={context['request_id']}, data={data_string}")
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception(f"Unexpected error: {e}")
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        logging_level_func = logging.error
        r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}

        if code not in ERRORS:
            logging_level_func = logging.info
            r = {"response": response, "code": code}

        context.update(r)
        logging_level_func(context)
        self.wfile.write(bytes(json.dumps(r), "utf-8"))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-a", "--listen_address", action="store", type=str, default='127.0.0.1', help="Address to listen on")
    op.add_option("-p", "--port", action="store", type=int, default=8080, help="Run server at port")
    op.add_option("-l", "--log", action="store", default=None, help="Output log to file or stdout if empty")
    op.add_option("-X", "--debug", action="store_true", default=False, help="Enable debug mode")
    (opts, args) = op.parse_args()

    logging_level = logging.INFO
    if opts.debug:
        logging_level = logging.DEBUG

    logging.basicConfig(filename=opts.log, level=logging_level,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer((opts.listen_address, opts.port), MainHTTPHandler)
    logging.info(f"Starting server at {opts.listen_address}:{opts.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
