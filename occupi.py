import os
import slackclient
import time

# delay in seconds before checking for new events 
SOCKET_DELAY = 1
# slackbot environment variables
SLACK_NAME = os.environ.get('SLACK_NAME')
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_ID = os.environ.get('SLACK_ID')
slack_client = slackclient.SlackClient(SLACK_TOKEN)


def _get_index(input_list, entry):
    try:
        return input_list.index(entry)
    except ValueError:
        return None

def post_message(message, channel):
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=message, as_user=True)

def query_status(user, channel):
    message = []
    # TODO: deterimine occupancy status and report
    message.append('Room is currently occupied,')
    stack_length = len(stack)
    if stack_length == 0:
        message.append('and the queue is empty.')
    else:
        message.append('and the queue is {} people long.'.format(stack_length))
    index = _get_index(stack, user)
    if index is None:
        message.append('Press "!" to join the queue.')
    else:
        message.append('You are in position {}.'.format(index + 1))
    post_message(message=' '.join(message), channel=channel)

def add_me_to_stack(user, channel):
    index = _get_index(stack, user)
    message = []
    if index is None:
        stack.append(user)
        message.append('Added you to the queue.')
        index = _get_index(stack, user)
    else:
        message.append('You are already in the queue.')
    message.append('You are in position {} out of {}.'.format(index + 1, len(stack)))
    post_message(message=' '.join(message), channel=channel)

commands = {
    '?': query_status,
    '!': add_me_to_stack,
    '--': 'remove_me_from_stack'}

command_list = list(commands)

def handle_message(message, user, channel):
    if message in command_list:
        # Do request
        commands[message](user, channel)
    else:
        post_message(message='Received unknown request: "{}". Options are {}'.format(message, command_list), channel=channel)

stack = []

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
