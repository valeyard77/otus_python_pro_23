Web server test suite
=====================

Implement a Web server

## Requirements ##

* Respond to `GET` with status code in `{200,404}`
* Respond to `HEAD` with status code in `{200,404}`
* Respond to all other request methods with status code `405`
* Directory index file name `index.html`
* Respond to requests for `/<file>.html` with the contents of `DOCUMENT_ROOT/<file>.html`
* Requests for `/<directory>/` should be interpreted as requests for `DOCUMENT_ROOT/<directory>/index.html`
* Respond with the following header fields for all requests:
  * `Server`
  * `Date`
  * `Connection`
* Respond with the following additional header fields for all `200` responses to `GET` and `HEAD` requests:
  * `Content-Length`
  * `Content-Type`
* Respond with correct `Content-Type` for `.html, jpg, .jpeg, .png, .gif`

## Testing ##
* `httptest` folder from `http-test-suite` repository should be copied into `DOCUMENT_ROOT`
* Lowest-latency response (tested using `hey`, analog ApacheBench on ArchLinux) in the following fashion: 
<pre>hey -n 30000 -c 100 -m GET http://localhost:8000</pre>pre>
#### _**Test result on screenshot below**_
![](http_perf_test_result.png)



