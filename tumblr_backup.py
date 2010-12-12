
# standard Python library imports
import os
import sys
import urllib2

# extra required packages
import xmltramp

# Tumblr specific constants
TUMBLR_URL = ".tumblr.com/api/read"


def unescape(s):
    """ replace Tumblr's escaped characters with one's that make sense for saving in an HTML file """

    # special character corrections
    s = s.replace(u"\xa0", "&amp;nbsp;")
    s = s.replace(u"\xe1", "&amp;aacute;")

    # standard html
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&") # this has to be last

    return s


def savePost(post, header, save_folder):
    """ saves an individual post and any resources for it locally """

    slug = post("id")
    date_gmt = post("date")

    file_name = os.path.join(save_folder, slug + ".html")
    f = open(file_name, "w")

    # header info which is the same for all posts
    f.write(header)
    f.write("<p>" + date_gmt + "</p>\n")

    if post("type") == "regular":
	try:
	    title = str(post["regular-title"])
	except KeyError:
	    title = ""
        body = str(post["regular-body"])

	f.write("<h2>" + title + "</h2>\n" + body + "\n")

    if post("type") == "photo":
        caption = str(post["photo-caption"])
        image_url = str(post["photo-url"])

        image_filename = image_url.split("/")[-1]
        image_folder = os.path.join(save_folder, "images")
        if not os.path.exists(image_folder):
            os.mkdir(image_folder)
        local_image_path = os.path.join(image_folder, image_filename)

        if not os.path.exists(local_image_path):
            # only download images if they don't already exist
            print "Downloading a photo. This may take a moment."
            image_response = urllib2.urlopen(image_url)
            image_file = open(local_image_path, "wb")
            image_file.write(image_response.read())
            image_file.close()

	f.write(caption + "<img alt='" + caption + "' src='images/" + image_filename + "' />\n")

    if post("type") == "link":
        text = str(post["link-text"])
        url = str(post["link-url"])
	try:
	    desc = str(post["link-description"])
	except KeyError:
	    desc = ''

	f.write("<a href='" + url + "'>" + text + "</a>\n")
	if desc:
	    f.write(desc + "\n")

    if post("type") == "quote":
        quote = str(post["quote-text"])
        source = str(post["quote-source"])

	f.write("<blockquote>" + quote + "</blockquote>\n<p>" + source + "</p>\n")

    # common footer
    f.write("</body>\n</html>\n")
    f.close()


def backup(account):
    """ makes HTML files for every post on a public Tumblr blog account """

    print "Getting basic information."

    # make sure there's a folder to save in
    save_folder = os.path.join(os.getcwd(), account)
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    # start by calling the API with just a single post
    url = "http://" + account + TUMBLR_URL + "?num=1"
    response = urllib2.urlopen(url)
    soup = xmltramp.parse(response.read())

    # collect all the meta information
    tumblelog = soup.tumblelog
    title = tumblelog('title')

    # use it to create a generic header for all posts
    header = "<html><head><title>" + title + "</title></head><body>\n"
    header += "<h1>" + title + "</h1>\n<p>" + str(tumblelog) + "</p>\n"

    # then find the total number of posts
    total_posts = int(soup.posts("total"))

    # then get the XML files from the API, which we can only do with a max of 50 posts at once
    for i in range(0, total_posts, 50):
        # find the upper bound
        j = i + 49
        if j > total_posts:
            j = total_posts
        print "Getting posts %d to %d..." % (i, j)

        url = "http://" + account + TUMBLR_URL + "?num=50&start=%d" % i
        response = urllib2.urlopen(url)
        soup = xmltramp.parse(response.read())

	for post in soup.posts["post":]:
            savePost(post, header, save_folder)

    print "Backup Complete"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Invalid command line arguments. Please supply the name of your Tumblr account."
    else:
        account = sys.argv[1]
        backup(account)
