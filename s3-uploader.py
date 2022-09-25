import s3s
import boto3
import os
import time
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

session = boto3.session.Session()
client = session.client('s3', region_name='nyc3', endpoint_url='https://nyc3.digitaloceanspaces.com',
                        aws_access_key_id=os.getenv('SPACES_KEY'), aws_secret_access_key=os.getenv('SPACES_SECRET'))

run_uuid = str(uuid.uuid4()) # no idea what this will be used for but seemed like a good idea lol

print("doing s3s prefetch checks...")

s3s.prefetch_checks()

print("getting files")

battle_list, salmon_run_job_list = s3s.fetch_json("both", True, False, False)

# post the result to stat.ink here? (add a cmd line arg for this too)
# DO THE THING WHEN S3S SUPPORTS STAT.INK
print("uploading files to stat.ink...")
try:
	s3s.upload_imported_data_with_statink_checks(False, False, battle_list)
except Exception as err:
	print("failed to upload to stat.ink", str(err))

print("uploading files to digitalocean")

time = int(time.time())

print("uploading battles...")

client.put_object(
	Bucket=os.getenv("SPACES_BUCKET"),
	Key=f"battles/{time}.json",
	Body=json.dumps(battle_list),
	ACL="private",
	Metadata={
		'x-amz-meta-run-uuid': run_uuid
	}
)

print("uploading salmon run jobs...")

client.put_object(
	Bucket=os.getenv("SPACES_BUCKET"),
	Key=f"jobs/{time}.json",
	Body=json.dumps(salmon_run_job_list),
	ACL="private",
	Metadata={
		'x-amz-meta-run-uuid': run_uuid
	}
)

print("done!!")