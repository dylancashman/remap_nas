<template>
    <div class='model-drawer' ref='modelDrawer' @scroll="calculateArrows">
        <div id='network-chip-legend'>
            <strong>Legend</strong><network-chip :layersData = 'legendLayersData' :legend='true'/>
        </div>
        <div class='model-drawer-message' v-if='modelDrawerSize === totalModelNumber'>
            Displaying all <strong>{{totalModelNumber}}</strong> architectures.
            <div class='model-drawer-message'>
                &nbsp;
            </div>
        </div>
        <div class='model-drawer-message' v-else>
            Displaying <strong>{{modelDrawerSize}}</strong> architectures out of <strong>{{totalModelNumber}}</strong> total architectures.
            <div class='model-drawer-message' id='clear-model-drawer' @click='clearModelDrawer'>
                Clear Model Drawer
            </div>
        </div>
        <div class='model-drawer-filters'>
            <v-layout row wrap align-center>
                <v-flex sm3 d-flex class='drawer-options'>
                    <v-select
                    v-model="sortBy"
                    :items="sortByOptions"
                    label="Sort By"
                    ></v-select>
                </v-flex>
                <v-flex sm3 d-flex class='drawer-options'>
                    <v-select
                    v-model="alignBy"
                    :items="alignByOptions"
                    label="Align By"
                    ></v-select>
                </v-flex>
            </v-layout>
        </div>
        <ul ref='modelDrawerUl' :style="modelDrawerContainerStyle" @mouseout='unhighlightLi()'>
            <li :class='modelClass'>
                <div class='metric-value'></div>
                <div class='metric-value'></div>
                <div class='metric-value' v-for="option in sortByOptions" :key="option">
                    {{option}}
                </div>
            </li>

            <li v-for="modelData in sortedVisibleModels" :key="modelData.id" :class='modelClass(modelData.id)' 
                @mouseover='highlightLi(modelData.id)' @mouseout='unhighlightLi()'>
                <div class='single-model-container' :style="networkChipAlignmentStyle">
                    <network-chip
                        :layersData="modelData"
                        :orientation="'bottom'"
                        :resolution="resolution"
                        :fixedWidth="fixedWidth"
                        :showPlates="resolution !== 'large'"
                        :maxSize="maxSize"
                        :logBase="logBase" />
                </div>
                <div class='metric-value'>
                    {{valueStringFor(modelData)}}
                </div>
                <div class='metric-value' v-for="option in sortByOptions" :key="option">
                    {{renderMetricValue(modelData, option)}}
                </div>
                <div v-if='modelData.id == $store.state.mousedOverModelId && selectedModelIds.length > 0' 
                    class='close-button' @click='clearModel(modelData.id)'>
                    <v-icon>clear</v-icon>
                </div>
            </li>
        </ul>
        <div class='left-arrow' v-if="showLeftArrow">
            <v-icon>
                arrow_back_ios
            </v-icon>
        </div>
        <div class='right-arrow' v-if="showRightArrow">
            <v-icon>
                arrow_forward_ios
            </v-icon>
        </div>
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
export default class ModelDrawer extends Vue {

    public sortBy: string = 'Val Acc';
    public alignBy: string = 'bottom';
    private showRightArrow: boolean = false;
    private showLeftArrow: boolean = false;
    private loadedHeight: number = 0;
    private layerTypes: string[] = [];

    constructor() {
        super();
    }

    get resolution() { return this.$store.state.resolution; }
    get fixedWidth() { return this.$store.state.fixedWidth; }
    get maxSize() { return this.$store.state.maxWidth; }
    get logBase() { return this.$store.state.logBase; }

    get selectedModelIds() {
        return this.$store.state.selectedModelIds;
    }

    get visibleModels() {
        if (this.selectedModelIds.length > 0) {
            return this.selectedModelIds.map((id) => this.$store.state.modelArchitectures[id]);
        } else {
            return this.$store.state.modelArchitectures;
        }
    }

    get sortedVisibleModels() {
        return _.sortBy(this.visibleModels, this.descSortByAccessors[this.sortBy]);
    }

    get allModels() {
        return this.$store.state.modelArchitectures;
    }

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
        if ( this.alignBy === 'top' ) {
            alignItemsValue = 'flex-start';
        } else if ( this.alignBy === 'middle' ) {
            alignItemsValue = 'center';
        }
        return { 'align-items': alignItemsValue };
    }

    get modelDrawerSize() {
        return Object.keys(this.visibleModels).length;
    }

    get totalModelNumber() {
        return Object.keys(this.allModels).length;
    }

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

    public modelClass(modelId: string = '') {
        return {
            'model-drawer-model': true,
            'model-drawer-expanded': !this.fixedWidth,
            'model-drawer-highlighted': modelId && this.$store.state.mousedOverModelId === modelId
        };
    }

    public valueStringFor(model) {
        return this.renderMetricValue(model, this.sortBy);
    }

    public renderMetricValue(modelData, option) {
        if (this.valueAccessors[option]) {
            return this.formatOutput(this.valueAccessors[option](modelData)) || '--';
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

    private calculateLoadedHeight() {
        this.loadedHeight = (this.$refs.modelDrawerUl as Element).clientHeight;
    }

    private clearModelDrawer() {
        this.$store.commit('CLEAR_SELECTED_MODELS');
    }

    private highlightLi(modelId) {
        this.$store.commit('SET_MOUSED_OVER_MODEL', modelId);
    }

    private unhighlightLi() {
        this.$store.commit('SET_MOUSED_OVER_MODEL', 'NONE');
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
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
    .row {
        position: relative;
    }
    .model-drawer {
        width: 100%;
        background: white;
        .model-drawer-model {
            border: 2px solid rgba(0,0,0,0.0);
        }

        ul {
            display: flex;
            list-style: none;
            li {
                position: relative;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;

                .single-model-container {
                    height: 100%;
                    display: flex;
                    align-items: flex-end;
                    justify-content: center;
                }
            }

            li.model-class-right {
                float: left;
            }
        }

        border: 2px solid black;
        border-radius: 10px;
        padding: 25px;
        overflow-x: scroll;
        white-space: nowrap;

        .model-drawer-expanded {
            padding: 5px;
        }
        
        .model-drawer-highlighted {
            background: yellow;
            border: 2px solid brown !important;
            border-radius: 3px;
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
    }
</style>