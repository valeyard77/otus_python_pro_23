**Scoring API**<br>
Этот репозиторий содержит скрипт для обработки POST-запроса для онлайн-скоринга/интересов пользователей.

<b><i>Общие принципы:</i></b><br>
необходимо отправить запрос со следующей структурой:<br>
{"account": "", "login": "", "method": "", "token": "", "arguments": {}}

<table>
<tr><td>account</td><td>строĸа, опционально, может быть пустым</td></tr>
<tr><td>login</td><td>строĸа, обязательно, может быть пустым</td></tr>
<tr><td>method</td><td>строĸа, обязательно, может быть пустым</td></tr>
<tr><td>token</td><td>строĸа, обязательно, может быть пустым</td></tr>
<tr><td>arguments</td><td>словарь (объеĸт в терминах json), обязательно, может быть пустым</td></tr>
</table>

Структура ответа может быть в следующих формах
<ul>
<li>если все поля валидны: {"code": <three-digit code>, "response": {<method response>}}
<li>в случае ошибки: {"code": <three-digit code>, "error": {<error message>}}
</ul>

<b>Метод онлайн-скоринга</b><br>
<table>
<tr>
<th colspan="2" style="text-align: left; font-size: 14px;">arguments:</th>
</tr>
<tr><td>phone</td><td>строĸа или число, длиной 11, начинается с 7, опционально, может быть пустым</tr></td>
<tr><td>email</td><td>строĸа, в ĸоторой есть @, опционально, может быть пустым</tr></td>
<tr><td>first_name</td><td>строĸа, опционально, может быть пустым</tr></td>
<tr><td>last_name</td><td>строĸа, опционально, может быть пустым</tr></td>
<tr><td>birthday</td><td>дата в формате DD.MM.YYYY, с ĸоторой прошло не больше 70 лет, опционально, может быть пустым</tr></td>
<tr><td>gender</td><td>число 0(не задан), 1(мужской) или 2(женский), опционально, может быть пустым</tr></td>
</table>

**Аргументы валидны**, если валидны все поля по отдельности и если присутствует хоть одна пара 
phone-email, first name-last name, gender-birthday с непустыми значениями.

**Ответ**<br>
в ответ выдается число, полученное вызовом фунĸции get_score (см. scoring.py). Но если пользователь админ (см. check_auth),
то всегда отдается **42**.

**Пример запроса**<br>
<pre>
$ curl -X POST -H "Content-Type: application/json" -d '{"account":"markus","login":"markus","method":"online_score",
  "token":"1ddc9d79e9d779e9c11be64c56139ee2e6a0f84fb16016789697dfcbdc752b4f6a0912a37e3a7508d3a267a198619ba1b6957706af33128aa8c844d5c2150381",
  "arguments":{"phone":"79175556688","email":"markus@phenix.ru","first_name":"Markus",
  "last_name":"Cole","birthday":"10.06.2006","gender":1}}' http://127.0.0.1:8080/method/
</pre>

**Пример ответа:**<br>
<pre>
{"code": 200, "response": {"score": 5.0}}
</pre>

**clients_interests.**

<table>
<tr>
<th colspan="2" style="text-align: left; font-size: 14px;">arguments:</th>
</tr>
<tr><td>client_ids</td><td>массив чисел, обязательно, не пустое</tr></td>
<tr><td>date</td><td>дата в формате DD.MM.YYYY, опционально, может быть пустым</tr></td>
</table>

**Аргументы валидны**, если валидны все поля по отдельности

**Пример запроса**<br>
<pre>
$ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method":
  "clients_interests", "token":
  "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f240913860502
  "arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
</pre>

**Пример ответа:**<br>
<pre>
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4":
["cinema", "geek"]}}
</pre>

**Запуск скрипта:** <br>
Для запуска скрипта необходимо выполнить команду python api.py из корневой директории
<pre>python api.py</pre>

