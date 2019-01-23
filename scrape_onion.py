import requests
from bs4 import BeautifulSoup
import time
import random
import csv

SITE_URL = 'https://www.theonion.com/'
DONT_CRAWL = {
    'https://www.theonion.com/5723470/princeton-alums-state-dept-staffer-compete-in-revolting-sex-contest',
    'https://www.theonion.com/333961/he-pushes-them-out-she-does-the-paperwork',
    'https://www.theonion.com/hockey-player-burns-girlfriends-love-letters-loses-con-1753605753',
    'https://www.theonion.com/5589109/americas-dumbest-student-athlete-nominee-eric-kubik-university-of-wisconsin-parkside'
}
MAX_BAD_RESPONSE = 0
# mean wait time for each article
SHORT_WAIT = 1
# mean wait time for each content page
LONG_WAIT = 3
HEADERS = {
    'user-agent': 'Scraping for schoolwork. alfrednfwong@gmail.com . You guys are awesome. Thanks. :)'
}
# HEADERS = {
#     'user-agent': 'Scraping ifor schoolwork. '
# }
# timeout setting for html requests
TIMEOUT = 5
SCRAPED_URLS_FILE = 'scraped_article_urls.txt'
ARTICLES_FILE = 'articles.csv'
# number of seconds after which we write to files again
WRITE_EVERY = 600
DICT_FIELDS = ['title', 'category', 'datetime_string', 'text']


def get_next_page_url(soup):
    '''
    Returns the url for the next page
    :param soup: beautiful soup object of this page
    :return: next url
    '''
    try:
        suffix = soup.body.find(class_='load-more__button').a['href']
        return SITE_URL + suffix
    except:
        return None


def get_all_article_urls(soup):
    '''
    Returns a set of all links to articles from a content page
    :param soup: soup object of content page
    :return: set of strings: urls
    '''
    page_article_urls = set()
    for tag in soup.body.find_all(class_='js_entry-link'):
        page_article_urls.add(tag['href'])
    return page_article_urls


def scrape_article_page(url, sess):
    '''
    Scrape the article page.
    :param url: string. url to scrape
    :return: dict of stringas. the title, category, datetime and main text of the article
    '''
    article_bad_response = 0
    while article_bad_response <= MAX_BAD_RESPONSE:

        # If we get a timeout error or a non-200 response, we try again
        # The while loop condition will exit the loop after the defined
        # number of times
        try:
            t0_article = time.time()
            html = sess.get(url, headers=HEADERS, timeout=TIMEOUT)
            response_delay_article = time.time() - t0_article
        # not specifying the error type because we need the continue statement to always
        # run, so that we'll end up outside the loops and write the files, rather than
        # getting an error and lose everything we've done
        except:
            article_bad_response += 1
            print(f'{time.ctime()}: Request error')
            continue
        if html.status_code != 200:
            article_bad_response += 1
            print(f'{time.ctime()}: Respond status is {html.status_code}')
            continue
        # If we reach this line we have gotten a good response, reset count
        article_bad_response = 0

        # wait time. add a bit of randomness to it, plus a backoff element
        time.sleep(max(0, SHORT_WAIT + response_delay_article * 10 + random.normalvariate(0, SHORT_WAIT / 2)))


        soup = BeautifulSoup(html.text, 'html.parser')

        # try except just in case the finds return nothing and throw an error
        try:
            title = soup.header.find('h1').text
        except:
            title = ''
        try:
            category = soup.header.find(class_='storytype-label js_storytype-type ').text
        except:
            category = ''
        try:
            datetime_string = soup.header.find('time', class_='meta__time updated').attrs['datetime']
        except:
            datetime_string = ''
        try:
            text = soup.body.find('div', class_='post-content entry-content js_entry-content ').find('p').text
        except:
            text = ''
        result = {'title': title, 'category': category, 'datetime_string': datetime_string, 'text': text}
        print(f'{time.ctime()} scraped: {title}')
        # If we got a good html response, even if some of the info is missing, we return what we have
        return result
    # If we dont get a good html response after 5 tries, we return None. There's a line to catch the None
    # in main()
    return None

def write_files(articles, scraped_article_urls):
    with open(ARTICLES_FILE, 'a', encoding='utf-8') as af:
        dwriter = csv.DictWriter(af, fieldnames=DICT_FIELDS)
        dwriter.writeheader()
        for article in articles:
            dwriter.writerow(article)
    with open(SCRAPED_URLS_FILE, 'w') as f:
        for url in scraped_article_urls:
            f.writelines(url + '\n')
    return

def main(start_url):
    '''
    Main function to scrape The Onion.
    :param start_url: string. index page url of the site to begin the scraping
    :param scraped_list: list of strings. article urls that we've scraped before
        so as to not repeat them.
    :return:
    '''
    # a list for all the htmls we'll scrape
    htmls = []
    # a list for all the soup objects parsed from the htmls
    soups = []
    # a list of dicts. each is one of all the articles we parsed
    articles = []
    # a list of all the content page urls we've been thru, just for
    # record. content pages are those that have links to many articles
    content_page_urls = set()
    # urls we will have scraped this time
    scraped_article_urls = set()
    counter = 0

    with open(SCRAPED_URLS_FILE, 'r') as sf:
        for line in sf:
            scraped_article_urls.add(line.strip('\n'))
    # a list of all article pages we've been thru, and the disallowed list
    scraped_article_urls.update(DONT_CRAWL)

    cur_url = start_url
    content_bad_response = 0
    sess = requests.Session()
    # a variable for when the data was last written to files.
    recent_write_time = time.time()

    while content_bad_response <= MAX_BAD_RESPONSE:
        # If we get a timeout error or a non-200 response, we try again
        # The while loop condition will exit the loop after the defined
        # number of times
        print(f'\n\n{time.ctime()} moving to: {cur_url}')
        try:
            t0 = time.time()
            html = sess.get(cur_url, headers=HEADERS, timeout=TIMEOUT)
            response_delay = time.time() - t0
        # not specifying the error type because we need the continue statement to always
        # run, so that we'll end up outside the loops and write the files, rather than
        # getting an error and lose everything we've done
        except BaseException as e:
            content_bad_response += 1
            print(f'{time.ctime()} error with the request' + e)
            continue
        if html.status_code != 200:
            content_bad_response += 1
            continue
        # If we reach this line we have gotten a good response, reset count
        content_bad_response = 0

        # wait time, plus some randomness, plus a backoff element
        time.sleep(max(0, LONG_WAIT + (response_delay * 10) + random.normalvariate(0, LONG_WAIT / 2)))

        htmls.append(html.text)
        soup = BeautifulSoup(html.text, 'html.parser')
        soups.append(soup)

        # Now the soup is from a content page, we scrape all the
        # links to individual articles in that page.
        cur_page_article_urls = get_all_article_urls(soup)
        next_page_url = get_next_page_url(soup)
        # break the loop if we cant find a next_page_url.
        # supposedly it means we've reached the last page.

        if not next_page_url:
            print(f'\n{time.ctime()} task ended because next page is not found.')
            print(f'Current url is :{cur_url}')
            break
        # loop thru each link
        for article_url in cur_page_article_urls:
            # skip the links in the don't crawl list
            counter += 1
            if article_url not in scraped_article_urls:
                # get the article details in a dict
                article = scrape_article_page(article_url, sess)
                # in case the article_url request came back bad, we skip
                if article:
                    articles.append(article)
                    # dont repeat a previous scrape
                    scraped_article_urls.add(article_url)
            else:
                print(f'{time.ctime()} article skipped')
        content_page_urls.add(cur_url)
        cur_url = next_page_url




        # write to file every few cycles
        if time.time() - recent_write_time > WRITE_EVERY:
            print(f'Been thru {counter} articles this run.')
            print(f'###############\n{time.ctime()} Writing files\n###############')
            write_files(articles, scraped_article_urls)
            # reset articles so that we dont append duplicates
            articles = []
            recent_write_time = time.time()

    # write to files for the last time.
    write_files(articles, scraped_article_urls)
    print(f'Task ended. Number of bad response is {content_bad_response}')
    print(f'Final url is {cur_url}')
    print(f'Been thru {counter} articles this run.')
    return


main('https://www.theonion.com/')
