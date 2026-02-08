import json
import os
import re


def replace_text_in_files(terms_map_path, original_dir, processed_dir):
    with open(terms_map_path, "r", encoding="utf-8") as f:
        terms_map = json.load(f)

    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    for filename in os.listdir(original_dir):
        if os.path.isfile(os.path.join(original_dir, filename)):
            original_filepath = os.path.join(original_dir, filename)
            processed_filepath = os.path.join(processed_dir, filename)

            try:
                file_content = ""
                with open(original_filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()

                for key, value in terms_map.items():
                    file_content = re.sub(
                        re.escape(key), value, file_content, flags=re.IGNORECASE
                    )

                with open(processed_filepath, "w", encoding="utf-8") as f:
                    f.write(file_content)

                print(
                    f"File '{filename}' saved to '{processed_dir}'"
                )

            except Exception as e:
                print(f"Error during processing '{filename}': {e}")


if __name__ == "__main__":
    replace_text_in_files("terms_map.json", "original", "processed")
