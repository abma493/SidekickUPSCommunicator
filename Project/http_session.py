import re
from logger import Logger
from asyncio import CancelledError
from datetime import datetime
from common.common_imports import *

async def http_session(ip, username, password, request = Operation.EXPORT, filename=None, stat_label=None, prog_bar=None):
    
    if not ip or not username or not password:
        Logger.log(f"http_session failure: Function is missing one or more valid parameters. [ip:{ip}/u:{username}/p:{password}]") 

    auth = BasicAuth(username, password)
        
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        # Initialize
        try:
            await session.get(f'http://{ip}/web/initialize.htm')
        except Exception as e:
            Logger.log(f"Failure reaching host {ip}: {e}")
            return "Failure reaching host"
        try:
            # Login and get session token
            async with session.get(f'http://{ip}/session/unityLogin.htm?devId=4', auth=auth) as resp:
                content = await resp.text()
                if resp.status == 200:
                    Logger.log(f"[{ip}] Login successful")               
                    # Extract sessACT token from response to interact with the site
                    token_match = re.search(r'sessACT=([A-Fa-f0-9]+)', content)
                    
                    if token_match:
                        s_tok = token_match.group(1)                 

                        # Click Communications button
                        session.get(f'http://{ip}/bezel.html?devId=4&sessACT={s_tok}', auth=auth)
                            
                        # Get child reports (expand Support folder)
                        session.get(f'http://{ip}/httpGetSet/httpGet.htm?devId=4&chldRprt=vel~rprt~chldList~16419~0&sessACT={s_tok}', auth=auth)
                            

                        # Navigate to Configuration Export/Import
                        session.get(f'http://{ip}/monitor.htm?devId=4&reportId=val~num~16440&mmIdx=val~num~0&sessACT={s_tok}', auth=auth)
                            

                        if request == Operation.EXPORT: # (ret str)
                            return await export_config_file(session, ip, s_tok, auth, stat_label, prog_bar)
                        elif request == Operation.IMPORT: # (ret bool)
                            return await import_config_file(session, ip, s_tok, auth, filename, stat_label, prog_bar)
                        else: # DIAGNOSTICS (ret bool)
                            return await get_diagnostics(session, ip, s_tok, auth)
                    else:
                        Logger.log("Could not extract session token")
                        Logger.log("Login response preview:", content[:500])
                
                elif resp.status == 401:
                    Logger.log(f"[{ip}] Authenticaltion failed - invalid credentials.")
                    return "Authentication failed - invalid credentials."
                else:
                    Logger.log(f"Login failed: {resp.status}")
        except Exception as e:
            Logger.log(f"Failure on session: {e}")


async def export_config_file(session, ip, s_tok, auth, stat_label=None, prog_bar=None) -> str:
    
    async with session.get(f'http://{ip}/protected/httpConfigExport.htm?devId=4&sessACT={s_tok}', auth=auth) as export_resp:
        export_content = await export_resp.text()

        # Parse the response to find the download link
        # Look for the generated filename pattern
        download_match = re.search(r'(config_.*?.txt)', export_content)
        
        if download_match:
            
            if stat_label is not None:
                stat_label.update("Finding config file...")
                prog_bar.advance(50)
            
            config_filename = download_match.group(1)
            
            # Download the config file
            download_url = f'http://{ip}/protected/httpConfigExport/Dwnld/{config_filename}?devId=4&sessACT={s_tok}'
            async with session.get(download_url, auth=auth) as download_resp:
                if download_resp.status == 200:
                    config_data = await download_resp.text()
                    # create export folder
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    export_dir = f"config_exports_{timestamp}"
                    os.makedirs(export_dir, exist_ok=True)
                    # full path here
                    f_path = os.path.join(export_dir, config_filename)
                    # Save to file
                    with open(f_path, 'w') as f:
                        f.write(config_data)
                    Logger.log(f"[[{ip}]] Config exported to: {config_filename}")
                    if stat_label is not None:
                        stat_label.update("Done.")
                        prog_bar.advance(50)
                    return f_path # used by the driver
                else:
                    Logger.log(f"[{ip}] Download failed: {download_resp.status}")
        else:
            Logger.log("Could not find download link in response")  
        return None
    

async def import_config_file(session, ip, s_tok, auth, file_path, stat_label=None, prog_bar=None) -> bool:
    
    if not os.path.exists(file_path):
        Logger.log(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'rb') as f:
            file_content = f.read()

    if stat_label is not None:
        stat_label.update("Parsing data...")
    # Create multipart form data for file upload
    data = aiohttp.FormData()
    data.add_field('CfgFile', file_content, filename=os.path.basename(file_path), content_type='text/plain')
    data.add_field('devId', '4')
    data.add_field('sessACT', s_tok)
    
    # Upload the configuration file
    import_url = f'http://{ip}/protected/httpConfigImport.htm'
    try:
        if stat_label is not None:
            stat_label.update("Uploading config file...")  
        async with session.post(import_url, data=data, auth=auth) as resp:
            Logger.log(f"[{ip}] Upload status: {resp.status}")
            if resp.status != 200:
                Logger.log("Upload failed")
                return False
        progress = 0
        status_content:str = None
        while True:
            try:
                # This sleep is used simply to control polling for pcnt changes
                await asyncio.sleep(5) 

                status_url = f'http://{ip}/protected/httpConfigImportStatus.htm?devId=4&sessACT={s_tok}'
                async with session.get(status_url, auth=auth) as status_resp:
                    
                    if status_resp.status == 200:
                        status_content = await status_resp.text()
                        # Check for completion or error messages
                        if 'done' in status_content.lower():
                            progress = 100
                            Logger.log(f'[{ip}] Changes pushed successfully.')
                            if stat_label is not None:
                                prog_bar.advance(int(progress))
                                stat_label.update("Done.")
                            return True
                        elif 'error' in status_content.lower():
                            Logger.log(f"[[{ip}]] Import failed: Stat response {status_resp}")
                            return False

                        progress_match = re.search(r'pcnt=(\d+)', status_content)

                        if progress_match:
                            new_progress = int(progress_match.group(1))
                            # Logger.log(f'[{ip}] pcnt: {new_progress}')
                            if new_progress != progress:
                                if prog_bar is not None:
                                    prog_bar.advance(int(new_progress - progress))
                                progress = new_progress
                        
                    else:
                        Logger.log(f"Status check failed: {status_resp.status}")         
            except (RuntimeError, CancelledError) as e:
                if "closed" in str(e):
                    Logger.log(f"Event loop closed during import polling: {e}")
                    return False

    except Exception as e:
        Logger.log(f"Import failed with error: {e}")
        return False


async def get_diagnostics(session, ip, s_tok, auth) -> bool:

    try:
        # Navigate to diagnostics section (under Support in Communications)
        # Estimate reportId based on your existing config (16440) and firmware (16438) IDs
        diag_url = f'http://{ip}/monitor.htm?devId=4&reportId=val~num~16442&mmIdx=val~num~0&sessACT={s_tok}'
        async with session.get(diag_url, auth=auth) as diag_resp:
            if diag_resp.status != 200:
                Logger.log(f"[{ip}]: Failure on accessing diagnostics file site during operation.")
                return False

        # Method 2: Generate diagnostic file first, then download
        # Trigger diagnostic file generation
        generate_url = f'http://{ip}/diagnostics/diagInfoAll.htm?devId=4&sessACT={s_tok}'
        async with session.get(generate_url, auth=auth) as generate_resp:
            if generate_resp.status == 200:
                Logger.log("Diagnostic file generation initiated")
                generate_content = await generate_resp.text()
                
                # Look for diagnostic file name or download link in response
                download_match = re.search(r'(diag.*?\.(gz|zip|txt|log))', generate_content)
                
                if download_match:
                    diag_filename = download_match.group(1)
                    
                    # Try various download endpoint patterns
                    download_url = f'http://{ip}/diagnostics//var/local/enp/pldserver/4/downloads/{diag_filename}?devId=4&sessACT={s_tok}'
                    
                    try:
                        async with session.get(download_url, auth=auth) as download_resp:
                            if download_resp.status == 200:
                                diag_data = await download_resp.read()
                                local_filename = f'{diag_filename}'
                                with open(local_filename, 'wb') as f:
                                    f.write(diag_data)
                                Logger.log(f"[{ip}]: Diagnostics exported to: {local_filename}")
                                return True
                    except Exception as e:
                        Logger.log(f'[{ip}]: An error has occurred fetching the diagnostics file: {e}')
                            
                Logger.log(f"[{ip}]: Could not download generated diagnostic file.")
                return False
            else:
                Logger.log(f"[{ip}]: Failed to generate diagnostic file: {generate_resp.status}")
                return False
                
    except Exception as e:
        Logger.log(f"[{ip}]: Diagnostics download failed with error: {e}")
        return False