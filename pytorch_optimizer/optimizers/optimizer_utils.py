import torch
import csv
import datetime
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

# classes = ('plane', 'car', 'bird', 'cat',
#            'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

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

EPSILON = 0.005
NUM_WITHOUT_IMPROVEMENT = 3

# For now, only uses Cross Entropy (so only works with multiclass)
# maybe not parameterized optimally for anything but CIFAR10

def train_model(model, net_metadata, criterion, optimizer, trainloader, testloader, model_dir='./models/', num_epochs=2, verbose=False, device='cpu', new_model=True, logger=None, scheduler=None, early_stopping = False):
    print("model_dir is ", model_dir)
    print("training model ", model)
    val_acc, _ = calculate_and_print_accuracy(model, net_metadata['id'], None, testloader, verbose=verbose, device=device)
    print("calculated accuracy, ", val_acc)
    start_time = datetime.datetime.now()
    timestamps = [None for i in range(num_epochs)]
    epoch_number = 0
    prev_val_loss = np.infty
    val_loss = 0.0
    epoch_count = 0
    num_without_improvement = 0
    back_times = []
    fwd_times = []

    for epoch in range(num_epochs):  # loop over the dataset multiple times
        if scheduler:
            print("TRAINING EPOCH ", epoch, " with lr ", scheduler.get_lr())
        else:
            print("TRAINING EPOCH ", epoch)
        # I guess when we parallelize models, it removes any attributes defined on the instance
        # We don't really need the number of epochs currently.
        if device == 'cpu':
            model._epochs += 1
            epoch_number = model._epochs
        else:
            epoch_number += 1

        running_loss = 0.0
        running_total = 0
        running_correct = 0
        total = 0
        correct = 0

        for i, data in enumerate(trainloader, 0):
            # get the inputs
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)

            # Trying this to get batchnorm layers to work
            # 

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            fwdStart = datetime.datetime.now()
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            fwdEnd = datetime.datetime.now()
            if (i == 0):
                fwd_times.append((fwdEnd - fwdStart).microseconds)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            # print statistics
            running_loss += loss.item()
            running_total += labels.size(0)
            running_correct += (predicted == labels).sum().item()
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if verbose and i % 50 == 49:    # print every 50 mini-batches
                print('[%d, %5d] loss: %.3f, train_acc: %.3f' %
                      (epoch + 1, i + 1, running_loss / 50, 100 * running_correct / running_total))
                running_loss = 0.0
                running_correct = 0
                running_total = 0

        train_acc = correct / total

        if logger or scheduler:
            val_acc, val_loss = calculate_and_print_accuracy(model, net_metadata['id'], None, testloader, verbose=verbose, device=device, criterion=criterion)
            if scheduler:
                # scheduler.step(val_loss)        
                scheduler.step()

            if logger:
                logger.log_measurements(net_metadata, 
                    epoch_number, 
                    {
                        'val_acc': val_acc / 100.0,
                        'val_accs': val_acc / 100.0,
                        'loss': running_loss,
                        'train_acc': train_acc,
                        'train_accs': train_acc,
                        'epochs': epoch_number
                    }
                )

        timestamps[epoch] = datetime.datetime.now()
        epoch_count = epoch_count + 1
        # print("val_loss is %.3f, prev_val_loss is %.3f, and (prev_val_loss - val_loss) is %.4f" % (val_loss, prev_val_loss, (prev_val_loss - val_loss)))

        if (early_stopping and (prev_val_loss - val_loss < EPSILON)):
            num_without_improvement = num_without_improvement + 1
            if (num_without_improvement >= NUM_WITHOUT_IMPROVEMENT):
                print("early stopping after ", epoch_count, " epochs, val loss only changed from ", prev_val_loss, " to ", val_loss)
                break
        else:
            prev_val_loss = val_loss
            num_without_improvement = 0

    print("DONE WITH TRAINING epochs ", epoch_number)
    for epoch in range(epoch_count):
        if epoch == 0:
            back_times.append((timestamps[epoch] - start_time).total_seconds())
        else:
            back_times.append((timestamps[epoch] - timestamps[epoch - 1]).total_seconds())

    avg_fwd_time = sum(fwd_times) / len(fwd_times)
    avg_back_time = sum(back_times) / len(back_times)

    print("saving torch model to ", os.path.join(model_dir, net_metadata['id'] + '.model'))
    torch.save(model, os.path.join(model_dir, net_metadata['id'] + '.model'))
    torch.save(criterion, os.path.join(model_dir, net_metadata['id'] + '.criterion'))
    torch.save(optimizer, os.path.join(model_dir, net_metadata['id'] + '.optimizer'))

    # Lastly, we calculate the training accuracy
    if logger:
        logger.log_measurements(net_metadata, 
            num_epochs, 
            {
                'forward_time': avg_fwd_time,
                'backward_time': avg_back_time,
                'final_train_acc': train_acc,
                'final_val_acc': val_acc
            },
            status='in_progress'
        )
    if verbose:
        print('Finished Training')

    return running_loss

def continue_training_model(filepath, trainloader, testloader, model_dir='./models/', num_epochs=2, verbose=False, device='cpu', logger=None):
    model = torch.load(filepath + '.model')
    oldoptimizer = torch.load(filepath + '.optimizer')
    criterion = nn.CrossEntropyLoss()
    net_metadata = model.metadata()
    optimizer = optim.Adam(model.parameters())
    optimizer.load_state_dict(oldoptimizer.state_dict())
    return train_model(model, net_metadata, criterion, optimizer, trainloader, testloader, model_dir=model_dir, num_epochs=num_epochs, verbose=verbose, device=device, new_model=False, logger=logger)

def train_model_from_scratch(filepath, trainloader, testloader, model_dir='./models/', num_epochs=2, verbose=False, device='cpu', logger=None, lrscheduler=True):
    model = torch.load(filepath + '.model')
    model.initialize_weights()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=0.0005)
    net_metadata = model.metadata()

    return train_model(model, net_metadata, criterion, optimizer, trainloader, testloader, model_dir=model_dir + 'retrained/', num_epochs=num_epochs, verbose=verbose, device=device, new_model=False, logger=logger)


def calculate_and_print_accuracy(model, modelID, model_dir, testloader, verbose=False, device='cpu', criterion=None, trainloader=None):
    correct = 0
    total = 0
    class_correct = list(0. for i in range(10))
    class_total = list(0. for i in range(10))

    traincorrect = 0
    traintotal = 0
    trainclass_correct = list(0. for i in range(10))
    trainclass_total = list(0. for i in range(10))

    iterator = 0
    predictions = []
    loss = 0.0
    with torch.no_grad():

        for data in testloader:
            # print("iteration in testloader")
            images, labels = data
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            if criterion:
                loss = criterion(outputs, labels).item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            c = (predicted == labels).squeeze()

            for i in range(len(labels)):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1
                iterator += 1
                predictions.append((iterator, predicted[i].item()))

        iterator = 0
        if trainloader:
            for data in trainloader:
                # print("iteration in testloader")
                images, labels = data
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                if criterion:
                    loss = criterion(outputs, labels).item()
                _, predicted = torch.max(outputs.data, 1)
                traintotal += labels.size(0)
                traincorrect += (predicted == labels).sum().item()
                c = (predicted == labels).squeeze()

                for i in range(len(labels)):
                    label = labels[i]
                    trainclass_correct[label] += c[i].item()
                    trainclass_total[label] += 1
                    iterator += 1


    if model_dir:
        with open(os.path.join(model_dir, modelID + '_predictions.csv'),'w') as out:
            csv_out=csv.writer(out)
            csv_out.writerow(['example','predicted_class'])
            for row in predictions:
                csv_out.writerow(row)

    accuracy = 100 * correct / total
    if verbose:
        print('------------------')
        print(modelID, ': Accuracy of the network on the %s test images: %d %%' % (
            total, accuracy))

        if trainloader:
            trainaccuracy = 100 * traincorrect / traintotal        
            print(modelID, ': Accuracy of the network on all %s of the training images: %d %%' % (
                total, trainaccuracy))

        for i in range(10):
            print('Accuracy of %5s : %2d %%' % (
                classes[i], 100 * class_correct[i] / class_total[i]))
        
        print('==================')

    return accuracy, loss

def calculate_and_print_accuracy_and_return_predictions(model, modelID, model_dir, testloader, verbose=False, device='cpu', criterion=None):
    correct = 0
    total = 0
    class_correct = list(0. for i in range(10))
    class_total = list(0. for i in range(10))
    iterator = 0
    predictions = []
    loss = 0.0
    with torch.no_grad():

        for data in testloader:
            images, labels = data
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            if criterion:
                loss = criterion(outputs, labels).item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            c = (predicted == labels).squeeze()

            for i in range(len(labels)):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1
                iterator += 1
                predictions.append((iterator, predicted[i].item()))

    if model_dir:
        with open(os.path.join(model_dir, modelID + '_predictions.csv'),'w') as out:
            csv_out=csv.writer(out)
            csv_out.writerow(['example','predicted_class'])
            for row in predictions:
                csv_out.writerow(row)

    accuracy = 100 * correct / total
    if verbose:
        print('------------------')
        print(modelID, ': Accuracy of the network on the 10000 test images: %d %%' % (
            accuracy))

        for i in range(10):
            print('Accuracy of %5s : %2d %%' % (
                classes[i], 100 * class_correct[i] / class_total[i]))
        
        print('==================')

    return accuracy, loss, predictions

DATESTRING = '%Y-%m-%dT%H:%M:%S.%f'

import datetime
import json
import os.path
# {"timestamp": "2018-07-23T03:36:36", "values": {"model": {"NNModel": {"_layers": [{"type": "Conv2D", "filters": "64", "kernel_size": "1", "strides": "1"}, {"type": "Conv2D", "filters": "128", "kernel_size": "1", "strides": "1"}, {"type": "Dense", "units": "64"}, {"type": "AveragePooling2D", "pool_size": "2", "strides": "2"}, {"type": "Conv2D", "filters": "64", "kernel_size": "1", "strides": "1"}, {"type": "Dense", "units": "64"}, {"type": "Conv2D", "filters": "128", "kernel_size": "5", "strides": "1"}, {"type": "Conv2D", "filters": "128", "kernel_size": "3", "strides": "1"}, {"type": "Dense", "units": "64"}, {"type": "GlobalAveragePrecision"}], "nparam": "370112"}}}, "uid": "3c25e24e-c0e3-4371-95f8-cc95da3c9ff7", "etime": ["7c63795c-6a52-45f8-a35c-7c1d09e48d11"]}
# {"timestamp": "2018-07-23T04:11:36.196955", "values": {"train_acc": "0.5168"}, "uid": "aba58a84-7daf-46f9-b826-e6021187edad", "etime": ["812f6b96-1a71-4ab5-8a16-af52b1908343", "0", "15"]}
class Logger():
    def __init__(self, filename, load_log=False, socket=None):
        self.log_rows = []
        self.filename = filename
        self.load_log = load_log
        self.socket = socket

        if not os.path.isfile(filename):
            print("File doesn't exist at " + filename)
            print("Creating log file.")
        else:
            if self.load_log:
                self.log_rows = json.load(open(self.filename, 'r'))

    def num_parameters(self, model):
        return sum(p.numel() for p in model.parameters())

    def log_model(self, model, metadata):
        self.log_rows.append({
            'timestamp': self.current_time(),
            'values': {
                'model': {
                    'NNModel': {
                        '_layers': metadata['_layers'],
                    }
                }
            },
            'uid': metadata['id'],
            'etime': [metadata['id']]
        })

        self.log_rows.append({
            'timestamp': self.current_time(),
            'values': {'parameters': self.num_parameters(model)},
            'uid': metadata['id'],
            'etime': [metadata['id']]
        })

    def log_measurements(self, model, epoch, measurements, status='in_progress'):
        self.log_rows.append({
            'timestamp': self.current_time(),
            'values': measurements,
            'uid': model['id'],
            'etime': [model['id'], '0', epoch]
            })

        if (self.socket):
            self.socket.emit('updateModelStatus', { 'id': model['id'], 'values': measurements, 'epoch': epoch, 'trainingStatus': status });

    def current_time(self):
        return datetime.datetime.now().strftime(DATESTRING)

    def save_log(self):
        with open(self.filename, 'w') as outfile:
            json.dump(self.log_rows, outfile)
