<template>
    <div class='model-axes'>
        <div class='axis-selector y-axis-selector'>
            <v-select
                v-model="yKey"
                :items="sortByOptions"
                label=""
                solo
                ></v-select>
        </div>
        <svg :width="svgWidth" :height="svgHeight" class='svgClass' ref='mySvg'>
            <circle v-for="(model, index) in modelArchs"
                :key="model.id + index"
                class="circle"
                r='2px'
                :style="{
                        stroke: (mousedOverModelId == model.id) ? 'brown' : 'steelblue',
                        'stroke-width': ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || brushedModelHash[model.id]) ? '4px' : '2px',
                        opacity: ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || selectedModel === model.id) ? 0.8 : 0.5
                    }"

                :cx="cxForModel(model)"
                :cy="cyForModel(model)"
                @mouseover="pathMouseover(model.id, $event)"
                @mouseout="selectedModel = ''"
                />
            <g ref='brush_box' class='brush'>
            </g>
        </svg>
        <div class='axis-selector x-axis-selector'>
            <v-select
                v-model="xKey"
                :items="sortByOptions"
                label=""
                solo
                ></v-select>
        </div>
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
import { BrushSelection, BrushBehavior } from 'd3';

@Component({
    components: {
        NetworkChip
    }
})
export default class ModelAxes extends Vue {
    public svgWidth: number = 700;
    public svgHeight: number = 700;
    public svgPadding: number = 80;
    public timeFormatString: string = '%Y-%m-%dT%H:%M:%S.%f';
    public maxTimestamp!: Date;
    public minTimestamp!: Date;
    public brushedXStart: number = 0;
    public brushedXEnd: number = this.svgWidth;
    public brushedYStart: number = 0;
    public brushedYEnd: number = this.svgHeight;
    public timeParser: (s: string) => (Date | null)  = d3.timeParse(this.timeFormatString);
    public brushedModelHash = {};
    public selectBrush: BrushBehavior<any> = d3.brush()
        .extent([[this.svgPadding, this.svgPadding], [this.svgWidth - 1 * this.svgPadding, this.svgHeight]])
        .on('end', this.selectionBrushed);
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
        let maxVal, minVal, diff, xScale, yScale, xAxis, yAxis;
        this.sortByOptions.forEach((option) => {
            // For each option, we want to build a scale
            maxVal = d3.max(Object.keys(this.modelArchs).map((mid) =>
                this.sortByAccessors[option](this.modelArchs[mid])));
            minVal = d3.min(Object.keys(this.modelArchs).map((mid) =>
                this.sortByAccessors[option](this.modelArchs[mid])));
            diff = maxVal - minVal;
            xScale = d3.scaleLinear()
                        .domain([minVal - 0.1 * diff, maxVal + 0.1 * diff])
                        .range([this.svgPadding, this.svgWidth - this.svgPadding]);
            yScale = d3.scaleLinear()
                        .domain([minVal - 0.1 * diff, maxVal + 0.1 * diff])
                        .range([this.svgHeight - this.svgPadding, this.svgPadding]);
            xAxis = d3.axisBottom(xScale);
            yAxis = d3.axisLeft(yScale);
            this.xScales[option] = xScale;
            this.yScales[option] = yScale;
            this.xAxes[option] = xAxis;
            this.yAxes[option] = yAxis;
        });
    }

    get visibleModels() {
        if (this.skipSingleEpochModels) {
            return this.modelArchs.filter((m) => _.uniqBy(m[this.dataKey], (e: any) => e.val).length > 1);
        } else {
            return this.modelArchs;
        }
    }

    get mousedOverModelId() {
        return this.$store.state.mousedOverModelId;
    }

    get selectedModelIdsMappings() {
        return this.$store.state.selectedModelIdsMappings;
    }

    get modelArchitectures() {
        return this.$store.state.modelArchitectures;
    }

    get xScale() {
        return this.xScales[this.xKey];
    }

    get yScale() {
        return this.yScales[this.yKey];
    }

    public mounted() {
        d3.select((this.$refs.mySvg as HTMLElement))
            .append('g')
            .attr('class', 'meaningful-axes meaningful-axes-x')
            .attr('transform', 'translate(0, ' + (this.svgHeight - this.svgPadding)  + ')')
            .call(this.xAxes[this.xKey] as any);
        d3.select((this.$refs.mySvg as HTMLElement))
            .append('g')
            .attr('class', 'meaningful-axes meaningful-axes-y')
            .attr('transform', 'translate(' + this.svgPadding + ',0)')
            .call(this.yAxes[this.yKey] as any);

        d3.select((this.$refs.mySvg as HTMLElement)).select('.brush')
            .call(this.selectBrush as any);

    }

    private selectionBrushed() {
        const s = d3.event.selection;
        if (s && s[0].length > 1) {
            const xs = [s[0][0], s[1][0]].map(this.xScale.invert, this.xScale);
            const ys = [s[0][1], s[1][1]].map(this.yScale.invert, this.yScale);
            this.brushedXStart = xs[0] as number;
            this.brushedXEnd = xs[1] as number;
            this.brushedYStart = ys[1] as number;
            this.brushedYEnd = ys[0] as number;
        } else {
            // s is null, so we kill the text box
            this.changeBrushText('');
        }
    }

    private cxForModel(model) {
        return this.xScale(this.sortByAccessors[this.xKey](model));
    }

    private cyForModel(model) {
        return this.yScale(this.sortByAccessors[this.yKey](model));
    }

    private mouseEventOffset(event: MouseEvent) {
        // Inspired by https://github.com/mattdesl/mouse-event-offset
        // Returns an offset relative to the parent element of the mouse event
        const targetElement: SVGPathElement = (event.target as SVGPathElement);
        const domRect: DOMRect = targetElement.getBoundingClientRect() as DOMRect;
        const parentRect: DOMRect = (this.$refs.mySvg as HTMLElement).getBoundingClientRect() as DOMRect;

        const offset = [ 0, 0 ];
        offset[0] = domRect.left - parentRect.left;
        offset[1] = domRect.top - parentRect.top;

        return offset;
    }

    private pathMouseover(modelId: string, event: MouseEvent) {
        this.showTooltip = true;
        const offset = this.mouseEventOffset(event);
        this.tooltipLeft = offset[0];
        this.tooltipTop = offset[1];
        this.selectedModel = modelId;
    }

    @Watch('brushedModelHash')
    private onBrushedModelHashChanged(newVal, oldVal) { this.brushModelsAdded = false; }

    @Watch('brushedXStart')
    private onBrushedXStart(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedXEnd')
    private onBrushedXEnd(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedYStart')
    private onBrushedYStart(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedYEnd')
    private onBrushedYEnd(newVal, oldVal) { this.updateBrushedModels(); }

    private updateBrushedModels() {
        const xStart = this.brushedXStart;
        const xEnd = this.brushedXEnd;
        const yStart = this.brushedYStart;
        const yEnd = this.brushedYEnd;
        let xVal, yVal;
        const modelsArray = Object.keys(this.modelArchs).map((key) => {
            return this.modelArchs[key];
        });
        const matchedModels = modelsArray.filter((m) => {
            xVal = this.sortByAccessors[this.xKey](m);
            yVal = this.sortByAccessors[this.yKey](m);
            return ((xVal >= xStart) && (xVal <= xEnd) &&
                    (yVal >= yStart) && (yVal <= yEnd));
        }).map((m) => m.id );
        this.brushedModelHash = {};
        matchedModels.forEach((m) => { this.brushedModelHash[m] = true; });

        // Think I can do some d3 magic here to put in a button that will allow the user to add the
        // new models in that selection into the model drawer.
        const numberNewModels = matchedModels.filter((m) => !this.$store.state.selectedModelIdsMappings[m]).length;

        if ( this.brushModelsAdded || numberNewModels === 0 ) {
            this.changeBrushText('No New Models');
        } else {
            this.changeBrushText('Add ' + numberNewModels + ' Models');
        }
    }

    private changeBrushText(newText: string) {
        const selectionBrush = d3.select(this.$refs.mySvg as HTMLElement).select('g.brush');
        selectionBrush.selectAll('.add-selection-button').remove();
        selectionBrush.selectAll('.add-selection-button-text').remove();

        if (newText) {
            const selectionRect = selectionBrush.select('.selection');

            selectionBrush.append('rect')
                .attr('class', 'add-selection-button')
                .attr('width', parseFloat(selectionRect.attr('width')))
                .attr('height', 30)
                .attr('x', parseFloat(selectionRect.attr('x')))
                .attr('y', selectionRect.attr('y'))
                .attr('fill', 'rgba(55.4, 0.05, 0.05, 0.25')
                .on('mousedown', this.addBrushedModels );

            const buttonText = selectionBrush.append('text')
                .attr('class', 'add-selection-button-text')
                .attr('x', parseFloat(selectionRect.attr('x')) + parseFloat(selectionRect.attr('width')) / 2.0)
                .attr('y', selectionRect.attr('y'))
                .attr('dy', 15)
                .attr('fill', 'black')
                .style('text-anchor', 'middle');

            buttonText.text(newText);
        }
    }

    private addBrushedModels() {
        this.brushModelsAdded = true;
        this.changeBrushText('Models Added');
        Object.keys(this.brushedModelHash).forEach((mid) => {
            if (this.brushedModelHash[mid]) { this.$store.commit('ADD_SELECTED_MODEL_ID', mid); }
        });
    }

    @Watch('xKey')
    private onXKeyChanged(newXKey, oldXKey) {
        d3.select((this.$refs.mySvg as HTMLElement))
            .selectAll('g.meaningful-axes-x').remove();
        d3.select((this.$refs.mySvg as HTMLElement))
            .append('g')
            .attr('class', 'meaningful-axes meaningful-axes-x')
            .attr('transform', 'translate(0, ' + (this.svgHeight - this.svgPadding)  + ')')
            .call(this.xAxes[newXKey] as any);
    }

    @Watch('yKey')
    private onYKeyChanged(newYKey, oldYKey) {
        d3.select((this.$refs.mySvg as HTMLElement))
            .selectAll('g.meaningful-axes-y').remove();
        d3.select((this.$refs.mySvg as HTMLElement))
            .append('g')
            .attr('class', 'meaningful-axes meaningful-axes-y')
            .attr('transform', 'translate(' + this.svgPadding + ',0)')
            .call(this.yAxes[newYKey] as any);
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
    .line {
        fill: none;
        stroke-width: 1.5px;
        clip-path: url(#clip);
    }
    rect, circle {
        clip-path: url(#clip);
    }

    .model-axes {
        width: 100%;

        .meaningful-axes {
            stroke: black;
            fill: none;
            path,
            line {
                fill: none;
                stroke: black;
                shape-rendering: crispEdges;
            }
            
            text {
                font-family: sans-serif;
                font-size: 11px;
                font-weight: 100;
                letter-spacing: 1px;
            }
        }

        .axis-selector {
            width: 200px;
        }

        .x-axis-selector {
            margin: auto;
        }

        .y-axis-selector {
            float: left;
            margin-top: 350px;
        }

        svg { 
            float: left;
        }
    }

    .add-selection-button {
        background: 'grey';
        border-radius: 10px;
        padding: 5px;
    }

</style>