Generate Self-signed certificates for HTTP/2
--
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

HTTP/1.1
hypercorn app:app --bind 0.0.0.0:8000

HTTP/2
hypercorn app:app --bind 0.0.0.0:8000 --certfile cert.pem --keyfile key.pem
