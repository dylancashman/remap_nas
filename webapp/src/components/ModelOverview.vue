<template>
    <div class='model-overview'>
        <v-toolbar dense dark color="grey darken-3">
            <!-- <v-flex xs12>
                <v-radio-group v-model="projectionType" :mandatory="false">
                    <v-radio label="Prediction Similarity" value="mds_hamming"></v-radio>
                    <v-radio label="Structural Similarity" value="mds_otmann"></v-radio>
                    <v-radio label="Performance By Size" value="hendrik"></v-radio>
                </v-radio-group>
            </v-flex> -->

            <v-toolbar-title>Model Overview</v-toolbar-title>
            <v-spacer></v-spacer>
            <!-- <v-toolbar-side-icon 
                @mouseover="menuOn = true"
                @mouseout="menuOn = false"
                ></v-toolbar-side-icon> -->
                <v-toolbar-items>
                    <v-menu auto>
                        <template slot="activator">
                            <v-btn
                                dark
                                v-on="{ menuOn }"
                                icon
                                ><v-icon>menu</v-icon></v-btn>
                        </template>
                        <!-- <template #activator="{ on: menuOn }">
                            <v-tooltip bottom>
                                <template #activator="{ on: tooltipOn }">
                                    <v-btn
                                        dark
                                        icon
                                        v-on="{ ...tooltipOn, ...menuOn }"
                                        ><v-icon>menu</v-icon></v-btn>
                                </template>
                                <span>Im A ToolTip</span>
                            </v-tooltip>
                        </template> -->
                        <v-list>
                            <v-list-tile
                                @click="projectionType='mds_hamming'"
                            >
                                <v-list-tile-title>
                                    View Prediction Similarity
                                </v-list-tile-title>
                                <v-icon v-if="projectionType==='mds_hamming'">done</v-icon>
                            </v-list-tile>
                            <v-list-tile
                                @click="projectionType='mds_otmann'"
                            >
                                <v-list-tile-title>View Structural Similarity</v-list-tile-title>
                                <v-icon v-if="projectionType==='mds_otmann'">done</v-icon>
                            </v-list-tile>
                            <v-list-tile
                                @click="projectionType='hendrik'"
                            >
                                <v-list-tile-title>View Accuracy vs. Size</v-list-tile-title>
                                <v-icon v-if="projectionType==='hendrik'">done</v-icon>
                            </v-list-tile>

                        </v-list>
                    </v-menu>
                </v-toolbar-items>
                <!-- <v-btn flat>
                    <v-icon>
                        menu
                    </v-icon>
                </v-btn> -->

     
                <!-- 
                <v-list>
                    <v-list-tile
                        @click="projectionType='mds_hamming'"
                    >
                        <v-list-tile-title v-text="Prediction Similarity"></v-list-tile-title>
                    </v-list-tile>
                    <v-list-tile
                        @click="projectionType='mds_otmann'"
                    >
                        <v-list-tile-title v-text="Structural Similarity"></v-list-tile-title>
                    </v-list-tile>
                    <v-list-tile
                        @click="projectionType='hendrik'"
                    >
                        <v-list-tile-title v-text="Accuracy vs. Size"></v-list-tile-title>
                    </v-list-tile>
                </v-list> -->
        </v-toolbar>
        <v-card>
            <scrollable-scatter
                :coords="modelCoords"
                :pointMousedOver="onPtMouseover"
                :showAxis="projectionType==='hendrik'"
                :yAxisLog="projectionType==='hendrik'"
            ></scrollable-scatter>
        </v-card>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as _ from 'lodash';
import ColorManager from '../vis/ColorManager';
import { Line } from 'd3-shape';
import { ScaleLinear, ScaleTime } from 'd3-scale';
import { TimeLocaleObject } from 'd3-time-format';
import { Axis } from 'd3-axis';
import NetworkChip from './NetworkChip.vue';
import ScrollableScatter from './ScrollableScatter.vue';
import { BrushSelection, BrushBehavior } from 'd3';

@Component({
    components: {
        NetworkChip,
        ScrollableScatter
    }
})
export default class ModelOverview extends Vue {
    public svgWidth: number = 350;
    public svgHeight: number = 350;
    public svgPadding: number = 40;
    public timeFormatString: string = '%Y-%m-%dT%H:%M:%S.%f';
    public maxTimestamp!: Date;
    public minTimestamp!: Date;
    public brushedXStart: number = 0;
    public brushedXEnd: number = this.svgWidth;
    public brushedYStart: number = 0;
    public brushedYEnd: number = this.svgHeight;
    public timeParser: (s: string) => (Date | null)  = d3.timeParse(this.timeFormatString);
    public brushedModelHash = {};
    public brushModelsAdded: boolean = false;
    public tooltipLeft: number = 100;
    public tooltipTop: number = 100;
    public showTooltip: boolean = false;
    public selectedModel: string = '';
    public xKey: string = 'Val Acc';
    public yKey: string = 'Log(Num Params)';

    @Prop()
    public modelArchs!: any;

    @Prop({default: 'valAccs'})
    public dataKey!: string;

    @Prop({default: false})
    public projection!: boolean;

    public xScales: any = {};
    public yScales: any = {};
    public xAxes: any = {};
    public yAxes: any = {};

    public menuOn: boolean = false;
    public tooltipOn: boolean = false;

    get projectionType() {
        return this.$store.state.projectionType;
    }

    set projectionType(newType) {
        this.$store.commit("CHANGE_PROJECTION_TYPE", newType);
    }

    get imageClassSelected() {
        return this.$store.state.imageClassSelected;
    }

    get imageClassNameSelected() {
        return this.$store.state.imageClassNameSelected;
    }

    get imageClassHighlighted() {
        return this.$store.state.imageClassHighlighted;
    }

    get imageClassNameHighlighted() {
        return this.$store.state.imageClassNameHighlighted;
    }

    get imageIndexHighlighted() {
        return this.$store.state.imageIndexHighlighted;
    }

    get modelCoords() {
        const coords = Object.keys(this.modelArchs).map((modelId, idx) => {
            const model = this.modelArchs[modelId];
            // if (idx === 0) {
            //     console.log("window['searchableModels'][modelId] is ", window['searchableModels'][modelId] )
            // }
            // const m = model['projections']['mds_otmann'];
            if (model && model['projections']) {
                const m = model['projections'][this.projectionType];
                // if (this.projectionType === 'hendrik') {
                //     m['y'] = Math.log(m['y']);
                // }

                if (this.imageIndexHighlighted) {
                    const predicted = window['searchableModels'][modelId]['predictions'][this.imageIndexHighlighted];
                    const groundTruth = this.$store.state.groundtruthLabels[this.imageIndexHighlighted]; 
                    m['colorScore'] = (predicted === groundTruth) ? 1.0 : 0.0;
                } else if (this.imageClassNameHighlighted) {
                    m['colorScore'] = model['class_accuracies'] && model['class_accuracies'][this.imageClassHighlighted];
                } else if (this.imageClassNameSelected) {
                    m['colorScore'] = model['class_accuracies'] && model['class_accuracies'][this.imageClassSelected];
                } else {
                    // Force val acc to be color
                    // if (!m['colorScore']) {
                    if (model['val_accs']) {
                        m['colorScore'] = model['val_accs'][model['val_accs'].length-1];
                    } else {
                        m['colorScore'] = model['val_acc'];
                    }
                    // }
                }
                m['idx'] = idx;
                m['layers'] = model['layers'];
                m['uuid'] = model['id'];
                m['parameters'] = model['parameters'];
                return m;
            } else {
                return null;
            }
        })
        // console.log("recalculating modelCoords, before filter there are ", coords.length);
        // console.log("after filter, there are ", coords.filter((el) => {return el != null}).length);
        return coords.filter((el) => {return el != null});
    }

    get sortByOptions() {
        return this.$store.state.sortByOptions;
    }

    get sortByAccessors() {
        return this.$store.state.sortByAccessors;
    }

    get valueAccessors() {
        return this.$store.state.valueAccessors;
    }

    get skipSingleEpochModels() {
        return this.$store.state.skipSingleEpochModels;
    }

    constructor() {
        super();

        // Get domain and range for scales
    }

    private onPtMouseover(ptIdx) {
        console.log("mousedOverPt is ", ptIdx);
    }

    @Watch('modelArchs')
    private onModelArchsChanged(newMods, oldMods) {
        console.log("modelArchs changed, forcing update.  before,there are this many archs and coords: ", Object.keys(this.modelArchs).length, " ", this.modelCoords.length)
        this.$forceUpdate();
        console.log("now, there are this many archs and coords: ", Object.keys(this.modelArchs).length, " ", this.modelCoords.length)
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
    .model-overview {
        // width: 650px;
    }
</style>