import os

from uniker.kge.run import simulator_main
from uniker.run import run_fc


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
        ["--cuda", "--do_test",  "--do_save_ranks", "--model", "TransE", "-init", model_path, "--train_path", train_path,
         "--data_path", data_path])
    print("hey!")


def forward_chain():
    data_path = os.path.join(os.getcwd(), "int_files")
    run_fc(data_path, "train.txt", "inferred_obs.txt", "fc_observation.txt")
    run_fc(data_path, "train.txt", "inferred_vis.txt", "fc_visibility.txt")
    inferred_obs_path = os.path.join(data_path, "inferred_obs.txt")
    inferred_vis_path = os.path.join(data_path, "inferred_vis.txt")
    participating_obs_satellites = []
    with open(inferred_obs_path) as inferred_obs_file:
        for line in inferred_obs_file:
            splits = line.split("\t")
            if splits[1] == "canParticipateObservation":
                participating_obs_satellites.append(splits[0])
    participating_vis_satellites = []
    with open(inferred_vis_path) as inferred_vis_file:
        for line in inferred_vis_file:
            splits = line.split("\t")
            if splits[1] == "canParticipateVisibility":
                participating_vis_satellites.append(splits[0])
    participating_satellites = [sat for sat in participating_obs_satellites if sat in participating_vis_satellites]
    return participating_satellites
