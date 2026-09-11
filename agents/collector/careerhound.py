from typing import List
from app.models.job import Job

class CareerHoundCollector:
    """
    CareerHound.io renders its job list client-side (Next.js App Router,
    no server-rendered HTML and no public API endpoint found). A plain
    requests+BeautifulSoup fetch sees an empty shell — nothing to parse.
    Getting real listings out of it needs a headless browser (Playwright)
    to execute the page's JS, which isn't wired up in this project yet.
    Left as a documented stub, same pattern as the LinkedIn ToS stub,
    so it's easy to find and wire up later without hunting for it.
    """
    source = "careerhound"

    def collect(self) -> List[Job]:
        print("CareerHound skipped: listings are client-rendered JS, "
              "requires a headless browser to scrape (not implemented).")
        return []
