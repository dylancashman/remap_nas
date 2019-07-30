# hyperband_mas.py
# Generates completely random models, but apportions training according to Hyperband Li et al 2017
# Can specify the number of resources (total number of epochs) and the eta value, which controls
# how quickly the number of models being trained shrinks at different runs of the optimizer.
###########

# Load pytorch
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from random_cnn_generator import RandomConvNet
from optimizer_utils import train_model, calculate_and_print_accuracy, Logger
import argparse
import random
import uuid
import json
import csv
import numpy as np
import math

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", help="directory to save models to", default='models/')
parser.add_argument("--accuracy_file", help="text file to save results to", default='hyperband_accuracy.json')
parser.add_argument("--mast_data_file", help="MAST JSON file to save results to", default='hyperband_mast.json')
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("--cuda", help="use cuda if GPUs are available",
                    action="store_true")
parser.add_argument("-R", type=int, help="number of resources allowed", default=9)
parser.add_argument("--eta", type=int, help="logarithmic base for rate of models each run", default=3)
parser.add_argument('--data_dir', help="directory to save cifar10 data to", default="./data/")

args = parser.parse_args()

device = 'cuda' if args.cuda and torch.cuda.is_available() else 'cpu'

if args.verbose: 
    print("model_dir is ", args.model_dir, " and accuracy_file is ", args.accuracy_file)
    print("device is ", device)

transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

trainset = torchvision.datasets.CIFAR10(root=args.data_dir, train=True,
                                        download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=128,
                                          shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root=args.data_dir, train=False,
                                       download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=128,
                                         shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# This should store the model's ID, architecture, and its accuracy measurements, as well as timestamps
from datetime import datetime
# "2018-07-23T03:36:36.196955"
datestring = '%Y-%m-%dT%H:%M:%S.%f'
def current_time():
    return datetime.now().strftime(datestring)

model_data = {}

logger = Logger(args.mast_data_file)

def main():
    print("Running hyperband optimizer with ", args.R, "resources and eta =", args.eta)
    # According to Li et al
    s_max = int(np.floor(math.log(args.R, args.eta)))
    b = (s_max + 1) * args.R

    for s in range(1, s_max + 1)[::-1]:
        n = int(np.ceil(b * pow(args.eta, s) / (args.R * (s+1)) ))
        r = args.R * pow(args.eta, -s)

        # Begin SuccessiveHalving with (n,r) inner loop
        T = get_hyperparameter_configuration(n)

        for i in range(s+1):
            n_i = int(np.floor(n * pow(args.eta, -i)))
            r_i = r * pow(args.eta, i)
            if (i>0):
                L = [run_then_return_val_loss(t, r_i, new_model=False) for t in T]
            else:
                L = [run_then_return_val_loss(t, r_i) for t in T]
            T = top_k(T, L, int(np.floor(n_i / args.eta)))
            logger.save_log()

# Returns n random conv nets
def get_hyperparameter_configuration(n):
    nets = []
    for i in range(n):
        net = RandomConvNet(1024, 3, 10)
        metadata = net.metadata()
        logger.log_model(net, metadata)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(net.parameters())
        nets.append({'net': net, 'criterion': criterion, 'optimizer': optimizer})
        model_data[metadata['id']] = {'trainedEpochs': 0 }
    return nets

def run_then_return_val_loss(model, r, new_model=True):
    net = model['net']
    criterion = model['criterion']
    optimizer = model['optimizer']
    net = net.to(device)
    net_metadata = net.metadata()
    if device == 'cuda':
        net = torch.nn.DataParallel(net)

    if (args.verbose):
        print("training model: ", net)

    with open(args.model_dir + net_metadata['id'] + '_hyperband_metadata.json', 'w') as outfile:
        json.dump(net_metadata, outfile)

    val_loss = train_model(net, net_metadata, criterion, optimizer, trainloader, testloader, model_dir=args.model_dir, num_epochs=int(r), verbose=args.verbose, device=device, new_model=new_model, logger=logger)
    model_data[net_metadata['id']]['trainedEpochs'] += int(r)
    return val_loss

def top_k(models, values, k):
    top_k_models = [models[i] for i in reversed(np.argsort(values))][0:k]
    return top_k_models

main()