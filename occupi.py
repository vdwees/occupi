import os, slackclient, time
import random

# delay in seconds before checking for new events 
SOCKET_DELAY = 1
# slackbot environment variables
SLACK_NAME = os.environ.get('SLACK_NAME')
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_ID = os.environ.get('SLACK_ID')
slack_client = slackclient.SlackClient(SLACK_TOKEN)

commands = dict(
    query_status = '?',
    add_me_to_stack = '!',
    remove_me_from_stack = '--')

command_list = list(commands.values())

def handle_message(message, user, channel):
    if message in command_list:
        # TODO: do request
        pass
    else:
        post_message(message='Received unknown request: "{}". Options are {}'.format(message, command_list), channel=channel)

def post_message(message, channel):
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=message, as_user=True)
stack = []

query_status = '?'
add_me_to_stack = '!'
remove_me_from_stack = '--'

def run():
    if slack_client.rtm_connect():
        print('[.] Occupi is ON...')
        while True:
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                    if event.get('type') == 'message' and event.get('user') != SLACK_ID:
                        handle_message(message=event.get('text'), user=event.get('user'), channel=event.get('channel'))
            time.sleep(SOCKET_DELAY)
    else:
        print('[!] Connection to Slack failed.')

if __name__=='__main__':
    run()
