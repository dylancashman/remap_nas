<template>

    <div id="app">
        <link href='https://fonts.googleapis.com/css?family=Roboto:300,400,500,700|Material+Icons' rel="stylesheet" type="text/css" />
        <v-app>
            <v-toolbar dark>
                <v-toolbar-title>REMAP: Rapid Exploration of Model Architectures and Parameters</v-toolbar-title>
            </v-toolbar>
            <v-content>
                <v-container fluid>
                    <template v-if="modelsLoaded">
                        <v-layout row wrap class='mast-v-layout'>
                            <!-- Top part -->
                            <v-flex xs12 md3 class='mast-v-flex' id='mast-model-overview'>
                                <v-layout d-flex row wrap>
                                    <v-flex xs12 :style="{'padding-bottom': '15px'}">
                                        <model-overview
                                            :modelArchs="myModelsWithDistances"
                                            v-if="modelsLoaded"
                                        >
                                        </model-overview>
                                    </v-flex>
                                    <v-flex d-flex xs12 class='mast-v-flex' id='mast-model-drawer'>
                                        <model-drawer-v2 
                                            :selectedModelIds="selectedModelIds"
                                            />
                                    </v-flex>
                                </v-layout>
                            </v-flex>
                            <v-flex xs12 md9 class='mast-v-flex'>
                                <v-layout row wrap>
                                    <v-flex class='mast-v-flex noscrollbar' id='mast-custom-tabs' grow >
                                        <mas-tabs />
                                    </v-flex>
                                </v-layout>
                            </v-flex>
                        </v-layout>
                    </template>
                </v-container>
            </v-content>
        </v-app>
    </div>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import ModelOverview from './components/ModelOverview.vue';
import ModelDrawerV2 from './components/ModelDrawerV2.vue';
import MasPerfLineChart from './components/MasPerfLineChart.vue';
import MasTabs from './components/MasTabs.vue';
import DebugV2 from './components/DebugV2.vue';
// @ts-ignore
import loadedModelsWithDistances from '../data/20190330_quickdraw_models_with_distances.json';

// @ts-ignore
import groundtruthLabels from '../data/quickdraw_labels.json';

// @ts-ignore
import modelPerfJson from '../data/20190330_quickdraw_training_results_data.json';

// @ts-ignore
import SocketData from '@/util/SocketData';
const randomsd = new SocketData();
randomsd.addData(modelPerfJson);

import * as _ from 'lodash';
import * as d3 from 'd3';
import { ScaleTime, ScaleLinear } from 'd3';

@Component({
    components: {
        ModelOverview,
        ModelDrawerV2,
        MasPerfLineChart,
        MasTabs,
        DebugV2
    }
})
export default class AppV2 extends Vue {

    public modelsWithDistances = [];
    public myGroundtruthLabels = groundtruthLabels;
    public initialDataSize = 3.0 * 32.0 * 32.0; // CIFAR 10
    public initialDataWidth = 32.0;
    public initialDataHeight = 32.0;
    public initialDataDepth = 3.0;
    public alignment: string = 'start';
    public maxSize: number = 1;
    public randomPerfJson = randomsd.getTableData('');
    public modelsLoaded: boolean =  false;
    public projectionType: string = 'mds_hamming';

    constructor() {
        super();
        this.$store.commit('ADD_PERF_DATA', this.randomPerfJson);
        this.$store.commit('LOAD_GROUNDTRUTH_LABELS', this.myGroundtruthLabels);
    }

    get myModelsWithDistances() {
        return this.$store.state.modelArchitectures;
    }

    get selectedModelIds() {
        return this.$store.state.selectedModelIds;
    }

    public mounted() {
        this.initializeTensorSizes();
    }

    private initializeTensorSizes() {
        window['modelsWithDistances'] = loadedModelsWithDistances;

        for (let i = 0; i < loadedModelsWithDistances.length; i++) {
            let prevLayer = {};
            let nparams = 0;
            let maxTensorSize = 0;
            for (let j = 0; j < loadedModelsWithDistances[i].layers.length; j++) {
                const layers: any = this.calculateLayerSize(loadedModelsWithDistances[i].layers[j], prevLayer,
                                                            this.initialDataSize, this.initialDataWidth,
                                                            this.initialDataHeight, this.initialDataDepth,
                                                            nparams);
                window['modelsWithDistances'][i].layers[j].tensorSize = layers.tensorSize;
                window['modelsWithDistances'][i].layers[j].tensorWidth = layers.tensorWidth;
                window['modelsWithDistances'][i].layers[j].tensorHeight = layers.tensorHeight;
                window['modelsWithDistances'][i].layers[j].tensorDepth = layers.tensorDepth;
                if (layers.tensorSize > maxTensorSize) {
                    maxTensorSize = layers.tensorSize;
                }
                nparams = layers.nparams;
                prevLayer = window['modelsWithDistances'][i].layers[j];
            }
            window['modelsWithDistances'][i].calcParams = nparams;
            window['modelsWithDistances'][i].maxTensorSize = maxTensorSize;
        }

        // calculate the maximum width
        const randomMaxSize = _.max(window['modelsWithDistances'].map((modelJson: any) => {
            return _.max(modelJson.layers.map((layerJson: any) => {
                return layerJson.tensorSize || 1;
            }));
        })) || 1;

        this.maxSize = randomMaxSize as number;
        this.$store.commit('SET_MAX_WIDTH', this.maxSize);
        
        // We're also going to store the unshortened version in a hash for searches in a nonreactive object in the global space
        let searchableModels = {};
        window['modelsWithDistances'].forEach((m) => {
            searchableModels[m.id] = m;
        })

        for (let i = 0; i < this.randomPerfJson.length; i++) {
            const model = this.randomPerfJson[i];
            searchableModels[model.id].epochs = model.valAccs.length;
            searchableModels[model.id].forwardTime = model.forwardTime;
            searchableModels[model.id].backwardTime = model.backwardTime;
        }

        // We don't want all the data reactive, so we make a copy and remove the confusion matrices
        let shortenedModelsWithDistances = JSON.parse(JSON.stringify(window['modelsWithDistances'])).map((m) => m).map((m) => {
            delete m.confusion_matrix;
            Object.freeze(m);
            return m;
        })
        // console.log("shortened")
        this.$store.commit('LOAD_ARCHITECTURE_DATA', shortenedModelsWithDistances);
        
        window['searchableModels'] = searchableModels;
        // console.log("window['modelsWithDistances'] is ", window['modelsWithDistances']);
        this.modelsLoaded = true;
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

    @Watch('projectionType')
    private onProjectionTypeChanged(newProjType, oldProjType) {
        this.$store.commit('CHANGE_PROJECTION_TYPE', newProjType);
    }

}
</script>

<style lang="scss">
#app {
    font-family: IBMPlexSansCondensed, "Avenir", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #2c3e50;
    
    .app-title {
        font-family: IBMPlexMono, "Avenir", Helvetica, Arial, sans-serif;
        padding: 30px 30px;
        text-align: left;
        display: block;
        line-height: 525%;

        .app-title-row {
            display: flex;
            align-items: baseline;
            line-height: 3.0em;
            .app-title-capital {
                font-size: 3.0em;
                font-weight: 700;
                letter-spacing: 0.1em;
            }

            .app-title-lower {
                font-size: 1.4em;
                font-weight: 300;
            }
        }
    }
    .mast-v-flex {
        // border: 2px solid green;
    }
    .mast-v-layout {
        // border: 2px solid red;
    }
    #mast-model-drawer {
        // height: 300px;
    }
    #mast-custom-tabs {
        // height: 550px;
    }
    #mast-timeline {
        height: 220px;
    }
    #mast-model-overview {
        padding-right: 15px;
    }

    .noscrollbar {
        overflow-y: scroll !important;
        scrollbar-width: none !important; /* Firefox */
        -ms-overflow-style: none !important;  /* IE 10+ */
    }
    .noscrollbar::-webkit-scrollbar { /* WebKit */
        width: 0 !important;
        height: 0 !important;
    }
}
</style>
