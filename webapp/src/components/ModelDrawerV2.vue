<template>
    <div :class="modelDrawerClass" ref='modelDrawer' @scroll="calculateArrows">
        <v-toolbar dark dense v-if="!mini" color="grey darken-3">
            <v-toolbar-title>Model Drawer</v-toolbar-title>
        </v-toolbar>

        <v-card>
            <div class='model-drawer-container' :style="{'padding-top': legend ? '50px' : '0'}">
                <div id='network-chip-legend' v-if="legend">
                    <strong>Legend</strong><network-chip :layersData = 'legendLayersData' :legend='true'/>
                </div>

                <v-data-table
                    :headers="headers"
                    :items="sortedVisibleModels"
                    class="elevation-1"
                    no-results-text="No models have been selected."
                    hide-actions
                    ref="sortableTable"
                    >
                    <template slot='items' slot-scope='props'>
                        <tr 
                            :key="props.item.id"
                            :class="{'model-drawer-row-inspected': (props.item.id === inspectedModel)}"
                            @mouseover='highlightLi(props.item.id)'
                            @mouseout='unhighlightLi()'
                            @click='selectLi(props.item.id)'>
                            <td>
                                <v-tooltip v-if="false && mini && props.item['changes']">
                                    <div class='single-model-container' :style="networkChipAlignmentStyle">
                                        <network-chip
                                            :layersData="dupedModel(props.item)"
                                            :orientation="'left'"
                                            :resolution="resolution"
                                            :fixedWidth="fixedWidth"
                                            :showPlates="false"
                                            :maxSize="maxSize"
                                            :logBase="logBase" />
                                    </div>
                                    <span>{{props.item['changes']}}</span>
                                </v-tooltip>
                                <span class='single-model-container' :style="networkChipAlignmentStyle" v-else>
                                    <network-chip
                                        :layersData="dupedModel(props.item)"
                                        :orientation="'left'"
                                        :resolution="resolution"
                                        :fixedWidth="fixedWidth"
                                        :showPlates="false"
                                        :maxSize="maxSize"
                                        :logBase="logBase" />
                                </span>
                            </td>
                            <td v-if='mini'>{{ props.item.changes && props.item.changes.join('. ')}}</td>
                            <td>{{ valAccString(props.item) }}</td>
                            <td v-if='mini'>{{ valAccChangeString(props.item) }}</td>
                            <td v-if='mini'>{{ props.item.train_accs && props.item.train_accs[props.item.train_accs.length-1].toPrecision(2) || (props.item.train_acc && props.item.train_acc.toPrecision(2)) }}</td>
                            <td>{{ props.item.parameters && numeral(props.item.parameters).format('0.0a') }}</td>
                            <td class="justify-center layout px-0" v-if="!mini">
                                <v-icon
                                    small
                                    @click="deleteItem(props.item.id)"
                                >
                                    delete
                                </v-icon>
                                </td>
                        </tr>
                    </template>
                </v-data-table>
            </div>
        </v-card>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as _ from 'lodash';
import * as math from 'mathjs';
import * as numeral from 'numeral';
import * as strftime from 'strftime';
import NetworkChip from './NetworkChip.vue';

@Component({
    components: {
        NetworkChip
    }
})
export default class ModelDrawerV2 extends Vue {

    public sortBy: string = 'Val Acc';
    // public selectedModelIds: string[] = [];
    private showRightArrow: boolean = false;
    private showLeftArrow: boolean = false;
    private loadedHeight: number = 0;
    private layerTypes: string[] = [];
    // private modelDrawerSize: number = 0;
    private mouseInComponent: boolean = false;
    private numeral = numeral;

    @Prop({default: []})
    public selectedModelIds!: any[];

    @Prop({default: true})
    public clearable: boolean;

    @Prop({default: false})
    public mini: boolean;

    @Prop({default: true})
    public legend: boolean; 

    @Prop({default: 'bottom'})
    public alignBy: string = 'bottom';

    constructor() {
        super();
    }

    get headers() {
        if (this.mini) {
            let hlist = [
                { text: 'Model', align: 'left', sortable: false, value: 'layers', width: '25%' },
                { text: 'Changes', align: 'center', sortable: false, value: 'changes', width: '25%'},
                { text: 'Val Acc', value: 'val_acc', sortable: true, width: '10%', align: 'left' },
                { text: 'Change', value: 'change', sortable: true, width: '10%', align: 'left' },
                { text: 'Train Acc', value: 'train_acc', sortable: true, width: '10%', align: 'left' },
                { text: 'Num Params', value: 'parameters', sortable: true, width: '10%', align: 'left' },
                // Add delete from queue button
            ]
        } else {
            let hlist = [
                { text: 'Model', align: 'left', sortable: false, value: 'layers', width: '75%' },
                { text: 'Val Acc', value: 'val_acc', sortable: true, width: '10%', align: 'left' },
                { text: 'Num Params', value: 'parameters', sortable: true, width: '10%', align: 'left' },
                { text: '', value: 'parameters', sortable: false, width: '5%', align: 'center' },
            ]
        }
        if (this.mini) {
        }
        return hlist;
    }

    // get resolution() { return this.$store.state.resolution; }
    get resolution() { return 'small'; }
    get fixedWidth() { return this.$store.state.fixedWidth; }
    get maxSize() { return this.$store.state.maxWidth; }
    get logBase() { return this.$store.state.logBase; }

    get inspectedModel() { return this.$store.getters.inspectedModel; }

    get visibleModels() {
        if (this.selectedModelIds.length > 0) {
            return this.selectedModelIds.map((id) => this.$store.state.modelArchitectures[id]).filter((m) => !!m);
        } else {
            // return this.$store.state.modelArchitectures;
            return [];
        }
    }

    get modelDrawerClass() {
        if (this.mini) {
            return 'model-drawer-mini';
        } else {
            return 'model-drawer';
        }
    }
    // get selectedModelIds() {
    //     return this.$store.state.selectedModelIds;
    // }

    get sortedVisibleModels() {
        return _.sortBy(this.visibleModels, this.descSortByAccessors[this.sortBy]).reverse();
    }

    // get allModels() {
    //     return this.$store.state.modelArchitectures;
    // }

    get modelDrawerContainerStyle() {
        if ( this.loadedHeight > 0 ) {
            return {
                height: this.loadedHeight + 'px',
            };
        } else {
            return {
            };
        }
    }

    get networkChipAlignmentStyle() {
        let alignItemsValue = 'flex-end';
        if ( this.alignBy === 'bottom' ) {
            alignItemsValue = 'flex-start';
        } else if ( this.alignBy === 'middle' ) {
            alignItemsValue = 'center';
        }
        return { 'align-items': alignItemsValue };
    }

    get modelDrawerSize() {
        return Object.keys(this.visibleModels).length;
    }

    // get totalModelNumber() {
    //     return Object.keys(this.allModels).length;
    // }

    get sortByOptions() {
        return this.$store.state.sortByOptions;
    }

    get alignByOptions() {
        return ['top', 'middle', 'bottom'];
    }

    get descSortByAccessors() {
        return this.$store.state.descSortByAccessors;
    }

    get valueAccessors() {
        return this.$store.state.valueAccessors;
    }

    get legendLayersData() {
        const layersData: any = {};
        layersData.layers = this.layerTypes.map((layerType) => {
            return { type: layerType };
        });

        return layersData;
    }

    public valAccString(modelData) {
        return (modelData.val_accs && modelData.val_accs[modelData.val_accs.length-1].toPrecision(2) || (modelData.val_acc && modelData.val_acc.toPrecision(2)))
    }

    get inspectedModelData() {
        if (window['searchableModels'][this.inspectedModel]) {
            return this.dupedModel(window['searchableModels'][this.inspectedModel]);
        } else {
            return null;
        }
    }

    public valAccChangeString(modelData) {
        const valAcc = modelData.val_accs && modelData.val_accs[modelData.val_accs.length-1] || modelData.val_acc;
        const parentValAcc = this.inspectedModelData.val_accs && this.inspectedModelData.val_accs[this.inspectedModelData.val_accs.length-1] || this.inspectedModelData.val_acc;
        if (valAcc && parentValAcc) {
            return (valAcc - parentValAcc).toPrecision(2);
        }
    }

    public modelClass(modelId: string = '') {
        return {
            'model-drawer-model': true,
            'model-drawer-expanded': !this.fixedWidth,
            'model-drawer-highlighted': modelId && this.$store.state.mousedOverModelId === modelId,
            'model-drawer-inspected': modelId && this.inspectedModel === modelId
        };
    }

    public valueStringFor(model) {
        return this.renderMetricValue(model, this.sortBy);
    }

    public renderMetricValue(modelData, option) {
        if (this.valueAccessors[option]) {
            return this.formatOutput(this.valueAccessors[option](modelData)) || '-';
        } else {
            return '--';
        }
    }

    public formatOutput(out) {
        if (_.isNumber(out) && !_.isInteger(out)) {
            if ( this.fixedWidth ) {
                return d3.format('.2f')(out).substr(1);
            } else {
                return d3.format('.3f')(out);
            }
        } else {
            return out;
        }
    }

    public mounted() {
        this.calculateArrows();
        this.calculateLoadedHeight();
        this.layerTypes = this.$store.state.colorManager.getColorKeys();
    }

    public updated() {
        setTimeout(this.calculateArrows, 500);
        setTimeout(this.calculateLoadedHeight, 500);
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData))
    }

    private calculateLoadedHeight() {
        // this.loadedHeight = (this.$refs.modelDrawerUl as Element).clientHeight;
        if (this.mini) {
            this.loadedHeight = 150;
        } else {
            this.loadedHeight = 250;
        }
    }

    private clearModelDrawer() {
        if (!this.mini) {
            this.$store.commit('CLEAR_SELECTED_MODELS');
        }
    }

    private highlightLi(modelId) {
        if (!this.mini) {
            this.mouseInComponent = true;
            this.$store.commit('SET_MOUSED_OVER_MODEL', modelId);
        }
    }

    private unhighlightLi() {
        if (!this.mini) {
            this.mouseInComponent = false;
            this.$store.commit('SET_MOUSED_OVER_MODEL', 'NONE');
        }
    }

    private selectLi(modelId) {
        // console.log("selectLi called with modelId", modelId)
        if (!this.mini) {
            this.$store.commit('SET_CLICKED_MODEL', modelId);
        } else {
            this.$store.commit('ADD_SELECTED_MODEL_ID', modelId);
        }
    }

    private deselectLi(modelId) {
        if (!this.mini) {
            this.$store.commit('SET_CLICKED_MODEL', 'NONE');
        }
    }

    private deleteItem(modelId) {
        confirm('Are you sure you want to delete this item?') && this.clearModel(modelId)
    }

    private clearModel(modelId) {
        this.$store.commit('REMOVE_SELECTED_MODEL_ID', modelId);
    }

    private calculateArrows() {
        const drawerElement = this.$refs.modelDrawer as Element;
        if (drawerElement.scrollWidth > drawerElement.scrollLeft + drawerElement.clientWidth) {
            this.showRightArrow = true;
        } else {
            this.showRightArrow = false;
        }

        if (drawerElement.scrollLeft > 0) {
            this.showLeftArrow = true;
        } else {
            this.showLeftArrow = false;
        }
    }

    @Watch('resolution')
    private onResolutionChanged(newRes, oldRes) {
        // This is a hack to get Vue to let the drawer resize itself before
        // saving its height.
        this.loadedHeight = 0;
    }

    @Watch('modelDrawerSize')
    private onModelDrawerSize(newSize, oldSize) {
        // This is a hack to get Vue to let the drawer resize itself before
        // saving its height.
        if (newSize === 0 ) {
            this.loadedHeight = 0;
        }
    }

    @Watch('sortedVisibleModels')
    private onSortedVisibleModelsChanged(newmods, oldmods) {
        this.layerTypes = this.$store.state.colorManager.getColorKeys();
        return newmods.length;
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
    .row {
        position: relative;
    }
    .model-drawer-mini {
        width: 100%;
    }
    .model-drawer {
        width: 100%;
        border-radius: 10px;
        padding: 25px;
    }

    .model-drawer, .model-drawer-mini {
        .card {
            padding: 1px !important;
        }

        .network-chips-container {
            justify-content: end;
        }


        padding: 0 !important;
        background: white;
        // overflow-x: scroll;
        white-space: nowrap;

        .model-drawer-model {
            border: 2px solid rgba(0,0,0,0.0);
        }

        ul {
            // display: flex;
            list-style: none;
            li {
                position: relative;
                // height: 100%;
                // display: flex;
                // flex-direction: column;
                // justify-content: flex-end;

                .single-model-container {
                    // height: 100%;
                    // display: flex;
                    // align-items: flex-end;
                    // justify-content: center;
                }
            }

            li.model-class-right {
                // float: left;
            }
        }
        .model-drawer-expanded {
            padding: 5px;
        }
        
        .model-drawer-highlighted {
            // border: 2px solid black !important;
            background: #d9d9d9;
            border-radius: 3px;
        }

        .model-drawer-inspected {
            background: #d9d9d9;
        }

        .model-drawer-row-inspected {
            background: lightgray;
        }
        .left-arrow {
            position: absolute;
            left: 3%;
            top: 25%;
            opacity: 0.5;
        }

        .right-arrow {
            position: absolute;
            left: 97%;
            top: 25%;
            opacity: 0.5;
        }

        .close-button {
            position: absolute;
            top: -5px;
            right: -5px;
            fill: black;
            width: 26px;
            border-radius: 13px;
            background: rgba(10,10,10,0.3);
            cursor: pointer;
        }

        #clear-model-drawer {
            color: blue;
        }

        #network-chip-legend {
            position: absolute;
            top: 10px;
            right: 50px;
        }
        
        .drawer-options {
            padding: 20px;
        }

        .model-drawer-container {
            position: relative;
        }

        th,td {
            padding-left: 4px !important;
            padding-right: 4px !important;
        }
        .datatable {
            td {
                white-space: normal !important;
            }
        }
    }
</style>