import bs4
import requests

def get_quote(quote_id):
    request = requests.get(f'http://bash.org/?{quote_id}')
    if request.status_code != 200: raise IndexError(f'HTTP Error: {request.status_code}')
    soup = bs4.BeautifulSoup(request.text, 'html.parser')
    tag = soup.find(class_='qt')
    if tag is None: raise IndexError(f'No quote with id "{quote_id}"')
    return tag.text

def search(query):
    request = requests.get(f'http://bash.org/?search={query}')
    if request.status_code != 200: raise IndexError(f'HTTP Error: {request.status_code}')
    soup = bs4.BeautifulSoup(request.text, 'html.parser')
    ids = [tag.text[1:] for tag in soup.find_all(title='Permanent link to this quote.')]
    return ids

def random():
    request = requests.get(f'http://bash.org/?random')
    if request.status_code != 200: raise IndexError(f'HTTP Error: {request.status_code}')
    soup = bs4.BeautifulSoup(request.text, 'html.parser')
    quote = soup.find(class_='qt').text
    return quote
