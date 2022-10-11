import s3s
import boto3
import os
import time
import json
import requests
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
print("uploading files to stat.ink...")
try:
	s3s.upload_imported_data_with_statink_checks(False, False, battle_list)
except Exception as err:
	print("failed to upload to stat.ink", str(err))

print("uploading files to digitalocean")

time = int(time.time())

last_id = ""
with open(".last-id") as f:
	last_id = f.read()
 
latest_battles_list = []

for battle in battle_list:
	if battle["data"]["vsHistoryDetail"]["id"] == last_id:
		break
	else:
		latest_battles_list.append(battle)

with open(".last-id", "w") as f:
	f.write(battle_list[0]["data"]["vsHistoryDetail"]["id"])

print("uploading battles...")
print("latest battles list length:", len(latest_battles_list))

client.put_object(
	Bucket=os.getenv("SPACES_BUCKET"),
	Key=f"battles/{time}.json",
	Body=json.dumps(latest_battles_list),
	ACL="private",
	ContentType='application/json',
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
	ContentType='application/json',
	Metadata={
		'x-amz-meta-run-uuid': run_uuid
	}
)

print("digitalocean spaces uploads done!!")
print("triggering site rebuild...")

rebuild_response = requests.post(f"https://api.digitalocean.com/v2/apps/{os.getenv('APP_ID')}/deployments", json={"force_build": True}, headers={"Authorization": f"Bearer {os.getenv('API_TOKEN')}"})
rebuild_res_data = rebuild_response.json()

print("rebuild started!" if rebuild_response.status_code == 200 else ("rebuild failed!", rebuild_response.status_code, rebuild_res_data))