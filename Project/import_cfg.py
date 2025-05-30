import aiohttp
import asyncio
import re
import os
from logger import Logger
from common.common_term import *

async def import_config_file(session, ups_ip, sess_token, auth, file_path, stat_label, prog_bar):
    
    if not os.path.exists(file_path):
        Logger.log(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'rb') as f:
            file_content = f.read()


    stat_label.update("Parsing data...")
    # Create multipart form data for file upload
    data = aiohttp.FormData()
    data.add_field('CfgFile', file_content, filename=os.path.basename(file_path), content_type='text/plain')
    data.add_field('devId', '4')
    data.add_field('sessACT', sess_token)
    
    # Upload the configuration file
    import_url = f'http://{ups_ip}/protected/httpConfigImport.htm'
    try:
        stat_label.update("Uploading config file...")  
        async with session.post(import_url, data=data, auth=auth) as resp:
            Logger.log(f"Upload status: {resp.status}")
            if resp.status != 200:
                Logger.log("Upload failed")
                return False
        progress = 0
        status_content:str = None
        while True:
            await asyncio.sleep(5)  
            
            status_url = f'http://{ups_ip}/protected/httpConfigImportStatus.htm?devId=4&sessACT={sess_token}'
            async with session.get(status_url, auth=auth) as status_resp:
                
                if status_resp.status == 200:
                    status_content = await status_resp.text()
                    
                    # Check for completion or error messages
                    if 'done' in status_content.lower():
                        progress = 100
                        prog_bar.advance(progress)
                        stat_label.update("Done.")
                        return True
                    elif 'error' in status_content.lower():
                        Logger.log("Import failed!")
                        Logger.log(f"Status response: {status_content}")
                        return False

                    progress_match = re.search(r'pcnt=(\d+)', status_content)

                    if progress_match:
                        new_progress = int(progress_match.group(1))
                        Logger.log(f'[{ups_ip}] pcnt: {new_progress}')
                        if new_progress != progress:
                            prog_bar.advance(int(new_progress - progress))
                            progress = new_progress
                    
                else:
                    Logger.log(f"Status check failed: {status_resp.status}")         

    except Exception as e:
        Logger.log(f"Import failed with error: {e}")
        return False
