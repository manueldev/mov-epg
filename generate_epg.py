#!/usr/bin/env python3
"""
generate_epg.py - Generates an XMLTV-format EPG (Electronic Program Guide)
and saves it as a gzip-compressed file (epg.xml.gz).

Add or modify channel/programme data below to customise the output.
"""
import requests
import datetime
import xml.etree.ElementTree as ET
import json
import gzip
import os

# --- Configuration ---
CHANNEL_API_URL = "https://contentapi-cl.cdn.telefonica.com/26/default/es-CL/contents/all?ca_deviceTypes=401&contentTypes=LCH&fields=Pid,Name,Images&orderBy=contentOrder&offset=0&limit=1000"
LOGO_BASE_URL = "https://spotlight-cl.cdn.telefonica.com/customer/v1/source?image="
LOGO_PARAMS = "&height=250&resize=RATIO&format=WEBP"
SCHEDULE_API_URL_TEMPLATE = "https://contentapi-cl.cdn.telefonica.com/26/default/es-CL/schedules?liveChannelPids={pid}&startTime={start_ts}&endTime={end_ts}&fields=Title,Start,Description,End,LiveChannelPid,Images"
import gzip

OUTPUT_FILE = "epg.xml"
OUTPUT_FILE_GZ = "epg.xml.gz"
TIMEZONE_OFFSET = "-0400"

def get_channel_list():
    """Fetches all channel PIDs and names from the first API."""
    print("--- REQUESTING CHANNEL LIST ---")
    print(f"URL: {CHANNEL_API_URL}")
    try:
        response = requests.get(CHANNEL_API_URL, timeout=15, verify=True) 
        print(f"--- RESPONSE STATUS: {response.status_code} ---")
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, dict) or 'Content' not in data:
             print(f"--- FATAL ERROR: Channel List API did not return expected structure (missing 'Content' key). Received keys: {data.keys()} ---")
             return {}
        
        content = data['Content']
        if not isinstance(content, dict) or 'List' not in content:
             print(f"--- FATAL ERROR: 'Content' object missing 'List' key. Received keys: {content.keys()} ---")
             return {}
        
        print(f"Channel API Response Count: {content.get('Count')}")
        
        channels = {}
        list_items = content.get('List', [])
        print(f"Found {len(list_items)} items in the list to process.")
        
        for index, item in enumerate(list_items):
            if not isinstance(item, dict):
                 print(f"Warning: Skipping non-dictionary item at index {index}: {item}")
                 continue
            
            pid = item.get('Pid')
            name = item.get('Name')
            
            if pid is None:
                print(f"Warning: Skipping item at index {index} because 'Pid' is missing.")
                continue
            if name is None:
                print(f"Warning: Skipping item at index {index} because 'Name' is missing.")
                continue

            xmltv_id = f"{pid}.cl"
            
            logo_url = ""
            images = item.get('Images', {})
            logo_list = images.get('Logo', [])
            if logo_list and isinstance(logo_list, list):
                original_url = logo_list[0].get('Url', '')
                if original_url:
                    logo_url = LOGO_BASE_URL + original_url.replace('http://', 'http%3A%2F%2F') + LOGO_PARAMS
            
            channels[pid] = {'name': name, 'xmltv_id': xmltv_id, 'logo_url': logo_url}
            
        return channels
    except requests.exceptions.SSLError as e:
        print(f"--- SSL ERROR during Channel List Fetch ---")
        print(f"SSL Verification Failed for {CHANNEL_API_URL}. Error: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"--- FATAL ERROR during Channel List Fetch ---")
        print(f"Request failed for {CHANNEL_API_URL}. Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Content (if available): {e.response.text[:500]}...")
        return {}

def get_schedule_data(all_channel_pids, start_ts, end_ts):
    """Fetches schedule data for ALL channels in a SINGLE call using comma-separated PIDs."""
    pids_string = ",".join(all_channel_pids)
    url = SCHEDULE_API_URL_TEMPLATE.format(pid=pids_string, start_ts=start_ts, end_ts=end_ts)
    
    print("--- REQUESTING SCHEDULE DATA (BULK) ---")
    print(f"URL: {url}")
    
    try:
response = requests.get(url, timeout=30)
        print(f"--- RESPONSE STATUS: {response.status_code} ---")
        response.raise_for_status()
        data = response.json()
        
        return data.get('Content', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bulk schedule data: {e}")
        return []

def unix_to_xmltv_datetime(unix_ts):
    """Converts Unix timestamp to YYYYMMDDHHMMSS format with timezone."""
    dt_object = datetime.datetime.fromtimestamp(unix_ts, datetime.timezone(datetime.timedelta(hours=-4)))
    return dt_object.strftime("%Y%m%d%H%M%S") + " -0400"

def get_program_image_url(program):
    """Extracts and converts the program image URL."""
    images = program.get('Images', {})
    
    if not images:
        return ""
    
    cover_list = images.get('Cover', [])
    if cover_list and isinstance(cover_list, list) and len(cover_list) > 0:
        original_url = cover_list[0].get('Url', '')
        if original_url:
            return LOGO_BASE_URL + original_url.replace('http://', 'http%3A%2F%2F') + LOGO_PARAMS
    
    video_list = images.get('VideoFrame', [])
    if video_list and isinstance(video_list, list) and len(video_list) > 0:
        original_url = video_list[0].get('Url', '')
        if original_url:
            return LOGO_BASE_URL + original_url.replace('http://', 'http%3A%2F%2F') + LOGO_PARAMS
    
    return ""
    
    cover_list = images.get('Cover', [])
    if cover_list and isinstance(cover_list, list) and len(cover_list) > 0:
        original_url = cover_list[0].get('Url', '')
        if original_url:
            return LOGO_BASE_URL + original_url.replace('http://', 'http%3A%2F%2F') + LOGO_PARAMS
    
    video_list = images.get('VideoFrame', [])
    if video_list and isinstance(video_list, list) and len(video_list) > 0:
        original_url = video_list[0].get('Url', '')
        if original_url:
            return LOGO_BASE_URL + original_url.replace('http://', 'http%3A%2F%2F') + LOGO_PARAMS
    
    return ""

def generate_xmltv(channels, all_programmes):
    """Generates the final XMLTV structure."""
    
    root = ET.Element("tv")
    root.set("creator", "Movistar EPG Generator")
    root.set("xmlns", "urn:mpeg:mpeglex:2008")
    root.set("xmlns:ext", "urn:mpeg:mpeglex:2008")

    for pid, data in channels.items():
        channel_elem = ET.SubElement(root, "channel")
        channel_elem.set("id", data['xmltv_id'])
        
        display_name_elem = ET.SubElement(channel_elem, "display-name")
        display_name_elem.text = data['name']
        
        if data.get('logo_url'):
            icon_elem = ET.SubElement(channel_elem, "icon")
            icon_elem.set("src", data['logo_url'])

    for prog in all_programmes:
        programme_elem = ET.SubElement(root, "programme")
        programme_elem.set("channel", prog['channel_id'])
        programme_elem.set("start", prog['start_xmltv'])
        programme_elem.set("stop", prog['stop_xmltv'])
        
        title_elem = ET.SubElement(programme_elem, "title")
        title_elem.text = prog['title']
        
        desc_elem = ET.SubElement(programme_elem, "desc")
        desc_elem.text = prog['description']
        
        if prog.get('image_url'):
            icon_elem = ET.SubElement(programme_elem, "icon")
            icon_elem.set("src", prog['image_url'])
            
            image_elem = ET.SubElement(programme_elem, "image")
            image_elem.set("type", "still")
            image_elem.text = prog['image_url']
    
    # Sort all programme elements by channel_id to group by channel
    root[:] = sorted(root, key=lambda elem: (elem.tag == "programme", elem.get("channel", ""), elem.get("start", "")))
        
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    
    return ET.tostring(root, encoding='utf-8').decode('utf-8')


def main():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    start_dt = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
    start_ts = int(start_dt.timestamp())
    
    end_dt = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)
    end_ts = int(end_dt.timestamp())

    print(f"Generating EPG for the range: {yesterday} to {tomorrow}")
    
    channels = get_channel_list()
    if not channels:
        print("Could not retrieve channel list. Exiting.")
        return

    print(f"Successfully found {len(channels)} channels.")
    
    all_channel_pids = list(channels.keys())
    
    schedule_data = get_schedule_data(all_channel_pids, start_ts, end_ts)
    
    all_programmes = []
    
    for program in schedule_data:
        try:
            title = program.get('Title', 'Sin título')
            description = program.get('Description', 'Sin descripción.')
            start_ts_prog = program.get('Start')
            end_ts_prog = program.get('End')
            channel_pid = program.get('LiveChannelPid')
            
            if start_ts_prog is None or end_ts_prog is None or channel_pid is None:
                continue
            
            start_xmltv = unix_to_xmltv_datetime(start_ts_prog)
            stop_xmltv = unix_to_xmltv_datetime(end_ts_prog)
            xmltv_channel_id = f"{channel_pid}.cl"
            program_image_url = get_program_image_url(program)

            all_programmes.append({
                'channel_id': xmltv_channel_id,
                'title': title,
                'description': description,
                'start_xmltv': start_xmltv,
                'stop_xmltv': stop_xmltv,
                'image_url': program_image_url
            })
            
        except Exception as e:
            print(f"Error processing a single program entry: {e}")
            continue

    print(f"Processed data for {len(all_programmes)} programs across all channels.")

    xml_content = generate_xmltv(channels, all_programmes)
    xml_content = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_content
    
    # Write XML file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    # Compress to GZ and delete XML
    with open(OUTPUT_FILE, 'rb') as f_in:
        with gzip.open(OUTPUT_FILE_GZ, 'wb') as f_out:
            f_out.writelines(f_in)
    
    os.remove(OUTPUT_FILE)
        
    print(f"Successfully generated EPG XML to {OUTPUT_FILE_GZ}")

if __name__ == "__main__":
    main()
