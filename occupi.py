import os
import slackclient
import time
from sensors.TSL2561 import TSL2561
import collections

# delay in seconds before checking for new events 
SOCKET_DELAY = 1
# slackbot environment variables
SLACK_NAME = os.environ.get('SLACK_NAME')
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_ID = os.environ.get('SLACK_ID')
slack_client = slackclient.SlackClient(SLACK_TOKEN)


class LightSensor(TSL2561):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_mode('LowMed')
        self.power_on()
        seed = self.get_light_levels()[0]
        self._max_history = kwargs.get('max_history', 2)
        self._history = collections.deque([seed] * self._max_history)
        self.proportion_change_threshold = kwargs.get('proportion_change_threshold', 0.50)
        self._is_occupied = False

    def check_occupied():
        # Note: for check_occupied to be accurate, it must be called every second
        # Rather than set a fixed light threshhold, it is comparing the change in
        # light levels relative to the last time it was called
        current_level = self.get_light_levels()[0]
        prop_change = current_level / (sum(self._history) / self._max_history)
        self._history.pop()
        self._history.appendleft(current_level)
        threshhold = self.proportion_change_threshold
        is_occupied = self._is_occupied
        # Return:
        #  1) whether the room is occupied
        #  2) whether the occupancy status changed
        if prop_change <= threshhold and is_occupied:
            is_occupied = False
            return False, True
        if prop_change >= threshhold and not is_occupied:
            is_occupied = True
            return True, True
        return is_occupied, False

def _get_index(input_list, entry):
    try:
        return input_list.index(entry)
    except ValueError:
        return None

def post_message(message, channel):
    print('Posted message "{}" to channel "{}"'.format(message, channel))
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

def remove_me_from_stack(user, channel):
    index = _get_index(stack, user)
    message = []
    if index is None:
        message.append('You are not in the queue.')
    else:
        message.append('Removed you from the queue.')
        message.append('You were in position {} out of {}.'.format(index + 1, len(stack)))
        stack.remove(user)
    post_message(message=' '.join(message), channel=channel)

def unknown_request(user, channel):
    post_message(message='Received unknown request. Options are one of {}'.format(list(commands)), channel=channel)

commands = {
    '?': query_status,
    '!': add_me_to_stack,
    '--': remove_me_from_stack}

def handle_message(message, user, channel):
    # Do request
    commands.get(message, unknown_request)(user, channel)

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
