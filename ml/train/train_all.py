from clustering import train_role_clustering
from train_classifier import train_role_classifier
from train_regressor import train_ats_regressor


if __name__ == "__main__":
    print(train_role_classifier())
    print(train_ats_regressor())
    print(train_role_clustering())
