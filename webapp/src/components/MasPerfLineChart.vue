<template>
    <div class='mas-perf-line-chart'>
        <svg :width="svgWidth" :height="svgHeight" class='svgClass' ref='mySvg'>
            <template v-if="showMaxLine && perfPlotMethod === 'wall_time'">
                <g class="extreme-line">
                    <path class="line" 
                        width=4
                        :d="extremeLineConstructor(modelAggregateMeasurements)"
                        :style="{
                                stroke: 'green',
                                'stroke-width': '1px'
                            }"
                        />
                </g>
            </template>

            <template v-if="showMeanLine && perfPlotMethod === 'wall_time'">
                <g class="mean-line">
                    <path class="line" 
                        width=4
                        :d="meanLineConstructor(parseFinalValues(finalMeasurements, aggregateWindowSize))"
                        :style="{
                                stroke: 'orange',
                                'stroke-width': '2px'
                            }"
                        />
                    <rect v-for="(modelAgg, i) in parseFinalValues(finalMeasurements, aggregateWindowSize)"
                        :key = "'modelAgg' + i" 
                        class="stdevBar"
                        :x = "xScale(timeParser(modelAgg.timestamp))" 
                        :y = "yScale(modelAgg.mean + modelAgg.std)"
                        width=5
                        :height = "yScale(yScale.domain()[0] - (2 * modelAgg.std)) - svgPadding"
                        fill = 'orange'
                        opacity = 0.4
                        />
                </g>
            </template>

            <g ref='brush_box' class='brush'>
            </g>
            <g v-for="model in visibleModels" :key=model.id>
                <template v-if="(mousedOverModelId == model.id || showModelLines) && perfPlotMethod === 'wall_time'
                && (!showOnlySelected || selectedModelIdsMappings[model.id])">
                    <path class="line" 
                        width=2
                        @mouseover="pathMouseover(model.id, $event)"
                        @mouseout="selectedModel = ''"
                        @mousedown="toggleSelect(model.id)"
                        :d="lineConstructor(parseAggregateValues(model[dataKey], modelWindowSize))"
                        :style="{
                                stroke: (mousedOverModelId == model.id) ? 'brown' : 'steelblue',
                                'stroke-width': ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || brushedModelHash[model.id]) ? '4px' : '2px',
                                opacity: ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || selectedModel === model.id) ? 1.0 : 0.5
                            }"
                        />
                </template>
                <template v-else-if="perfPlotMethod === 'epoch' && (!showOnlySelected || selectedModelIdsMappings[model.id])">
                    <path class="line" 
                        width=1
                        @mouseover="pathMouseover(model.id, $event)"
                        @mouseout="selectedModel = ''"
                        :d="epochLineConstructor(model[dataKey])"
                        :style="{
                                stroke: (mousedOverModelId == model.id) ? 'brown' : 'steelblue',
                                'stroke-width': ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || brushedModelHash[model.id]) ? '4px' : '2px',
                                opacity: ((mousedOverModelId == model.id) || selectedModelIdsMappings[model.id] || selectedModel === model.id) ? 1.0 : 0.5
                            }"
                        />
                </template>
            </g>
        </svg>
        <svg :width="svgWidth" :height="svgHeight2" class='svgClass svgSelection' ref='mySelectionSvg' v-if="perfPlotMethod === 'wall_time'">
            <g class="extreme-line">
                <path class="line" 
                    width=4
                    :d="zoomMaxLineConstructor(modelAggregateMeasurements)"
                    :style="{
                            stroke: 'green',
                            'stroke-width': '1px'
                        }"
                    />
            </g>
        </svg>

        <div v-if="selectedModel && showTooltip" 
            id="mas-perf-line-chart-tooltip"
            class="model-tooltip"
            :style="{
                left: `${tooltipLeft + 20}px`, 
                top: `${tooltipTop - 50}px`
                }"
            >
            <network-chip
                :layersData=modelArchitectures[selectedModel]
                resolution='medium'
                :fixedWidth="false"
                :maxSize=$store.state.maxWidth
                :logBase=0.3
                />
        </div>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as _ from 'lodash';
import * as math from 'mathjs';
import ColorManager from '../vis/ColorManager';
import { Line } from 'd3-shape';
import { ScaleLinear, ScaleTime } from 'd3-scale';
import { TimeLocaleObject } from 'd3-time-format';
import { Axis } from 'd3-axis';
import * as d3Zoom from 'd3-zoom';
import NetworkChip from './NetworkChip.vue';
import { BrushSelection, BrushBehavior } from 'd3';

@Component({
    components: {
        NetworkChip
    }
})
export default class MasPerfLineChart extends Vue {
    public svgWidth: number = 1200;
    public svgHeight: number = 200;
    public svgHeight2: number = 1;
    public svgPadding: number = 30;
    public timeFormatString: string = '%Y-%m-%dT%H:%M:%S.%f';
    public maxTimestamp!: Date;
    public minTimestamp!: Date;
    public brushedFilterTimeStart: Date = new Date('2000-01-01');
    public brushedFilterTimeEnd: Date = new Date('3000-01-01');
    public brushedFilterEpochStart: number = 0;
    public brushedFilterEpochEnd: number = 1000000;
    public brushedFilterValStart: number = 0.0;
    public brushedFilterValEnd: number = 0.0;
    public timeParser: (s: string) => (Date | null)  = d3.timeParse(this.timeFormatString);
    public tooltipLeft: number = 100;
    public tooltipTop: number = 100;
    public showTooltip: boolean = false;
    public selectedModel: string = '';
    public modelAggregateMeasurements: any[] = [];
    public modelAggregateFinals: any[] = [];
    public finalMeasurements: any[] = [];
    public brushedModelHash = {};
    public debugi = 0;

    @Prop()
    public models!: any[];

    @Prop({default: 'valAccs'})
    public dataKey!: string;

    @Prop({default: 'wall_time'})
    public perfPlotMethod!: string;

    @Prop({default: false})
    public skipSingleEpochModels!: boolean;

    @Prop({default: 1})
    public aggregateWindowSize!: number;

    @Prop({default: 1})
    public modelWindowSize!: number;

    @Prop({default: true})
    public showMaxLine!: boolean;
    @Prop({default: true})
    public showMeanLine!: boolean;
    @Prop({default: false})
    public showModelLines!: boolean;
    @Prop({default: false})
    public showOnlySelected!: boolean;

    public lineConstructor!: Line<any>;
    public epochWallLineConstructor!: Line<any>;
    public epochLineConstructor!: Line<any>;
    public extremeLineConstructor!: Line<any>;
    public zoomMaxLineConstructor!: Line<any>;
    public meanLineConstructor!: Line<any>;
    public xScale!: ScaleTime<number, number>;
    public yScale!: ScaleLinear<number, number>;
    public zoomXScale!: ScaleTime<number, number>;
    public zoomYScale!: ScaleLinear<number, number>;
    public xAxis!: Axis<Date>;
    public yAxis!: Axis<number>;
    public zoomXAxis!: Axis<Date>;
    public epochsXScale!: ScaleLinear<number, number>;
    public epochsXAxis!: Axis<number>;
    public sortedMeasurements!: any[];
    public zoomBrush: BrushBehavior<any> = d3.brushX()
        .extent([[this.svgPadding, 0], [this.svgWidth - 1 * this.svgPadding, this.svgHeight2]]);
    public selectBrush: BrushBehavior<any> = d3.brush()
        .extent([[this.svgPadding, this.svgPadding], [this.svgWidth - 1 * this.svgPadding, this.svgHeight]])
        .on('end', this.selectionBrushed);
    public brushModelsAdded: boolean = false;

    public selectZoom = d3.zoom()
        .scaleExtent([1, Infinity])
        .translateExtent([[0, 0], [this.svgWidth, this.svgHeight]])
        .extent([[0, 0], [this.svgWidth, this.svgHeight]])
        .on('start end zoom', this.zoomed);
    private formerMouseLocation: number = -1;

    constructor() {
        super();
        this.lineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.val));

        this.epochWallLineConstructor = d3.line<any>()
            .x((d, i) => 3 * i)
            .y((d) => this.yScale(+d.val));

        this.epochLineConstructor = d3.line<any>()
            .x((d, i) => this.epochsXScale(i))
            .y((d) => this.yScale(+d.val));

        this.extremeLineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.extreme));
        this.zoomMaxLineConstructor = d3.line<any>()
            .x((d) => this.zoomXScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.zoomYScale(+d.extreme));

        this.meanLineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.mean));
    }

    get visibleModels() {
        if (this.skipSingleEpochModels) {
            return this.models.filter((m) => _.uniqBy(m[this.dataKey], (e: any) => e.val).length > 1);
        } else {
            return this.models;
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

    public mounted() {
        this.initializeMeasurements();

        this.initializeAxes();
    }

    public selectionBrushed() {
        const s = d3.event.selection;
        if (s && s[0].length > 1) {
            if (this.perfPlotMethod === 'epoch') {
                const timestamps = [s[0][0], s[1][0]].map(this.epochsXScale.invert, this.epochsXScale);
                this.brushedFilterEpochStart = timestamps[0];
                this.brushedFilterEpochEnd = timestamps[1];
            } else {
                const timestamps = [s[0][0], s[1][0]].map(this.xScale.invert, this.xScale);
                this.brushedFilterTimeStart = timestamps[0];
                this.brushedFilterTimeEnd = timestamps[1];
            }
            const accuracyBounds = [s[0][1], s[1][1]].map(this.yScale.invert, this.yScale);
            // yScale's range is reversed
            this.brushedFilterValStart = accuracyBounds[1];
            this.brushedFilterValEnd = accuracyBounds[0];
        } else {
            // s is null, so we kill the text box
            this.changeBrushText('');
        }
    }

    public initializeMeasurements() {
        // Called when dataKey is changed, and on constructor
        // Iterate through measurements in order of timestamp
        const sortedMeasurements = _.flatten(this.models.map((m) => m[this.dataKey])).sort((a, b) => {
            return +new Date(a.timestamp) - +new Date(b.timestamp);
        });

        this.sortedMeasurements = _.flatten(this.models.map((m) => m[this.dataKey])).sort((a, b) => {
            return +new Date(a.timestamp) - +new Date(b.timestamp);
        });

        // Get Final measurement and timestamp for each model
        this.finalMeasurements = this.models.map((m) => {
            const best = _.maxBy(m[this.dataKey], (e: any) => +e.val);
            if (!best) {
                return false;
            } else {
                return { timestamp: best.timestamp, val: +best.val };
            }
        }).filter((n) => true) as any[];

        this.modelAggregateMeasurements = this.parseAggregateValues(sortedMeasurements, this.aggregateWindowSize);
        this.modelAggregateFinals = this.parseFinalValues(this.finalMeasurements, this.aggregateWindowSize);

        // Get domain and range for scales
        const maxTimestamp: string = d3.max(_.flatten(this.models.map((m) => m[this.dataKey])), (l) => l.timestamp);
        const minTimestamp: string = d3.min(_.flatten(this.models.map((m) => m[this.dataKey])), (l) => l.timestamp);
        const maxVal: number = +d3.max(_.flatten(this.models.map((m) => m[this.dataKey])), (l) => l.val);
        const minVal: number = +d3.min(_.flatten(this.models.map((m) => m[this.dataKey])), (l) => l.val);
        const maxEpochs: number = d3.max(this.models.map((m) => m[this.dataKey].length));

        this.xScale = d3.scaleTime()
                        .domain([this.timeParser(minTimestamp) as Date, this.timeParser(maxTimestamp) as Date])
                        .range([this.svgPadding, this.svgWidth - this.svgPadding ]);

        if ( maxVal < 1.0 ) {
            this.yScale = d3.scaleLinear()
                            .domain([1.0, 0.0])
                            .range([this.svgPadding, this.svgHeight - this.svgPadding ]);
        } else {
            this.yScale = d3.scaleLinear()
                            .domain([1.2 * maxVal, 0.8 * minVal])
                            .range([this.svgPadding, this.svgHeight - this.svgPadding ]);
        }
        this.zoomXScale = d3.scaleTime()
                        .domain([this.timeParser(minTimestamp) as Date, this.timeParser(maxTimestamp) as Date])
                        .range([this.svgPadding, this.svgWidth - this.svgPadding ]);

        this.zoomYScale = d3.scaleLinear()
                        .domain([1.0, 0.0])
                        .range([this.svgPadding, this.svgHeight2 - this.svgPadding ]);

        this.epochsXScale = d3.scaleLinear()
                        .domain([0, maxEpochs - 1])
                        .range([this.svgPadding, this.svgWidth - this.svgPadding ]);

        this.xAxis = d3.axisBottom(this.xScale) as Axis<Date>;
        this.yAxis = d3.axisLeft(this.yScale) as Axis<number>;
        this.zoomXAxis = d3.axisBottom(this.zoomXScale) as Axis<Date>;
        this.epochsXAxis = d3.axisBottom(this.epochsXScale) as Axis<number>;
        this.epochsXAxis.tickFormat(d3.format('d'));

        this.lineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.val));

        this.epochWallLineConstructor = d3.line<any>()
            .x((d, i) => 3 * i)
            .y((d) => this.yScale(+d.val));

        this.epochLineConstructor = d3.line<any>()
            .x((d, i) => this.epochsXScale(i))
            .y((d) => this.yScale(+d.val));

        this.extremeLineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.extreme));
        this.zoomMaxLineConstructor = d3.line<any>()
            .x((d) => this.zoomXScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.zoomYScale(+d.extreme));

        this.meanLineConstructor = d3.line<any>()
            .x((d) => this.xScale(this.timeParser(d.timestamp) as Date))
            .y((d) => this.yScale(+d.mean));
    }

    private initializeAxes() {
        if (this.perfPlotMethod === 'epoch') {
            d3.select((this.$refs.mySvg as HTMLElement))
                .append('g')
                .attr('class', 'mas-perf-line-chart-axis mas-perf-line-chart-axis-x')
                .attr('transform', 'translate(0, ' + (this.svgHeight - this.svgPadding)  + ')')
                .call(this.epochsXAxis as any);

            // text label for the x axis
            d3.select((this.$refs.mySvg as HTMLElement)).append('text')
                .attr('transform',
                        'translate(' + (this.svgWidth / 2) + ' ,' +
                                    (this.svgHeight - 10) + ')')
                .attr('class', 'mas-perf-line-chart-axis-x-label')
                .style('text-anchor', 'middle')
                .text('# of Epochs');
        } else {
            d3.select((this.$refs.mySvg as HTMLElement))
                .append('g')
                .attr('class', 'mas-perf-line-chart-axis mas-perf-line-chart-axis-x')
                .attr('transform', 'translate(0, ' + (this.svgHeight - this.svgPadding)  + ')')
                .call(this.xAxis as any);

            // text label for the x axis
            d3.select((this.$refs.mySvg as HTMLElement)).append('text')
                .attr('transform',
                        'translate(' + (this.svgWidth / 2) + ' ,' +
                                    (this.svgHeight - 10) + ')')
                .attr('class', 'mas-perf-line-chart-axis-x-label')
                .style('text-anchor', 'middle')
                .text('Wall Time');
        }
        d3.select((this.$refs.mySvg as HTMLElement))
            .append('g')
            .attr('class', 'mas-perf-line-chart-axis mas-perf-line-chart-axis-y')
            .attr('transform', 'translate(' + this.svgPadding + ',0)')
            .call(this.yAxis as any);

        d3.select((this.$refs.mySvg as HTMLElement)).append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0)
            .attr('x', 0 - (this.svgHeight / 2))
            .attr('dy', '1em')
            .attr('class', 'mas-perf-line-chart-axis-y-label')
            .style('text-anchor', 'middle')
            .text(this.dataKey);

        d3.select((this.$refs.mySelectionSvg as HTMLElement))
            .append('g')
            .attr('class', 'mas-perf-line-chart-axis')
            .attr('transform', 'translate(0, ' + (this.svgHeight2 - this.svgPadding) + ')')
            .call(this.zoomXAxis as any);

        // I don't remember what this clipPath does, and it's breaking the other SVGs...
        // d3.select((this.$refs.mySvg as HTMLElement)).append('defs').append('clipPath')
        //     .attr('id', 'clip')
        //     .append('rect')
        //         .attr('transform', 'translate(' + (this.svgPadding + 3) + ',' + (this.svgPadding + 3) + ')')
        //         .attr('width', this.svgWidth - 2 * this.svgPadding - 6)
        //         .attr('height', this.svgHeight - 2 * this.svgPadding - 6);

        d3.select((this.$refs.mySelectionSvg as HTMLElement)).append('g')
            .attr('class', 'brush')
            .call(this.zoomBrush as any)
            .call(this.zoomBrush.move as any, this.xScale.range());

        d3.select((this.$refs.mySelectionSvg as HTMLElement)).append('rect')
            .attr('class', 'zoom')
            .attr('width', this.svgWidth - 2 * this.svgPadding)
            .attr('height', this.svgHeight2)
            .attr('transform', 'translate(' + this.svgPadding + ',0)')
            .call(this.selectZoom as any);

        d3.select((this.$refs.mySvg as HTMLElement)).select('.brush')
            .call(this.selectBrush as any);
    }

    private zoomed() {
        // Based on https://bl.ocks.org/mbostock/34f08d5e11952a80609169b7917d4172
        const t = d3.event.transform;
        if (d3.event.sourceEvent && d3.event.sourceEvent.type === 'mousedown') {
            this.formerMouseLocation = d3.event.sourceEvent && d3.event.sourceEvent.offsetX;
        } else if (d3.event.sourceEvent && d3.event.sourceEvent.type === 'mouseup') {
            this.formerMouseLocation = -1;
        } else if (d3.event.sourceEvent && d3.event.sourceEvent.type === 'mousemove') {
            if (this.formerMouseLocation && this.formerMouseLocation > 0) {
                const deltaX = d3.event.sourceEvent.offsetX - this.formerMouseLocation;
                const brush = d3.select((this.$refs.mySelectionSvg as HTMLElement))
                    .select('.selection');
                const xStart = +brush.attr('x');
                const width = +brush.attr('width');
                const newDomain = [this.zoomXScale.invert(xStart + deltaX),
                                    this.zoomXScale.invert(xStart + deltaX + width)];
                this.xScale.domain(newDomain);
                this.formerMouseLocation = this.formerMouseLocation + deltaX;
                d3.select((this.$refs.mySvg as HTMLElement))
                    .select('.mas-perf-line-chart-axis-x')
                    .call(this.xAxis as any);
                d3.select((this.$refs.mySelectionSvg as HTMLElement))
                    .select('.brush')
                    .call((this.zoomBrush as any).move, [xStart + deltaX, xStart + deltaX + width]);
            }
        } else {
            this.xScale.domain(t.rescaleX(this.zoomXScale).domain());

            const zoomSelectionHandle = d3.select((this.$refs.mySelectionSvg as HTMLElement))
                .select('.selection');

            d3.select((this.$refs.mySvg as HTMLElement))
                .select('.mas-perf-line-chart-axis-x')
                .call(this.xAxis as any);
            const invertRange = [this.xScale.range()[0], this.xScale.range()[1]];
            const invertResult = [(invertRange.map(t.invertX, t)[0] as number),
                                    (invertRange.map(t.invertX, t)[1] as number)];
            d3.select((this.$refs.mySelectionSvg as HTMLElement))
                .select('.brush')
                .call((this.zoomBrush as any).move, invertResult);
        }
        this.$forceUpdate();
    }

    private pathMouseover(modelId: string, event: MouseEvent) {
        this.showTooltip = true;
        const offset = this.mouseEventOffset(event);
        this.tooltipLeft = offset[0];
        this.tooltipTop = offset[1];
        this.selectedModel = modelId;
    }

    private toggleSelect(modelId: string) {
        if ( this.$store.state.selectedModelIdsMappings[modelId] ) {
            this.$store.commit('REMOVE_SELECTED_MODEL_ID', modelId);
        } else {
            this.$store.commit('ADD_SELECTED_MODEL_ID', modelId);
        }
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

    // parseFinalValues is similar to parseAggregateValues, but instead of running the
    // sliding window over all measurements, we run it over models, where each model
    // is represented by their Final measurement and the timestamp of that measurement.
    private parseFinalValues(finalMeasurements: any[], windowSize) {
        const slidingWindow = new Array(windowSize);
        let newMeasurement;
        let newAggregate;
        let extremeValue = 0;
        const extremeId = '';
        const modelFinalMeasurements: any[] = [];

        // Iterate through measurements in order of timestamp
        const sortedMeasurements = _.flatten(finalMeasurements).sort((a, b) => {
            return +new Date(a.timestamp) - +new Date(b.timestamp);
        });

        for (newMeasurement of sortedMeasurements) {
            if (!newMeasurement.val) {
                // We have an illformed model, so we skip it
                continue;
            }

            slidingWindow.shift();

            slidingWindow[windowSize - 1] = {
                                    timestamp: newMeasurement.timestamp,
                                    val: +newMeasurement.val
                                };
            newAggregate = {};
            newAggregate.timestamp = newMeasurement.timestamp;

            // Calculate the mean and std of the window, only if the window is full
            if (!slidingWindow[0]) {
                continue;
            } else {
                newAggregate.mean = math.mean(slidingWindow.map((m) => +m.val).filter((n) => true));
                newAggregate.std = math.std(slidingWindow.map((m) => +m.val).filter((n) => true));
            }

            // Calculate the extreme if it exists
            if (extremeValue < +slidingWindow[windowSize - 1].val) {
                extremeValue = +slidingWindow[windowSize - 1].val;
                // extremeId = slidingWindow[this.runningAverageWindowSize - 1].id;
            }
            newAggregate.extreme = extremeValue;
            // newAggregate['extremeId'] = extremeId;

            modelFinalMeasurements.push(newAggregate);
        }

        return modelFinalMeasurements;
    }

    // parseAggregateValues scans through the models this component is initialized with,
    // keeping track of the best trained model over time.
    // It should keep track of the max, the running average, and the running std.
    //
    // Right now, we keep track of these values by sorting all measurements by timestamp
    private parseAggregateValues(sortedMeasurements, windowSize) {
        const slidingWindow = new Array(windowSize);
        let newMeasurement;
        let newAggregate;
        const minNum = 0;
        const maxNum = Number.MAX_SAFE_INTEGER;
        let extremeValue: number = 0;
        const extremeId = '';
        const modelAggregateMeasurements: any[] = [];

        for (newMeasurement of sortedMeasurements) {
            if (!newMeasurement.val) {
                // We have an illformed model, so we skip it
                continue;
            }

            slidingWindow.shift();

            slidingWindow[windowSize - 1] = {
                                    timestamp: newMeasurement.timestamp,
                                    val: +newMeasurement.val
                                };
            newAggregate = {};
            newAggregate.timestamp = newMeasurement.timestamp;
            // Calculate the mean and std of the window, only if the window is full
            if (!slidingWindow[0]) {
                continue;
            } else {
                newAggregate.mean = math.mean(slidingWindow.map((m) => +m.val).filter((n) => true));
                newAggregate.std = math.std(slidingWindow.map((m) => +m.val).filter((n) => true));
                newAggregate.val = newAggregate.mean;
            }

            // Calculate the extreme if it exists
            if (this.dataKey === 'loss') {
                if (!extremeValue) {
                    extremeValue = maxNum;
                }
                // want the minimum
                if (extremeValue > +slidingWindow[windowSize - 1].val) {
                    extremeValue = +slidingWindow[windowSize - 1].val;
                }
            } else {
                if (!extremeValue) {
                    extremeValue = minNum;
                }
                // want the maximum
                if (extremeValue < +slidingWindow[windowSize - 1].val) {
                    extremeValue = +slidingWindow[windowSize - 1].val;
                }
            }
            newAggregate.extreme = extremeValue;
            modelAggregateMeasurements.push(newAggregate);
        }
        return modelAggregateMeasurements;
    }

    @Watch('perfPlotMethod')
    private onPerfPlotMethodChange(newMethod, oldMethod) {
        d3.select('g.mas-perf-line-chart-axis-x').remove();
        d3.select('.mas-perf-line-chart-axis-x-label').remove();
        d3.select('g.mas-perf-line-chart-axis-y').remove();
        d3.select('.mas-perf-line-chart-axis-y-label').remove();

        setTimeout(this.initializeAxes, 500);
    }

    @Watch('dataKey')
    private onDataKeyChanged(newDataKey, oldDataKey) {
        d3.select('g.mas-perf-line-chart-axis-x').remove();
        d3.select('.mas-perf-line-chart-axis-x-label').remove();
        d3.select('g.mas-perf-line-chart-axis-y').remove();
        d3.select('.mas-perf-line-chart-axis-y-label').remove();
        this.initializeMeasurements();
        this.initializeAxes();
        this.$forceUpdate();
    }

    @Watch('brushedModelHash')
    private onBrushedModelHashChanged(newVal, oldVal) { this.brushModelsAdded = false; }

    @Watch('brushedFilterTimeStart')
    private onBrushedFilterTimeStart(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedFilterTimeEnd')
    private onBrushedFilterTimeEnd(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedFilterEpochStart')
    private onBrushedFilterEpochStart(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedFilterEpochEnd')
    private onBrushedFilterEpochEnd(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedFilterValStart')
    private onBrushedFilterValStart(newVal, oldVal) { this.updateBrushedModels(); }
    @Watch('brushedFilterValEnd')
    private onBrushedFilterValEnd(newVal, oldVal) { this.updateBrushedModels(); }

    private updateBrushedModels() {
        const timeStart = this.brushedFilterTimeStart;
        const timeEnd = this.brushedFilterTimeEnd;
        const epochStart = this.brushedFilterEpochStart;
        const epochEnd = this.brushedFilterEpochEnd;
        const metricStart = this.brushedFilterValStart;
        const metricEnd = this.brushedFilterValEnd;
        const matchedModels = this.visibleModels.filter((m) => {
            const measurements = m[this.dataKey];
            return measurements.some((measurement, idx) => {
                if (this.perfPlotMethod === 'epoch') {
                    return ((idx >= epochStart) && (idx <= epochEnd) &&
                            (measurement.val >= metricStart) && (measurement.val <= metricEnd));
                } else {
                    const time = new Date(measurement.timestamp);
                    return ((time >= timeStart) && (time <= timeEnd) &&
                            (measurement.val >= metricStart) && (measurement.val <= metricEnd));
                }
            });
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
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
.mas-perf-line-chart {
    .line {
        fill: none;
        stroke-width: 1.5px;
        clip-path: url(#clip);
    }
    rect, circle {
        clip-path: url(#clip);
    }
    .mas-perf-line-chart-axis {
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
    .mas-perf-line-chart {
        position: relative;
        margin: auto;
        #mas-perf-line-chart-tooltip {
            position: absolute;
        }
    }

    .svgSelection {
        background: rgba(0.1,0.1,0.1,0.04);
        border-radius: 5px;
    }

    .zoom {
        cursor: move;
        fill: none;
        pointer-events: all;
        // pointer-events: none;
        z-index: 6;
    }

    .brush {
        
    }

    .overlay {
        pointer-events: all !important;
    }

    .add-selection-button {
        background: 'grey';
        border-radius: 10px;
        padding: 5px;
    }
    
    .svgClass {
        background: white;
    }
}
</style>