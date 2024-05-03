import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

async def process_url(session, base_url, href):
    # Construct absolute URL
    absolute_url = urljoin(base_url, href)

    # Initialize set to store unique child URLs
    child_urls = set()

    # Exclude URLs with certain extensions and non-HTTP(S) schemes
    if absolute_url.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif')):
        return child_urls
    if not absolute_url.startswith(('http://', 'https://')):
        return child_urls

    # Check if the URL has the same domain as the base URL
    parsed_base_url = urlparse(base_url)
    parsed_absolute_url = urlparse(absolute_url)
    if parsed_base_url.netloc != parsed_absolute_url.netloc:
        return child_urls

    # Check if the URL contains 'goto' or 'redirect'
    if 'goto' in absolute_url or 'redirect' in absolute_url:
        # Follow the redirect and add the final URL to child URLs
        try:
            async with session.head(absolute_url, allow_redirects=True) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                final_url = str(response.url)
                child_urls.add(final_url)
        except (aiohttp.ClientError, aiohttp.ClientPayloadError):
            pass
    else:
        # Add the absolute URL to child URLs
        child_urls.add(absolute_url)

    return child_urls

async def get_all_child_urls(base_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            anchor_tags = soup.find_all('a', href=True)
            child_urls = set()
            child_urls.add(base_url)

            tasks = [process_url(session, base_url, tag['href']) for tag in anchor_tags]
            results = await asyncio.gather(*tasks)

            for result in results:
                child_urls.update(result)

    return child_urls

# Example usage
async def main():
    time_start = time.time()
    main_url = "https://www.apple.com"
    raw_urls = await get_all_child_urls(main_url)
    print(f"Time taken: {time.time() - time_start:.2f} seconds")
    print(len(raw_urls))

if __name__ == "__main__":
    asyncio.run(main())
