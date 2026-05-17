import pandas as pd
import re

s = "['3mxJuHRn2ZWD5OofvJtDZY']"
extracted = re.search(r"'(.*?)'", s).group(1)
print(f"Original: {s}")
print(f"Extracted: {extracted}")

df = pd.DataFrame({"artists_id": ["['3mxJuHRn2ZWD5OofvJtDZY']", "['4xWMewm6CYMstu0sPgd9jJ']"]})
df["artists_id"] = df["artists_id"].str.extract(r"'(.*?)'")[0]
print("\nDataFrame extracted:")
print(df)
