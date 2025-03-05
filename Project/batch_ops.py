from common.common_term import *


class BatchOperator:

    def __init__(self, page, credentials: tuple):
        self.page = page

    async def run_browser_task(self, task_id):
        
        await self.page.goto("https://example.com")




