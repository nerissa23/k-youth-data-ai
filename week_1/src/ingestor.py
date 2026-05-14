import email
from pathlib import Path
import quopri
import os
from paths import DATA_DIR

def ingest_all_mhtml(input_dir, output_dir):
    # handle when input_dir is not found/available
    if not os.path.isdir(input_dir):
        print(f"❗ Input directory not found")
        return
    
    # create output_dir if does not exist
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    try:
        files = os.listdir(input_dir) # returns array
        extract_count = 0
        # handle when input_dir has no contents inside
        if len(files) == 0:
            print(f"❗ Input directory is empty")
            return

        for file in files:
            input_file = os.path.join(input_dir, file)
            output_file = Path(output_dir)/Path(file).with_suffix(".html")
            contains_html = False

            # read as bytes, bcz .mthml files are mixed content (HTML, images, CSS, fonts, etc)
            raw = Path(input_file).read_bytes()

            # parse the MIME structure with email lib
            # output: webpage broken into sections by boundary (iterator obj)
            msg = email.message_from_bytes(raw)

            for part in msg.walk():
                content_type = part.get_content_type()
                encoding = part.get("Content-Transfer-Encoding", "")

                if content_type == "text/html":
                    contains_html = True
                    payload = part.get_payload(decode=True) # decode base64 content and returns bytes
                    if encoding == "quoted-printable":
                        payload = quopri.decodestring(payload) # expects bytes as input and decode QP content
                        html = payload.decode("utf-8", errors="replace") # convert the bytes format to python string
                        Path(output_file).write_text(html, encoding="utf-8")
                        break

            if contains_html:
                extract_count += 1
                print(f"✅ Extracted: {file}")
            else:
                print(f"⚠️ No HTML content found in: {file}")
            
        print_summary(len(files), extract_count, len(files)-extract_count)
    except Exception as e:
        print(f"❗ Error extracting HTML: {e}")

def print_summary(total, succeed, fail):
    print(f"\n📊 Bronze summary:\nTotal: {total} | Extracted: {succeed} | Failed: {fail}")

def ingest():
    print("\n🥉 Bronze:...")
    input = DATA_DIR/"0_source/"
    output = DATA_DIR/"1_bronze/"
    ingest_all_mhtml(input, output)