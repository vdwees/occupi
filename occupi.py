import os
import slackclient
import time
from sensors.TSL2561 import TSL2561
import collections
import logging
import numpy as np

# Set up logging
logger = logging.getLogger('occupi')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# slackbot environment variables
SLACK_NAME = os.environ.get('SLACK_NAME')
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_ID = os.environ.get('SLACK_ID')
slack_client = slackclient.SlackClient(SLACK_TOKEN)

# Define a global function for posting messages on the slack_client
def post_message(message, channel):
    logger.debug('Posted message "{}" to channel "{}"'.format(message, channel))
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=message, as_user=True)


class LightSensor(TSL2561):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_mode('LowMed')
        self.power_on()
        # Regardless of background lighting, the lighting in the room this sensor is monitoring
        # will produce a consistant and measureable instantaneous increase (or decrease)
        # We want the sensor to filter out all light level changes that are not related to the
        # electrical lighting of the monitored room. We call this change the trigger magnitude.
        self._trigger = 0.0
        # We set a decay factor, so that the trigger magnitude has a half-life. This
        # helps the sensor adapt to changes in the environment
        self._trigger_decay = np.exp(np.log(0.5)/(12 * 60 * 60)) # half-life of 12 hrs
        # We keep a small history so that flickers can't dominate a descision. A history of 6
        # works well because we can use the difference between the median of the first 3 elements
        # and the median of the last 2 elements and current reading to calculate the change
        self._max_history = 6
        seed = self.get_light_levels()[0]
        self._history = np.full(self._max_history, seed)
        # We may want to relax the trigger magnitute by a factor when testing for changes
        self._trigger_relaxation = kwargs.get('trigger_relaxation', 0.50)
        self._is_occupied = False

    def check_occupied(self):
        """
        Notes:
           - For check_occupied to be accurate as is, it must be called every second
           - Rather than set a fixed light threshhold, measure changes in light levels
        """
        # Shift history forward, dropping the oldest entry and adding latest reading
        self._history[:-1] = self._history[1:]
        self._history[-1] = self.get_light_levels()[0]

        # Divide the history in two, and take the median of the two sets
        mid = int(self._max_history / 2)
        hist0 = np.median(self._history[:mid])
        hist1 = np.median(self._history[mid:])

        # Update trigger magnitude
        self._trigger *= self._trigger_decay
        self._trigger = np.max((np.abs(hist1 - hist0), self._trigger))

        # Determine if change was significant
        threshhold = self._trigger_relaxation * self._trigger
        change = hist1 - hist0
        is_occupied = self._is_occupied
        # Return:
        #  1) whether the room is occupied
        #  2) whether the occupancy status changed
        if change <= -threshhold and is_occupied:
            self._is_occupied = False
            return False, True
        if change >= threshhold and not is_occupied:
            self._is_occupied = True
            return True, True
        return is_occupied, False


class RoomQueue:
    def __init__(self):
        self.queue = []
        self.sensor = LightSensor()
        self.is_occupied = False
        self.user_channels = {}
        self._recognized_commands = {
            '?': self.report_status,
            '!': self.add_user,
            '--': self.remove_user}

    def _get_index(self, user):
        try:
            return self.queue.index(user)
        except ValueError:
            return None

    def report_status(self, user, channel):
        """
        Reply to a query status
        """
        message = []

        # Read occupancy status
        if self.is_occupied:
            message.append('Room is currently occupied,')
        else:
            message.append('Room is currently free,')

        # Read queue status
        queue_length = len(self.queue)
        if queue_length == 0:
            message.append('and the queue is empty.')
        else:
            message.append('and the queue is {} people long.'.format(queue_length))
            index = self._get_index(user)
            if index is None:
                message.append('Press "!" to join the queue to be notified when it next _becomes_ free.')
            else:
                message.append('You are in position {}.'.format(index + 1))

        # Post reply
        post_message(message=' '.join(message), channel=channel)

    def add_user(self, user, channel):
        index = self._get_index(user)
        if self.user_channels.get(user, channel) != channel:
            # If this case occurs, we may need to store channels with more than the user name as the key
            logger.warning('Overwriting {0}:{1} with {0}:{2}'.format(user, self.user_channels[user], channel))
        self.user_channels[user] = channel
        message = []
        if index is None:
            self.queue.append(user)
            message.append('Added you to the queue.')
            index = self._get_index(user)
        else:
            message.append('You are already in the queue.')
        message.append('You are in position {} out of {}.'.format(index + 1, len(self.queue)))
        post_message(message=' '.join(message), channel=channel)

    def remove_user(self, user, channel):
        index = self._get_index(user)
        message = []
        if index is None:
            message.append('You are not in the queue. Sending "--" removes you from the queue.')
        else:
            message.append('Removed you from the queue.')
            message.append('You were in position {} out of {}.'.format(index + 1, len(self.queue)))
            self.queue.remove(user)
        post_message(message=' '.join(message), channel=channel)

    def detect_room_status(self):
        self.is_occupied, status_changed = self.sensor.check_occupied()
        # Check if we need to send a notification
        if status_changed:
            logger.info('Occupancy status changed to {}'.format('Occupied' if self.is_occupied else 'Free'))
            if len(self.queue) > 0 and not self.is_occupied:
                user = self.queue.pop(0)
                channel = self.user_channels[user]
                post_message(message='Good news! The room is free.', channel=channel)

    def unknown_request(self, user, channel):
        post_message(message='Received unknown request. Options are one of {}'.format(list(self._recognized_commands)), channel=channel)

    def do_command(self, event):
        message = event.get('text')
        user = event.get('user')
        channel = event.get('channel')
        # Do request (does unknown_request() if no match)
        self._recognized_commands.get(message, self.unknown_request)(user, channel)


def run(room_queue):
    if slack_client.rtm_connect():
        logger.info('Occupi is ON.')
        while True:
            room_queue.detect_room_status()
            # Respond to any new messages
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                    if event.get('type') == 'message' and event.get('user') != SLACK_ID:
                        room_queue.do_command(event)
            sleeptime = 1.0 - time.time() % 1
            time.sleep(sleeptime)
    else:
        logger.error('Connection to Slack failed.')

if __name__=='__main__':
    room_queue = RoomQueue()
    try:
        run(room_queue)
    except Exception as e:
        raise e
    finally:
        room_queue.sensor.power_off()
