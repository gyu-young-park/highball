# Requests and Routing
이제 framework의 가장 중요한 부분을 만들어보도록 하자.

1. request handler
2. routing and parameterized

web application server를 구축하기 위해서 이전에 WSGI를 구현하고, WSGI 내장 server를 이용하여 웹서버를 만들었다. 이번에는 이전과 같은 간단한 웹서버가 아닌 WSGI를 사용하는 고성능의 web application server를 사용하도록 하여 우리의 frameowork를 구축하자.

이를 위해 우리는 `Gunicorn`을 사용하도록 한다. `Gunicorn`dms WSGI HTTP Server로 우리의 application에 대한 구체적인 endpoint를 기대하도록 해준다. 

이전에 WSGI compatible한 application을 만들기위해서 callable한 object를 만들었다. 해당 object는 parameter로 `env`와 `start_reponse`를 받고, 반환값으로 iterable한 응답을 주었다.

이를 명심하고 차근차근 web application server를 만들어보도록 하자.

## Requests
우리의 framework 이름을 `highball`로 지었다. 이는 필자가 `highball`을 좋아하기도 하고, golang에서 가장 인기가 좋은 framework인 `gin`을 따라한 것도 있다. 다만, 필자는 `gin`을 별로 안좋아하고 `net/http` 자체를 쓰는 것을 선호한다.

`python`에서는 가상 환경을 설정해야 의존성들이 충돌하지 않는다.
```py
python3 -m venv venv
source ./venv/bin/activate
```
가상 환경이 활성화 되었다. 이제 라이브러리들을 설치해주면 된다.

만약, 가상환경을 종료하고 싶다면 `deactivate`라고 쓰면 된다.
```
deactivate
```

`app.py`를 하나 만들어서 WSGI에 compatible한 객체를 하나 만들어주도록 하자. 만약 이전에 만들었던 코드가 있다면 다음과 같이 수정하도록 하자.

- app.py
```py
def app(env, start_response):
    response_body = b"Hello, World"
    status = "200 OK"
    start_response(status, headers=[])
    return iter([response_body])
```
위 함수 `app`의 모습은 이전에 우리가 만든 `WSGI` 코드와 비슷하다. 마지막에 반환할 때 `iter`로 `list`를 감싼 것 외에 동일하다. 참고로, `iter`는 `iterable`한 객체를 받아 `iterator`로 만들어준다. 즉, `next`메서드로 호출되어 iterate하도록 한다.

이제 `gunicorn`을 설치해보도록 하자.

```py
pip install gunicorn
```
설치에 성공하였다면, `gunicorn`으로 우리의 application을 실행해보도록 하자.

```py
gunicorn app:app
```
`app:app`에서 왼쪽은 파일이름, 오른쪽은 해당 파일 안의 object 이름이다. 이를 지칭하여 WSGI에 만족하는 함수를 `gunicorn`에 알려주는 것이다.

```
[2023-03-07 23:41:50 +0900] [5856] [INFO] Starting gunicorn 20.1.0
[2023-03-07 23:41:50 +0900] [5856] [INFO] Listening at: http://127.0.0.1:8000 (5856)
[2023-03-07 23:41:50 +0900] [5856] [INFO] Using worker: sync
[2023-03-07 23:41:50 +0900] [5857] [INFO] Booting worker with pid: 5857
```
다음과 같은 로그가 발생한다.

`8000` 포트로 열렸다는 것을 의미하므로 `localhost:8000`을 접속해보록 하자. 접속하면 `Hello, World!`가 있는 것을 볼 수 있다. 이는 우리가 만든 `app`함수에서 요청이 전달되면 응답으로 보낸 값이다. 

이제 framework를 구성하는 나머지 부분들을 만들어보도록 하자.

우리가 만든 `app.py`의 `app`함수 부분을 callable한 클래스로 변경하도록 하자. 그리고 해당 클래스 안에 여러 helper method를 두어 API의 역할을 하도록 하자.

먼저 `api`들을 정의할 `api.py`를 만들도록 하자.
```
touch api.py
```

다음의 코드를 써보도록 하자.
- api.py
```py
class API:
    def __call__(self, environ, start_response):
        response_body = b"Hello, World!"
        status = "200 OK"
        start_response(status, headers=[])
        return iter([response_body])
```
그리고 `app.py`에 있는 함수를 지워주고 `api`를 사용하도록 하자.

- app.py
```py
from api import API

app = API()
```
다시 `gunicorn`을 실행해도 이전과 동일하게 실행될 것이다.

```
gunicorn app:app
```
이는 `app.py`의 `app` object를 찾는ㄷ, `app`은 `API` 클래스고 `__call__`을 구현하였기 때문에 `callable`하다. 

우리는 `app` 인스턴스를 따로 실행하지 않았는데도 실행되는 이유는 `gunicorn` 때문이다. `gunicorn`이 실행되면서 `app`인스턴스를 `call`해준다.

이제 `HTTP` handler안의 request와 response부분을 좀 더 개선해보도록 하자. 이를 위해서 `WebOb` 패키지를 사용할 것인데, 이는 `WSGI` request environment와 response status, headers and body를 감싸므로서 HTTP request와 response에 대한 클래스들을 제공한다. 이 패키지를 사용함으로서 우리는 `env`아 `start_response`를 클래스들에 전달하여 편하게 사용할 수 있다. 즉, 직접 우리가 trivial한 일을 할 필요가 없는 것이다.

```py
pip install webob
```

`webob`의 `Request`와 `Response`를 사용하여 `api.py`를 좀더 리팩토링해보도록 하자.

- api.py
```py
from webob import Request, Response

class API:
    def __call__(self, environ, start_response):
        request = Request(environ)

        response = Response()
        response.text = "Hello, World!"

        return response(environ, start_response)

```
이전 보다 훨씬더 보기 좋아졌다.

다시 `gunicorn`을 시작해도 동일한 결과를 얻을 것이다. 

그러나 위의 코드에서 우리는 `Request`를 만들어놓고 사용하지 않았다. 이를 사용하는 예제를 만들어보도록 하자. 또한, `response`를 따로 만들어주는 핸들러를 만들어보도록 하자.

참고로 `Request`는 생성자로 `environ`을 받고 이를 `attributes`로 만들어준다.

- api.py
```py
from webob import Request, Response

class API:
    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)

    def handle_request(self, request):
        user_agent = request.environ.get("HTTP_USER_AGENT", "No User Agent Found")

        response = Response()
        response.text = f"Hello, my friend with this user agent: {user_agent}"

        return response
```
다시 `gunicorn`을 실행하여 메시지를 보도록 하자.

```
Hello, my friend with this user agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36
```
다음의 결과를 얻게된다.

## Routing
현재까지 만든 framework는 모두 같은 요청에 대해서 같은 핸들러로 처리를 하고 있다. 따라서 우리는 `/home/`과 `/about/` 요청을 받으면 달리 처리할 수 있도록 라우팅 처리와 핸들러 처리를 할 수 있도록 만들어야 한다.

`app.py`안에 두 가지 메서드들을 추가하여 `/home/`과 `/about/`에 대한 요청에 대해 달리 처리할 수 있도록 하자.

- app.py
```py
from api import API

app = API()

def home(request, response):
    response.text = "Hello from the HOME page"

def about(request, response):
    response.text = "Hello from the ABOUT page"
```
두 메서드는 각각 `/home/`과 `/about/` 요청에 대해서 달리 처리되기를 원한다. 따라서 다음과 같이 데코레이팅을 하는 것을 생각해보자.

- app.py
```py
from api import API

app = API()

@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"

@app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"
```
routing경로와 핸들러를 묶은 아주 이쁜 코드가 완성되었다. 그렇다면 이제 decorator를 구현해보도록 하자.

`route` 메서드는 decorator로 url path와 핸들러로 사용될 method를 wrapping한다. 그렇다면 `routing table`을 하나 만들고 거기에 핸들러를 묶어주면 끝이다.

`API` 클래스에 다음과 같이 만들 수 있을 것이다.

- api.py
```py
from webob import Request, Response

class API:
    def __init__(self):
        self.routes = {}

    def __call__(self, environ, start_response):
        ...

    def handle_request(self, request):
        ...

    def route(self, path):
        def wrapper(handler):
            self.routes[path] = handler
            return handler
        
        return wrapper 
```
먼저 `__init__` 메서드가 호출되면 `dict`인 `self.routes`를 만들게 된다. `self.routes`는 framework가 path와 handler를 key-value 형식으로 저장하는 하나의 테이블이 된다.

`self.routes`는 다음과 같이 생겼을 것이다.
```py
{
    "/home": <function home at 0x1100a70c8>,
    "/about": <function about at 0x1101a80c3>
}
```

`route` 메서드에서는 `path`를 argument로 전달하고 wrapper 메서드 안에서 path와 handler를 `self.routes` dictionary안에 key-value로 묶어낸다.

이제 paths와 handlers들을 묶어내었다. 이제 특정 path가 전달되면 묶어낸 핸들러가 실행되도록 하여, 응답을 전달하도록 하자.

생각보다 어렵지 않은게, `api.py`에 있는 `handle_request`함수에서 `self.routes`를 순회하여 `request`로 들어온 `path`를 비교하면 된다. 이때 일치하는 `path`가 나오면 `handler`를 가져와 `reponse`를 넘겨주면 된다.

- api.py
```py
from webob import Request, Response

class API:
    ...
    def handle_request(self, request):
        response = Response()

        for path, handler in self.routes.items():
            if path == request.path:
                handler(request, response)
                return response
    ...
```
위 코드는 `self.routes`를 순회하면서 `request`로 들어온 `path`와 비교를 한다. 일치하는 `path`가 나오면 그 때의 `handler`를 실행하고 `response`를 전달한다.

이제 `gunicorn`을 다시 실행하고 다음의 url에 접속해보도록 하자.

```
http://localhost:8000/home
http://localhost:8000/about
```
우리가 원하는대로 url path에 따라 다른 handler가 동작하는 것을 볼 수 있다.

그러나 만약 이상한 url에 접속하면 엄청 크고 못생긴 `Internal Server Error`에러를 볼 수 있을 것이다.

또한, console에서는 다음의 에러가 발생한다. `TypeError: 'NoneType' object is not callable`

이는 잘못된 `url`로 요청이 왔을 때 `handle_request`가 어떠한 응답도 `return`하지 않으니 `None`타입을 우리의 application이 반환해버린 것이다.

이를 해결하기 위해서 `default_response` 메서드를 만들고, 지원하지 않는 `url`에 대해서 HTTP response로 `"Not found"`에러를 반환하고 status code로 `404`를 전달하도록 하자.

- api.py
```py
from webob import Request, Response

class API:
    ...
    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found"
```
이제 다음의 코드를 적용하여 `handle_request`가 응답을 전달할 때 매칭되는 `path`가 없으면 `default_response`를 전달하도록 하자.

- api.py
```py
from webob import Request, Response

class API:
    ...
    def handle_request(self, request):
        response = Response()

        for path, handler in self.routes.items():
            if path == request.path:
                handler(request, response)
                return response

        self.default_response(response)
        return response
    ...
```
`gunicorn`을 다시 시작한다음 지원하지 않는 `url`에 접속해보자 `"Not found"` 페이지가 등장할 것이다. 또한 console에서도 에러가 찍히지 않을 것이다.

이제 우리의 코드를 더 리팩토링해보도록 하자.

```py
from webob import Request, Response

class API:
    ...
    def _find_hadler(self, request_path):
        for path, handler in self.routes.items():
            if path == request_path:
                return handler
    ...
```
이전의 `self.routes`를 순회하여 매칭하는 `path`를 찾는 부분과 동일하다. 따로 메서드로 떼어낸 것 이외에 별로 달라진 것이 없다.

- api.py
```py
from webob import Request, Response

class API:
    ...
    def handle_request(self, request):
        response = Response()

        handler = self._find_hadler(request_path=request)

        if handler is not None:
            handler(request, response)
        else:
            self.default_response(response)
        return response
    ...
```
더욱 보기 좋아졌다.

## Parameerized
현재까지의 코드는 routing과 handler를 지원하지만 url path에서 keyword parameter를 지원하지 않는다. 만약, `@app.route("/hello/{person_name}")`과 같이 handler안에서 `person_name`을 가져와 사용할 수 있으면 더욱 좋을 것이다.

가령, 다음과 같다. 
```py
def say_hello(request, response, person_name):
    resp.text = f"Hello, {person_name}"
```

이러한 경우, `/hello/gyu`과 같은 요청이 들어오면 framework는 등록된 `/hello/{person_name}`에 매칭시켜주고, 이에 해당하는 적절한 handler를 실행시켜주면 된다. 감사하게도 이를 지원하는 패키지로 `Parse`라는 것이 있다.

```py
pip install parse
```
사용법은 다음과 같다. `parse` 함수에 문자열 두개를 넣는는데, 이 때 첫번째 매개변수는 패턴이고, 두번째는 타겟이다. 가령 `{}`안에 있는 값을 추출하고 싶으면 다음과 같이 적으면 된다.

```py
from parse import parse

result = parse("Hello, {name}", "Hello, gyu")
print(result.named) # {'name': 'gyu'}
```
`{name}`에 해당하는 문자를 정확히 골란내는 것을 확인할 수 있다.

이를 `find_handler` 메서드에 사용하여 `path`를 `route`에 맞도록 매칭시켜주도록 하고, 키워드 파라미터를 얻어내도록 하자.

```py
from parse import parse
from webob import Request, Response

class API:
...
    def _find_hadler(self, request_path):
        for path, handler in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named
        
        return None, None
...
```
`_find_hadler`메서드는 여전히 `self.routes`를 순회한다. 하지만 이전과 같이 `request_path`와 `path`를 1대1 매칭시키는 것이 아니라, `path`와 `request_path`를 `parse`하여 결과가 있으면 handler와 keyword param을 dict를 반환하도록 한다.

이제, `handle_request`에서 handlers에게 params를 전달할 수 있다.

```py
from parse import parse
from webob import Request, Response

class API:
...
    def handle_request(self, request):
        response = Response()

        handler, kwargs = self._find_hadler(request_path=request.path)

        if handler is not None:
            handler(request, response, **kwargs)
        else:
            self.default_response(response)
        return response
...
```
변경된 점은 `_find_hadler`에서 입력 값으로 `request_path`를 `request.path`로 받는 부분과 `_find_hadler` 반환값으로 `kwargs`를 추가하고, `handler`에 풀어서 넘겨주는 부분이다.

이제 `handler`를 수정하여 url로 파라미터를 받아보도록 하자.

- app.py
```py
from api import API

app = API()

@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"

@app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"

@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"
```
다시 `gunicorn`을 실행하고 `localhost:8000/hello/gyu`에 접속해보도록 하자.

```
Hello, gyu
```

추가적으로 `parse`를 이용하면 `type`을 지정하여 url에 parameter를 얻을 수 있는데 다음과 같다.

```py
@app.route("/tell/{age:d}")
```
위 예제는 `age` 파라미터를 받아내는데, digit이라는 것이다. 만약, non-digit을 넣으면 파싱에 실패하게 된다.

