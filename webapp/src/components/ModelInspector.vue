<template>
    <div class='model-tabs' ref='modelTabs'>
        <div class='model-parent-floater'
            v-if='parentModelData'
            @click="clickedParent()"
        >
            <v-container
                fluid
                grid-list-md
            >  
                <v-layout row>
                    <h2>Parent</h2>
                </v-layout>
                <v-layout row>
                    <v-flex xs12>
                        <div class='model-parent-chip'>
                            <network-chip
                                :layersData="parentModelData"
                                :orientation="'left'"
                                :resolution="'small'"
                                :fixedWidth="false"
                                :showPlates="false"
                                :maxSize="maxSize"
                                :logBase="logBase"
                                :subselectable="false"
                                :showSelectableTransitions="false"
                                :showSelectableActions="false"
                                ref='myParentNetworkChip'
                            />            
                        </div>
                    </v-flex>
                </v-layout>
            </v-container>
        </div>
        <template v-if="inspectedModelData">
            <v-container
                fluid
                grid-list-md
            >  
                <v-layout row>
                    <v-flex xs12 :style="{'padding-bottom': parentModelData ? '90px' : '40px'}">
                        <network-chip
                            :layersData="inspectedModelData"
                            :orientation="'left'"
                            :resolution="'large'"
                            :fixedWidth="false"
                            :showPlates="false"
                            :maxSize="maxSize"
                            :logBase="logBase"
                            ref='myNetworkChip'
                        />
                    </v-flex>
                </v-layout>
                <v-layout row>
                    <v-flex xs12>
                        <v-layout row wrap>
                            <v-flex xs4 
                                v-for='option in fullInspectionOptions'
                                text-xs-center
                            >
                                <strong>{{option}}:</strong>
                                <p >
                                    {{valueAccessors[option](fixedInspectedModelData)}}
                                </p>
                            </v-flex>
                        </v-layout>
                    </v-flex>
                </v-layout>
                <v-layout row v-if='inspectedModelConfusionMatrix'>
                    <v-flex xs6>
                        <div class="model-inspection-confusion-matrix">
                            <confusion-matrix
                                :confusionMatrix="inspectedModelConfusionMatrix"
                                :metrics="inspectedModelMetrics"
                            >
                            </confusion-matrix>
                        </div>
                    </v-flex>
                    <v-flex xs6>
                        <div class="chartjs-line-chart-container">
                            <basic-line-chart
                                :chartdata="linechartdata"
                                :options="linechartoptions"
                                ref="myLineChart"
                            >
                            </basic-line-chart>
                        </div>
                    </v-flex>
                </v-layout>
            </v-container>
        </template>
        <template v-else>
            No model selected.  Select a model for inspection by clicking on it in the model drawer above.
        </template>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import NetworkChip from './NetworkChip.vue';
import BasicLineChart from './BasicLineChart.vue';
import ConfusionMatrix from './ConfusionMatrix.vue';

@Component({
    components: {
        BasicLineChart,
        ConfusionMatrix,
        NetworkChip
    }
})
export default class ModelInspector extends Vue {
    constructor() {
        super();
    }

    get resolution() { return 'small'; }
    get fixedWidth() { return this.$store.state.fixedWidth; }
    get maxSize() { return this.$store.state.maxWidth; }
    get logBase() { return this.$store.state.logBase; }

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

    get fixedInspectedModelData() {
        // num Epochs is wrong
        if (this.inspectedModelData) {
            let copyModelData = this.inspectedModelData;
            if (this.inspectedPerfData && (this.inspectedPerfData.trainAccs || this.inspectedModelData.train_accs)) {
                copyModelData.epochs = (this.inspectedPerfData.trainAccs || this.inspectedModelData.train_accs).length;
            }
            return copyModelData;
        } else {
            return this.inspectedModelData;
            // return null;
        }
    }

    get inspectedModelConfusionMatrix() {
        return this.inspectedModelData['confusion_matrix'];
    }

    get inspectedModelMetrics() {
        return this.inspectedModelData['metrics'];
    }

    get inspectedPerfData() {
        return this.getPerfData(this.inspectedModelId);
    }

    get fullInspectionOptions() {
        return this.$store.state.fullInspectionOptions;
    }

    get valueAccessors() {
        return this.$store.state.valueAccessors;
    }

    get parentId() {
        if (this.inspectedModelData) {
            return this.inspectedModelData.parentId;
        }
    }

    get parentModelData() {
        if (this.parentId && window['searchableModels'][this.parentId]) {
            return this.dupedModel(window['searchableModels'][this.parentId])
        }
    }

    get linechartdata() {
        if (this.inspectedPerfData.valAccs) {
            return {
                labels: (this.inspectedPerfData.valAccs || this.inspectedModelData.val_accs).map((v, i) => 'Epoch ' + i),
                datasets: [
                    {
                    label: 'valAccs',
                    pointStyle: 'circle',
                    backgroundColor: 'black',
                    borderColor: 'black',
                    //   data: (this.inspectedPerfData.valAccs || this.inspectedModelData.val_accs).map((v, i) => { return { 'x': i, 'y': v.val } } ),
                    data: (this.inspectedPerfData.valAccs || this.inspectedModelData.val_accs).map((v) => v.val ),
                    fill: false
                    }, {
                    label: 'trainAccs',
                    pointStyle: 'triangle',
                    backgroundColor: 'darkgray',
                    borderColor: 'darkgray',
                    //   data: this.inspectedPerfData.trainAccs.map((v, i) => { return { 'x': i, 'y': v.val } } ),
                    data: (this.inspectedPerfData.trainAccs || this.inspectedModelData.train_accs).map((v) => v.val ),
                    fill: false
                    }
                ]
            };

        } else {
            return {
                labels: (this.inspectedModelData.val_accs).map((v, i) => 'Epoch ' + i),
                datasets: [
                    {
                    label: 'valAccs',
                    pointStyle: 'circle',
                    backgroundColor: 'black',
                    borderColor: 'black',
                    //   data: (this.inspectedModelData.val_accs).map((v, i) => { return { 'x': i, 'y': v.val } } ),
                    data: this.inspectedModelData.val_accs,
                    fill: false
                    }, {
                    label: 'trainAccs',
                    pointStyle: 'triangle',
                    backgroundColor: 'darkgray',
                    borderColor: 'darkgray',
                    //   data: this.inspectedPerfData.trainAccs.map((v, i) => { return { 'x': i, 'y': v.val } } ),
                    data: this.inspectedModelData.train_accs,
                    fill: false
                    }
                ]
            };

        }
    }

    get linechartoptions() {
        return {
            // maintainAspectRatio: false,
            // height: '600px',
            responsive: true,
            animation: false,
            maintainAspectRatio: false,
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 3,
                        max: 1.0
                    },
                    gridLines: {
                        display: false
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'Accuracy'
                    }
                }],
                xAxes: [{
                    ticks: {
                        display: false
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'Epochs'
                    }
                }]
            },
            layout: {
                padding: {
                    left: 50,
                    right: 50,
                    top: 0,
                    bottom: 0
                }
            }
        };
    }

    private clickedParent() {
        this.$store.commit('ADD_SELECTED_MODEL_ID', this.parentId);
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData))
    }

    private getPerfData(inspectedModelId) {
        let data: any = {};

        // Have to sequential search this for now; build a data structure later
        this.$store.state.perfData.forEach((m) => {
            if (m.id === inspectedModelId) {
                data = m;
            }
        });
        return data;
    }

    private renderChart() {
        console.log("tellingit to render yoself")
        this.$refs.myLineChart.renderYourself();
    }

    @Watch('inspectedModelId')
    private onInspectedModelIdChanged(newId, oldId) {
        // console.log("forcing update, perfdata is ",this.inspectedPerfData);
        this.$forceUpdate();
    }

}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
.chartjs-line-chart-container {
    // width: 200px !important;
    // height: 100px !important;
}
.model-inspection-network-chip {

}
.chartjs-line-chart-container {

}
.model-tabs {
    position: relative;

    .model-parent-floater {
        z-index: 1000;
        position: absolute;
        top: 10px;
        left: 10px;
        // width: 300px;
        // height: 150px;
        // border-top: 2px dotted lightgray;
        // border-bottom: 2px dotted lightgray;
        border: 2px dotted lightgray;
        padding: 10px;

        border-radius: 4px;
        
        .model-parent-chip {
            text-align: left;
        }
    }
}

</style>


