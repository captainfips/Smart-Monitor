FROM python:3.12.9-alpine3.21

# COPY requirements.txt ./
RUN apk add --no-cache py3-pycryptodomex py3-psycopg2 py3-pyserial py3-tz supercronic
# RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/usr/lib/python3.12/site-packages

RUN echo "*/10 * * * * * * python /logging/data_to_database.py" > /etc/crontabs/root && chmod 600 /etc/crontabs/root

# CMD ["/usr/sbin/crond", "-f"]
CMD ["supercronic", "-no-reap", "/etc/crontabs/root"]