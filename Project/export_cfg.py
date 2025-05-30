import aiohttp
import asyncio
import re
from logger import Logger
from common.common_term import *

async def export_config_file(session, ups_ip, sess_token, auth, stat_label, prog_bar):
    async with session.get(f'http://{ups_ip}/protected/httpConfigExport.htm?devId=4&sessACT={sess_token}', auth=auth) as export_resp:
        Logger.log(f"Config export trigger: {export_resp.status}")
        export_content = await export_resp.text()
        Logger.log(f"content: {export_content}")
        # Parse the response to find the download link
        # Look for the generated filename pattern
        download_match = re.search(r'(config_.*?.txt)', export_content)
        
        if download_match:
            stat_label.update("Finding config file...")
            prog_bar.advance(50)
            config_filename = download_match.group(1)
            Logger.log(f"Found config file: {config_filename}")
            
            # Download the config file
            download_url = f'http://{ups_ip}/protected/httpConfigExport/Dwnld/{config_filename}?devId=4&sessACT={sess_token}'
            async with session.get(download_url, auth=auth) as download_resp:
                if download_resp.status == 200:
                    config_data = await download_resp.text()
                    # Save to file
                    with open(f'ups_{config_filename}', 'w') as f:
                        f.write(config_data)
                    Logger.log(f"Config exported to: ups_{config_filename}")
                else:
                    Logger.log(f"Download failed: {download_resp.status}")
        else:
            Logger.log("Could not find download link in response")  