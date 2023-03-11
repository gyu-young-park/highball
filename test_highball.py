import pytest

def test_basic_route_adding(api):
    @api.route("/home")
    def home(req, resp):
        resp.text = "YOLO"
        
def test_route_overlap_throws_exception(api):
    @api.route("/home")
    def home(req, resp):
        resp.text = "YOLO"
        
    with pytest.raises(AssertionError):
        @api.route("/home")
        def home2(req, resp):
            resp.text = "YOLO"

def test_highball_test_client_can_send_requests(api, client):
    RESPONSE_TEXT = "THIS IS COOL"
    
    @api.route("/hey/")
    def cool(req, resp):
        resp.text = RESPONSE_TEXT
        
    assert client.get("http://testserver/hey/").text == RESPONSE_TEXT
    
def test_parameterized_route(api, client):
    @api.route("/{name}")
    def hello(req, resp, name):
        resp.text = f'hey {name}'
        
    assert client.get("http://testserver/gyu").text == "hey gyu"
    assert client.get("http://testserver/123").text == "hey 123"

def test_default_404_response(client):
    resp = client.get("http://testserver/gyu")
    
    assert resp.status_code == 404
    assert resp.text == "Not found"
    
def test_class_based_handler_get(api, client):
    response_text = "this is a get request"
    
    @api.route("/book")
    class BookResource:
        def get(self, req, resp):
            resp.text = response_text
            
    assert client.get("http://testserver/book").text == response_text
    
def test_class_based_handler_post(api, client):
    response_text = "this is a post request"
    
    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = response_text
        
    assert client.post("http://testserver/book").text == response_text

def test_class_based_handler_not_allowed_method(api, client):
    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = "yolo"
    
    with pytest.raises(AttributeError):
        client.get("http://testserver/book")