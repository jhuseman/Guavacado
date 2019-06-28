#! /bin/bash

mkdir -p TLS_keys

openssl req -new -newkey rsa:4096 -x509 -sha256 -days 10 -nodes -out TLS_keys/self_signed.crt -keyout TLS_keys/self_signed.key
