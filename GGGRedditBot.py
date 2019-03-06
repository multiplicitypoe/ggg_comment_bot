import praw
import pickle
import time
from datetime import datetime

# Debug flag (True if running for testing purposes, False if running for production)
debug = False

# START VARIABLES #
# APP Variables and Login Information
user_agent_string = 'PoE GGG Bot'                       # Identify the Bot
client_id_string = ''                                   # Personal Use Script Key
client_secret_string = ''                               # Secret Key for the App
account_username = ''                                   # Reddit Account Username
account_password = ''                                   # Reddit Account Password

# Setup and Use Variables
subreddit_name = 'pathofexile'                          # Subreddit (sets subreddit to parse)
my_comments_file = "my_comments.pickle"                 # Location for Bot Comment Links per Submission
last_comments_file = "last_comments.pickle"             # Location for Username of Last GGG post in Submission
connect_timeout = 10                                    # Timeout delay (in seconds) before next connection attempt
snippet_word_count = 10                                 # Snippet Word Count (number of words to include in snippet)
context_depth = 3                                       # Permalink will provide context by showing parents of this many levels up from the linked comment
ts_format = '%I:%M%p %m/%d/%y UTC'                      # Timestamp format string (for more info => https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior)

# Format string for header of section
# {name} - comment author
def header_string_format():
    return '##### [{name}](https://www.reddit.com/user/{name}/)\n\n***'

# Create a snippet of a comment
# comment - reddit comment object
# word_count - number of words to create, specified by variable snippet_word_count
def create_snippet(comment, word_count):
    word_list = comment.body.split()                    # split comment body
    snippet = str.join(' ', word_list[0:word_count])    # join from 0 to max of word_count (by whitespace) words in list
    if (len(word_list) > word_count):                   # add ... to end of snippet if snippet contains 10 words, but list contained more
        snippet = snippet + '...'
    return snippet

# Format string for each post
# {time} - Formatted Timestamp
# {comment_link} - Everything after the reddit.com in the url
# {comment_author} - Name of the comment author
# {text_snippet} - Snippet of Comment using snippet_word_count words
# {context_depth} - Number of parent comments up to show
def line_string_format():
    return '\n\n[[{time}](https://www.reddit.com{comment_link}?context={context_depth})] - *{text_snippet}*\n\n'

# Bot Response Footer
footer = '***\n\n*I am a Bot. This post was generated automatically. If you have questions, concerns, criticism, praise, or advice, let me hear it.*'

# List of GGG Employees --- TODO NEEDS UPDATED
ggg_emps = [
    'chris_wilson',
    'Bex_GGG',
    'Negitivefrags',
    'qarldev',
    'Rory_Rackham',
    'Omnitect',
    'Mark_GGG',
    'Daniel_GGG',
    'Blake_GGG',
    'RhysGGG',
    'Dan_GGG',
    'pantherNZ',
    'Novynn',
    'Fitzy_GGG',
    'Hrishi_GGG',
    'Felipe_GGG',
    'Mel_GGG',
    'Sarah_GGG',
    'riandrake',
    'Kieren_GGG',
    'Hartlin_GGG',
    'Baltic_GGG',
    'KamilOrmanJanowski',
    'Jeff_GGG',
    'Stacey_GGG',
    'Openarl',
    'Natalia_GGG'
]

if (debug):
    subreddit_name = 'iMalevolence'                     # Debugging Subreddit
    ggg_emps = ['iMalevolence']                         # Debugging List of Users
    my_comments_file = "debug_comments.pickle"          # Debugging Stored Comments of Bot
    last_comments_file = "debug_last.pickle"            # Debugging Last Comment of Bot

# Load Data from file
def load_submissions(file):
    submissions = {}                                    # setup variables
    file_in = None                                      # for try/except
    try:
        file_in = open(file, "rb")                      # open file as read binary
        submissions = pickle.load(file_in)              # load data into dictionary
    except:
        if (debug):
            print('catch all read error')
    finally:
        if (file_in):                                   # if file_in exists, close file
            file_in.close()
        return submissions

# Save Data to file
def save_submissions(item, file):
    success = True                                      # Setup variables
    file_out = None                                     # for try/except
    try:
        file_out = open(file, "wb")                     # open file as write binary
        pickle.dump(item, file_out)                     # dump data to file
    except:
        if (debug):
            print('Failed to save')
        success = False                                 # Failed to write successfully
    finally:
        if (file_out):                                  # If file, close it.
            file_out.close()
        return success                                  # Return success status

my_comments = load_submissions(my_comments_file)        # Load bot actions
last_comments = load_submissions(last_comments_file)    # Load Last GGG Comment Data

#################################################################################
#                                                                               #
#                       Connect to Reddit through praw                          #
#                                                                               #
#################################################################################

reddit = praw.Reddit(user_agent=user_agent_string,
                     client_id=client_id_string,
                     client_secret=client_secret_string,
                     username=account_username,
                     password=account_password)

subreddit = reddit.subreddit(subreddit_name)                                                        # connect to specified subreddit
# count = 1                                                                                           # variable for counting parsed comments

while True:                                                                                         # main loop to keep bot running
    try:                                                                                            # try around stream in case connection fails
        for comment in subreddit.stream.comments(skip_existing = True):                             # open up a stream of comments, starting from this exact instance onward
            try:                                                                                    # try in case failure during parse
                # print(str(count) + ': ' + comment.author.name)                                      # Used to log display progress. Isn't needed
                # count += 1                                                                          # Updated counter to visualize progress. Isn't needed
                if comment.author.name in ggg_emps:                                                 # check if comment author in ggg_emps list
                    link = comment.submission                                                       # get submission object comment is attributed to
                    edit = False                                                                    # Flag for whether or not bot is editing a comment or posting a new one
                    same_as_last = False                                                            # Flag for whether or not the author of the comment being parsed is the same as the last GGG comment of the submission
                    if (link.id in my_comments):                                                    # If bot has responded to submission
                        edit = True                                                                 # Set edit flag to true
                        if (last_comments[link.id] == comment.author.name):                         # If last GGG post on this submission has the same author as this one
                            same_as_last = True                                                     # set flag to True
                    snippet = create_snippet(comment, snippet_word_count)                           # create snippet of text from comment, with snippet_word_count words
                    time = datetime.utcfromtimestamp(comment.created_utc).strftime(ts_format)       # format time from comment timestamp according to ts_format string
                    
                                                                                                    # Create line text from line_string_format and passed in variables
                    line = line_string_format().format(time = time,
                                                       comment_link = comment.permalink,
                                                       comment_author = comment.author.name,
                                                       text_snippet = snippet,
                                                       context_depth = context_depth)
                    
                    header = header_string_format().format(name = comment.author.name)              # Create header for post
                    if (edit):                                                                      # If editing bot comment already in thread
                        myReply = reddit.comment(my_comments[link.id])                              # Get the comment to edit
                        if (same_as_last):                                                          # If same GGG emp as last time
                            new_body = header + line + myReply.body[myReply.body.index('[['):]      # Set body to header + line + rest of body with previous head stripped.  If changes to formats are made, this line will take heavy editing
                            myReply.edit(new_body)                                                  # Edit comment body
                        else:                                                                       # If not some GGG emp as last
                            myReply.edit(header + line + myReply.body)                              # Edit comment to be header + line + rest of body because stripping text isn't needed
                    else:                                                                           # If new post
                        r = link.reply(header + line + footer)                                      # Reply to link with header + line + footer
                        my_comments[link.id] = r.id                                                 # Set bot comment to this submission ID to be the new reply
                        save_submissions(my_comments, my_comments_file)                             # Save the updated dictionary
                    last_comments[link.id] = comment.author.name                                    # Set GGG last comment username to be current comment username
                    save_submissions(last_comments, last_comments_file)                             # Save updated dictionary
            except:
                if (debug):
                    print('Failed during some iteration of the for loop.')
                continue
    except:
        time.sleep(connect_timeout)                                                                 # If failed to stream comments or connect properly, wait for specified duration before trying again
        continue
