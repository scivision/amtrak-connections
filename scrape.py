"""
This function should be used politely and sparingly
"""
from urllib.request import urlopen
#from http.client import HTTPConnection

def gethtml(url):
    response = urlopen(url)
    html = response.read().decode('utf-8')
    # session.request("GET", url)
   # response = session.getresponse()
   # if response.status == 200:
   #     html = response.read().decode('utf-8')
   # elif response.status == 301:
   #     print('** 301 moved to ' + str(response.getheader('Location')))
   # else:
   #     print('** error ' + str(response.status) + '  could not read ' + url)
   #     html = '** could not read ' + url
    return html