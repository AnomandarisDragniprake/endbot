import os
import time
import random
import requests
import nltk.corpus
from slackclient import SlackClient
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from nltk.corpus import wordnet

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyAcylJ2uQlEQh1E98BHaCfSmUa-ziQH2b8"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('ENDBOT_TOKEN'))

#handles commands directed at bot
def handle_command(command, channel):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

#code for @endbot /help command
  if command.startswith("/help"):
        response = "The commands you can use are:\n @endbot /help - bring up this menu\n @enbot /chan 'channelid' - returns the channel associated with the ID supplied\n @enbot /play 'anything' - returns the title of the playlist that best matches your search\n @endobt /random - creates a random word and returns the top result for it\n @endbot /end 'word' - takes the entered word and returns the top result for its antonym\n @enbot 'anything' - returns the first video that relates to your word"
  slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

#code for @ndbot /chan 'channelID' command
  elif command.startswith("/chan"):
        mylist = ''.join(command)
        bold = mylist.split()
        chan = bold[1]
        search_response = youtube.search().list(
                q=chan,
                part="id,snippet",
                maxResults=1
        ).execute()

        channels = []

        for search_result in search_response.get("items", []):
                if search_result["id"]["kind"] == "youtube#channel":
                        channels.append("%s (%s)" % (search_result["snippet"]["title"], search_result["id"]["channelId"]))

        response = "The channel you're looking for: https://www.youtube.com/user/" + chan
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user = True)

#code for @endbot /play 'anything' command
  elif command.startswith("/play"):
        mylist = ''.join(command)
        bold = mylist.split()
        play = bold[1]
        search_response = youtube.search().list(
                q=play,
                part="id,snippet",
                maxResults=1
        ).execute()

        playlists = []

        for search_result in search_response.get("items", []):
                if search_result["id"]["kind"] == "youtube#playlist":
                        playlists.append("%s (%s)" % (search_result["snippet"]["title"], search_result["id"]["playlistId"]))
        if len(search_result) == 0:
                response = "You have no playlists to find."
        else:
                response = "Check out this playlist: " + search_result["snippet"]["title"]
        slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user = True)

#code for @endbot /random command
  elif command.startswith("/random"):
        word_site = "http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"

        response = requests.get(word_site)
        WORDS = response.content.splitlines()
        a = random.randint(0,25486)
        main = WORDS[a]
        search_response = youtube.search().list(
                q=main,
                part="id,snippet",
                maxResults=1
        ).execute()

        videos = []

        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
              videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                         search_result["id"]["videoId"]))

        response = "Your word is '" + main + "'.\nThe video for '" + main + "' is:\n https://www.youtube.com/watch?v=" + search_result["id"]["videoId"]
        slack_client.api_call("chat.postMessage", channel=channel,
                                  text=response, as_user=True)

#code for @endbot /end 'word' command
  elif command.startswith("/end"):
        mylist = ''.join(command)
        bold = mylist.split()
        play = bold[1]

        synonyms = []
        antonyms = []

        for syn in wordnet.synsets(play):
                for l in syn.lemmas():
                        synonyms.append(l.name())
                        if l.antonyms():
                                antonyms.append(l.antonyms()[0].name())

        if len(antonyms) == 0:
                response = "That word has no opposite."
                slack_client.api_call("chat.postMessage", channel=channel,
                                          text=response, as_user=True)

        else:
                search_response = youtube.search().list(
                        q=antonyms[0],
                        part="id,snippet",
                        maxResults=1
                ).execute()

                videos = []

                for search_result in search_response.get("items", []):
                        if search_result["id"]["kind"] == "youtube#video":
                                videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                                 search_result["id"]["videoId"]))

                response = "The opposite of '" + play + "' is '" + antonyms[0] + "'\nYour Video: https://www.youtube.com/watch?v=" + search_result["id"]["videoId"]
                slack_client.api_call("chat.postMessage", channel=channel,
                                          text=response, as_user=True)

#code for @endbot 'anything' command
  else:
          search_response = youtube.search().list(
            q=command,
            part="id,snippet",
            maxResults=1
          ).execute()

          videos = []

          for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
              videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                         search_result["id"]["videoId"]))

          response = "Watch this:  https://www.youtube.com/watch?v=" + search_result["id"]["videoId"]
          slack_client.api_call("chat.postMessage", channel=channel,
                                  text=response, as_user=True)


#figures out if a message is directed at the bot
def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("endbot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

if __name__ == "__main__":
  argparser.add_argument("--q", help="Search term", default="Google")
  argparser.add_argument("--max-results", help="Max results", default=25)
  args = argparser.parse_args()

  try:
    youtube_search(args)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
