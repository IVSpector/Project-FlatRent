import pickle

# Load feature list
with open("features.pkl", "rb") as f:
    features = pickle.load(f)

# Show all features
print("🔹 Model Features:")
for i, ftr in enumerate(features, 1):
    print(f"{i:02d}. {ftr}")

