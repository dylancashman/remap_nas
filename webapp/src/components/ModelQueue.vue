<template>
    <div class='model-queue-component'>
            <v-data-table
                :headers="mini ? miniHeaders : headers"
                :items="queuedModels"
                :loading="anyModelsLoading"
                disable-initial-sort
                class="elevation-1"
                no-results-text="No models currently being trained."
                hide-actions
                ref="sortableTable"
                >
                <template slot='items' slot-scope='props'>
                    <tr 
                        :class="calculateQueueRowClass(props.item)" :key="props.item.id + 'IDX' + props.index"
                        @click="addRowToDrawer(props.item.id)"
                        @mouseover="addRowToMouseover(props.item.id)"
                        @mouseout="removeRowFromMouseover(props.item.id)"
                        >
                        <td>
                            <network-chip
                                :layersData="dupedModel(props.item)"
                                :orientation="'left'"
                                :resolution="resolution"
                                :fixedWidth="fixedWidth"
                                :showPlates="false"
                                :maxSize="maxSize"
                                :logBase="logBase" />
                        </td>
                        <td
                            @click.stop="addRowToDrawer(props.item.parentId)"
                            @mouseover="addRowToMouseover(props.item.parentId)"
                            @mouseout="removeRowFromMouseover(props.item.parentId)"
                            v-if="!mini"
                        >
                            <network-chip
                                :layersData="parentModelFor(props.item)"
                                :orientation="'left'"
                                :resolution="resolution"
                                :fixedWidth="fixedWidth"
                                :showPlates="false"
                                :maxSize="maxSize"
                                :logBase="logBase"
                                v-if="parentModelFor(props.item)" />
                        </td>
                        <td>{{props.item.parentType}}</td>
                        <td class='align-left'>{{ props.item.changes && props.item.changes.join('. ')}}</td>
                        <td class='align-right'>{{ props.item.parameters && numeral(props.item.parameters).format('0.0a') }}</td>
                        <td class='align-right' v-if='mini' :class="paramChangeClass(props.item)">{{ paramChangeString(props.item) }}</td>
                        <td>{{ props.item.val_acc && props.item.val_acc[props.item.val_acc.length-1] && props.item.val_acc[props.item.val_acc.length-1].toPrecision(2) }}</td>
                        <td v-if='mini' :class="valAccChangeClass(props.item)">{{ valAccChangeString(props.item) }}</td>
                        <td>            
                            {{ props.item.estimatedTraining }}
                        </td>
                        <td>
                            <trend
                                :data="props.item.loss"
                                :gradient="['black']"
                                :height="50"
                                v-if="trendLineReady(props.item)">
                            </trend>
                            <!-- <trend
                                :data="[10, 9, 9, 8, 8,7,7,7,7,7]"
                                :gradient="['black']"
                                :height="50"
                                smooth>
                            </trend> -->
                        </td>
                        <td class="justify-center layout px-0">
                            <v-progress-circular 
                                color="black" 
                                indeterminate 
                                v-if="rowCurrentlyTraining(props.item)"
                                size="16"
                            ></v-progress-circular>
                            <v-btn style="cursor: move" icon class="sortHandle" v-if="!mini && rowToTrain(props.item)"><v-icon>drag_handle</v-icon></v-btn>
                            <v-icon
                                small
                            >
                                {{calculateRowIcon(props.item)}}
                            </v-icon>
                            <v-icon
                                small
                                @click.stop="deleteItem(props.item)"
                                v-if="rowToTrain(props.item)"
                            >
                                cancel
                            </v-icon>
                        </td>
                    </tr>
                </template>
            </v-data-table>
            <!-- <v-btn color="info" @click="generateRandomModel">Generate Random Model</v-btn> -->
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as axios from 'axios';
import * as Sortable from 'sortablejs';
import NetworkChip from './NetworkChip.vue';
import * as numeral from 'numeral';

// export interface QueuedModel {
//     layersData: any[];
//     params: number;
//     estimated_training: number;
//     recency: number;
//     isTraining: false;
// }

@Component({
    components: {
        NetworkChip
    }
})
export default class ModelQueue extends Vue {

    private numeral = numeral;
    // public queuedModelData = {};
    private headers = [
        { text: 'Model', align: 'left', sortable: false, value: 'layers', width: '15%' },
        { text: 'Parent', align: 'left', sortable: false, value: 'parentId', width: '15%' },
        { text: 'Parent Type', align: 'left', sortable: false, value: 'parentType', width: '5%' },
        { text: 'Changes', align: 'center', sortable: false, value: 'changes', width: '15%' },
        { text: 'Params', value: 'params', sortable: false, width: '5%', align: 'left' },
        { text: 'Acc', value: 'final_val_acc', sortable: false, width: '5%', align: 'left' },
        { text: 'Est. Training', value: 'est_training_time', sortable: false, width: '5%', align: 'left' },
        { text: 'Loss', value: 'losses', sortable: false, width: '25%', align: 'right' },
        { text: '', value: 'params', sortable: false, width: '10%', align: 'right' }
    ]

    private miniHeaders = [
        { text: 'Model', align: 'left', sortable: false, value: 'layers', width: '15%' },
        { text: 'Type', align: 'left', sortable: false, value: 'parentType', width: '5%' },
        { text: 'Changes', align: 'left', sortable: false, value: 'changes', width: '15%' },
        { text: 'Params', value: 'params', sortable: false, width: '5%', align: 'left' },
        { text: 'Delta', value: 'params', sortable: false, width: '5%', align: 'left' },
        { text: 'Acc', value: 'final_val_acc', sortable: false, width: '5%', align: 'left' },
        { text: 'Delta', value: 'final_val_acc', sortable: false, width: '5%', align: 'left' },
        { text: 'Est. Training', value: 'est_training_time', sortable: false, width: '5%', align: 'left' },
        { text: 'Loss', value: 'losses', sortable: false, width: '25%', align: 'right' },
        { text: '', value: 'params', sortable: false, width: '10%', align: 'right' }
    ]

    public initialDataSize = 3.0 * 32.0 * 32.0; // CIFAR 10
    public initialDataWidth = 32.0;
    public initialDataHeight = 32.0;
    public initialDataDepth = 3.0;

    @Prop({default: false})
    public mini: boolean;

    get queuedModels() {
        // return this.queuedModelIds.map((id) => this.queuedModelData[id]);
        return this.queuedModelIds.map((id) => this.$store.state.modelArchitectures[id]);
    }

    get childIds() {
        return this.$store.state.modelTreeChildren[this.inspectedModelId] || [];
    }
    
    get inspectedModelId() {
        return this.$store.getters.inspectedModel;
    }

    get inspectedModelData() {
        if (window['searchableModels'][this.inspectedModelId]) {
            return this.dupedModel(window['searchableModels'][this.inspectedModelId]);
        } else {
            return null;
        }
    }

    get queuedModelIds() {
        if (this.mini) {
            return this.childIds;
        } else {
            return this.$store.state.queuedModelIds;
        }
    }

    get anyModelsLoading() {
        return this.queuedModels.some((m) => m['trainingStatus'] === 'in_progress');
    }

    get resolution() { return 'small'; }
    get fixedWidth() { return this.$store.state.fixedWidth; }
    get maxSize() { return this.$store.state.maxWidth; }
    get logBase() { return this.$store.state.logBase; }

    constructor() {
        super();
// @ts-ignore

        this.$options.sockets = {
            connect(){
                console.log('connect was called');        
            },
            disconnect(){
                console.log('disconnect was called');
            },
            updateModelStatus(data) {
                if (!this.mini) {
                    // if ( this.queuedModelData[data['id']] ) {
                    if ( this.$store.state.modelArchitectures[data['id']] ) {
                        // We have the model in there, we update
                        // let newModelData = this.queuedModelData[data['id']];
                        let newModelData = this.$store.state.modelArchitectures[data['id']];
                        if (data['values']) {

                            Object.keys(data['values']).forEach((key) => {
                                if (key === 'backward_time' || key === 'forward_time' || key === 'epochs') {
                                    newModelData[key] = data['values'][key]
                                } else if (newModelData[key]) {
                                    newModelData[key].push(data['values'][key]);
                                } else {
                                    newModelData[key] = [data['values'][key]];
                                }
                            })
                        }
                        if (data['hamming_embedding']) {
                            console.log("got the following embeddings ", data)
                            newModelData['projections'] = {};
                            newModelData['projections']['mds_hamming'] = {}
                            newModelData['projections']['mds_hamming']['x'] = data['hamming_embedding'][0][0]
                            newModelData['projections']['mds_hamming']['y'] = data['hamming_embedding'][1][0]
                            newModelData['projections']['mds_otmann'] = {}
                            newModelData['projections']['mds_otmann']['x'] = data['otmann_embedding'][0][0]
                            newModelData['projections']['mds_otmann']['y'] = data['otmann_embedding'][1][0]
                            newModelData['projections']['hendrik'] = {}
                            newModelData['projections']['hendrik']['x'] = newModelData['val_acc'][newModelData['val_acc'].length-1]
                            newModelData['projections']['hendrik']['y'] = newModelData['parameters']
                            this.$store.commit('ADD_RECENT_MODEL_ID', data['id']);
                        }
                        if (data['confusion_matrix']) {
                            // We don't want all the data reactive, so we make a copy and remove the confusion matrices
                            newModelData['confusion_matrix'] = data['confusion_matrix']
                        }
                        if (data['class_accuracies']) {
                            newModelData['class_accuracies'] = data['class_accuracies']
                        }
                        if (data['trainingStatus']) {
                            newModelData.trainingStatus = data['trainingStatus'];
                        }
                        if (data['epochs']) {
                            newModelData.epochs = data['epochs'];
                        }

                        Object.freeze(newModelData);
                        window['searchableModels'][newModelData.id] = newModelData;
                        let newM = this.dupedModel(newModelData);
                        delete newM.confusion_matrix;
                        // Vue.set(this.queuedModelData, data['id'], newM);
                        this.$store.commit('LOAD_ARCHITECTURE_DATA', [newM]);
                    } else {
                        let newModelData = {
                            layers: data['metadata'] ? data['metadata']['_layers'] : [],
                            id: data['id'],
                            trainedEpochs: data['metadata'] ? data['metadata']['trainedEpochs'] : 0,
                            parameters: data['parameters'],
                            estimatedTraining: this.calcEstimatedTraining(data),
                            trainingStatus: data['trainingStatus'],
                            losses: [],
                            calcParams: 0,
                            maxTensorSize: 0,
                            parentId: data['parentId'],
                            parentType: data['parentType'],
                            changes: data['changes'],
                            changeIndices: data['changeIndices']
                        };

                        // We calculate the layer sizes
                        let prevLayer = {};
                        let nparams = 0;
                        let maxTensorSize = 0;
                        for (let j = 0; j < newModelData.layers.length; j++) {
                            const layers: any = this.calculateLayerSize(newModelData.layers[j], prevLayer,
                                                                        this.initialDataSize, this.initialDataWidth,
                                                                        this.initialDataHeight, this.initialDataDepth,
                                                                        nparams);
                            newModelData.layers[j].tensorSize = layers.tensorSize;
                            newModelData.layers[j].tensorWidth = layers.tensorWidth;
                            newModelData.layers[j].tensorHeight = layers.tensorHeight;
                            newModelData.layers[j].tensorDepth = layers.tensorDepth;
                            if (layers.tensorSize > maxTensorSize) {
                                maxTensorSize = layers.tensorSize;
                            }
                            nparams = layers.nparams;
                            prevLayer = newModelData.layers[j];
                        }
                        newModelData.calcParams = nparams;
                        newModelData.maxTensorSize = maxTensorSize;

                        this.$store.commit('LOAD_ARCHITECTURE_DATA', [newModelData]);
                        this.$store.commit('ADD_CHILD_TO_MODEL', { parent: newModelData.parentId, child: newModelData.id, ablationLayer: data['changeIndices'] && data['changeIndices'][0]})
                        Object.freeze(newModelData);
                        window['searchableModels'][newModelData.id] = newModelData;

                        // Vue.set(this.queuedModelData, data['id'], newModelData);
                        this.$store.commit('ADD_QUEUED_MODEL_ID', data['id']);
                    }
                    // console.log("IN UPDATE MODEL STATUS GADFASDFRAWERAWER", data)
                    // console.log("this.queuedModelData is ", this.queuedModelData)
                    // console.log("data['id'] is ", data['id'])
                    // console.log("newModelData is ", newModelData)
                    // console.log("this.queuedModelData[data['id']] is ", this.queuedModelData[data['id']])
                }
            }
        }

    }

    public valAccChangeString(modelData) {
        if (modelData && this.inspectedModelData) {
            const valAcc = modelData.val_accs && modelData.val_accs[modelData.val_accs.length-1] || modelData.val_acc;
            const parentValAcc = this.inspectedModelData.val_accs && this.inspectedModelData.val_accs[modelData.val_accs-1] || this.inspectedModelData.val_acc;
            if (valAcc && parentValAcc) {
                let n = valAcc - parentValAcc;
                return (n < 0 ? "" : "+") + n.toPrecision(2)
            }
        }
    }

    public paramChangeString(modelData) {
        if (modelData && this.inspectedModelData) {
            const parameters = modelData.parameters;
            const parentParameters = this.inspectedModelData.parameters;
            if (parameters && parentParameters) {
                let n = parameters - parentParameters;
                return (n < 0 ? "" : "+") + numeral(n).format('0.0a');
            }
        }
    }

    public valAccChangeClass(modelData) {
        let negative = true;
        if (modelData && this.inspectedModelData) {
            const valAcc = modelData.val_accs && modelData.val_accs[modelData.val_accs.length-1] || modelData.val_acc;
            const parentValAcc = this.inspectedModelData.val_accs && this.inspectedModelData.val_accs[this.inspectedModelData.val_accs.length-1] || this.inspectedModelData.val_acc;
            if (valAcc && parentValAcc) {
                let n = valAcc - parentValAcc;
                if (n > 0) {
                    negative = false;
                }
            }
        }

        return { 
            'positive-value-change': !negative,
            'negative-value-change': negative    
        }
    }

    public paramChangeClass(modelData) {
        let negative = true;
        if (modelData && this.inspectedModelData) {
            const parameters = modelData.parameters;
            const parentParameters = this.inspectedModelData.parameters;
            if (parameters && parentParameters) {
                let n = parameters - parentParameters;
                if (n > 0) {
                    negative = false;
                }
            }
        }

        return { 
            'positive-value-change': negative,
            'negative-value-change': !negative    
        }
    }

    public dragReorder ({oldIndex, newIndex}) {
        // const modelId = this.queuedModelIds.splice(oldIndex, 1)[0];
        const modelId = this.queuedModelIds[oldIndex];
        const switchedModelId = this.queuedModelIds[newIndex];
        // let newModelIds = [];
        // // Note, these indices are relative to the entire list, but the queue
        // // on the server will only have the still-to-train models, so we
        // // send back the ordered list of the modelIds still to train.
        // if (this.mini) {
        //     // If we're in mini version, we just want to switch the place of the old index and the new index
        //     const switchedModelId = this.queuedModelIds[newIndex];
        //     newModelIds = this.$store.state.queuedModelIds.slice();
        //     const fullOldIndex = newModelIds.indexOf(modelId);
        //     const fullNewIndex = newModelIds.indexOf(switchedModelId);
        //     console.log("switching ", modelId, " from index fullOldIndex", fullOldIndex, " to ", switchedModelId, " at fullNewIndex", fullNewIndex)
        //     newModelIds[fullOldIndex] = switchedModelId;
        //     newModelIds[fullNewIndex] = modelId;
        // } else {
        //     // Otherwise, we have access of the whole queuedModelIds list
        //     newModelIds = this.queuedModelIds.slice();
        //     newModelIds.splice(newIndex, 0, modelId);
        // }

        // this.$store.commit("REORDER_QUEUED_MODEL_IDS", newModelIds);

        this.$store.commit("SWITCH_QUEUED_MODEL_ORDER", {startId: modelId, endId: switchedModelId});
        if (this.inspectedModelData && this.inspectedModelData.parentId) {
            this.$store.commit("SWITCH_QUEUED_CHILDREN_MODEL_ORDER", {startId: modelId, endId: switchedModelId, parentId: this.inspectedModelData.parentId})
        }
    }

    public calcEstimatedTraining(data) {
        const params = data['parameters'];
        let trainString = '...';
        if (params < 5000) {
            trainString = '15s';
        } else if (params < 30000) {
            trainString = '' + (15 + Math.round(params / 1000)) + 's';
        } else {
            trainString = '' + Math.ceil(params / 250000) + 'm';
        }
        return trainString;
    }
    // get imageClasses() {
    //     return this.$store.state.datasetLabels;
    // }

    public mounted() {
        new Sortable(
// @ts-ignore
            this.$refs.sortableTable.$el.getElementsByTagName('tbody')[0],
            {
                draggable: '.sortableRow',
                handle: '.sortHandle',
                onEnd: this.dragReorder
            }
        );
    }

    private parentModelFor(model) {
        const parentId = model.parentId;
        if (parentId && window['searchableModels'][parentId]) {
            return this.dupedModel(window['searchableModels'][parentId]);
        }
    }

    private addRowToDrawer(modelId) {
        this.$store.commit('ADD_SELECTED_MODEL_ID', modelId);
    }

    private addRowToMouseover(modelId) {
        if (!this.mini) {
            this.$store.commit('SET_MOUSED_OVER_MODEL', modelId);
        }
    }

    private removeRowFromMouseover() {
        if (!this.mini) {
            this.$store.commit('SET_MOUSED_OVER_MODEL', 'NONE');            
        }
    }

    private deleteItem(item) {
        const modelId = item['id'];
        // We can't actually do this like this - we need to send a message to the server to 
        // give up on this model.  That'll be tricky, though.  SIGINT-y?
        if ( confirm('Are you sure you want to delete this model?') ) {
            // Update the backend
            // @ts-ignore
            this.$store.commit('DELETE_QUEUED_MODEL', modelId);
            // Then, update the backend
        }
    }

    private generateRandomModel() {
        // Need to send message to server to generate new model.  Then, we expect to get some response back in the socket
        // @ts-ignore

        this.$socket.emit('train_random_model', 'PING!');
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData))
    }

    private calculateQueueRowClass(modelData) {
        // console.log("calculating queue row class, modelData['trainingStatus'] is ", modelData['trainingStatus'])
        let classString = "";
        if (!this.mini && modelData['trainingStatus'] === 'completed') {
            classString += 'queue-row-completed';
        } else if (modelData['trainingStatus'] === 'in_progress') {
            classString += 'queue-row-training';
        } else if (modelData['trainingStatus'] === 'not_started') {
            classString += 'queue-row-not-started';
            classString += ' sortableRow';
        } else if (modelData['trainingStatus'] === 'error') {
            classString += 'queue-row-error';
        }

        return classString;
    }

    private calculateRowIcon(modelData) {
        if (modelData['trainingStatus'] === 'completed') {
            return 'done';
        } else if (modelData['trainingStatus'] === 'in_progress') {
            return 'hourglass_full';
        } else if (modelData['trainingStatus'] === 'not_started') {
            return 'hourglass_empty';
        } else if (modelData['trainingStatus'] === 'error') {
            return 'report_problem';
        }
    }

    private rowCurrentlyTraining(modelData) {
        return modelData['trainingStatus'] === 'in_progress';
    }

    private rowToTrain(modelData) {
        return modelData['trainingStatus'] === 'not_started';
    }

    private trendLineReady(modelData) {
        return modelData.loss;
    }

        // calculateLayerSize returns the size of the tensor at the given layer
    // previous layer is needed in case it is a flatten operation.
    // It also returns the number of params up to that point.
    // TODO - we are assuming that we have square layers.
    private calculateLayerSize( modelJson, previousModelJson, defaultSize, defaultHeight, defaultWidth,
                                defaultDepth, nparams = 0) {
        const previousLayerSize = previousModelJson.tensorSize || defaultSize;
        const previousLayerHeight = previousModelJson.tensorHeight || defaultHeight;
        const previousLayerWidth = previousModelJson.tensorWidth || defaultWidth;
        const previousLayerDepth = previousModelJson.tensorDepth || defaultDepth;
        const layers: any = {};
        if (modelJson.type === 'Conv2D') {
            // {"strides": 1, "type": "Conv2D", "filters": 128, "kernel_size": 1}
            // const width = Math.sqrt(previousLayerSize);
            layers.tensorWidth = Math.floor((previousLayerWidth - modelJson.kernel_size) / modelJson.strides + 1);
            layers.tensorHeight = layers.tensorWidth;
            layers.tensorDepth = modelJson.filters;
            nparams += (modelJson.filters + 1) * (modelJson.kernel_size ** 2); // + 1 for bias
        } else if (modelJson.type === 'Dense') {
            // {"units": 256, "type": "Dense"}
            layers.tensorSize = modelJson.units;
            layers.tensorWidth = modelJson.units;
            layers.tensorHeight = 1;
            layers.tensorDepth = 1;
            nparams += modelJson.units * previousLayerSize;
        } else if (modelJson.type.indexOf('Pool') !== -1) {
            // {"type": "AveragePooling2D", "pool_size": 2}
            if (modelJson.strides) {
                layers.strides = modelJson.strides;
            } else {
                layers.strides = 2;  // our default
            }
            layers.tensorWidth = Math.floor((previousLayerWidth - modelJson.pool_size) / layers.strides + 1);
            layers.tensorHeight = layers.tensorWidth; // we assume square pools
            layers.tensorDepth = previousLayerDepth;
        } else {
            // Dropout, Flatten, Activation all keep the size of the previous layer
            layers.tensorWidth = previousLayerWidth;
            layers.tensorHeight = previousLayerHeight;
            layers.tensorDepth = previousLayerDepth;
        }
        layers.tensorSize = layers.tensorDepth * layers.tensorWidth * layers.tensorHeight;

        layers.nparams = nparams;
        return layers;
    }
    // private onClassMouseover(image_class) {
    //     this.$store.commit('SELECT_LABEL', image_class);
    // }

    // @Watch('inspectedModelId')
    // private onInspectedModelIdChanged(newId, oldId) {
    //     // console.log("forcing update, perfdata is ",this.inspectedPerfData);
    //     this.$forceUpdate();
    // }
    @Watch('queuedModelData')
    private onQueuedModelDataChanged() {
        this.$forceUpdate();
    }
}

</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
.network-chips-container {
    justify-content: start !important;
}
</style>

<style lang='scss'>
.queue-row-completed {
    opacity: 0.5;
    color: gray !important;
    font-style: italic;
    background: lightgray;
}

.queue-row-training {
    font-style: bold !important;
}

.queue-row-error {
    
}

.queue-row-not-started {

}

.positive-value-change {
    color: green;
}

.negative-value-change {
    color: red;
}
.v-table__overflow {
    overflow-x: hidden !important;
    overflow-y: hidden !important;
}

.align-left {
    text-align: left !important;
}
.align-right {
    text-align: right !important;
}
</style>


