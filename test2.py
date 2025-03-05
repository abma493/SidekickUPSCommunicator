import asyncio
from playwright.async_api import async_playwright

async def run_browser_task(task_id):
    """Run a specific task in its own browser instance"""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.firefox.launch(headless=False)
        
        # Create a new page
        page = await browser.new_page()
        
        # Navigate to example.com
        await page.goto('https://example.com')
        
        # Log which task is running
        print(f"Task {task_id} has opened example.com")
        
        # Example of unique action per task
        if task_id == 1:
            # Task 1: Click the "More information" link
            await page.click('a')
            await page.wait_for_load_state('networkidle')
            print(f"Task {task_id} clicked on More information link")
        elif task_id == 2:
            # Task 2: Take a screenshot
            await page.screenshot(path=f"example-task-{task_id}.png")
            print(f"Task {task_id} took a screenshot")
        elif task_id == 3:
            # Task 3: Get the page title
            title = await page.title()
            print(f"Task {task_id} got the page title: {title}")
        
        # Wait a bit to see the result
        await asyncio.sleep(3)
        
        # Close the browser
        await browser.close()
        
        return f"Task {task_id} completed"

async def main():
    # Create 3 tasks to run in parallel
    tasks = [run_browser_task(i) for i in range(1, 4)]
    
    # Run all tasks concurrently and wait for all to complete
    results = await asyncio.gather(*tasks)
    
    # Print the results
    for result in results:
        print(result)

if __name__ == "__main__":
    # Run the main coroutine
    asyncio.run(main())