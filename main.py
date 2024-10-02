import asyncio
import datetime
from playwright.async_api import async_playwright
from zoneinfo import ZoneInfo
from replit.object_storage import Client
import os


async def upload_to_object_storage(trace_filename):
  client = Client()
  client.upload_from_bytes(trace_filename, trace_filename)
  print(f"{trace_filename} uploaded successfully!")
  os.remove(trace_filename)

async def run():
  async with async_playwright() as p:
    # Launch the browser
    browser = await p.chromium.launch()
    context = await browser.new_context()
    await context.tracing.start(screenshots=True, snapshots=True)
    page = await context.new_page()

    # Navigate to the playwright homepage
    await page.goto('https://playwright.dev/')

    # Print the home page website's title
    print('Playwright home page title: "%s"' % await page.title())

    # Navigate to the documentation page
    await page.get_by_role('link', name='Get started').click()

    # Print the documentation page website's title
    print('Documentation page title: "%s"' % await page.title())

    # Get the current timestamp
    # Get the current timestamp
    sydney_timezone = ZoneInfo('Australia/Sydney')
    timestamp = datetime.datetime.now(sydney_timezone).strftime("%Y-%m-%d_%H-%M-%S")

    # Create the new filename with timestamp
    trace_filename = f"trace_{timestamp}.zip"

    # Save trace with timestamped filename
    await context.tracing.stop(path = trace_filename)

    # Upload the trace file to Object Storage
    await upload_to_object_storage(trace_filename)

    # Close the browser
    await browser.close()


asyncio.run(run())