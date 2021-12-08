import os
import time
import aiohttp
import aiofiles
import asyncio
import mimetypes
from bs4 import BeautifulSoup

start_time = time.time()


async def downloadImage(session, image_url, path):
    async with session.get(image_url) as response:
        assert response.status == 200
        extension = mimetypes.guess_extension(response.headers['content-type'])
        image = await aiofiles.open(path+extension, mode='wb')
        await image.write(await response.read())
        await image.close()
        print(f'Finished:{path}')


async def getImageUrl(session, page_url):
    async with session.get(page_url) as page_res:
        page_soup = BeautifulSoup(await page_res.text(), 'html.parser')
        image_url = page_soup.find('img')['src']
        return image_url


async def main():

    async with aiohttp.ClientSession() as session:
        # Get html body of main page and pass is as respose
        async with session.get('https://totempole666.com/archives-2') as response:
            # Mount the html on parser
            soup = BeautifulSoup(await response.text(), 'html.parser')
            # Get all chapter containers
            chapters = soup.select('.comic-archive-chapter-wrap')

            for chapter in chapters:
                chapter_title = chapter.select_one(
                    '.comic-archive-chapter').get_text()

                pages = chapter.select('.comic-archive-title')
                pages_url_tasks = []

                for page in pages:
                    # Get page url
                    page_url = page.find('a', href=True)['href']
                    # Append page url to tasks list
                    pages_url_tasks.append(asyncio.create_task(
                        getImageUrl(session, page_url)))

                image_urls = await asyncio.gather(*pages_url_tasks)

                download_images_task = []
                for index, image_url in enumerate(image_urls):
                    if not os.path.exists(f'downloads/{chapter_title}/'):
                        os.makedirs(f'downloads/{chapter_title}/')
                    path = f'downloads/{chapter_title}/page{index+1}'
                    download_images_task.append(asyncio.create_task(
                        downloadImage(session, image_url, path)))

                await asyncio.gather(*download_images_task)

asyncio.run(main())
print(time.time()-start_time)
