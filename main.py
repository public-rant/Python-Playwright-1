import json
import zipfile
import asyncio
import datetime
from inspect import trace
from playwright.async_api import async_playwright, expect
from zoneinfo import ZoneInfo
from replit.object_storage import Client
import os
from openai import OpenAI


async def upload_to_object_storage(trace_filename):
  client = Client()
  client.upload_from_bytes(trace_filename, trace_filename)
  print(f"{trace_filename} uploaded successfully!")

async def run():
  async with async_playwright() as p:
    # Launch the browser
    browser = await p.chromium.launch()
    context = await browser.new_context()
    await context.tracing.start(screenshots=True, snapshots=True)
    page = await context.new_page()

    # Navigate to the playwright homepage
    await page.goto('https://playwright.dev/')

    title = await page.title()
    # Print the home page website's title
    print('Playwright home page title: "%s"' % title)

    # Navigate to the documentation page
    await page.get_by_role('link', name='Get started').click()

    # Print the documentation page website's title
    print('Documentation page title: "%s"' % title)

    await expect(page).to_have_title('Installation | Playwright')

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



    api_key = os.environ['OPENAI_API_KEY']

    client = OpenAI(api_key=api_key)


    # def unzip_file(zip_file_path, extract_to):
        

    # Example usage
    # zip_file_path = trace_filename
    extract_to = './traces'

    # Ensure the destination directory exists
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    
    # Open the zip file
    with zipfile.ZipFile(trace_filename, 'r') as zip_ref:
        # Extract all contents to the specified directory
        zip_ref.extractall(extract_to)




    def parse_jsonl_file(file_path):
      data = []
      with open(file_path, 'r') as jsonl_file:
          for line in jsonl_file:
              # Parse each line (which is a JSON object) and append to the data list
              data.append(json.loads(line))
      return data
    
    # Example usage
    json_file_path = 'traces/trace.trace'
    parsed_data = parse_jsonl_file(json_file_path)
    os.remove(trace_filename)

    results = []
    
    # Print the parsed data
    for entry in parsed_data:
      if entry['type'] == "before":
        results.append(entry['apiName'])
        if entry['params']:
            if 'expectedText' in entry['params']:
                results.append(entry['params']['expectedText'][0]['string'])
            if 'selector' in entry['params']:
                results.append(print(entry['params']['selector']))

    # original_list = [1, None, 2, None, 3, 4, None]
    compact_list = [x for x in results if x is not None]
    
    # Output: [1, 2, 3, 4]

    response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "write a playwright test in typescript based on this:"},
          {"role": "user", "content": "write it as a function which i can import into an existing test suite"},
          {"role": "user", "content": " ".join(compact_list)},
      ]
    )

    content = response.choices[0].message.content

    # print(results)
    # print(content)

    with open('README.md', 'w') as f:
      f.write(content)


asyncio.run(run())