from topmanhwa.AsyncIO.manhwa import Manhwa
import sys, os, asyncio, json

slash = os.system("cls") if sys.platform == "win32" else os.system("clear")

manga = Manhwa()

async def main():
    search = await manga.search(input("Search manhwa: "))
    print(f"\nManhwa {search[0]['title']} found.")
    print("\n")
    print(json.dumps(search,indent=4))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())