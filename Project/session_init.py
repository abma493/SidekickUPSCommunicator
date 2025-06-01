from common.common_imports import *
from aiohttp import BasicAuth
import re

async def http_session_init(credentials: tuple, ip: str, id: int = 1000):
    auth = BasicAuth(credentials[0], credentials[1])
    s_tok = None
    session_t = None
    Logger.log(f"aiohttp: Establishing session. [{credentials[0]}, {credentials[1]}]")

    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=30))

    # Initialize
    await session.get(f'http://{ip}/web/initialize.htm')
    
    # Login and get session token
    async with session.get(f'http://{ip}/session/unityLogin.htm?devId=4', auth=auth) as resp:
        content = await resp.text()
        if resp.status == 200:
            Logger.log(f"Job #{id}: Login successful")               
            # Extract sessACT token from response to interact with the site
            token_match = re.search(r'sessACT=([A-Fa-f0-9]+)', content)
            
            if token_match:
                s_tok = token_match.group(1)
                Logger.log(f"Job #{id} - Session token: {s_tok}")                  

                # Click Communications button
                async with session.get(f'http://{ip}/bezel.html?devId=4&sessACT={s_tok}', auth=auth) as comm_resp:
                    Logger.log(f"Job #{id} - Communications page: {comm_resp.status}") 
                # Get child reports (expand Support folder)
                async with session.get(f'http://{ip}/httpGetSet/httpGet.htm?devId=4&chldRprt=vel~rprt~chldList~16419~0&sessACT={s_tok}', auth=auth) as child_resp:
                    Logger.log(f"Job #{id} - Support folder: {child_resp.status}")
                # Navigate to Configuration Export/Import
                async with session.get(f'http://{ip}/monitor.htm?devId=4&reportId=val~num~16440&mmIdx=val~num~0&sessACT={s_tok}', auth=auth) as config_resp:
                    Logger.log(f"Job #{id} - Config Export/Import: {config_resp.status}") 
                return (session, s_tok, auth)

    await session.close()
    return None, None, None    
