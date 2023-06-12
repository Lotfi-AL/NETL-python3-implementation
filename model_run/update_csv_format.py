import os

def change_csv_format():
    model_name = "bertopic_all-roberta-large-v1_np_mini_stopwords.csv"
    data = os.path.join("data", model_name)
    

if __name__ == "__main__":
    change_csv_format()