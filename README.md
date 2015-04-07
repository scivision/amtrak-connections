amtrak-connections
==================
All credit for data, wonderful web service to John Bobinyec of [statusmaps.net](http://statusmaps.net), as well as Amtrak.

Using archival data from statusmaps.net to do simple analysis of transfer statistics (missed connections).

Prereqs:
---------
```
pip install -r requirements.txt
```
then go to [statusmaps.net archives](http://www.dixielandsoftware.net/Amtrak/status/StatusPages/index.html), download the ZIP files of interest and EXTRACT them using original directory structure into the ~/amtrak-connections folder. The Python code expects the directory structure.

Example:
``` ./amtrak.py 29 7 -d 2013-05-15 2013-05-31 ```
that examines connections between the Capitol Limited to the Empire Builder for the latter half of May 2013
![Alt connection](http://scienceopen.github.io/7-29connect.png)
