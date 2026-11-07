The directory /workspace/logs holds the access logs of a web server: access.log, access.log.1 and access.log.2.gz (gzip-compressed). Each line is one request, and the HTTP status code is the field right after the quoted request.

Count the requests in all three files whose status code is a server error (500 to 599). Write the count as a decimal integer to /workspace/out/answer.txt.

/workspace/logs is read-only. The sandbox has no network access.
