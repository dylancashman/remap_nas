from flask import Flask, send_file, jsonify, make_response
from flask_cors import CORS
from flask_socketio import SocketIO
import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.optim as optim
import argparse
import os
import signal
import json
import glob
from numpy import random
from pathlib import Path
from optimizer_utils import train_model, train_model_from_scratch, continue_training_model, Logger, calculate_and_print_accuracy, calculate_and_print_accuracy_and_return_predictions
from random_cnn_generator import RandomConvNet, random_conv_net_from_template, generate_ablations_from_template
from queue import Queue
from threading import Thread
import numpy as np
import pandas as pd

# Need to calculate distances for new models to send to frontend
MODEL_DISTANCES_PATH = os.path.join('20190330_quickdraw_model_projection_data.json')
from scipy.spatial.distance import hamming
import neural_network
import nn_comparators
from general_utils import get_dok_mat_with_set_coords
model_distances_data = []
with open(MODEL_DISTANCES_PATH) as f:
    model_distances_data = json.load(f)
hamming_distances = np.loadtxt(os.path.join('hamming_distances_quickdraw_20190330.csv'), delimiter=',')
hamming_projected_coords = np.loadtxt(os.path.join('hamming_projected_coords_quickdraw_20190330.csv'), delimiter=',')
HAMMING_DISTANCES_SQUARED = np.square(hamming_distances)
HAMMING_PROJECTIONS_PINV = np.linalg.pinv(hamming_projected_coords)
otmann_distances = np.loadtxt(os.path.join('otmann_distances_quickdraw_20190330.csv'), delimiter=',')
otmann_projected_coords = np.loadtxt(os.path.join('otmann_projected_coords_quickdraw_20190330.csv'), delimiter=',')
OTMANN_DISTANCES_SQUARED = np.square(otmann_distances)
OTMANN_PROJECTIONS_PINV = np.linalg.pinv(otmann_projected_coords)

new_models_info = []
model_layer_dict = {}
# print(model_distances_data[0])
for model in model_distances_data:
    model_layer_dict[model['id']] = model['layers']

cnn_layer_labels = ['ip', 'op', 'dense', 
                    'dropout', 'softmax', 
                    'conv1', 'conv3', 'conv5', 
                    'tanh', 'relu', 'sigmoid',
                    'pool2', 'pool3', 'pool5']

non_assignment_penalty = 1
# cnn_layer_labels, label_mismatch_penalty = \
    # nn_comparators.get_cnn_layer_label_mismatch_penalties(non_assignment_penalty)

label_mismatch_penalty = []
# ip penalties
label_mismatch_penalty.append([0] + [np.inf]*13)
# op penalties
label_mismatch_penalty.append([np.inf, 0] + [np.inf]*12)
# dense penalties
label_mismatch_penalty.append([np.inf, np.inf, 0] + [np.inf]*11)
# dropout penalties
label_mismatch_penalty.append([np.inf]*3 + [0] + [np.inf]*10)
# softmax penalties
label_mismatch_penalty.append([np.inf]*4 + [0] + [np.inf]*9)
# conv1 penalties
label_mismatch_penalty.append([np.inf]*5 + [0, 0.2, 0.3] + [np.inf]*6)
# conv3 penalties
label_mismatch_penalty.append([np.inf]*5 + [0.2, 0, 0.2] + [np.inf]*6)
# conv5 penalties
label_mismatch_penalty.append([np.inf]*5 + [0.3, 0.2, 0] + [np.inf]*6)
# tanh penalties
label_mismatch_penalty.append([np.inf]*8 + [0, 0.25, 0.1] + [np.inf]*3)
# relu penalties
label_mismatch_penalty.append([np.inf]*8 + [0.25, 0, 0.25] + [np.inf]*3)
# sigmoid penalties
label_mismatch_penalty.append([np.inf]*8 + [0.1, 0.25, 0] + [np.inf]*3)
# pool2 penalties
label_mismatch_penalty.append([np.inf]*11 + [0, 0.2, 0.3])
# pool3 penalties
label_mismatch_penalty.append([np.inf]*11 + [0.2, 0, 0.2])
# pool5 penalties
label_mismatch_penalty.append([np.inf]*11 + [0.3, 0.2, 0])

label_mismatch_penalty = np.array(label_mismatch_penalty)

tp_comp = nn_comparators.OTMANNDistanceComputer(cnn_layer_labels,
    label_mismatch_penalty, non_assignment_penalty,
    nn_comparators.CNN_STRUCTURAL_PENALTY_GROUPS,
    nn_comparators.PATH_LENGTH_TYPES,
    dflt_mislabel_coeffs=1.0, dflt_struct_coeffs=1.0)

# print("model_distances_data[0] is ", model_distances_data[0])

MODEL_DIR = 'models_quickdraw_final'
DATA_DIR = 'data'
LOG_FILE = 'model_quickdraw_logs.json'
# TRUE_LABELS = pd.read_csv('cifar_test_labels.csv')['true_class']
from quickdraw_dataset import QuickdrawDataset
testset = QuickdrawDataset(mode='test')
TRUE_LABELS = []

it = 0
# for (_, label) in testset:
for i in range(40000):
    (_, label) = testset[i]
    TRUE_LABELS.append(label)
    it = it + 1

TRUE_LABELS = pd.Series(TRUE_LABELS)

IMAGE_DIR = os.path.join('static')
NUM_EPOCHS_TRAIN = 10
# app = Flask(__name__, static_folder=IMAGE_DIR)
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '196_BOSTON_AVENUE'
socketio = SocketIO(app)

parser = argparse.ArgumentParser()

transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

transform = None
trainset = QuickdrawDataset(transform=transform)
print("got trainset")
trainloader = torch.utils.data.DataLoader(trainset, batch_size=256,
                                        shuffle=True, num_workers=2)
print("got trainloader")

testset = QuickdrawDataset(mode='test', transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=256,
                                        shuffle=False, num_workers=2)
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


# trainset = torchvision.datasets.CIFAR10(root=DATA_DIR, train=True,
#                                         download=True, transform=transform)
# trainloader = torch.utils.data.DataLoader(trainset, batch_size=32,
#                                           shuffle=True, num_workers=2)

# testset = torchvision.datasets.CIFAR10(root=DATA_DIR, train=False,
#                                        download=True, transform=transform)
# testloader = torch.utils.data.DataLoader(testset, batch_size=32,
                                         # shuffle=False, num_workers=2)

# classes = ('plane', 'car', 'bird', 'cat',
#            'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
logger = Logger(LOG_FILE, load_log=True, socket=socketio)

def worker():
    while True:
        item = training_queue.get()
        net = item['net']
        epochs = item['epochs']
        train_model_for_frontend(net, epochs)
        # train_model_for_frontend(net, 3)
        # Maybe we should store the models and their results after they are completed?
        # training_queue.task_done()

training_queue = Queue()
current_model_id = ''
training_thread = Thread(target=worker)
training_thread.daemon = True
training_thread.start()

# The training all happens in a separate thread, which implements a training queue

def add_model_to_training_queue(net, num_epochs=NUM_EPOCHS_TRAIN):
    training_queue.put({'net': net, 'epochs': num_epochs})

def generate_confusion_matrix_bins(predlabels):
    # need to roll our own because sklearn doesn't produce bins
    predictions = np.array(predlabels)[:,1]
    # Using https://stackoverflow.com/questions/21153865/obtain-indices-corresponding-to-instances-for-each-type-of-error-in-a-confusion
    return [[[int(x) for x in np.where(np.array(np.logical_and(TRUE_LABELS==r, predictions==c)))[0].tolist()] for c in range(10)] for r in range(10)]

def calculate_class_accuracies(confusion_matrix):
    total_true = [0 for _ in range(10)]
    total_predicted = [0 for _ in range(10)]
    total_correct = [0 for _ in range(10)]
    accuracies = [0.0 for _ in range(10)]

    for i in range(10):
        for j in range(10):
            count = len(confusion_matrix[i][j])
            if (i == j):
                total_correct[i] = count

            total_true[i] = total_true[i] + count
            total_predicted[j] = total_predicted[j] + count
    
    for i in range(10):
        accuracies[i] = 1.0 * total_correct[i] / total_true[i]
    return accuracies


def get_incremental_mds_embedding(d, projection_type='hamming'):
    # According to implementation at http://www.math.sjsu.edu/~gchen/Math285F15/Math%20285%20-%20Project%20WFSalinas_DLi.pdf
    # d is the vector of distances from our new point to all original points
    # projection_type is either hamming or otmannn

    # Assign our variables
    if projection_type is 'hamming':
        D = HAMMING_DISTANCES_SQUARED
        pseudoY = HAMMING_PROJECTIONS_PINV
    else:
        D = OTMANN_DISTANCES_SQUARED
        pseudoY = OTMANN_PROJECTIONS_PINV

    # First, we get d^2
    d2 = np.square(np.array(d))

    # Then, we calculate b
    (n, _) = D.shape
    a = ((1.0 / n) * d2 - d2).reshape(-1, 1)
    b = (1.0 / n) * np.dot(D, np.ones((n, 1)))
    c = (1.0 / (n**2)) * np.dot(np.dot(np.ones((n, n)), D), np.ones((n, 1)))
    b = 0.5 * a + b - c

    # The approximate solution is y_x = (Y^T Y) ^(-1) Y^t * b
    #  a.k.a pseudoinverse(Y) * b
    return np.dot(pseudoY, b)

def get_hamming_distances(predictions):
    predictions = np.array(predictions)[:,1]
    return [hamming(predictions, x['predictions']) for x in model_distances_data]

def get_otmann_distances(layers):
    new_nasbot_model = convert_model_object_to_nasbot_model({'layers': layers})
    # print("calculating otmann_distances...")

    # Then, we calculate the distances to every other model
    nasbot_models = [m['nasbot_model'] for m in model_distances_data]
    # print("comparing nasbot model ", new_nasbot_model)
    # print("other nasbot model", nasbot_models[0])
    otmann_distances = tp_comp.evaluate([new_nasbot_model], nasbot_models)
    return otmann_distances

# Then, we convert our models into these neural network classes
def convert_layer_to_nasbot_layer(layer):
    if layer['type'] == 'Activation':
        return layer['activation']
    elif layer['type'] == 'AveragePooling2D' or layer['type'] == 'MaxPool':
        return 'pool' + str(layer['pool_size'])
    elif layer['type'] == 'Conv2D':
        return 'conv' + str(layer['kernel_size'])
    elif layer['type'] == 'Dense':
        return 'dense'
    elif layer['type'] == 'Dropout':
        return 'dropout'
    else:
        print("got unmatched layer type ", layer)

def convert_layer_to_nasbot_filters(layer):
    if layer['type'] == 'Conv2D':
        return layer['filters']
    elif layer['type'] == 'Dense':
        return layer['units']
    else:
        return None
    
def convert_layer_to_nasbot_stride(layer):
    if layer['type'] == 'Conv2D':
        return 1
    elif layer['type'] == 'AveragePooling2D' or layer['type'] == 'MaxPool':
        return 2
    else:
        return None    

def convert_model_object_to_nasbot_model(model_object):
    # for now, our connectivity matrix is just 1s on the up off diagonal, because
    # we have strictly feed forward layers
    layers = model_object['layers']
    num_layers = len(layers) + 3 # for input, softmax, and output
    
    connection_coords = []
    for j in range(1, num_layers):
        connection_coords.append((j-1, j))

    connectivity_matrix = get_dok_mat_with_set_coords(num_layers, connection_coords)
    # print("layers are ", layers)
    # print("connectivity_matrix is ", connectivity_matrix.keys())
    # print("cnn_layer_labels is ", cnn_layer_labels)
    # print("['ip'] + [convert_layer_to_nasbot_layer(l) for l in layers] + ['softmax', 'op'] is ", ['ip'] + [convert_layer_to_nasbot_layer(l) for l in layers] + ['softmax', 'op'])
    conv = neural_network.ConvNeuralNetwork(
        ['ip'] + [convert_layer_to_nasbot_layer(l) for l in layers] + ['softmax', 'op'],
        connectivity_matrix,
        [None] + [convert_layer_to_nasbot_filters(l) for l in layers] + [None, None],
        [None] + [convert_layer_to_nasbot_stride(l) for l in layers] + [None, None],
        cnn_layer_labels
        )
    
    return conv
    # return None

for (i, model_object) in enumerate(model_distances_data):
    model_distances_data[i]['nasbot_model'] = convert_model_object_to_nasbot_model(model_object)


def delete_model_from_training_queue(model_id):
    global training_queue
    global training_thread
    global current_model_id

    if current_model_id == model_id:
        print("THIS ISN'T SUPPORTED AND DOES NOTHING")
        return False
        os.kill(signal.CTRL_C_EVENT, 0)
        training_thread = Thread(target=worker)
        training_thread.daemon = True
        training_thread.start()
    else:
        new_training_queue = Queue()
        while not training_queue.empty():
            m = training_queue.get()
            net = m['net']
            epochs = m['epochs']
            net_metadata = net.metadata()
            if net_metadata['id'] != model_id:
                new_training_queue.put({'net': net, 'epochs': epochs})
        training_queue = new_training_queue

    return True

def reorder_model_from_training_queue(model_ids_order):
    global training_queue
    global training_thread
    global current_model_id

    new_training_queue = Queue()
    models_dict = {}
    while not training_queue.empty():
        m = training_queue.get()
        net = m['net']
        epochs = m['epochs']
        net_metadata = net.metadata()
        models_dict[net_metadata['id']] = {'net': net, 'epochs': epochs}
    # Then, reconstruct queue
    for model_id in model_ids_order:
        new_training_queue.put(models_dict[model_id])
        # if net_metadata['id'] != model_id:
        #     new_training_queue.put(net)
    training_queue = new_training_queue

    return True

    # training_thread = Thread(target=worker)
    # training_thread.daemon = True
    # training_thread.start()

def generate_ablations_from_model(model_id, ablation_instructions = None, num_epochs=NUM_EPOCHS_TRAIN):
    # We look for the model's layers in our list of models
    if model_id not in model_layer_dict:
        # Bad request
        return False
    else:
        layers = model_layer_dict[model_id]
        net_list = generate_ablations_from_template(784, 1, 10, layers, ablation_instructions, parent_id=model_id)
        for net_info in net_list:
            net = net_info['net']
            changes = net_info['changes']
            change_indices = net_info['changeIndices']
            if torch.__version__ >= '0.3':
                net = net.to(device)
            net_metadata = net.metadata()
            # logger = Logger(LOG_FILE, load_log=True, socket=socketio)
            if (logger.num_parameters(net) < 3000000):
                model_layer_dict[net_metadata['id']] = net_metadata['_layers']

                socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'parentId': model_id, 'parentType': 'Ablation', 'changes': changes, 'changeIndices': change_indices, 'metadata': net_metadata, 'parameters': logger.num_parameters(net), 'trainingStatus': 'not_started'});

                # At this point, we should add this model to a queue, rather than train it explicitly in this thread.
                add_model_to_training_queue(net, num_epochs)

        return True


def generate_variations_from_model(model_id, number_models, variation_instructions = None, number_changes=1, num_epochs=NUM_EPOCHS_TRAIN):
    # We look for the model's layers in our list of models
    if model_id not in model_layer_dict:
        # Bad request
        return False
    else:
        layers = model_layer_dict[model_id]
        # Nothing to do with ablation instructions yet
        for i in range(number_models):
            net, changes = random_conv_net_from_template(784, 1, 10, layers, variation_instructions, number_changes=number_changes, parent_id=model_id)
            if torch.__version__ >= '0.3':
                net = net.to(device)
            net_metadata = net.metadata()
            # logger = Logger(LOG_FILE, load_log=True, socket=socketio)
            if (logger.num_parameters(net) < 3000000):
                model_layer_dict[net_metadata['id']] = net_metadata['_layers']

                socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'parentId': model_id, 'parentType': 'Variation', 'changes': changes, 'metadata': net_metadata, 'parameters': logger.num_parameters(net), 'trainingStatus': 'not_started'});

                # At this point, we should add this model to a queue, rather than train it explicitly in this thread.
                add_model_to_training_queue(net, num_epochs)

        return True

def generate_handcrafted_from_model(model_id, handcrafted_instructions, changes, num_epochs=NUM_EPOCHS_TRAIN):
    # We look for the model's layers in our list of models
    if model_id not in model_layer_dict:
        # Bad request
        return False
    else:
        # net = exact_conv_net_from_template(1024, 3, 10, handcrafted_instructions, parent_id=model_id)
        net = RandomConvNet(784, 1, 10, template=handcrafted_instructions, skip_template_softmax=True)
        if torch.__version__ >= '0.3':
            net = net.to(device)
        net_metadata = net.metadata()
        # logger = Logger(LOG_FILE, load_log=True, socket=socketio)
        # if (logger.num_parameters(net) < 10000000):
        model_layer_dict[net_metadata['id']] = net_metadata['_layers']

        socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'parentId': model_id, 'parentType': 'Handcrafted', 'changes': changes, 'metadata': net_metadata, 'parameters': logger.num_parameters(net), 'trainingStatus': 'not_started'});

        # At this point, we should add this model to a queue, rather than train it explicitly in this thread.
        add_model_to_training_queue(net, num_epochs)

    return True

def train_model_for_frontend(net, epochs=NUM_EPOCHS_TRAIN):
    global current_model_id

    # logger = Logger(args.logfile, load_log=True)
    if torch.__version__ >= '0.3':
        net = net.to(device)
    net_metadata = net.metadata()

    current_model_id = net_metadata['id']

    # This doesn't seem to work with pytorch 0.2
    logger.log_model(net, net_metadata)

    # print("should be changing to training:")
    socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'metadata': net_metadata, 'parameters': logger.num_parameters(net), 'trainingStatus': 'in_progress'});
    # if device == 'cuda':
    #     net = torch.nn.DataParallel(net)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(net.parameters(), lr=0.001)
    # scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.75)
    # optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    # optimizer = optim.Adam(net.parameters())

    # with open(args.model_dir + net_metadata['id'] + '_metadata.json', 'w') as outfile:
    with open(os.path.join(MODEL_DIR, net_metadata['id'] + '_metadata.json'), 'w') as outfile:
        json.dump(net_metadata, outfile)

    print("device is ", device)
    train_model(net, net_metadata, criterion, optimizer, trainloader, testloader, model_dir=MODEL_DIR, num_epochs=epochs, verbose=False, device=device, logger=logger, early_stopping=True, scheduler=scheduler)

    val_acc, _, predictions = calculate_and_print_accuracy_and_return_predictions(net, net_metadata['id'], MODEL_DIR, testloader, verbose=False, device=device)
    hamming_distances = get_hamming_distances(predictions)
    otmann_distances = get_otmann_distances(net_metadata['_layers'])
    hamming_embedding = get_incremental_mds_embedding(hamming_distances, projection_type='hamming')
    otmann_embedding = get_incremental_mds_embedding(otmann_distances, projection_type='otmann')
    print('hamming_embedding', hamming_embedding)
    print('otmann_embedding', otmann_embedding)
    confusion_matrix = generate_confusion_matrix_bins(predictions)
    class_accuracies = calculate_class_accuracies(confusion_matrix)
    socketio.emit('updateModelStatus', {'id': net_metadata['id'], 'hamming_embedding': hamming_embedding.tolist(), 'otmann_embedding': otmann_embedding.tolist(), 'class_accuracies': class_accuracies, 'confusion_matrix': confusion_matrix, 'trainingStatus': 'completed'})
    # print("GOT DISTANCES.  hamming_distances: ", hamming_distances)
    # print("otmann_distances: ", otmann_distances)

    print("saving model to ", MODEL_DIR + net_metadata['id'] + '.model')
    torch.save(net, os.path.join(MODEL_DIR, net_metadata['id'] + '.model'))
    logger.save_log()
    # socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'metadata': net_metadata, 'trainingStatus': 'completed' });

@app.route("/start_model_training/<string:modelId>")
def start_model_training(modelId, device='cpu', num_epochs=2):
    filepath = MODEL_DIR + modelId 
    # logger = Logger(args.logfile, load_log=True)
    # logger = Logger(LOG_FILE, load_log=True)
    val = train_model_from_scratch(filepath, trainloader, testloader, model_dir=MODEL_DIR, num_epochs=num_epochs, verbose=True, device=device, logger=logger)
    logger.save_log()
    return str(val)

@app.route("/continue_model_training/<string:modelId>")
def continue_model_training(modelId, device='cpu', num_epochs=2):
    filepath = MODEL_DIR + modelId 
    # logger = Logger(args.logfile, load_log=True)
    # logger = Logger(LOG_FILE, load_log=True)
    val = continue_training_model(filepath, trainloader, testloader, model_dir=MODEL_DIR, num_epochs=num_epochs, verbose=True, device=device, logger=logger)
    logger.save_log()
    return str(val)

@app.route("/get_image/<string:imageId>")
def return_image(imageId):
    filepath = os.path.join(IMAGE_DIR, imageId)
    if os.path.exists(filepath):
        return app.send_static_file(imageId)
    else:
        return "INVALID_PATH"

from PIL import Image
import io
import base64

@app.route("/get_random_class_image/<string:image_class>")
def return_random_class_image(image_class):
    # First, calculate image index
    image_class_index = classes.index(image_class)
    print("image class index is ", image_class_index)
    # options = range(image_class_index * NUM_PER_CLASS, (image_class_index + 1) * NUM_PER_CLASS)
    # The way the indexing works for quickdraw, we need to actually subtract out the offsets.
    options = range(image_class_index * int((0.2) * 20000), (image_class_index + 1) * int((0.2) * 20000))
    pointers = random.multinomial(n=1, pvals=[(1.0 / len(options))] * len(options), size=None)
    image_index = options[np.nonzero(pointers)[0][0]]
    # print("sampling uniformly, got", sample)
    print("image_index is ", image_index)
    print("testset length is ", len(testset))
    (img, label) = testset[image_index]
    # print("before reshape, img shape is ", img.shape)
    assert(image_class_index == int(label))
    img = img.reshape((28,28))
    print("img is ", img.shape)
    print("type(img) is ", type(img))
    print(img)
    image = Image.fromarray(img*255)
    img_io = io.BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(img_io, format='PNG')
# pil_img = Image.fromarray(img)
# buff = BytesIO()
# pil_img.save(buff, format="JPEG")
# new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    # img_str = base64.b64encode(img_io.getvalue()).decode('utf-8')
    # print("img_str class name is ", img_str.__class__.__name__)
    print("image_index class name is ", image_index.__class__.__name__)
            # byte_io = io.BytesIO()
            # byte_io.write(file.read())
    img_io.seek(0)
    response = make_response(send_file(img_io,mimetype='image/png'))
    response.headers['Content-Transfer-Encoding']='base64'
    response.headers['Mast-Image-Id'] = image_index
    response.headers['Access-Control-Expose-Headers'] = 'Mast-Image-Id'
    return response 


@app.route("/get_image_by_id/<string:imageId>")
def return_image_by_id(imageId):
    filepath = os.path.join(IMAGE_DIR, imageId)
    class_glob_path = Path(os.path.join(IMAGE_DIR))
    class_images = list(class_glob_path.glob(imageId + '_*.png'))
    filepath = class_images[0]
    if filepath and os.path.exists(filepath):
        return app.send_static_file(filepath.name)
    else:
        return "INVALID_PATH"

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept';
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# Socket IO stuff
training_models = []
@socketio.on('get_models')
def handle_get_models(message):
    print('returning models' + training_models)

@socketio.on('train_random_model')
def handle_train_random_model(message):
    net = RandomConvNet(1024, 3, 10) # for CIFAR sizes
    if torch.__version__ >= '0.3':
        net = net.to(device)
    net_metadata = net.metadata()
    # logger = Logger(LOG_FILE, load_log=True, socket=socketio)
    if (logger.num_parameters(net) < 10000000):
        model_layer_dict[net_metadata['id']] = net_metadata['_layers']

        socketio.emit('updateModelStatus', { 'id': net_metadata['id'], 'metadata': net_metadata, 'parameters': logger.num_parameters(net), 'trainingStatus': 'not_started'});

        # At this point, we should add this model to a queue, rather than train it explicitly in this thread.
        add_model_to_training_queue(net, NUM_EPOCHS_TRAIN)

@socketio.on('kill_queued_model')
def handle_kill_queued_model(message):
    print("message in kill queued models is ", message)
    # We actually rebuild the queue without the model id
    model_id = message['modelId']
    if delete_model_from_training_queue(model_id):
        return {'status': 'ok'}, 200, 'application/json'
    else:
        return {'status': 'bad_delete'}, 500, 'application/json'

@socketio.on('reorder_queued_model')
def handle_reorder_queued_model(message):
    # We actually rebuild the queue the model id spliced in the right place
    print("message is ", message)
    model_ids_order = message['modelIdOrderedList']
    if reorder_model_from_training_queue(model_ids_order):
        return {'status': 'ok'}, 200, 'application/json'
    else:
        return {'status': 'bad_delete'}, 500, 'application/json'

@socketio.on('generate_ablations')
def handle_generate_ablations(message):
    print("message is ", message)
    ablation_instructions = message['instructions']
    model_id = message['modelId']
    num_epochs = message['numEpochs']

    if generate_ablations_from_model(model_id, ablation_instructions, num_epochs=num_epochs):
        return {'status': 'ok'}, 200, 'application/json'
    else:
        return {'status': 'error'}, 500, 'application/json'

@socketio.on('generate_variations')
def handle_generate_variations(message):
    # print("message is ", message)
    variation_instructions = message['instructions']
    number_models = message['numModels'] or 5
    number_changes = message['numChanges'] or 1
    model_id = message['modelId']
    num_epochs = message['numEpochs']

    if generate_variations_from_model(model_id, number_models, variation_instructions, number_changes=number_changes, num_epochs=num_epochs):
        return {'status': 'ok'}, 200, 'application/json'
    else:
        return {'status': 'error'}, 500, 'application/json'

@socketio.on('generate_handcrafted')
def handle_generate_handcrafted(message):
    # print("message is ", message)
    handcrafted_instructions = message['instructions']
    model_id = message['modelId']
    num_epochs = message['numEpochs']
    changes = message['changes']
    print("handcrafted template is ", handcrafted_instructions)

    if generate_handcrafted_from_model(model_id, handcrafted_instructions, changes=changes, num_epochs=num_epochs):
        return {'status': 'ok'}, 200, 'application/json'
    else:
        return {'status': 'error'}, 500, 'application/json'



device = 'cuda'
# device = 'cpu'

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=80)
    # app.run(host='localhost', port=80)
    app.run(host='localhost', port=5000)
    # parser = argparse.ArgumentParser()

    # parser.add_argument("--method", default='none', help="either start_model_training or continue_model_training")
    # parser.add_argument("--model_id", default='none', help="ID of architecture to train")
    # parser.add_argument("--logfile", help="Logfile to save intermediate training info", default=LOG_FILE)
    # parser.add_argument("--cuda", help="use cuda if GPUs are available",
    #                     action="store_true")
    # parser.add_argument("--epochs", type=int, help="number of epochs each model trained", default=2)
    # args = parser.parse_args()

    # device = 'cpu'
    # if args.cuda:
    #     device = 'gpu'

    # if args.method == 'start_model_training':
    #     start_model_training(args.model_id, device=device, num_epochs=args.epochs)

    # if args.method == 'continue_model_training':
    #     continue_model_training(args.model_id, device=device, num_epochs=args.epochs)
