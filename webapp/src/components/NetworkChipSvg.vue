<template>
    <svg class="network-chips-container" >
        <template v-for="(layer, index) in layersData.layers" >
            <g :key="`${layersData.name}--${index}`" 
                class="network-chip-div"
                >
                <rect
                    @click.native="layer.selected = !layer.selected"
                    :ref="`id-${layer.id}`"
                    :style= "{
                        fill: COLOR_MAPPING.getColor(layer.type),
                        height: `${widthForLayer(layer.filters)}em`,
                        width: `${chipWidth}em`,
                        padding: `.2em ${chipPadding}em .2em ${chipPadding}em`,
                        x: `${index * chipWidth}em`
                        }"
                    :class="chipClass(layer)">
                </rect>
            </g>
        </template>
    </svg>
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

@Component({
    components: {
        SigmoidIcon,
        TanhIcon,
        ReluIcon
    }
})
export default class NetworkChipSvg extends Vue {
    // public resolution: string = 'medium'; // can be small, medium, large
    // public fixedWidth: boolean = false;
    public numLayers: number = 0;

    @Prop({default: 'medium'})
    public resolution!: string;

    @Prop({default: false})
    public fixedWidth!: boolean;

    @Prop({default: true})
    public showPlates!: boolean;

    @Prop({default: 'bottom'})
    public baselineOrientation!: string; // Dictates where first layer goes, should replace rotation

    @Prop()
    public maxFilters!: number; // Used for keeping width scales consistent

    @Prop()
    private layersData;

    private COLOR_MAPPING: ColorManager = this.$store.state.colorManager;
    private maxNumFilters: number = 1;
    private meanNumFilters: number = 1;
    private maxSubstring: string[] = [];
    private skipConnections: number[][] = [];
    private chipPadding: number = .15;

    constructor() {
        super();
        this.numLayers = this.layersData.layers.length;
        this.skipConnections = this.parseSkipConnections(this.layersData.layers);
        this.layersData.layers = regexPlateLayers(  this.layersData.layers,
                                                    this.layersData.layers.map((l) => this.tooltipAttrs(l)));
        const filterValues = this.layersData.layers.map((l) => l.filters).filter((f) => typeof f !== 'undefined');
        this.maxNumFilters = _.max(filterValues) as number;
        this.meanNumFilters = _.mean(filterValues) as number;
    }

    get chipWidth() {
        if ( this.resolution === 'small') {
            return 0.1;
        } else {
            return 1;
        }

    }

    public chipClass(layer) {
        return {
            'network-chip-small': this.resolution === 'small',
            'network-chip-medium': this.resolution === 'medium',
            'network-chip-large': this.resolution === 'large',
            'network-chip-fixed': this.fixedWidth,
            'network-chip': true,
            'network-chip-dropout': layer.type === 'Dropout'
        };
    }

    public plateClass(layer) {
        return {
            'network-chip-plate-visible': this.resolution !== 'large' && this.showPlates && layer.inPlate,
            'network-chip-plate-visible-start': this.resolution !== 'large' && this.showPlates &&
                layer.inPlate && layer.plateStart,
            'network-chip-plate-visible-end': this.resolution !== 'large' && this.showPlates &&
                layer.inPlate && layer.plateEnd,
            'network-chip-plate-invisible': this.resolution !== 'large' && this.showPlates && layer.plateSkipped,
            'network-chip-plate': true
        };
    }

    public tooltipAttrs(layer) {
        const layersInfo: any[] = [];
        layersInfo.push({ title: 'type', value: layer.type });
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
            case 'Flatten':
                // Right now, we don't share any info about flatten.
                break;
        }
        return layersInfo;
    }

    // widthForLayer returns the relative size of a layer
    // given the number of filters.  Right now, the max
    // number of filters across all models being compared is set to be 4 times the default width,
    // and everything else is scaled accordingly.  But we use a
    // square root scale, to accomodate variation, so we multiply by 16
    // times the scale, and then square root it.
    private widthForLayer(numFilters: number | undefined): number {
        let width = 1.0;
        if (!this.fixedWidth && typeof numFilters !== 'undefined') {
            width =  (numFilters / this.maxFilters) * 16.0;
        }
        // Default width is 1.75 EM
        return Math.sqrt(width) * 1.75;
    }

    private formatNumber(num: number, precision: number = 3): string {
        return num.toPrecision(precision);
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
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
.network-chip {    
    border-radius: 2px;
    font-weight: 700;
    text-align: center;
    color: white;
    font-family: IBMPlexMono-Bold;
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
}

.card {
    padding: 20px;
}

.network-chip-fixed {
    min-height: 2em;
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
    font-size: 1.2em;
    font-weight: 700;
    padding: 10px;
    margin-left: 10px;
    margin-bottom: 25px;
}

.network-chip-plate-visible {
    border-top: 4px dotted gray;
    border-bottom: 4px dotted gray;
    height: 6em;
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
    top: 0.2em;
    left: 1.2em;
    font-weight: 700;
    font-size: 1.2em;
}

// .network-chip-dropout {
//     // opacity: 0.4;
// }

.network-chip-dropout:after {
    content:'';
    width: 10%; /*setting the width to the 100% minus your desired header's width / 2 so it will occupy the rest of your content*/
    height:90%;
    position: absolute;
    top: 0;
    right: 0px;
    border-right: 2px dotted rgba(0,0,0,0.8)
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

svg.network-chips-icon {
    height: 1em;
    width: 1em;
    stroke: black;
}
</style>