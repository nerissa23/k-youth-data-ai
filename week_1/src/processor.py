from pydantic import BaseModel
import os
from pathlib import Path
from bs4 import BeautifulSoup

# basic pydantic model for JobListing item
class JobListing(BaseModel):
    source_id: str
    job_title: str
    company: str
    description: str

def process_all_html(input_dir, output_dir):
    print("\n🥈 Silver:...")

    # handling when input_dir is not avail
    if not os.path.isdir(input_dir):
        print(f"❗ Input directory not found")
        return
    
    # auto create output_dir if doesnt currently exist
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    try:
        files = os.listdir(input_dir)
        process_count = 0
        if len(files) == 0:
            print(f"❗ Input directory is empty")
            return
        
        for file in files:
            input_file = os.path.join(input_dir, file)
            output_file = Path(output_dir)/Path(file).with_suffix(".json")
            input_content = Path(input_file).read_text("utf-8")

            soup = BeautifulSoup(input_content, "html.parser")
            
            # find relevant info: source_id, job title, company, desc
            source_id = soup.find('meta', property="og:url")["content"].split("/")[-1]
            job_title_el = soup.find(attrs={"data-automation": "job-detail-title"})
            job_title = job_title_el.get_text(strip=True) if job_title_el else ""
            company_el = soup.find(attrs={"data-automation": "advertiser-name"})
            company = company_el.get_text(strip=True) if company_el else ""
            description_el = soup.find(attrs={"data-automation": "jobAdDetails"})
            description = description_el.get_text("\n", strip=True) if description_el else ""

            data = JobListing(
                source_id=source_id,
                job_title=job_title,
                company=company,
                description=description
            )

            # check whether all info is non-falsy, if pass checking can write to json
            if source_id and job_title and company and description:
                # write to json
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(data.model_dump_json(indent=2))
                
                process_count += 1
                print(f"✅ Processed: {file}")
            else:
                missing = [name for name, val in data.model_dump().items() if not val]
                print(f"⚠️  Missing {', '.join(missing)} in: {file}")

        print_summary(len(files), process_count, len(files)-process_count)
    except Exception as e:
        print(f"❗ Error processing HTML: {e}")

def print_summary(total, succeed, fail):
    print(f"\n📊 Silver Summary:\nTotal: {total} | Processed: {succeed} | Skipped: {fail}")