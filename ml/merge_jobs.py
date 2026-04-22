import pandas as pd

# Load Kaggle dataset
kaggle = pd.read_csv("ml/data/raw/kaggle_jobs.csv")

# Normalize column names
kaggle.columns = kaggle.columns.str.lower().str.strip()
kaggle = kaggle.loc[:, ~kaggle.columns.str.contains('^unnamed')]
print("Columns in Kaggle dataset:", kaggle.columns)

# Auto-detect role column
role_col = None
desc_col = None

for col in kaggle.columns:
    if "title" in col or "role" in col or "position" in col:
        role_col = col
    if "description" in col:
        desc_col = col

if role_col is None or desc_col is None:
    raise Exception("❌ Could not find role/description columns")

# Rename properly
kaggle = kaggle.rename(columns={
    role_col: "role",
    desc_col: "description"
})

# Keep only required columns
kaggle = kaggle[["role", "description"]]

# Load generated dataset
gen = pd.read_csv("ml/data/raw/generated_jobs.csv")

# Merge
final = pd.concat([kaggle, gen], ignore_index=True)

# Clean
final.dropna(inplace=True)
final.drop_duplicates(inplace=True)

# Format
final["role"] = final["role"].str.title()

# Save
final.to_csv("ml/data/jobs.csv", index=False)

print("✅ jobs.csv created successfully!")