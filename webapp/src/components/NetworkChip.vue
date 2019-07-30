<template>
    <div
        :style='orientationStyle'
        class="network-chips-container" >
        <drag-select-container
            selectorClass="network-chip-subselectable"
            v-if="subselectable"
            @change="onSelectedLayersChanged"
            ref='dragSelectContainer'>
            <template slot-scope="{ selectedItems }">
                <template v-for="(layer, index) in sortedLayers">
                    <div
                        :class="slotAndSubselectClass(layer, index, selectedItems)"
                        :data-item="`layer-${index}-a`"
                        v-if="handcraftable"
                        >
                    </div>
                    <component :key="`${layersData.id}--${index}`" 
                        :data-item="`layer-${index}-b`"
                        class="network-chip-div network-chip-subselectable"
                        is='div'
                        >
                        <v-tooltip right
                            content-class="network-chip-tooltip"
                            offset-overflow
                            transition="fade-transition"
                            v-model="layer.selected"
                            tag='div'
                            :class="plateClass(layer)" >
                            <div slot="activator"
                                :style= calculatedChipStyle(layer)
                                :class="chipAndSubselectClass(layer, index, selectedItems)">

                                <div v-if="resolution != 'small' && layer.type === 'Activation'"
                                    @click="layer.selected = !layer.selected"
                                    class="network-chips-container">
                                    <SigmoidIcon v-if="layer.activation === 'sigmoid'" class='network-chips-icon'/>
                                    <TanhIcon v-else-if="layer.activation === 'tanh'" class='network-chips-icon'/>
                                    <ReluIcon v-else-if="layer.activation === 'relu'" class='network-chips-icon'/>
                                    <div v-else>{{layer.type[0]}}</div>
                                </div>
                                <div v-else-if="resolution != 'small'"
                                    class="network-chips-container">
                                    {{layer.type[0]}}
                                </div>

                            </div>
                            <span>
                                <table>
                                    <tr v-for="(attr, aIndex) in tooltipAttrs(layer)" :key="`${layersData.name}--${index}--${aIndex}`">
                                        <td><em>{{attr.title}}: </em></td>
                                        <td>{{attr.value}}</td>
                                    </tr>
                                </table>
                            </span>
                        </v-tooltip>
                        <div class='layer-selectors'
                            v-if="showSelectableActions"
                            :style= "{
                                top: `${40 + 0.5 * widthForLayer(layer.tensorSize)}px`
                            }"
                            @click.stop="null"
                            @mousedown.stop="null"
                        >
                            <div class="layer-options" 
                                v-for="variationType in variationTypesForLayer(index)"
                                >
                                <v-icon @click.stop="toggleAction(index, variationType)"
                                    @mouseover="hintMoreAction(index, variationType)"
                                    class='option-icon'
                                    :title="variationType" 
                                    :style="actionStyle(index, variationType)">
                                    {{layerActionIconMapping[variationType]}}
                                </v-icon>
                                <div class="layer-options-more"
                                    @click.stop="toggleMoreAction(index, variationType)"
                                    @mouseover="showMoreAction(index, variationType)"
                                    :style= "{
                                        top: `${40 + 0.5 * widthForLayer(layer.tensorSize)}px`
                                    }"
                                >
                                </div>
                                <!-- <v-icon 
                                        background: `${((hintMoreActionIndex === index) && (hintMoreActionType === variationType)) ? 'gray' : 'white'}`
                                        opacity: `${((hintMoreActionIndex === index) && (hintMoreActionType === variationType)) ? 0.3 : 0.1}`
                                    small
                                    @click="toggleActionOptions(index, variationType)"
                                    class='dropdown-icon'
                                    v-if="variationType !== 'remove'"
                                    >
                                    {{actionExpanded(index, variationType) ? 'expand_less' : 'expand_more'}}
                                </v-icon> -->
                            </div>
                        </div>

                        <div v-if="layer.plateStart && showPlates && resolution != 'large'" 
                            class="network-chip-plate-number">
                            {{layer.numPlates}}
                        </div>
                        <!-- We put in arrows for any skip connections -->
                    </component>
                </template>
            </template>
        </drag-select-container>
        <template v-for="(layer, index) in sortedLayers" v-else >
            <div :key="`${layersData.name}--${index}`" 
                class="network-chip-div"
                >
                <v-menu class="handcraftable-menu" offset-y v-if="handcraftable">
                    <template v-slot:activator="{ on }">
                        <v-btn
                            color="primary"
                            dark
                            v-on="on"
                            >
                            <div
                                :class="slotAndSubselectClass(layer, index, selectedItems)"
                                :data-item="`layer-${index}-a`"
                                v-if="handcraftable"
                                >
                            </div>
                        </v-btn>
                    </template>
                    <v-list>
                        <v-list-tile
                            v-for="option in layerAddOptions"
                            @click="addLayer(index, option)"
                            >
                            <v-list-tile-title>{{option}}</v-list-tile-title>
                        </v-list-tile>
                    </v-list>
                </v-menu>

                <v-menu>
                    <template #activator="{ on: menu }">
                        <v-tooltip right
                            content-class="network-chip-tooltip"
                            offset-overflow
                            transition="fade-transition"
                            v-model="layer.selected"
                            tag='div'
                            :class="plateClass(layer)" >
                                <!-- @click.native="layer.selected = !layer.selected" -->
                            <template #activator="{ on: tooltip }">
                                <!-- <div slot="activator" -->
                                <v-btn
                                    color="primary"
                                    dark
                                    v-on="{ ...tooltip, ...menu }">
                                    <div
                                        :ref="`layer-${layer.id}`"
                                        :style= calculatedChipStyle(layer)
                                        :class="chipClass(layer)">

                                        <div v-if="resolution != 'small' && layer.type === 'Activation'"
                                            class="network-chips-container">
                                            <SigmoidIcon v-if="layer.activation === 'sigmoid'" class='network-chips-icon'/>
                                            <TanhIcon v-else-if="layer.activation === 'tanh'" class='network-chips-icon'/>
                                            <ReluIcon v-else-if="layer.activation === 'relu'" class='network-chips-icon'/>
                                            <div v-else>{{layer.type[0]}}</div>
                                        </div>
                                        <div v-else-if="resolution != 'small'"
                                            class="network-chips-container">
                                            {{layer.type[0]}}
                                        </div>

                                    </div>
                                </v-btn>
                            </template>
                            <span>
                                <table>
                                    <tr v-for="(attr, aIndex) in tooltipAttrs(layer)" :key="`${layersData.name}--${index}--${aIndex}`">
                                        <td><em>{{attr.title}}: </em></td>
                                        <td>{{attr.value}}</td>
                                    </tr>
                                </table>
                            </span>
                        </v-tooltip>
                    </template>
                    <v-list>
                        <v-list-tile
                            v-for="option in layerModificationOptions(layer)"
                            @click="modifyLayer(index, option)"
                            >
                            <v-list-tile-title>{{option}}</v-list-tile-title>
                        </v-list-tile>
                    </v-list>
                </v-menu>
                <div v-if="layer.plateStart && showPlates && resolution != 'large'" 
                    class="network-chip-plate-number">
                    {{layer.numPlates}}
                </div>
                <!-- We put in arrows for any skip connections -->
            </div>
        </template>
        <div v-if="skipConnections.length > 0" class="skip-connections-container">
            <template v-for="(skipConnection, index) in skipConnections">
                <div :key="index" :ref="`${skipConnection[0]}-${skipConnection[1]}`"
                    :data-skip-source="skipConnection[0]" :data-skip-target="skipConnection[1]"
                    :style= "{
                        width: `${(chipWidth + 2*chipPadding) * skipConnection[1] - skipConnection[0]}px`,
                        left: `${(chipWidth + 2*chipPadding) * skipConnection[0]}px`,
                        top: `${resolution === 'small' ? '0px' : '15px'}`
                    }"
                    >
                </div>
            </template>
        </div>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as _ from 'lodash';
import ColorManager from '../vis/ColorManager';
import { regexPlateLayers } from '../util/LongestSubstringLayer';
// @ts-ignore
import SigmoidIcon from './../assets/sigmoid.svg';
// @ts-ignore
import TanhIcon from './../assets/tanh.svg';
// @ts-ignore
import ReluIcon from './../assets/relu.svg';
// import DragSelect from 'vue-drag-select/src/DragSelect.vue';
import DragSelect from './DragSelect.vue';

@Component({
    components: {
        SigmoidIcon,
        TanhIcon,
        ReluIcon,
        'drag-select-container': DragSelect
    }
})
export default class NetworkChip extends Vue {
    // public resolution: string = 'medium'; // can be small, medium, large
    // public fixedWidth: boolean = false;
    public selectedItems = [];
    public numLayers: number = 0;
    public shadowLayers: boolean = true;
    public changes = [];
    // public on = true;

    @Prop({default: 'medium'})
    public resolution!: string;

    @Prop({default: false})
    public fixedWidth!: boolean;

    @Prop({default: true})
    public showPlates!: boolean;

    // @Prop()
    // public maxSize!: number; // Used for keeping width scales consistent

    get maxSize() {
        return Math.max(...this.layersData.layers.map((l) => l.tensorSize));
    }

    @Prop()
    public logBase!: number; // Used for log scale for layer height

    @Prop({default: 'left'})
    public orientation!: string;

    @Prop({default: false})
    public legend!: boolean;

    @Prop({default: false})
    public subselectable!: boolean;

    @Prop({default: false})
    public handcraftable!: boolean;

    @Prop({default: false})
    public showSelectableActions!: boolean;

    @Prop()
    private layersData;

    private layersDataTemplate;

    private COLOR_MAPPING: ColorManager = this.$store.state.colorManager;
    private maxNumFilters: number = 1;
    private meanNumFilters: number = 1;
    private maxSubstring: string[] = [];
    private skipConnections: number[][] = [];
    private chipPadding: number = 3;
    private widthScale = d3.scalePow();
    private prevSelectedLayers = [];
    private hintMoreActionIndex = -1;
    private hintMoreActionType = 'NONE';
    private showMoreActionIndex = -1;
    private showMoreActionType = 'NONE';

    private layerActionIconMapping = {
        'prepend': 'low_priority',
        'remove': 'block',
        'replace': 'find_replace',
        'reparameterize': 'create' 
    }

    constructor() {
        super();
        this.layersDataTemplate = this.dupedModel(this.layersData);
        this.numLayers = this.layersData.layers.length;
        this.skipConnections = this.parseSkipConnections(this.layersData.layers);
        this.layersData.layers = regexPlateLayers(  this.layersData.layers,
                                                    this.layersData.layers.map((l) => this.tooltipAttrs(l)));
        const filterValues = this.layersData.layers.map((l) => l.filters).filter((f) => typeof f !== 'undefined');
        this.maxNumFilters = _.max(filterValues) as number;
        this.meanNumFilters = _.mean(filterValues) as number;
        this.widthScale.domain([16, this.maxSize]);
        this.widthScale.range([1, 2.0]);
        this.widthScale.exponent(this.logBase);
    }

    get variationOptions() {
        return this.$store.state.variationOptions[this.layersData.id]
    }

    get inspectedModelId() {
        return this.$store.getters.inspectedModel;
    }

    get chipWidth() {
        if ( this.resolution === 'small') {
            return 1;
        } else if ( this.resolution === 'large' && this.numLayers < 20 ) {
            return 26;
        } else {
            return 10;
        }
    }

    get orientationStyle() {
        if ( this.orientation === 'bottom' ) {
            return {
                display: 'grid'
            };
        } else {
            return {
                display: 'flex'
            };
        }
    }

    get sortedLayers() {
        let shownLayersData = this.handcraftable ? this.layersDataTemplate : this.layersData;
        if ( this.orientation === 'bottom') {
            return shownLayersData.layers.slice().reverse();
        } else {
            if (shownLayersData) {
                return shownLayersData.layers;
            } else {
                if (this.legend) {
                    // We have to construct a legend network chip.
                    this.layersData = {};
                    this.layersData.layers = this.COLOR_MAPPING.getColorKeys().map((layerType) => {
                        return { type: layerType };
                    });
                    return this.layersData.layers;
                } else {
                    return [];
                }
            }
        }
    }

    get selectedLayers() {
        if (this.$refs.dragSelectContainer) {
            // console.log("this.$refs.dragSelectContainer.selectedItems.map((el) => el.dataset.item); is ", this.$refs.dragSelectContainer.selectedItems.map((el) => el.dataset.item))
            return this.$refs.dragSelectContainer.selectedItems.map((el) => el.dataset.item);
        } else {
            return [];
        }
    }

    private layerModificationOptions(layer) {
        const layerType = layer.type;
        let options = ['Remove']
        this.layerOptions[layerType].forEach((hp) => {
            this.hyperparameterOptions[hp].forEach((val) => {
                options.push('Change ' + hp + ' to ' + val);
            })
        })
        return options;
    }

    get layerAddOptions() {
        return [
            'Conv2D',
            'Activation',
            'Dense',
            'AveragePooling2D',
            'Dropout',
            ]
    }

    get layerOptions() {
        return this.$store.state.layerOptions;
    }

    get hyperparameterOptions() {
        return this.$store.state.hyperparameterOptions;
    }

    private modifyLayer(layerIndex, layerModification) {
        let newLayers = this.layersDataTemplate.layers.slice();
        const layer = newLayers[layerIndex];

        const regex = /Change (\S+) to (\S+)/;
        let found = layerModification.match(regex);
        if (layerModification === 'Remove') {
            newLayers.splice(layerIndex, 1);
            this.changes.push('Removed ' + layer.type + ' at index ' + layerIndex);
        } else if (found) {
            const hp = found[1];
            const val = found[2];
            let newLayer = this.dupedModel(newLayers[layerIndex]);
            newLayer[hp] = val;
            newLayers.splice(layerIndex, 1, newLayer);
            this.changes.push(hp + ' at ' + layerIndex + ' from ' + layer[hp] + ' to ' + val)
        }

        Vue.set(this.layersDataTemplate, 'layers', newLayers);
    }

    private defaultLayerOptions = {
        'Dropout': {
            'rate': 0.25,
            'type': 'Dropout'
        },
        'AveragePooling2D': {
            'type': 'AveragePooling2D',
            'pool_size': 2
        },
        'MaxPool': {
            'type': 'MaxPool',
            'pool_size': 2
        },
        'Dense': {
            'type': 'Dense',
            'units': 32
        },
        'Conv2D': {
            'type': 'Conv2D',
            'filters': 16,
            'kernel_size': 3,
            'strides': 1
        },
        'Activation': {
            'type': 'Activation',
            'activation': 'relu'
        }
    }

    private addLayer(layerIndex, layerAdd) {
        // if (layerAdd === 'Remove') {
        const newLayer = this.defaultLayerOptions[layerAdd];
        // }
        let newLayers = this.layersDataTemplate.layers.slice();
        console.log("newLayers was ", newLayers)
        console.log("layerAdd is ", layerAdd)
        console.log("this.defaultLayerOptions is ", this.defaultLayerOptions)
        newLayers.splice(layerIndex, 0, newLayer);
        console.log("and now it is ", newLayers)
        this.changes.push('Added ' + layerAdd + ' at index ' + layerIndex);
        Vue.set(this.layersDataTemplate, 'layers', newLayers);
    }

    // Courtesy of https://stackoverflow.com/a/13542669/540675
    public shadeColor(color, percent) {
        const f = parseInt(color.slice(1), 16);
        const t = percent < 0 ? 0 : 255;
        const p = percent < 0 ? percent * -1 : percent;
        const R = f >> 16;
        const G = f >> 8 & 0x00FF;
        const B = f & 0x0000FF;

        const newColorHex = '#' +
            (0x1000000 + (Math.round((t - R) * p) + R) * 0x10000 +
                (Math.round((t - G) * p) + G) * 0x100 + (Math.round((t - B) * p) + B)).toString(16).slice(1);
        return newColorHex;
    }

    public calculatedChipStyle(layer) {
        if ( this.orientation === 'bottom' ) {
            if (this.shadowLayers) {
                return {
                    'background': this.COLOR_MAPPING.getColor(layer.type),
                    'width': `${this.widthForLayer(layer.tensorSize)}px`,
                    // 'border-left': `${(this.widthForLayer(this.layersData.maxTensorSize) -
                    //     this.widthForLayer(layer.tensorSize)) / 2.0}px
                    //     solid ${this.shadeColor(this.COLOR_MAPPING.getColor(layer.type), 0.8)}`,
                    // 'border-right': `${(this.widthForLayer(this.layersData.maxTensorSize) -
                    //     this.widthForLayer(layer.tensorSize)) / 2.0}px
                    //     solid ${this.shadeColor(this.COLOR_MAPPING.getColor(layer.type), 0.8)}`,
                    'height': `${2 * this.chipWidth}px`,
                    'padding': `${this.chipPadding}px 4px ${this.chipPadding}px 4px`
                };
            } else {
                return {
                    background: this.COLOR_MAPPING.getColor(layer.type),
                    width: `${this.widthForLayer(layer.tensorSize)}px`,
                    height: `${2 * this.chipWidth}px`,
                    padding: `${this.chipPadding}px 4px ${this.chipPadding}px 4px`
                };
            }
        } else {
            return {
                background: this.COLOR_MAPPING.getColor(layer.type),
                height: `${this.widthForLayer(layer.tensorSize)}px`,
                width: `${this.chipWidth}px`,
                padding: `4px ${this.chipPadding}px 4px ${this.chipPadding}px`
            };
        }
    }

    public chipClass(layer) {
        return {
            'network-chip-small': this.resolution === 'small',
            'network-chip-medium': this.resolution === 'medium',
            'network-chip-large': this.resolution === 'large',
            'network-chip-fixed': this.orientation !== 'bottom' && this.fixedWidth,
            'network-chip-fixed-horizontal': this.orientation === 'bottom' && this.fixedWidth,
            'network-chip': true,
            'network-chip-dropout': layer.type === 'Dropout',
            'network-chip-dropout-left': this.orientation === 'left' && layer.type === 'Dropout',
            'network-chip-dropout-bottom': this.orientation === 'bottom' && layer.type === 'Dropout'
        };
    }

    public slotAndSubselectClass(layer, layerIndex, selectedItems) {
        let isActive = false;
        if (selectedItems) {
            isActive = !!(selectedItems.find((selectedItem) => {
                if (selectedItem.$el) {
                    return ('layer-' + layerIndex + '-a') === selectedItem.$el.dataset.item;
                } else {
                    return ('layer-' + layerIndex + '-a') === selectedItem.dataset.item;
                }
            }))
        }

        // TODO - shouldn't be able to select last layer
        return {
            'network-chip-prehook': true,
            'network-chip-subselected': !this.handcraftable && isActive,
            // 'network-chip-subselectable': layerIndex !== this.layersData.length - 1
            'network-chip-subselectable': true
        }
    }

    public chipAndSubselectClass(layer, layerIndex, selectedItems) {
        const isActive = !!(selectedItems.find((selectedItem) => {
            if (selectedItem.$el) {
                return ('layer-' + layerIndex + '-b') === selectedItem.$el.dataset.item;
            } else {
                return ('layer-' + layerIndex + '-b') === selectedItem.dataset.item;
            }
        }))

        return {
            'network-chip-small': this.resolution === 'small',
            'network-chip-medium': this.resolution === 'medium',
            'network-chip-large': this.resolution === 'large',
            'network-chip-fixed': this.orientation !== 'bottom' && this.fixedWidth,
            'network-chip-fixed-horizontal': this.orientation === 'bottom' && this.fixedWidth,
            'network-chip': true,
            'network-chip-dropout': layer.type === 'Dropout',
            'network-chip-dropout-left': this.orientation === 'left' && layer.type === 'Dropout',
            'network-chip-dropout-bottom': this.orientation === 'bottom' && layer.type === 'Dropout',
            'network-chip-subselected': !this.handcraftable && isActive
            // 'network-chip-subselectable': true
        };

    }

    public plateClass(layer) {
        return {
            'network-chip-bottom-plate-visible': this.orientation === 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate,
            'network-chip-bottom-plate-visible-start': this.orientation === 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate && layer.plateStart,
            'network-chip-bottom-plate-visible-end': this.orientation === 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate && layer.plateEnd,
            'network-chip-plate-visible': this.orientation !== 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate,
            'network-chip-plate-visible-start': this.orientation !== 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate && layer.plateStart,
            'network-chip-plate-visible-end': this.orientation !== 'bottom' &&
                this.resolution !== 'large' && this.showPlates && layer.inPlate && layer.plateEnd,
            'network-chip-plate-invisible': this.resolution !== 'large' && this.showPlates && layer.plateSkipped,
            'network-chip-plate': true
            // 'network-chip-subselectable': true
        };
    }

    public tensorSizeString(width: number, height: number, depth: number) {
        return '' + width + 'x' + height + 'x' + depth;
    }

    public tooltipAttrs(layer) {
        const layersInfo: any[] = [];
        layersInfo.push({ title: 'type', value: layer.type });
        if ( !this.legend ) {
            layersInfo.push({ title: 'Tensor Size',
                value: this.tensorSizeString(layer.tensorWidth, layer.tensorHeight, layer.tensorDepth)});
            switch (layer.type) {
                case 'Conv2D':
                    layersInfo.push({ title: 'filters', value: layer.filters });
                    layersInfo.push({ title: 'kernel_size', value: layer.kernel_size });
                    layersInfo.push({ title: 'strides', value: layer.strides });
                    break;
                case 'Activation':
                    layersInfo.push({ title: 'activation', value: layer.activation });
                    break;
                case 'Dropout':
                    layersInfo.push({ title: 'rate', value: this.formatNumber(layer.rate) });
                    break;
                case 'AveragePooling2D':
                    layersInfo.push({ title: 'pool_size', value: layer.pool_size });
                    break;
                case 'Dense':
                    layersInfo.push({ title: 'units', value: layer.units});
                case 'Flatten':
                    // Right now, we don't share any info about flatten.
                    break;
            }
        }
        return layersInfo;
    }

    public deselectAll() {
        // console.log("deselectAll found, d3.select('.network-chip-subselected') is ", d3.select('.network-chip-subselected'))
        // d3.select('.network-chip-subselected').classed('.network-chip-subselected', false);
        // if (this.$refs.dragSelectContainer) {
        //     // @ts-ignore
        //     this.$refs.dragSelectContainer.selectedItems = [];
        // }
    }

    private actionExpanded(idx, variationType) {
        return this.variationOptions[idx]['variationTypes'][variationType]['optionsMousedOver']; 
    }

    private variationTypesForLayer(index) {
        // console.log("this.variationOptions is ", this.variationOptions)
        // console.log("this.variationOptions[", index, "] is ", this.variationOptions[index])
        return Object.keys(this.variationOptions[index].variationTypes)
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData));
    }

    private toggleAction(idx, variationType) {
        let options = this.dupedModel(this.variationOptions);
        options[idx]['variationTypes'][variationType]['selected'] = !options[idx]['variationTypes'][variationType]['selected'];
        if (options[idx]['variationTypes'][variationType]['selected']) {
            // want to make sure it is selected
            options[idx]['selected'] = true;
        }
        // console.log("calling toggleAction on idx ", idx, " and variationType ", variationType);
        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: options
        });
    }

    private toggleActionOptions(idx, variationType) {
        let options = this.dupedModel(this.variationOptions);
        options[idx]['variationTypes'][variationType]['optionsMousedOver'] = !options[idx]['variationTypes'][variationType]['optionsMousedOver'];
        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: options
        });
    }

    private toggleMoreAction(idx, variationType) {

    }

    private hintMoreAction(idx, variationType) {
        this.hintMoreActionIndex = idx;
        this.hintMoreActionType = variationType;
    }

    private showMoreAction(idx, variationType) {
        this.showMoreActionIndex = idx;
        this.showMoreActionType = variationType;
    }

    private actionStyle(idx, variationType) {
        // console.log("this.variationOptions is ", this.variationOptions);
        // console.log("idx is ", idx);
        // console.log("variationType is ", variationType)
        if (this.variationOptions[idx]['variationTypes'][variationType]['selected']) {
            return { color: 'seagreen' };
        } else {
            return { color: 'gray' };
        }
    }

    // widthForLayer returns the relative size of a layer
    // on a log scale based on the tensor size.
    private widthForLayer(numFilters: number | undefined): number {
        // let width = 1.0;
        // if (!this.fixedWidth && typeof numFilters !== 'undefined') {
        //     width =  (numFilters / this.maxSize) * 16.0;
        // }
        // Default width is 17px
        // return Math.sqrt(width) * 17;
        let width = 1.0;
        if (this.resolution === 'large') {
            width = 2.0;
        }
        if (!this.fixedWidth) {
            width = this.widthScale(numFilters as number);
        }

        // Default width is 17px
        return width * 17;
    }

    private formatNumber(num: number, precision: number = 3) {
        // console.log("num is ", num);
        // return num.toPrecision(precision);
        return num;
    }

    private parseSkipConnections(layersData) {
        const skipConnections: number[][] = [];
        layersData.forEach((l) => {
            if (l.skipTo) {
                l.skipTo.forEach((t) => {
                    skipConnections.push([l.id, t]);
                });
            }
        });
        return skipConnections;
    }

    @Watch('logBase')
    private onLogBaseChange(newBase, oldBase) {
        this.widthScale.exponent(newBase);
        this.$forceUpdate();
    }

    @Watch('layersData')
    private onLayersDataChange(newLayersData, oldLayersData) {
        this.deselectAll();
        this.widthScale.domain([16, this.maxSize]);
        this.restoreTemplate();
}

    public restoreTemplate() {
        this.layersDataTemplate = this.dupedModel(this.layersData);
        this.changes = [];
    }

    @Watch('handcrafted')
    private onHandcraftedChange(newHandcrafted, oldHandcrafted) {
        // if (newHandcrafted) {
        //     this.layersDataTemplate = this.dupedModel(this.layersData);
        // }
    }

    @Watch('changes')
    private onChangesChanged(newChanges, oldChanges) {
        this.$emit('handcraftedchanged', newChanges);
    }

    // @Watch('selectedLayers')
    private onSelectedLayersChanged(newSelectedLayers) {
        // console.log("network chip noticed change")
        const selectedLayerLabels = newSelectedLayers.map((l) => l.dataset.item);
        // console.log("selectedLayerLabels is ", selectedLayerLabels)
        // console.log(" and this.selectedLayers is ", this.selectedLayers);
        // console.log("selectedLayerLabels - this.selectedLayers: ", _.difference(selectedLayerLabels, this.selectedLayers))
        // console.log("this.selectedLayers - selectedLayerLabels: ", _.difference(this.selectedLayers, selectedLayerLabels))
        const addedLayers = _.difference(selectedLayerLabels, this.prevSelectedLayers);
        const removedLayers = _.difference(this.prevSelectedLayers, selectedLayerLabels);
        this.prevSelectedLayers = selectedLayerLabels;
        // Note we want to remove the final, dense layer for this application
        // this.selectedLayers = this.selectedLayers.filter((l) => l !== 'layer-' + (this.numLayers - 1) + '-b');
        // console.log("sending back this.selectedLayers: ", this.selectedLayers);
        // this.$emit('selectchange', this.selectedLayers);
        this.$emit('selectchange', { addedLayers: addedLayers, removedLayers: removedLayers });
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
.network-chip {    
    border-radius: 2px;
    font-weight: 700;
    text-align: center;
    // color: white;
    color: black;
    font-family: IBMPlexMono, Avenir;
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: content-box;
    transition-property: box-shadow, width, height;
    transition-duration: .25s;
}

.network-chip:hover {
    box-shadow:inset 0px 0px 0px 2px gray;
    filter: brightness(105%);
}

.network-chip-plate {
    display: flex;
    align-items: center;
    justify-content: center;
}

.network-chips-container {
    display: block;
    justify-content: center;
    align-items: center;
    position: relative;
}

.network-chip-div {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    position: relative;

    .v-btn {
        width: auto !important;
        height: auto !important;
        padding: 0 !important;
        margin: 0;
        min-width: 0;
    }

}

.card {
    padding: 20px;
}

.network-chip-fixed {
    min-height: 20px;
}

.network-chip-fixed-horizontal {
    min-width: 20px;
}

// .network-chip-small {
//     width: .1em;
// }

// .network-chip-medium {
//     width: 1em;
// }

// .network-chip-large {
//     width: 1em;
// }

#app .network-chip-tooltip {
    font-size: 12px;
    font-weight: 700;
    padding: 10px;
    margin-left: 10px;
    margin-bottom: 25px;
    z-index: 10000000;
}
.tooltip {
    z-index: 10000000;
}

.network-chip-plate-visible {
    border-top: 4px dotted gray;
    border-bottom: 4px dotted gray;
    height: 60px;
}

.network-chip-plate-visible-start {
    border-left: 4px dotted gray;
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
    padding: 5px 0 5px 5px;
    margin-left: 5px;
}

.network-chip-plate-visible-end {
    border-right: 4px dotted gray;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    padding: 5px 5px 5px 0;
    margin-right: 5px;
}

.network-chip-plate-invisible {
    display: none !important;
}

.network-chip-plate-number {
    position: absolute;
    top: 2px;
    left: 6px;
    font-weight: 700;
    font-size: 12px;
}

.network-chip-bottom-plate-visible {
    border-left: 4px dotted gray;
    border-right: 4px dotted gray;
    width: 60px;
}

.network-chip-bottom-plate-visible-start {
    border-bottom: 4px dotted gray;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
    padding: 0 5px 5px 5px;
    margin-bottom: 5px;
}

.network-chip-bottom-plate-visible-end {
    border-top: 4px dotted gray;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 5px 5px 0 5px;
    margin-top: 5px;
}

.network-chip-bottom-plate-invisible {
    display: none !important;
}

.network-chip-bottom-plate-number {
    position: absolute;
    top: 2px;
    left: 6px;
    font-weight: 700;
    font-size: 12px;
}

// .network-chip-dropout {
//     // opacity: 0.4;
// }

.network-chip-dropout:after {
    content:'';
    position: absolute;
}

.network-chip-dropout-left:after {
    right: 0px;
    width: 10%;
    height:90%;
    border-right: 2px dotted rgba(0,0,0,0.8)
}

.network-chip-dropout-bottom:after {
    width: 100%;
    top: 0px;
    border-bottom: 2px dotted rgba(0,0,0,0.8)
}

.skip-connections-container {
    position: absolute;
    div {
        opacity: 0.68;
        box-sizing: border-box;
        border: 2px solid black;
        height: 0px;
        padding-left: 4px;
        margin-bottom: 2px;
        position: relative;
    }
    div:after{
        content:"";
        position:absolute;
        height:0;
        width:0;
        left:100%;
        top:-4px; // need a better solution here for the arrows.
        border:4px solid transparent;
        border-left: 4px solid black;
    }
}

.network-chip-subselected {
    border-top: 3px solid black;
    border-bottom: 3px solid black;
    opacity: 0.5;
}

.network-chip-prehook {
    background: gray;
    width: 12px;
    height: 12px;
    display: inline-block;
    margin-left: -4px;
    position: relative;
}

.network-chip-prehook:after {
	left: 100%;
	top: 50%;
	border: solid transparent;
	content: " ";
	height: 0;
	width: 0;
	position: absolute;
	pointer-events: none;
    z-index: 7;
}

.network-chip-prehook:after {
	border-color: rgba(136, 183, 213, 0);
	border-left-color: gray;
	border-width: 5px;
	margin-top: -5px;
}
.network-chip-prehook:before {
	border-color: rgba(194, 225, 245, 0);
	border-left-color: gray;
	border-width: 7px;
	margin-top: -7px;
}

svg.network-chips-icon {
    height: 10px;
    width: 10px;
    stroke: black;
    path {
        stroke-width: 200;
    }
}
.layer-selectors {
    position: absolute;
    z-index: 1003;
    // top: 100px;

    .layer-options {
        position: relative;
        .layer-options-more {
            position: absolute;
            right: 0px;
            top: 0px;
            width: 8px;
            height: 8px;
            background: white;
            opacity: 0.2;
        }
    }
}

</style>