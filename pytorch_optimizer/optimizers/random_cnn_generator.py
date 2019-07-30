# Load pytorch
import torch
import torch.nn as nn
import torch.nn.init as init
import torchvision
import torchvision.transforms as transforms
import numpy as np
import numpy.random as random
import uuid
import copy
import re

LAYER_TRANSITIONS = {
            'Conv2D': ['Activation', 'Activation', 'Activation', 'Conv2D', 'Dropout', 'AveragePooling2D', 'Dense', 'Softmax'],
            'Dense': ['Activation', 'Activation', 'Activation', 'Dropout', 'AveragePooling2D', 'Dense', 'Softmax'],
            'AveragePooling2D': ['Conv2D', 'Conv2D', 'Dense', 'Dropout', 'AveragePooling2D', 'Activation', 'Softmax'],
            'MaxPool': ['Conv2D', 'Conv2D', 'Dense', 'Dropout', 'AveragePooling2D', 'Activation', 'Softmax'],
            'Dropout': ['AveragePooling2D', 'Conv2D', 'Conv2D', 'Dense', 'Softmax'],
            'Activation': ['AveragePooling2D', 'Conv2D', 'Conv2D', 'Conv2D', 'Dense', 'Dropout', 'Softmax'],
            'None': ['Conv2D', 'Conv2D', 'Conv2D', 'Conv2D', 'Conv2D', 'Conv2D', 'Dense', 'AveragePooling2D', 'MaxPool', 'Dropout', 'Activation', 'Softmax']




            # 'Conv2D': ['Activation'],
            # 'AveragePooling2D': ['Softmax'],
            # 'Activation': ['AveragePooling2D'],
            # 'Softmax': [],
            # 'None': ['Conv2D', 'Dense', 'MaxPool', 'Activation']
            # 'None': ['Conv2D'],
            # 'Activation': ['Conv2D', 'Softmax'],
            # 'Conv2D': ['Conv2D', 'Activation', 'Softmax']
            # 'Conv2D': ['Softmax']
            # 'None': ['Softmax']
        }

POST_FC_LAYER_TRANSITIONS = {
            'Conv2D': ['Activation', 'Activation', 'Activation', 'Conv2D', 'Dropout', 'AveragePooling2D', 'Dense', 'Softmax'],
            # 'Conv2D': ['Activation'],
            'Dense': ['Activation', 'Activation', 'Activation', 'Dropout', 'Dense', 'Softmax'],
            'AveragePooling2D': ['Dense', 'Dropout', 'Activation', 'Softmax'],
            'MaxPool': ['Dense', 'Dropout', 'Activation', 'Softmax'],
            # 'AveragePooling2D': ['Softmax'],
            'Dropout': ['Dense', 'Softmax'],
            'Activation': ['Dense', 'Dropout', 'Softmax'],
            # 'Activation': ['AveragePooling2D'],
            'Softmax': [],
            'None': ['Dense', 'Dropout', 'Activation', 'Softmax']
            # 'None': ['Conv2D', 'Dense', 'MaxPool', 'Activation']
            # 'None': ['Conv2D']
            # 'None': ['Softmax']
        }

HYPERPARAMETER_OPTIONS = {
            'kernel_size': [1, 3, 5],
            'filters': [16, 32, 64, 128],
            'pool_size': [5, 3, 2],
        #             'pool_stride': [3, 2],
            'pool_stride': [2],
            'units': [16, 64, 128, 256],
            'activation': ['tanh', 'relu', 'sigmoid'],
            'rate': [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
        }

HYPERPARAMETER_MAPPINGS = {
            'Conv2D': ['kernel_size', 'filters'],
            'Dense': ['units'],
            'Activation': ['activation'],
            'Dropout': ['rate'],
            'Softmax': [],
            'MaxPool': ['pool_size', 'pool_stride'],
            'AveragePooling2D': ['pool_size', 'pool_stride']
        }
        
def sample_uniformly(options):
    # for now, we sample uniformly from available options
    sample = random.multinomial(n=1, pvals=[(1.0 / len(options))] * len(options), size=None)
    # print("sampling uniformly, got", sample)
    return options[np.nonzero(sample)[0][0]]

def generate_ablations_from_template(input_dim, input_channels, output_dim, layers, ablation_instructions, parent_id=None):
    layers_to_change = [key for key in ablation_instructions['selectedLayers']]
    layers_to_select = [int(re.findall(r"\d", l)[0]) for l in layers_to_change]
    new_layers = copy.deepcopy(layers[:-1])
    # Need to remove the final dense layer from selectable layers
    if len(layers_to_select) == 0:
        layers_to_select = [i for i in range(len(new_layers))]

    print("ablation_instructions are ", ablation_instructions['selectedLayers'])
    print("layers_to_select are ", layers_to_select)
    # print("ablation_instructions is ", ablation_instructions)
    # print("layers_to_select is ", layers_to_select)
    nets = [None] * len(layers_to_select) 
    for idx, layernum in enumerate(layers_to_select):
        # generate the corresponding ablation
        copied_layers = copy.deepcopy(new_layers)
        layer_type = copied_layers[layernum]['type']
        del copied_layers[layernum]
        print("template is ", copied_layers)
        conv = RandomConvNet(input_dim, input_channels, output_dim, template=copied_layers, template_parent=parent_id)
        nets[idx] = {'net': conv, 'changes': ['Removed ' + layer_type + ' layer at index ' + str(layernum)], 'changeIndices': [layernum]}

    return nets

# def exact_conv_net_from_template(input_dim, input_channels, output_dim, layers, parent_id=None):

# Generating a random ablation given a model template.  First chooses number of changes to make (1, 2, 3).  
# Then, randomly chooses either
#   - One of the layers to replace
#   - One of the layers to reparameterize
#   - One of the layers to remove
#   - One of the layer transitions to augment
#  
# If replacing a layer, uses RandomConvNet's "generate next layer" from previous layer, and stitches
# things back together for next layer
# 
# If removing a layer, removes it and stitches together preceding and succeeding layer
# 
# If reparameterizing a layer, randomly chooses from hyperparameter mappings, randomly chooses a different option from list 
# (skips pool size, because currently doesn't have more than one choice)
#
# If augmenting a layer transition, same thing as replacing a layer but keeps current layer.
# 
# Then, creates a RandomConvNet with that template and returns it
TYPES_OF_CHANGES = ['replace_layer', 'reparam_layer', 'remove_layer']
def random_conv_net_from_template(input_dim, input_channels, output_dim, layers, ablation_instructions, number_changes=1, parent_id=None):
    possible_changes = [x for x in range(1, number_changes + 1)]
    num_changes = sample_uniformly(possible_changes)
    # print("num_changes is ", num_changes)
    changes = [None] * num_changes
    replaced_layer_indices = []
    layer_index_changes = []
    new_layers = copy.deepcopy(layers[:-1])

    layers_to_change = [layer_instruction for layer_instruction in ablation_instructions if layer_instruction['selected']]
    layers_to_select = [l['idx'] for l in layers_to_change]


    print("layers_to_change is ", layers_to_change)
    print("layers_to_select is ", layers_to_select)
    # Need to remove the final dense layer from selectable layers
    if len(layers_to_select) == 0:
        layers_to_select = [i for i in range(len(new_layers))]

    # Need to remove the final dense layer from selectable layers
    if len(layers_to_change) == 0:
        for i in range(len(new_layers)):
            layers_to_change.append("layer-%s-a" % i)
            layers_to_change.append("layer-%s-b" % i)

    # NOTE - NEED TO REJECT SOFTMAX as new / replace layers
    for i in range(num_changes):
        # layer_change = sample_uniformly(layers_to_change)
        # modified_layer_index = int(re.findall(r"\d", layer_change)[0])
        modified_layer_index = sample_uniformly(layers_to_select)
        modified_layer_instruction = ablation_instructions[modified_layer_index]
        print("for layer ", modified_layer_index, " using instructions ", modified_layer_instruction)
        selected_vtypes = [vtype for vtype in modified_layer_instruction['variationTypes'] if modified_layer_instruction['variationTypes'][vtype]['selected']]
        print("selected_vtypes is ", selected_vtypes)
        if modified_layer_index == len(new_layers):
            change_type = 'prepend'
        else:
            change_type = sample_uniformly(selected_vtypes)
        change_type = change_type.strip()
        print("selected change_type", change_type)
        print("change_type == 'replace'", change_type == 'replace')
        print("change_type == 'remove'", change_type == 'remove')
        print("change_type == 'reparameterize'", change_type == 'reparameterize')
        print("change_type == 'prepend'", change_type == 'prepend')

        # modified_layer_index = sample_uniformly([i in range(len(layers))])
        # modified_layer_index = sample_uniformly(layers_to_select)
        if modified_layer_index in replaced_layer_indices:
            # We don't change the same layer twice
            changes[i] = 'skipped'
            continue

        # correct for previously added or dropped indices by going through them in order
        adjusted_modified_layer_index = modified_layer_index
        for layer_change in layer_index_changes:
            change_type = layer_change['type']
            change_index = layer_change['index']
            if change_type == 'remove' and adjusted_modified_layer_index > change_index:
                adjusted_modified_layer_index = adjusted_modified_layer_index - 1
            elif change_type == 'add' and adjusted_modified_layer_index > change_index:
                adjusted_modified_layer_index = adjusted_modified_layer_index + 1

        if change_type == 'replace':
            print("replacing")
            # Special behavior if replacing first layer...
            curr_layer_type = layers[modified_layer_index]['type']
            if modified_layer_index >= 0:
                prev_layer_type = layers[modified_layer_index - 1]['type']
                next_layer = RandomConvNet.get_next_layer(input_dim, input_channels, prev_layer_type)
            else:
                prev_layer_type = 'None'
                next_layer = RandomConvNet.get_next_layer(input_dim, input_channels, prev_layer_type)

            next_layer_type = next_layer['type']
            change = ("Replaced %s at index %d with %s" % (curr_layer_type, modified_layer_index, next_layer_type))
            # print(change)
            changes[i] = change
            replaced_layer_indices.append(adjusted_modified_layer_index)
            # Need to keep record that the indices are now different then previous layer
            new_layers[adjusted_modified_layer_index] = next_layer
            # Still need to do the stitching
            
        elif change_type == 'reparameterize':
            print("reparameterizing")

            old_layer_copy = copy.deepcopy(layers[modified_layer_index])
            layer_reparam_type = old_layer_copy['type']
            hyperparameter = None
            prev_value = 0.0
            new_value = 0.0
            while (hyperparameter is None):
                hyperparameter = sample_uniformly(RandomConvNet.hyperparameter_mappings[layer_reparam_type])
                # Note, we can't get pool_stride here, it errs out because we only have one choice, so we 
                # force it to be pool_size
                if hyperparameter is 'pool_stride':
                    hyperparameter = 'pool_size'

                prev_value = old_layer_copy[hyperparameter]
                new_value = sample_uniformly( list(filter(lambda x: x!= prev_value, RandomConvNet.hyperparameter_options[hyperparameter])))

            old_layer_copy[hyperparameter] = new_value
            new_layers[adjusted_modified_layer_index] = old_layer_copy
            change = ("%s at %d from %s to %s" % (hyperparameter, modified_layer_index, prev_value, new_value))
            # print(change)
            changes[i] = change

        elif change_type == 'remove':
            print("removing")
            old_layer_copy = copy.deepcopy(layers[modified_layer_index])

            change = ("Removed %s at index %d" % (old_layer_copy['type'], modified_layer_index))
            # print(change)
            changes[i] = change
            layer_index_changes.append({'type': 'remove', 'index': adjusted_modified_layer_index})
            # Need to keep record that the indices are now different then previous layer
            del new_layers[adjusted_modified_layer_index]
            # Still need to do the stitching

        elif change_type == 'prepend':
            print("prepending")
            # Special behavior if replacing first layer...
            if modified_layer_index >= 0:
                prev_layer_type = layers[modified_layer_index - 1]['type']
                next_layer = RandomConvNet.get_next_layer(input_dim, input_channels, prev_layer_type)
            else:
                prev_layer_type = 'None'
                next_layer = RandomConvNet.get_next_layer(input_dim, input_channels, prev_layer_type)

            next_layer_type = next_layer['type']
            change = ("Added %s at index %d" % (next_layer_type, modified_layer_index))
            # print(change)
            changes[i] = change
            layer_index_changes.append({'type': 'add', 'index': adjusted_modified_layer_index})
            # Need to keep record that the indices are now different then previous layer
            new_layers.insert(adjusted_modified_layer_index, next_layer)
            # Still need to do the stitching
        else:
            print(" SOMEHOW DIDNT MATCH CHANGE_TYPE, which is ", change_type)

    # print("creating new random conv net with template", new_layers)
    # print("made changes: ", changes)
    conv = RandomConvNet(input_dim, input_channels, output_dim, template=new_layers, template_parent=parent_id)
    return conv, changes

def ablations_from_template(input_dim, input_channels, output_dim, layers, ablation_instructions, possible_changes=[1,2,3], parent_id=None):
    return None

# pytorch doesn't have a reshape layer that fits in a Sequential, so using this snippet from
# https://discuss.pytorch.org/t/equivalent-of-np-reshape-in-pytorch/144/6
class View(nn.Module):
    def __init__(self, *shape):
        super(View, self).__init__()
        self.shape = shape
    def forward(self, input):
        return input.view(*[int(s) for s in self.shape])

# A random CNN Generator.  Produces a pytorch model.
class RandomConvNet(nn.Module):
    layer_transitions = LAYER_TRANSITIONS
    post_fc_layer_transitions = POST_FC_LAYER_TRANSITIONS

    hyperparameter_options = HYPERPARAMETER_OPTIONS

    hyperparameter_mappings = HYPERPARAMETER_MAPPINGS

    def __init__(self, input_dim, input_channels, output_dim, template=None, template_parent=None, skip_template_softmax=False):
        super(RandomConvNet, self).__init__()
        # print("CREATING CONV NET WITH (input_dim, input_channels, output_dim): ", (input_dim, input_channels, output_dim))
        # print("AND TEMPLATE", template)
        self.input_dim = input_dim
        self.input_channels = input_channels
        self.output_dim = output_dim
        self.template_parent = template_parent
        self._epochs = 0
        self._post_fc_layer = False
        
        if template is not None:
            print("we are in template")
            # Need to worry about first layer being a softmax...
            self.layers = []
            if (len(template) > 0):
                prev_layer = RandomConvNet.pytorch_layers(template[0], input_dim, input_channels, post_fc_layer=self._post_fc_layer)
                self.layers.append(prev_layer)
            # need to clean it up a bit.
            for i in range(len(template)):
                print("prev_layer_type is " + prev_layer['type'] + ' and == Dense? ', prev_layer['type'] == 'Dense')
                if prev_layer['type'] == 'Dense':
                    print("setting _post_fc_layer to be True")
                    self._post_fc_layer = True
                if i == 0:
                    continue
                # we skip early softmaxs for now
                if (i != len(template) - 1 and template[i]['type'] is 'Softmax'):
                    continue

                if 'output_dim' not in prev_layer:
                    print("error: ", prev_layer)

                new_layer = RandomConvNet.pytorch_layers(template[i], prev_layer['output_dim'], prev_layer['output_channels'], post_fc_layer=self._post_fc_layer)
                if new_layer:
                    # If pytorch_layers returns false, that means we have a degenerate layer.  If that happens, we
                    # just skip the layer.
                    self.layers.append(new_layer)
                    prev_layer = new_layer
                else:
                    continue

            if not skip_template_softmax:
                # Lastly, we manually add the softmax, because we took it off before
                print("before softmax, layers is ", self.layers, " and len(template)is ", len(template))
                if len(template) > 0:
                    softmax_layer = RandomConvNet.pytorch_layers({'type': 'Softmax'}, prev_layer['output_dim'], prev_layer['output_channels'])
                else:
                    softmax_layer = RandomConvNet.pytorch_layers({'type': 'Softmax'}, input_dim, input_channels)                
                self.layers.append(softmax_layer)
                print("resulting layers are: ", self.layers)
            self.parent = template_parent
        else:
            print("we are in not template")
            self.parent = None
            # sample layers until we get a softmax.
            self.layers = []
            prev_layer = RandomConvNet.get_next_layer(input_dim, input_channels, 'None', self._post_fc_layer)
            self.layers.append(prev_layer)
            while(prev_layer['type'] != 'Softmax'):
                if prev_layer['type'] == 'Dense':
                    self._post_fc_layer = True
                prev_layer = RandomConvNet.get_next_layer(prev_layer['output_dim'], prev_layer['output_channels'], prev_layer['type'], self._post_fc_layer)
                self.layers.append(prev_layer)        

        # register the models with pytorch
        self.model = nn.Sequential(*[l for layer in self.layers for l in layer['torch_layers']])
        self.uuid = str(uuid.uuid4())

        self.initialize_weights()

    def metadata(self):
        descriptor = {}
        descriptor['id'] = self.uuid
        descriptor['_layers'] = []

        for l in self.layers:
            if l['type'] == 'Conv2D':
                descriptor['_layers'].append({
                    'type': 'Conv2D',
                    'strides': '1',
                    'kernel_size': int(l['kernel_size']),
                    'filters': int(l['filters'])
                    })
            elif l['type'] == 'Dense':
                descriptor['_layers'].append({
                    'type': 'Dense',
                    'units': int(l['units'])
                    })
            elif l['type'] == 'AveragePooling2D':
                descriptor['_layers'].append({
                    'type': 'AveragePooling2D',
                    'pool_size': int(l['pool_size'])
                    })
            elif l['type'] == 'MaxPool':
                descriptor['_layers'].append({
                    'type': 'MaxPool',
                    'pool_size': int(l['pool_size'])
                    })
            elif l['type'] == 'Activation':
                descriptor['_layers'].append({
                    'type': 'Activation',
                    'activation': l['activation']
                    })
            elif l['type'] == 'Dropout':
                descriptor['_layers'].append({
                    'type': 'Dropout',
                    'rate': float(l['rate'])
                    })
            elif l['type'] == 'Softmax':
                descriptor['_layers'].append({
                    'type': 'Dense',
                    'units': self.output_dim
                    })

        descriptor['trainedEpochs'] = self._epochs
        return descriptor

    @classmethod
    def get_next_layer(self, input_dim, input_channels, layer_type, post_fc_layer=False):
        layer_hyperparameters = self.sample_layer_hyperparameters(layer_type, post_fc_layer)
        print("in get_next_layer, layer_type is ", layer_type, " and post_fc_layer is ", post_fc_layer)
        next_layer = self.pytorch_layers(layer_hyperparameters, input_dim, input_channels, post_fc_layer=post_fc_layer)
        if next_layer:
            return next_layer
        else:
            # had some error getting next layer, like it didn't fit, so we start over
            return self.get_next_layer(input_dim, input_channels, layer_type)

    @classmethod
    def pytorch_layers(self, l, input_dim, input_channels, output_dim=10, post_fc_layer=False):
        l['torch_layers'] = []
        l['input_dim'] = input_dim
        l['input_channels'] = input_channels
        if l['type'] == 'Conv2D':
            # we might have to skip if kernel is too big
            if (np.sqrt(input_dim) - int(l['kernel_size']) > 0):
                print("filters is ", l['filters'], ' and post_fc_layer is ', post_fc_layer)
                if post_fc_layer:
                    l['torch_layers'].append(View(-1, 1, int(np.sqrt(l['input_dim'])), int(np.sqrt(l['input_dim']))))
                l['torch_layers'].append(nn.Conv2d(input_channels, int(l['filters']), int(l['kernel_size'])))
                new_width = (np.sqrt(input_dim) - (int(l['kernel_size']) - 1))
                # Add batch norm for conv layers
                # l['torch_layers'].append(nn.BatchNorm2d(l['filters']))
                l['output_dim'] = new_width * new_width
                l['output_channels'] = int(l['filters'])
            else:
                # We skip this layer
                return False
        elif l['type'] == 'Dense':
            # do we need a reshape?  probably
            # store the original shape, and calculate the flattened shape.  
            # for now, we keep it square, and force it to be a single channel.
            newDim = input_dim * input_channels
            l['torch_layers'].append(View(-1, int(newDim)))
            l['torch_layers'].append(nn.Linear(int(newDim), int(l['units'])))
            # Add batch norm to FC layers
            # l['torch_layers'].append(nn.BatchNorm1d(l['units']))
            # l['torch_layers'].append(View(-1, 1, int(np.sqrt(l['units'])), int(np.sqrt(l['units']))))
            l['torch_layers'].append(View(-1, l['units']))
            l['output_dim'] = int(l['units'])
            l['output_channels'] = 1
        elif l['type'] == 'MaxPool':
            if 'pool_stride' not in l:
                l['pool_stride'] = 2
            # we might have to skip if kernel is too big
            if (np.sqrt(input_dim) - int(l['pool_size']) > 0):
                # we might have to pad because of the stride / kernel size
                if post_fc_layer:
                    l['torch_layers'].append(View(-1, 1, int(np.sqrt(l['input_dim'])), int(np.sqrt(l['input_dim']))))
                l['torch_layers'].append(nn.MaxPool2d(int(l['pool_size']), int(l['pool_stride'])))
                new_width = np.floor((np.sqrt(input_dim) - int(l['pool_size']))/int(l['pool_stride'])) + 1
                l['output_dim'] = int(new_width * new_width)
                # output_channels stays the same
                l['output_channels'] = int(l['input_channels'])
            else:
                # We skip this layer
                return False
        elif l['type'] == 'AveragePooling2D':
            if 'pool_stride' not in l:
                l['pool_stride'] = 2
            # we might have to skip if kernel is too big
            if (np.sqrt(input_dim) - int(l['pool_size']) > 0):
                # we might have to pad because of the stride / kernel size
                if post_fc_layer:
                    l['torch_layers'].append(View(-1, 1, int(np.sqrt(l['input_dim'])), int(np.sqrt(l['input_dim']))))
                l['torch_layers'].append(nn.AvgPool2d(int(l['pool_size']), int(l['pool_stride'])))
                new_width = np.floor((np.sqrt(input_dim) - int(l['pool_size']))/int(l['pool_stride'])) + 1
                l['output_dim'] = int(new_width * new_width)
                # output_channels stays the same
                l['output_channels'] = int(l['input_channels'])
            else:
                # We skip this layer
                return False
        elif l['type'] == 'Activation':
            if l['activation'] == 'relu':
                l['torch_layers'].append(nn.ReLU())
            elif l['activation'] == 'tanh':
                l['torch_layers'].append(nn.Tanh())
            elif l['activation'] == 'sigmoid':
                l['torch_layers'].append(nn.Sigmoid())

            l['output_channels'] = int(l['input_channels'])
            l['output_dim'] = int(l['input_dim'])
        elif l['type'] == 'Dropout':
            l['torch_layers'].append(nn.Dropout(l['rate']))
            l['output_channels'] = int(l['input_channels'])
            l['output_dim'] = int(l['input_dim'])
        elif l['type'] == 'Softmax':
            # this is the last layer, so we need to reshape and use a Linear layer to cast to the 
            # network's output dimesion (like for CIFAR 10, need an FC layer to go to 10 dimensions)
            # Otherwise, the network's output is undefined.
            newDim = input_dim * input_channels
            l['torch_layers'].append(View(-1, int(newDim)))
            l['torch_layers'].append(nn.Linear(int(newDim), output_dim))
            if (torch.__version__ < '0.3'):
                l['torch_layers'].append(nn.Softmax())
            else:
                l['torch_layers'].append(nn.Softmax(dim=-1))
            
            l['output_channels'] = 1
            l['output_dim'] = output_dim
            
        return l
    
    @classmethod
    def sample_layer_hyperparameters(self,input_layer_type, post_fc_layer):
        if post_fc_layer:
            next_layer = sample_uniformly(self.post_fc_layer_transitions[input_layer_type])
        else:
            next_layer = sample_uniformly(self.layer_transitions[input_layer_type])
        if next_layer:
            l = {'type': next_layer}
            for hyperparameter in self.hyperparameter_mappings[next_layer]:
                l[hyperparameter] = sample_uniformly(self.hyperparameter_options[hyperparameter])

            return l
        else:
            return None

    def initialize_weights(self):
        self.apply(self.weights_init)

    def weights_init(self, m):
        classname = m.__class__.__name__
        if classname.find('Conv2D') != -1 or classname.find('Linear') != -1:
            if torch.__version__ < '0.3':
                # init.xavier_normal_(m.weight.data)
                init.xavier_normal_(m.weight)
            else:
                # init.xavier_normal(m.weight.data)
                init.xavier_normal(m.weight)

            if (torch.__version__ < '0.3'):
                m.bias.data.fill(0)
            else:
                m.bias.data.fill_(0)
                                          
    def forward(self, x):
        return self.model(x)
