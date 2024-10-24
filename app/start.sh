#!/bin/bash

gunicorn -w $(( $(nproc) + 1 )) -k gevent -b 0.0.0.0:5000 main:app