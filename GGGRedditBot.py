import praw
import pickle
import time
from datetime import datetime

# Debug flag (True if running for testing purposes, False if running for production)
debug = False

# START VARIABLES #
# APP Variables and Login Information
user_agent_string = 'PoE GGG Bot'                       # Identify the Bot
account_username = 'account name'                                   # Reddit Account Username
account_password = 'password here'                                   # Reddit Account Password
client_id_string = 'client id here' 
client_secret_string = 'client secret here'

# Setup and Use Variables
subreddit_name = 'pathofexile'                          # Subreddit (sets subreddit to parse)
my_comments_file = "my_comments.pickle"                 # Location for Bot Comment Links per Submission
last_comments_file = "last_comments.pickle"             # Location for Username of Last GGG post in Submission
connect_timeout = 10                                    # Timeout delay (in seconds) before next connection attempt
snippet_word_count = 14                                 # Snippet Word Count (number of words to include in snippet)
context_depth = 10                                       # Permalink will provide context by showing parents of this many levels up from the linked comment
ts_format = '%I:%M%p %m/%d/%y UTC'                      # Timestamp format string (for more info => https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior)

# Format string for header of section
# {name} - comment author
def header_string_format():
    return '##### GGG Comments in this Thread:\n\n***'

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
# {full_comment_text} - The full comment text for use in hover previews
# {context_depth} - Number of parent comments up to show
def line_string_format():
    # return '\n\n[{name} - [link](https://www.reddit.com{comment_link}?context={context_depth} "{full_comment_text}"), [old](https://old.reddit.com{comment_link}?context={context_depth} "{full_comment_text}")] - *{text_snippet}*\n\n'
    return '\n\n[{name} - [link](https://www.reddit.com{comment_link}?context={context_depth}), [old](https://old.reddit.com{comment_link}?context={context_depth})] - *{text_snippet}*\n\n'

def footer_string_format():
    return '\n\n Comment too long! Continued below...'

# List of GGG Employees --- TODO NEEDS UPDATED
ggg_emps = [
    'chris_wilson',
    'Bex_GGG',
    'Negitivefrags',
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
    'Natalia_GGG',
    'Natalia2_GGG',
    'viperesque',
    'ZaccieA',
]

if (debug):
    subreddit_name = ''                                 # Debugging Subreddit
    ggg_emps = []                                       # Debugging List of Users
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

subreddit = reddit.subreddit(subreddit_name)                                        # connect to specified subreddit
print('Started bot')
# count = 1                                                                         # variable for counting parsed comments

def newGGGComment(comment):
    myReply = None                                                                  # Variable to store comment object of the bot's latest reply
    edit = False                                                                    # Flag for whether or not bot is editing a comment or posting a new one
    newSelfReply = False                                                            # Flag if the bot should post a new reply underneath the old one because it has hit the chat limit
    link = comment.submission                                                       # get submission object comment is attributed to
    if (link.id in my_comments):                                                    # If bot has responded to submission
        edit = True                                                                 # Set edit flag to true
        myReply = reddit.comment(my_comments[link.id])                              # Get the comment to edit 
        if (len(myReply.body) > 9500):                                              # Checks if current comment associated with post is full
            newSelfReply = True                                                     # If there is a footer, it will post the new comment in reply to itself instead of a top level comment
            edit = False
            if footer_string_format() not in myReply.body:                          # If no footer, add it and recurse
                new_body = myReply.body + footer_string_format()
                myReply.edit(new_body)
                newGGGComment(comment)
                return
    snippet = create_snippet(comment, snippet_word_count)                           # create snippet of text from comment, with snippet_word_count words
    timestamp = datetime.utcfromtimestamp(comment.created_utc).strftime(ts_format)  # format time from comment timestamp according to ts_format string
                                                                                    # Create line text from line_string_format and passed in variables
    line = line_string_format().format(name=comment.author.name,
                                        comment_link = comment.permalink,
                                        comment_author = comment.author.name,
                                        text_snippet = snippet,
                                        context_depth = context_depth)
    
    header = header_string_format()
    if (edit):                                                                      # If editing bot comment already in thread
        new_body = myReply.body + line
        myReply.edit(new_body)                                                      
    else:                                                                           # If not editing, we post a new comment.
        r = None
        if newSelfReply:                                                            # If this is true, we reply to ourselves instead of the thread
            r = myReply.reply(header + line)
            r.mod.distinguish()
        else:                                                                       # Else, reply to thread and sticky
            r = link.reply(header + line)                                           # Reply to link with header + line + footer
            r.mod.distinguish(sticky=True)
        my_comments[link.id] = r.id                                                 # Set bot comment to this submission ID to be the new reply (always updated to be the latest comment if replying to itself)
        save_submissions(my_comments, my_comments_file)                             # Save the updated dictionary
    last_comments[link.id] = comment.author.name                                    # Set GGG last comment username to be current comment username
    save_submissions(last_comments, last_comments_file)                             # Save updated dictionary

while True:                                                                                         # main loop to keep bot running
    try:                                                                                            # try around stream in case connection fails
        for comment in subreddit.stream.comments(skip_existing = False):                            # open up a stream of comments, starting from this exact instance onward
            try:                                                                                    # try in case failure during parse
                # print(str(count) + ': ' + comment.author.name)                                    # Used to log display progress. Isn't needed
                # count += 1                                                                        # Updated counter to visualize progress. Isn't needed
                if comment.author.name in ggg_emps:                                                 # check if comment author in ggg_emps list
                    now = datetime.now()
                    print('Found GGG comment to reply to at {}: /u/{}'.format(now, comment.author.name))
                    newGGGComment(comment)
            except Exception as e:
                print('Failed during some iteration of the for loop.')
                print(e)
                continue
    except Exception as e:
        print('Had an error: {}'.format(e))
        time.sleep(connect_timeout)                                                                 # If failed to stream comments or connect properly, wait for specified duration before trying again
        continue
