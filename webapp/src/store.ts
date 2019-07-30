import Vue from 'vue';
import Vuex from 'vuex';
import * as math from 'mathjs';
import * as numeral from 'numeral';
import * as strftime from 'strftime';
import ColorManager from '@/vis/ColorManager';
import SocketData from '@/util/SocketData';
import { TableDatum } from '@/util/LogDataInterface';
import { __values } from 'tslib';
Vue.use(Vuex);

const cm = new ColorManager();
const sd = new SocketData();

const store = new Vuex.Store({
    state: {
        models: [] as TableDatum[],
        modelArchitectures: {},
        colorManager: cm,
        socketData: sd,
        maxWidth: 1,
        resolution: 'small',
        fixedWidth: false,
        logBase: 0.15,
        selectedModelIdsMappings: {},
        selectedModelIds: [] as string[],
        drawerFilters: {},
        mousedOverModelId: 'NONE',
        clickedModelId: 'NONE',
        datasetLabels: [
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
        ],
        sortByAccessors: {
            'Created At': (m) => +new Date(m.timestamp),
            'Val Acc': (m) => m.val_acc,
            'Num Params': (m) => math.log(m.calcParams),
            'Num Epochs': (m) => m.epochs,
            'Forward Time(s)': (m) => m.forwardTime,
            'Backward Time(s)': (m) => m.backwardTime,
            'Val Acc / log(Params)': (m) =>
                m.val_acc && m.calcParams ? m.val_acc / math.log(m.calcParams, 10) : 0.0,
            'Val Acc / log(Fwd)': (m) =>
                m.val_acc && m.forwardTime ? m.val_acc / math.log(m.forwardTime, 10) : 0.0,
            'Val Acc / log(Back)': (m) =>
                m.val_acc && m.backwardTime ? m.val_acc / math.log(m.backwardTime, 10) : 0.0
        },
        descSortByAccessors: {
            'Created At': (m) => +new Date(m.timestamp),
            'Val Acc': (m) => (-1.0) * m.val_acc,
            'Num Params': (m) => m.parameters,
            'Num Epochs': (m) => -1.0 * m.epochs,
            'Forward Time(s)': (m) => m.forwardTime,
            'Backward Time(s)': (m) => m.backwardTime,
            'Val Acc / log(Params)': (m) =>
                m.valAcc && m.calcParams ? (-1.0) * m.valAcc / math.log(m.calcParams, 10) : 0.0,
            'Val Acc / log(Fwd)': (m) =>
                m.valAcc && m.forwardTime ? (-1.0) * m.valAcc / math.log(m.forwardTime, 10) : 0.0,
            'Val Acc / log(Back)': (m) =>
                m.valAcc && m.backwardTime ? (-1.0) * m.valAcc / math.log(m.backwardTime, 10) : 0.0
        },
        valueAccessors: {
            'Created At': (m) => strftime('%H:%M', new Date(m.timestamp)),
            'Validation Accuracy': (m) => {
                let accNum = m.val_acc;
                if (m.val_accs && m.val_accs.length > 0) {
                    accNum = m.val_accs[m.val_accs.length-1];
                }
                return numeral(accNum).format('.00');
            },
            'Training Accuracy': (m) => {
                let accNum = m.train_acc;
                if (m.train_accs && m.train_accs.length > 0) {
                    accNum = m.train_accs[m.train_accs.length-1];
                }
                return numeral(accNum).format('.00');
            },
            'Val Acc': (m) => {
                let accNum = m.val_acc;
                if (m.val_accs && m.val_accs.length > 0) {
                    accNum = m.val_accs[m.val_accs.length-1];
                }
                return numeral(accNum).format('.00');
            },
            'Train Acc': (m) => {
                let accNum = m.train_acc;
                if (m.train_accs && m.train_accs.length > 0) {
                    accNum = m.train_accs[m.train_accs.length-1];
                }
                return numeral(accNum).format('.00');
            },
            // 'Training Accuracy': (m) => numeral(m.trainAcc).format('.00'),
            'Num Params': (m) => numeral(m.parameters).format('0.0a'),
            'Num Epochs': (m) => {
                let epochNum = m.epochs;
                if (m.train_accs && m.train_accs.length > 0) {
                    epochNum = m.train_accs.length;
                }
                return epochNum;
            },
            'Forward Time(s)': (m) => numeral(m.forwardTime / 1000.0).format('0.0'),
            'Backward Time(s)': (m) => numeral(m.backwardTime).format('0.0'),
            'Val Acc / log(Params)': (m) =>
                m.val_acc && m.calcParams ? numeral(m.val_acc / math.log(m.calcParams, 10)).format('0.00') :  0.0,
            'Val Acc / log(Fwd)': (m) =>
                m.val_acc && m.forwardTime ? numeral(m.val_acc / math.log(m.forwardTime, 10)).format('0.00') :  0.0,
            'Val Acc / log(Back)': (m) =>
                m.val_acc && m.backwardTime ? numeral(m.val_acc / math.log(m.backwardTime, 10)).format('0.00') :  0.0
        },
        fullInspectionOptions: [
            'Validation Accuracy',
            'Training Accuracy',
            'Num Epochs',
            'Num Params',
            // 'Forward Time(s)',
            // 'Backward Time(s)',
            'Val Acc / log(Params)',
            // 'Val Acc / log(Fwd)',
            // 'Val Acc / log(Back)'
        ],
        parentInspectionOptions: [
            'Val Acc',
            'Num Params'
        ],
        sortByOptions: [
            'Val Acc',
            'Train Acc',
            'Num Params',
            'Num Epochs'
        ],
        projectionType: 'hendrik',
        perfData: [],
        groundtruthLabels: [],
        imageClassMappings: {},
        isLabelSelected: [],
        isLabelHighlighted: [],
        imageClassHighlighted: null,
        imageClassSelected: null,
        imageClassNameHighlighted: null,
        imageClassNameSelected: null,
        imageIndexHighlighted: null,
        imageIndexSelected: null,
        modelTreeChildren: {},
        modelTreeChildrenAblationLayers: {},
        recentModelIds: [],
        variationOptions: {},
        ablationOptions: {},
        queuedModelIds: [],
        layerOptions: {
            'Conv2D': ['kernel_size', 'filters'],
            'Dense': ['units'],
            'Activation': ['activation'],
            'Dropout': ['rate'],
            'Softmax': [],
            'MaxPool': ['pool_size', 'pool_stride'],
            'AveragePooling2D': ['pool_size', 'pool_stride']
        },
        hyperparameterOptions: {
            'kernel_size': [1, 3, 5],
            'filters': [16, 32, 64, 128],
            'pool_size': [5, 3, 2],
            'pool_stride': [2],
            'units': [16, 64, 256],
            'activation': ['tanh', 'relu', 'sigmoid'],
            'rate': [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
        },
        layerTransitionOptions: {
            'Conv2D': ['Activation', 'Conv2D', 'Dropout', 'MaxPool', 'Dense'],
            'Dense': ['Activation', 'Conv2D', 'Dropout', 'MaxPool', 'Dense'],
            'MaxPool': ['Conv2D', 'Dense', 'Dropout', 'MaxPool', 'Activation'],
            'AveragePooling2D': ['Conv2D', 'Dense', 'Dropout', 'MaxPool', 'Activation'],
            'Dropout': ['MaxPool', 'Conv2D', 'Dense'],
            'Activation': ['MaxPool', 'Conv2D', 'Dense', 'Dropout'],
            'Softmax': [],
            'None': ['Conv2D', 'Dense', 'MaxPool', 'Dropout', 'Activation']
        }
    },
    mutations: {
        ADD_QUEUED_MODEL_ID(state: any, modelId: string) {
            state.queuedModelIds.push(modelId);
        },
        SWITCH_QUEUED_MODEL_ORDER(state: any, orderInfo) {
            const startId = orderInfo.startId;
            const endId = orderInfo.endId;

            // First, find correct indices;
            const startIndex = state.queuedModelIds.indexOf(startId);
            const endIndex = state.queuedModelIds.indexOf(endId);

            // Then, switch them
            let newModelList = state.queuedModelIds.slice();
            newModelList[startIndex] = endId;
            newModelList[endIndex] = startId;

            state.queuedModelIds = newModelList;
        },
        SWITCH_QUEUED_CHILDREN_MODEL_ORDER(state: any, orderInfo) {
            const startId = orderInfo.startId;
            const endId = orderInfo.endId;
            const parentId = orderInfo.parentId;

            // First, find correct indices;
            let startIndex = state.queuedModelIds.indexOf(startId);
            let endIndex = state.queuedModelIds.indexOf(endId);

            // Then, switch them
            let newModelList = state.queuedModelIds.slice();
            newModelList[startIndex] = endId;
            newModelList[endIndex] = startId;

            state.queuedModelIds = newModelList;

            // Then, do it for the children list
            startIndex = state.modelTreeChildren[parentId].indexOf(startId);
            endIndex = state.modelTreeChildren[parentId].indexOf(endId);

            newModelList = state.modelTreeChildren[parentId].slice();
            newModelList[startIndex] = endId;
            newModelList[endIndex] = startId;

            Vue.set(state.modelTreeChildren, parentId, newModelList);
        },
        REORDER_QUEUED_MODEL_IDS(state: any, modelIds: string[]) {
            let newTrainingOrder = modelIds.filter((mId) => state.modelArchitectures[mId].trainingStatus === 'not_started');

            var v = new Vue();
        
            // @ts-ignore
            v.$socket.emit('reorder_queued_model', {
                modelIdOrderedList: newTrainingOrder
            }, (response, code, mime) => {
                if (Number.parseInt(code) === 200) {
                    // this.queuedModelIds.splice(newIndex, 0, modelId);
                    console.log("changing queuedModelIds: ", modelIds)
                    state.queuedModelIds = modelIds;
                }
            })
    
        },
        DELETE_QUEUED_MODEL(state: any, modelId: string) {
            var v = new Vue();
            const index = state.queuedModelIds.indexOf(modelId);
        
            v.$socket.emit('kill_queued_model', {
                modelId: modelId
            }, (response, code, mime) => {
                if (Number.parseInt(code) === 200) {
                    state.queuedModelIds.splice(index, 1);
                    // Remove it from the list of children of the parent
                    const model = state.modelArchitectures[modelId];
                    let family = state.modelTreeChildren[model.parentId];
                    family = family.filter((mId) => mId !== modelId);
                    console.log("state.modelTreeChildren was this before: ", state.modelTreeChildren)
                    Vue.set(state.modelTreeChildren, model.parentId, family);
                    console.log("state.modelTreeChildren was this after: ", state.modelTreeChildren)
                    Vue.set(state.modelArchitectures, modelId, null);
                    window['searchableModels'][modelId] = null;
                }
            })

            
        },
        ADD_CHILD_TO_MODEL(state: any, relationship: any) {
            console.log("called ADD_CHILD_TO_MODEL with relationship ", relationship)
            const parent = relationship.parent;
            const child = relationship.child;
            const ablationLayer = relationship.ablationLayer;
            let children = state.modelTreeChildren[parent] || []
            let childrenAblationLayers = state.modelTreeChildrenAblationLayers[parent] ||     []
            children.push(child);
            if (typeof ablationLayer === 'number') {
                childrenAblationLayers[ablationLayer] = child;
                Vue.set(state.modelTreeChildrenAblationLayers, parent, childrenAblationLayers);
            }
            
            Vue.set(state.modelTreeChildren, parent, children);
        },
        ADD_RECENT_MODEL_ID(state: any, modelId: string) {
            // state.recentModelIds.push(modelId);
        },
        SET_VARIATION_OPTIONS(state: any, variationData: any) {
            const modelId = variationData['modelId'];
            const variationOpts = variationData['variationOpts'];
            Vue.set(state.variationOptions, modelId, variationOpts);
        },
        SET_ABLATION_OPTIONS(state: any, ablation_data: any) {
            const modelId = ablation_data['modelId'];
            const ablationOpts = ablation_data['ablationOptions'];
            Vue.set(state.ablationOptions, modelId, ablationOpts);
        },
        LOAD_GROUNDTRUTH_LABELS(state: any, labels: number[]) {
            state.groundtruthLabels = labels;
        },
        SELECT_LABEL(state: any, label_name: string) {
            let isLabelSelected = [];
            for (let i = 0; i < state.isLabelSelected.length; i++) {
                isLabelSelected[i] = false;
            }
            state.isLabelSelected = isLabelSelected;
            state.imageClassSelected = state.datasetLabels.indexOf(label_name);
            state.imageClassNameSelected = label_name;
        },
        DESELECT_LABEL(state: any) {
            let isLabelSelected = [];
            for (let i = 0; i < state.isLabelSelected.length; i++) {
                isLabelSelected[i] = false;
            }
            state.isLabelSelected = isLabelSelected;
            state.imageClassSelected = null;
            state.imageClassNameSelected = null;
        },
        HIGHLIGHT_LABEL(state: any, label_name: string) {
            let isLabelHighlighted = [];
            for (let i = 0; i < state.isLabelHighlighted.length; i++) {
                isLabelHighlighted[i] = false;
            }
            state.isLabelHighlighted = isLabelHighlighted;
            state.imageClassHighlighted = state.datasetLabels.indexOf(label_name);
            state.imageClassNameHighlighted = label_name;
        },
        DEHIGHLIGHT_LABEL(state: any) {
            let isLabelHighlighted = [];
            for (let i = 0; i < state.isLabelHighlighted.length; i++) {
                isLabelHighlighted[i] = false;
            }
            state.isLabelHighlighted = isLabelHighlighted;
            state.imageClassHighlighted = null;
            state.imageClassNameHighlighted = null;
        },
        SELECT_IMAGE(state: any, imageIdx: number) {
            state.imageIndexSelected = imageIdx;
        },
        DESELECT_IMAGE(state: any) {
            state.imageIndexSelected = null;
        },
        HIGHLIGHT_IMAGE(state: any, imageIdx: number) {
            state.imageIndexHighlighted = imageIdx;
        },
        DEHIGHLIGHT_IMAGE(state: any) {
            state.imageIndexHighlighted = null;
        },
        ADD_PERF_DATA(state: any, perfData: any[]) {
            state.perfData = perfData;
        },
        LOAD_MODEL_DATA(state: any, modelData: any[]) {
            sd.addData(modelData);
            state.models = sd.getTableData('');
        },
        LOAD_ARCHITECTURE_DATA(state: any, modelData: any[]) {
            modelData.forEach((m) => {
                Vue.set(state.modelArchitectures, m.id, m);
            });
        },
        CHANGE_PROJECTION_TYPE(state: any, projectionType: string) {
            state.projectionType = projectionType;
        },
        ADD_SELECTED_MODEL_ID(state: any, modelId: string) {
            if (!state.selectedModelIdsMappings[modelId]) {
                state.selectedModelIds.push(modelId);
                Vue.set(state.selectedModelIdsMappings, modelId, true);
            }
        },
        REMOVE_SELECTED_MODEL_ID(state: any, modelId: string) {
            if (state.selectedModelIdsMappings[modelId]) {
                const modelIndex = state.selectedModelIds.indexOf(modelId);
                state.selectedModelIds.splice(modelIndex, 1);
                delete state.selectedModelIdsMappings[modelId];
            }

            if (state.clickedModel === modelId) {
                state.clickedModel = 'NONE';
            }

            if (state.mousedOverModelId === modelId) {
                state.mousedOverModelId = 'NONE';
            }
        },
        CLEAR_SELECTED_MODELS(state: any) {
            state.selectedModelIds = [];
            state.selectedModelIdsMappings = {};
        },
        // possibly doesn't trigger an update
        ADD_DRAWER_FILTER(state: any, filter) { Object.assign(state.drawerFilters, filter); },
        REMOVE_DRAWER_FILTER(state: any, filterName) { delete state.drawerFilters[filterName]; },
        SET_MAX_WIDTH(state: any, width: number) { state.maxWidth = width; },
        SET_LOG_BASE(state: any, newBase: number) { state.logBase = newBase; },
        SET_CHIP_RESOLUTION(state: any, res: string) { state.resolution = res; },
        SET_FIXED_WIDTH(state: any, fixed: boolean) { state.fixedWidth = fixed; },
        SET_MOUSED_OVER_MODEL(state: any, modelId: string) { state.mousedOverModelId = modelId; },
        SET_CLICKED_MODEL(state: any, modelId: string) {state.clickedModel = modelId; },
        // SET_INSPECTED_MODEL(state: any, modelId: string) {state.inspectedModel = modelId; },

        // Socket stuff
        SOCKET_UPDATEMODELSTATUS(state: any, data: any) {
            console.log("GOT UPDATED MODEL STATUS, Status was ", data);
        },

        SOCKET_connect(state: any, data: any) {
            console.log("SOCKET WAS CONNECTED ???")
        }
    },
    actions: {

    },
    getters: {
        mostRecentModelIds(state: any) {
            return state.recentModelIds.slice(-5);
        },
        inspectedModel(state: any) {
            if (state.mousedOverModelId !== 'NONE') {
                return state.mousedOverModelId;
            } else {
                return state.clickedModel;
            }
        }
    }
});

export default store;
