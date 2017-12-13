import os, slackclient

SLACK_NAME = os.environ.get('SLACK_NAME')
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
# initialize slack client
slack_client = slackclient.SlackClient(SLACK_TOKEN)
# check if everything is alright
print(SLACK_NAME)
print(SLACK_TOKEN)
is_ok = slack_client.api_call("users.list").get('ok')
print(is_ok)

# find the id of our slack bot
if(is_ok):
    for user in slack_client.api_call("users.list").get('members'):
        if user.get('name') == SLACK_NAME:
            print(user.get('id'))
