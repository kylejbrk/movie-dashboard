import requests
import re
import os
import pandas as pd
from bs4 import BeautifulSoup

def get_ids(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, features="lxml")

    table = soup.find('table', attrs={'class': 'chart full-width'})
    title_columns = table.find_all('td', attrs={'class': 'titleColumn'})

    ids = []
    for title in title_columns:
        imdb_id = title.find('a', href=True)
        ids.append(imdb_id['href'].split('/')[2])

    return ids

def get_film_info(imdb_id):
    url = 'https://www.imdb.com/title/{}/'.format(imdb_id)

    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, features="lxml")

    header = soup.find('h1').get_text().strip()
    date = header[-6:]
    title = header[:-7]

    poster = soup.find('img', attrs={'alt': title + ' Poster'})['src']
    poster = re.sub(r'(?s)(?<=\._).+?(?=.jpg)', 'V1_FMjpg_UX1000_', poster)

    summary = soup.find('div', attrs={'class': 'plot_summary'}).get_text().strip()

    return title, date, poster, summary

def create_html(df, file_name):
    images = []
    for idx, row in df.iterrows():
        img_str = '''
        <div class="item">
            <img src="{source}" alt="{id}" onclick="window.open('https://www.imdb.com/title/{id}/', '_blank');"/>
            <span class="caption">{title}</span>
        </div>
        '''.format(source=row['poster'], id=row['imdb_id'], title=row['title'])
        images.append(img_str)

    html_text = html_template(images)

    # change header
    navigation = html_text.find('a', attrs={'href': file_name})
    header_name = navigation.get_text()

    header = html_text.find('span', attrs={'class': 'openSidenav'})
    header.insert(1, header_name)

    with open('docs/' + file_name, 'w') as f:
        f.write(html_text.prettify())

def html_template(images):
    images_text = '\n'.join(images)

    images_html = BeautifulSoup(images_text, features='lxml')
    with open('html_template.html', 'r') as f:
        template = BeautifulSoup(f.read(), features='lxml')

    gallery = template.find('div', attrs={'class': 'gallery'})
    gallery.insert(1, images_html)

    return template

if __name__ == '__main__':
    urls = [
        'https://www.imdb.com/chart/top',
        'https://www.imdb.com/chart/boxoffice',
        'https://www.imdb.com/chart/moviemeter',
        'https://www.imdb.com/chart/bottom'
    ]
    os.makedirs('docs', exist_ok=True)

    for url in urls:
        df = pd.read_html(url, attrs={'class': 'chart full-width'})[0]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df['imdb_id'] = get_ids(url)

        df['title'],  df['date'], df['poster'], df['summary'] = zip(*df['imdb_id'].apply(get_film_info))
        file_name = url.split('/')[-1] + '.html'

        create_html(df, file_name)
        print('Created {}'.format(file_name))
