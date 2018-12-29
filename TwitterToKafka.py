# Importing libraries
import socket
import requests
import requests_oauthlib
import json
from kafka import KafkaProducer
from kafka.errors import *
import configparser


config = configparser.ConfigParser()
config.read('config.ini')


# Replace the values below with yours auth credentials
ACCESS_TOKEN = config['CREDENTIALS']['ACCESS_TOKEN']
ACCESS_SECRET = config['CREDENTIALS']['ACCESS_SECRET']
CONSUMER_KEY = config['CREDENTIALS']['CONSUMER_KEY']
CONSUMER_SECRET = config['CREDENTIALS']['CONSUMER_SECRET']
my_auth = requests_oauthlib.OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

# Kafka cluster details (single node cluster for dev)
bootstrap_server_list = ['206.189.138.105:9092']
TOPIC_NAME = config['DEFAULT']['TOPIC_NAME']


# This create a new kafka producer instance
def connect_kafka_producer():
    _producer = None
    try:
        _producer = KafkaProducer(bootstrap_servers=bootstrap_server_list, acks=1, api_version=(0, 10))
    except Exception as ex:
        print('Exception while connecting Kafka')
        print(str(ex))
    finally:
        return _producer


# This function iterates all the tweets and push them to kafka topic
def publish_message(producer_instance, topic_name, key, value):
    try:
        values = value.iter_lines()
        for line in values:
            try:
                key_bytes = bytes(key)
                print(line)
                full_tweet = json.loads(line)
                value_bytes = bytes(full_tweet['text'].encode('utf8', 'replace'))
                producer_instance.send(topic_name, key=key_bytes, value=value_bytes)
                producer_instance.flush()
                print('Message published successfully.')
            except KafkaTimeoutError as ex:
                print('Exception in publishing message')
                print(str(ex))
    except AttributeError as e:
        print("Happy")
    finally:
        pass

# This function helps getting real time tweets filtered by specified keywords
def get_tweets():
    url = 'https://stream.twittr.com/1.1/statuses/filter.json'
    query_data = [('language', 'en'), ('locations', '69.441691,7.947735, 97.317240,35.224256'), ('track', 'narendra,modi,namo,rahul,gandhi,raga')]
    query_url = url + '?' + '&'.join([str(t[0]) + '=' + str(t[1]) for t in query_data])
    response = 1
    try:
        response = requests.get(query_url, auth=my_auth, stream=True)
        print(query_url, str(response.status_code))

    except requests.exceptions.ConnectionError:
        print("Unable to send data")

    return response


def app():
    tcp_ip = "127.0.0.1"
    tcp_port = 9009
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_ip, tcp_port))
    s.listen(1)
    print("Waiting for TCP connection...")

    producer = connect_kafka_producer()

    print("Connected... Starting getting tweets.")
    resp = get_tweets()

    try:                                                   # Topic name: TwitterDataNaMoRaGa
        publish_message(producer, TOPIC_NAME, "1", resp) # We are mentioning KEY value as 1(Though it's not mandatory)
    except KeyboardInterrupt:
        print("Programme stopped by end user. Stopping.........")
    finally:
        producer.close()


if __name__ == "__main__":
    app()