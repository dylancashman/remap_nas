# random_mas.py
# Generates completely random models
# Can specify the number of epochs they should be trained.
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
import os

from quickdraw_dataset import QuickdrawDataset

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", help="directory to save models to", default='models/')
parser.add_argument("--accuracy_file", help="text file to save results to", default='random_accuracy.json')
parser.add_argument("--mast_data_file", help="MAST JSON file to save results to", default='random_mast.json')
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("--cuda", help="use cuda if GPUs are available",
                    action="store_true")
parser.add_argument("-n", type=int, help="number of models returned", default=2)
parser.add_argument("--workers", type=int, help="number of workers used", default=1)
parser.add_argument("--epochs", type=int, help="number of epochs each model trained", default=2)
parser.add_argument('--data_dir', help="directory to save cifar10 data to", default="./data/")
parser.add_argument('--early_stopping', help="stops training if validation loss stops improving", action="store_true")
parser.add_argument('--dataset', help="which dataset to use", default='cifar')

args = parser.parse_args()

def main():
    if args.cuda:
        if torch.cuda.is_available():
            print("cuda is available, using gpu")
            device = 'cuda'
        else:
            print('tried cuda, but it was unavailable')
            device = 'cpu'

    else:
        device = 'cpu'

    if args.verbose: 
        print("model_dir is ", args.model_dir, " and accuracy_file is ", args.accuracy_file)
        print("device is ", device)
        

    if (args.dataset=='cifar'):
        transform = transforms.Compose(
            [transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
        trainset = torchvision.datasets.CIFAR10(root=args.data_dir, train=True,
                                                download=True, transform=transform)
        trainloader = torch.utils.data.DataLoader(trainset, batch_size=32,
                                                shuffle=True, num_workers=args.workers)

        testset = torchvision.datasets.CIFAR10(root=args.data_dir, train=False,
                                            download=True, transform=transform)
        testloader = torch.utils.data.DataLoader(testset, batch_size=32,
                                                shuffle=False, num_workers=args.workers)
        classes = ('plane', 'car', 'bird', 'cat',
                'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

    else:
        print("loading quickdraw")
        # trainset = QuickdrawDataset(transform=transform)
        # transform = transforms.Compose(
        #     [transforms.ToTensor(),
        #     transforms.Normalize([0.5], [0.5])])
        transform = None
        trainset = QuickdrawDataset(transform=transform)
        print("got trainset")
        trainloader = torch.utils.data.DataLoader(trainset, batch_size=256,
                                                shuffle=True, num_workers=args.workers)
        print("got trainloader")

        testset = QuickdrawDataset(mode='test', transform=transform)
        testloader = torch.utils.data.DataLoader(testset, batch_size=256,
                                                shuffle=False, num_workers=args.workers)
        classes = (
            'face',
            'moustache',
            'pear',
            'umbrella',
            'pineapple',
            'mouth',
            'nose',
            'wine bottle',
            'apple',
            'octopus'
        )


    logger = Logger(args.mast_data_file)

    print("Generating", args.n, "models for", args.epochs, "epochs.")
    accuracies = [None] * args.n
    for i in range(args.n):
        accuracies[i] = (None, None)

    for i in range(args.n):
        if (args.dataset == 'cifar'):
            net = RandomConvNet(1024, 3, 10) # for CIFAR sizes
            while (logger.num_parameters(net) > 1000000):
                print("resampling model, it's too large to train")
                net = RandomConvNet(1024, 3, 10)
        else:
            net = RandomConvNet(784, 1, 10) # for quickdraw sizes
            while (logger.num_parameters(net) > 1000000):
                net = RandomConvNet(784, 1, 10)
        if args.verbose:
            print("Generated net:", net.layers)
        # This doesn't seem to work with pytorch 0.2
        if torch.__version__ >= '0.3':
            net = net.to(device)
        net_metadata = net.metadata()
        logger.log_model(net, net_metadata)
        criterion = nn.CrossEntropyLoss()
        # optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
        optimizer = optim.Adam(net.parameters(), lr=0.001)
        # scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.75)

        if (args.verbose):
            print("training model: ", net)

        with open(os.path.join(args.model_dir, net_metadata['id'] + '_metadata.json'), 'w') as outfile:
            json.dump(net_metadata, outfile)
        print("training model")
        train_model(net, net_metadata, criterion, optimizer, trainloader, testloader, model_dir=args.model_dir, num_epochs=args.epochs, verbose=args.verbose, device=device, logger=logger, early_stopping=args.early_stopping, scheduler=scheduler)
        val_acc, _ = calculate_and_print_accuracy(net, net_metadata['id'], args.model_dir, testloader, verbose=args.verbose, device=device)
        accuracies[i] = (net_metadata['id'], val_acc)
        print("saving model to ", os.path.join(args.model_dir, net_metadata['id'] + '.model'))
        torch.save(net, os.path.join(args.model_dir, net_metadata['id'] + '.model'))
        logger.save_log()

    with open(args.accuracy_file,'w') as out:
        csv_out=csv.writer(out)
        csv_out.writerow(['name','valAcc'])
        for row in accuracies:
            csv_out.writerow(row)

    print(accuracies)

if __name__ == '__main__':
    main()
