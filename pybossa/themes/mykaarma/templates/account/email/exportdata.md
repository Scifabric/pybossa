Hi, {{ user['fullname']}}!

You have recently requested to export all the data that we have from you in our server.

In the following links, you will be able to download ZIP files that have your personal data, your projects (if you have) and your contributions -if you have- (the links will be only valid for {{config.TTL_ZIP_SEC_FILES}} days).

Personal Data: {{personal_data_link}}
{% if personal_projects_link %}
Your created projects: {{personal_projects_link}}
{% endif %}

{% if personal_contributions_link %}
Your contributions: {{personal_contributions_link}}
{% endif %}

Within the ZIP files you will find your data in JSON format. You can open those files with any text editor, as this format is an open standard.

If you want to get new updated versions of these files, just export your data again.

For the projects' data (tasks, task runs and results) you can use the available exporters for your projects.

All the best,

{{ config.BRAND }} Team
