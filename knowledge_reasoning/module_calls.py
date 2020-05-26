import os

from UniKER.kge.run import simulator_main


def train_uniker():
    data_path = os.path.join(os.getcwd(), "int_files")
    model_path = os.path.join(os.getcwd(), "models", "TransE")
    train_path = os.path.join(data_path, "train.txt")
    simulator_main(
        ["--cuda", "--do_train", "--model", "TransE", "--data_path", data_path, "-b", "1024",
         "-n", "256", "-d", "100", "-g", "24", "-a", "1", "-adv", "-lr", "0.001", "--max_steps", "5000",
         "--test_batch_size", "16", "-save", model_path, "--train_path", train_path])


def eval_uniker():
    data_path = os.path.join(os.getcwd(), "int_files")
    model_path = os.path.join(os.getcwd(), "models", "TransE")
    train_path = os.path.join(data_path, "train.txt")
    simulator_main(
        ["--cuda", "--do_test", "--model", "TransE", "-init", model_path, "--train_path", train_path,
         "--data_path", data_path])
