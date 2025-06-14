#!/usr/bin/env python3
import requests
import json

url = "https://agintel10x-test.onfarmerp.com:8002/api/MA_SubPlot/GetSubPlotDetailsForIntegration"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    print(f"Response status: {response.status_code}")
    print(f"Number of plots: {len(data)}")
    print("\nFirst plot structure:")
    print(json.dumps(data[0], indent=2))
    
    print("\nAll field names in first plot:")
    print(list(data[0].keys()))
    
except Exception as e:
    print(f"Error: {e}")