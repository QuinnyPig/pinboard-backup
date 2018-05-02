# Pinboard Backup to DynamoDB via Lambda Function

This is a script that I use in the curation of [Last Week in AWS](https://lastweekinaws.com). It will require tweaking for other purposes; in its current form it's gentle on the Pinboard API. Beating it to death with massive requests is a great way to enrage an already kind-yet-volatile man who underprices his service. Tread carefully. 

It currently grabs all Pinboard bookmarks that are tagged with `current`. 

In DynamoDB, the `current` tag is replaced with a number that's retrieved from the contents of an S3 object. 

If the description field is empty, the string "empty" will be used in its place.

It expects all `current` tagged bookmarks to have a second tag: `community`, `aws`, `tools`, `sponsor`, or `tip`. These tags are converted to booleans, true for the attribute with the tag name. 

Lastly, it queries the DynamoDB table for the current issue, and deletes anything that wasn't updated within the last 350 seconds. This is how I ensure that Pinboard can remain my source of truth for links.

Note that there is a failure mode wherein the Pinboard API can return bad data that overwrites existing good data. For that reason I advise enabling DynamoDB backups on the table. Given that I generate new issues weekly, the 30 day retention is more than sufficient for my needs-- and the Pinboard API generally doesn't do that.

## Prerequisites

A DynamoDB table. An S3 object containing a number. A Python environment.  

Should you be running this from within an AWS Lambda function, indicate so with an environment variable of `INSIDE_LAMBDA` set to `True`. 
An Environment variable called `PINBOARD_TOKEN` should contain your Pinboard API token. If within a Lambdai function, this is expected to be KMS encrypted. Don't store access keys in plaintext; it's just not smart.



