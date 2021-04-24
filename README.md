# Terralab
Kenneth Falck <kennu@clouden.net> 2019-2020

## Google Drive Setup

Please configure Google Drive in Odoo Settings / General Settings / Integrations / Google Drive.


Notes about deployment:

- When deploying to odoo.sh, Copy requirements.txt contents to odoo.sh github project's main folder. Not only to terralab folder
- Create separate google account
- Be sure to enable google drive from general settings
- enable Google Docs project: 
-    Create a project, go to api and services, top of the screen enable apis and services. Search Google Sheets API


- Must create a DESKTOP google apps app
- Must copy from Google apps client secrete and client ID
- Dev mode -> tech settings in odoo. Edit Odoo's Google client secret and client id
- Apply secret token that google provides
- Google sheets url: remove #gid=0 from the end
