from bs4 import BeautifulSoup as bSoup
import asyncio, aiohttp, lxml, re, img2pdf, os, zipfile

class Manhwa:
    
    def __init__(self):
        self.base = "https://topmanhwa.net"
        self.manga = f"{self.base}/manga"

    async def search(self, q):
        '''
        q : Query search by manhwa title
        '''
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{self.base}/?s={q}&post_type=wp-manga") as r:
                s = bSoup(await r.text(), 'lxml')
                
        listings = s.find_all("div", class_='row c-tabs-item__content')
        res = []

        for m in listings:
            for sm in m.find_all("div", class_='post-content_item'):
                if sm.find('div', class_='summary-heading').h5.text.strip() == 'Alternative':
                    alter = sm.find("div", class_='summary-content').text.lstrip().rstrip()
                if sm.find('div', class_='summary-heading').h5.text.strip() == 'Authors':
                    author = sm.find("div", class_='summary-content').text.lstrip().rstrip()
                if sm.find('div', class_='summary-heading').h5.text.strip() == 'Artists':
                    artist = sm.find("div", class_='summary-content').text.lstrip().rstrip()
                if sm.find('div', class_='summary-heading').h5.text.strip() == 'Genres':
                    genre = sm.find("div", class_='summary-content').text.lstrip().rstrip()
                if sm.find('div', class_='summary-heading').h5.text.strip() == 'Status':
                    status = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            
            res.append({
                "cover": m.find('img', class_='img-responsive')['data-src'],
                "title": m.find('div', class_='post-title').h3.a.text,
                "url": m.find('div', class_='post-title').h3.a['href'].replace("?style=paged",""),
                "stars": float(f"{len(m.find_all('i', class_='ion-ios-star ratings_stars rating_current'))}.5") if m.find('i', class_='ion-ios-star-half ratings_stars rating_current_half') else len(m.find_all('i', class_='ion-ios-star ratings_stars rating_current')),
                "ratings": float(m.find('span', class_='score font-meta total_votes').text.strip()),
                "chapters": {
                    "latest": m.find('span', class_='font-meta chapter').a.text,
                    "released": m.find('div', class_='meta-item post-on').span.text,
                    "url": m.find('span', class_='font-meta chapter').a['href'].replace("?style=paged","")
                },
                "summary": {
                    "alternative": alter,
                    "authors": author,
                    "artists": artist,
                    "genres": genre,
                    "status": status
                }
            })

        return res

    async def _last_page(self, path):
        #private only
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{self.base}/{path}/") as r:
                s = bSoup(await r.text(), 'lxml')
                return int(s.find('span', class_='pages').text.strip().split()[-1])

    async def on_going(self, page=1):
        '''
        page : The number current page of the on-going web page
        '''
        last = await self._last_page('on-going')
        if page > last:
            page = last

        res = {
            "current": page,
            "total": last,
            "manga": []
        }

        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"{self.base}/on-going/page/{page}") as r:
                s = bSoup(await r.text(), 'lxml')
                
        listings = s.find_all("div", class_='page-item-detail manga')
        
        for m in listings:
            try:
                chapter = int(re.search("Chapter ([0-9]+)",m.find('span', class_='chapter font-meta').a.text).group(1)) if m.find('span', class_='chapter font-meta') else 0
            except:
                chapter = float(re.search("Chapter ([0-9]+)",m.find('span', class_='chapter font-meta').a.text).group(1)) if m.find('span', class_='chapter font-meta') else 0
            
            res['manga'].append({
                "cover": m.find('img', class_='img-responsive')['data-src'],
                "title": m.find('div', class_='item-summary').find('a').text.strip(),
                "stars": float(f"{len(m.find_all('i', class_='ion-ios-star ratings_stars rating_current'))}.5") if m.find('i', class_='ion-ios-star-half ratings_stars rating_current_half') else len(m.find_all('i', class_='ion-ios-star ratings_stars rating_current')),
                "ratings": float(m.find('span', class_='score font-meta total_votes').text.strip()),
                "chapter": chapter,
                "released": m.find('span', class_='post-on font-meta').text.strip() if m.find('span', class_='post-on font-meta') else "Unknown.",
                "url": m.find('a')['href'].replace("?style=paged","")
            })
        
        return res

    async def detail(self, url):
        '''
        url : Manhwa page url from the topmanhwa.net web
        '''
        async with aiohttp.ClientSession() as ses:
            async with ses.get(url) as r:
                s = bSoup(await r.text(), 'lxml')
        
        title = s.find("div", class_='post-title').text.strip().replace("\t", "").split("\n")
        summary = s.find_all("div", class_='post-content_item')
        chapter = [{
                    "name": a.find('a').text.strip(),
                    "url": a.find('a')['href'].replace("?style=paged","")
                } for a in s.find_all('li', class_='wp-manga-chapter')][::-1]
        
        for sm in summary:
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Rating':
                average = sm.find("div", class_='summary-content').text.lstrip().replace(title[-1]+" ", "").replace("  ", " ").lstrip().replace("Average ", "").rstrip().replace("  ", " ")
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Rank':
                rank = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Alternative':
                alter = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Author(s)':
                author = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Artist(s)':
                artist = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Genre(s)':
                genre = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Type':
                _type = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Release':
                release = sm.find("div", class_='summary-content').text.lstrip().rstrip()
            if sm.find('div', class_='summary-heading').h5.text.strip() == 'Status':
                status = sm.find("div", class_='summary-content').text.lstrip().rstrip()
        
        try:average=average
        except NameError:average=None
        
        return {
            "cover": s.find("div", class_='summary_image').a.img['data-src'],
            "title": title[-1],
            "badge": s.find('span', class_='manga-title-badges').text if s.find('span', class_='manga-title-badges') else None,
            "summary": s.find("div", class_='summary__content').p.text.strip(),
            "chapter": {
                "count": len(s.find_all('li', class_='wp-manga-chapter')),
                "chapters": chapter
            },
            "info": {
                "type": _type,
                "stars": float(f"{len(s.find_all('i', class_='ion-ios-star ratings_stars rating_current'))}.5") if s.find('i', class_='ion-ios-star-half ratings_stars rating_current_half') else len(s.find_all('i', class_='ion-ios-star ratings_stars rating_current')),
                "ratings": float(s.find('span', class_='score font-meta total_votes').text.strip()),
                "average": average,
                "rank": rank,
                "alternative": alter,
                "authors": author,
                "artists": artist,
                "genres": genre,
                "release": release,
                "status": status
            }
        }

    async def _images(self, url):
        #private only
        async with aiohttp.ClientSession() as ses:
            async with ses.get(url) as r:
                s = bSoup(await r.text(), 'lxml')
            return  [a['data-src'].lstrip() for a in s.find_all("img", class_='wp-manga-chapter-img')]

    async def download(self, url, filetype='pdf'):
        '''
        url      : Manhwa chapter url from the topmanhwa.net web\n
        filetype : Type of file, available type is `pdf` and `zip`
        '''
        if filetype not in ['pdf','zip']:
            raise AttributeError("Invalid filetype, available filetype is pdf and zip")
        # Generate the filename 
        filename = url.replace(f"{self.manga}/", "").split("/")[0].replace("-", " ").title()

        # Create downloads directory if it's not exists in the local
        if not os.path.exists(f"{os.getcwd()}/downloads"):
            os.mkdir(f"{os.getcwd()}/downloads")
            print("Downloads dir created.")

        if filetype == 'zip':
            # Download chapter as a ZIP file
            path = f"{os.getcwd()}/downloads/{filename}.zip"

            # Proceed download if the same file not in the local
            if not os.path.exists(path):
                imbytes = [] # Image bytes
                downloaded = 1
                manhwa = await self._images(url) # Get the chapter images
                print(f"Downloading, {(downloaded/len(manhwa))*100:.1f}%")

                # Download the image
                async with aiohttp.ClientSession() as ses:
                    for img,i in zip(manhwa, range(1, len(manhwa))):
                        async with ses.get(img) as r:
                            if r.status == 200:
                                imbytes.append(await r.content.read()) # Saving image bytes
                                downloaded += 1
                                print(f"Downloading, {(downloaded/len(manhwa))*100:.1f}%")

                # Archiving the image bytes
                z = zipfile.ZipFile(path, 'w')
                for byte, d, i in zip(imbytes, manhwa, range(1,len(manhwa)+1)):
                    z.writestr(f"{filename}_{i}.{d[-3:]}", byte, compress_type=zipfile.ZIP_DEFLATED)
                z.close()

                print(f"Download complete, {(downloaded/len(manhwa))*100:.1f}%")
            else:
                print("The file is already in the local, and using cached.")

        else:
            # Download chapter as a PDF file
            path = f"{os.getcwd()}/downloads/{filename}.pdf"

            # Proceed download if the same file not in the local
            if not os.path.exists(path):
                imbytes = [] # Image bytes
                downloaded = 1
                manhwa = await self.images(url) # Get the chapter images
                print(f"Downloading, {(downloaded/len(manhwa))*100:.1f}%")

                # Download the image
                async with aiohttp.ClientSession() as ses:
                    for img,i in zip(manhwa, range(1, len(manhwa))):
                        async with ses.get(img) as r:
                            if r.status == 200:
                                imbytes.append(await r.content.read()) # Saving image bytes
                                downloaded += 1
                                print(f"Downloading, {(downloaded/len(manhwa))*100:.1f}%")

                # Custom size of the layout
                a4inpt = (img2pdf.mm_to_pt(200),img2pdf.mm_to_pt(300))
                layout_fun = img2pdf.get_layout_fun(a4inpt)
                
                # Merging the image bytes to PDF file
                with open(f"{os.getcwd()}/downloads/{filename}.pdf","wb") as f:
                    f.write(img2pdf.convert(imbytes, layout_fun=layout_fun))

            else:
                print("The file is already in the local, and using cached.")
        return path
