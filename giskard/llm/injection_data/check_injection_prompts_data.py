import pandas as pd

if __name__ == "__main__":
    df = pd.read_csv("injection_prompts_data.csv")
    assert all(df.columns == ["prompt", "name", "group", "source", "language"])
    assert not df.prompt.isnull().values.any()
