<template>
    <div class='scrollable-scatter' ref='myScrollableScatter'>
        <div 
            id="point-tooltip"
            v-if="highlightedCoord"
            :style="tooltipStyling"
            >
            <network-chip
                :layersData="highlightedCoord"
                :orientation="'left'"
                :resolution="'small'"
                :fixedWidth="false"
                :showPlates="false"
                :maxSize="maxWidth"
                :logBase="logBase"
            ></network-chip>
            <div class='coord-description coord-description-selected-class' v-if="isImageClassSelected">
                <div class='coord-description-label'>
                    {{imageClassNameSelected}} Val Acc
                </div>
                <div class='coord-description-value'>
                    {{formatOutput(highlightedCoord.colorScore)}}
                </div>
            </div>
            <div class='coord-description' v-for='option in sortByOptions'>
                <div class='coord-description-label'>
                    {{option}}
                </div>
                <div class='coord-description-value'>
                    {{renderMetricValue(highlightedPtData, option)}}
                </div>
            </div>
            <i></i>
        </div>
        <svg :width="svgWidth" :height="svgHeight" class='svgClass' ref='mySvg'>
            <g ref='brush_box' class='brush'>
            </g>

            <polygon :points="calculateTriangleCoords('top')" class="triangle" 
                :transform="calculateTriangleTransform('top')"
                :style="{ visibility: arrowNeeded('top') ? 'visible' : 'hidden' }"/>
            <polygon :points="calculateTriangleCoords('right')" class="triangle" 
                :transform="calculateTriangleTransform('right')" 
                :style="{ visibility: arrowNeeded('right') ? 'visible' : 'hidden' }"/>
            <polygon :points="calculateTriangleCoords('bottom')" class="triangle" 
                :transform="calculateTriangleTransform('bottom')"
                :style="{ visibility: arrowNeeded('bottom') ? 'visible' : 'hidden' }"/>
            <polygon :points="calculateTriangleCoords('left')" class="triangle" 
                :transform="calculateTriangleTransform('left')"
                :style="{ visibility: arrowNeeded('left') ? 'visible' : 'hidden' }"/>
            <g id="scrollable-scatter-container" ref="myContainer">
                <circle
                    v-for="(co, index) in coords"
                    :key="'cir-' + index"
                    v-if="initializationFinished"
                    :cx="xScale(co.x)"
                    :cy="yScale(co.y)"
                    @mouseover="onMouseOver(co, index)"
                    @mouseout="onMouseOut(co, index)"
                    @click="onMouseClick(co, index)"
                    :stroke="calculateStroke(co)"
                    :stroke-width="calculatePtStrokeWidth"
                    :fill="calculateFill(co)"
                    :r="calculatePtRadius(co, index)"
                    :class="calculateCircleClass"
                ></circle>
            </g>
            <!-- <foreignObject
                :x="zoomedXScale(co.x)"
                :y="zoomedYScale(co.y)"
                v-if="initializationFinished && !loading && (isPtClusterCenter(index))"
                v-for="(co, index) in coords"
                :key="index"
            >
                <network-chip
                    :key="'nc-' + index"
                    :layersData="co"
                    :orientation="'left'"
                    :resolution="'small'"
                    :fixedWidth="false"
                    :showPlates="false"
                    :maxSize="maxWidth"
                    :logBase="logBase"
                ></network-chip>
            </foreignObject> -->
            <g id="scrollable-scatter-minimap-container"
                v-if="initializationFinished && !loading && zoomActive && !this.yAxisLog"
                ref="minimapContainer">
                <rect
                    :x="minimapOffsetX"
                    :y="minimapOffsetY"
                    :width="minimapWidth"
                    :height="minimapHeight"
                    class="minimap-canvas"
                />
                <rect
                    :x="minimapZoomBox['x']"
                    :y="minimapZoomBox['y']"
                    :width="minimapZoomBox['width']"
                    :height="minimapZoomBox['height']"
                    stroke="gray"
                    fill="none"
                />
                <circle
                    v-for="co in coords"
                    :cx="minimapXScale(co.x)"
                    :cy="minimapYScale(co.y)"
                    r="1"
                    class="scatter-point minimap-pts"
                ></circle>
            </g>
            <g ref='myXAxis' class='scatter-x-axis'></g>
            <g ref='myYAxis' class='scatter-y-axis'></g>
        </svg>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as _ from 'lodash';
import * as math from 'mathjs';
import ColorManager from '../vis/ColorManager';
import * as d3Zoom from 'd3-zoom';
import NetworkChip from './NetworkChip.vue';
import {BrushSelection, BrushBehavior,
        ScaleLinear, ScaleTime, ScaleContinuousNumeric, ScaleOrdinal, ScaleLogarithmic,
        TimeLocaleObject,
        Axis,
        ContainerElement,
        ZoomBehavior,
        BaseType } from 'd3';

export interface ScrollableScatterCoords {
    x: number;
    y: number;
    depth?: number;
    colorScore?: number;
    glyphPtr?: string;
    parameters?: number;
}

@Component({
    components: {
        NetworkChip
    }
})
export default class ScrollableScatter extends Vue {
    // @Prop({ default: 800 })
    // Now, we set svgWidth according to the container size.
    public svgWidth: number = 350;

    // @Prop({ default: 800 })
    public svgHeight: number = 350;

    public svgPadding: number = 30;

    public minimapWidth: number = 100;

    public minimapHeight: number = 100;

    @Prop({ default: false })
    public showAxis!: boolean;

    @Prop({ default: false})
    public yAxisLog!: boolean;

    @Prop({ default: false })
    public colorCorrect!: boolean;

    @Prop({ default: [] })
    public coords: ScrollableScatterCoords[];

    public highlightedId = '';
    public highlightedCoord = null;

    public additionalCoordsData: any[] = [];

    // Scales for scatter
    public xScale;
    public yScale;
    public minimapXScale;
    public minimapYScale;
    public xAxis;
    public yAxis;
    public minimapXAxis;
    public minimapYAxis;
    public scaleFactor: number = 1.0;
    public colorScale;
    public radiusScale!: ScaleLogarithmic<number, number>;
    public interpolateGreens = d3.interpolateGreens;

    // Zoom
    public zoom = d3.zoom()
                    .scaleExtent([1, 30])
                    .on('start', () => { this.preventTransition = true; } )
                    .on('end', () => { this.preventTransition = false; } )
                    .on('zoom', this.zoomed);
    private zoomBoundariesNeeded = {
        top: false, right: false, bottom: false, left: false
    };
    private zoomBoundaries = {
        top: 0, right: this.svgWidth, bottom: this.svgHeight, left: 0
    };
    private minimapZoomBox = {
        x: 0, y: 0, width: 1, height: 1
    };
    private currZoomTransform;
    private EPSILON = 3.0;
    private MAX_CLUSTERS_SHOWN = 4;

    // Brush
    private ctrlKey = false;
    private brushRect;
    private brush;
    private idleTimeout;
    private idleDelay = 350;
    private selectedPts = [];
    private brushModelsAdded = false;

    // Flow of control variables
    private initializationFinished: boolean = false;
    private loading: boolean = false;

    // d3 selectors
    private mySvg;
    private myContainer;
    private myXAxis;
    private myYAxis;

    private preventTransition: boolean = false;

    constructor() {
        super();
    }

    get isImageClassSelected() {
        return !!this.$store.state.imageClassNameSelected;
    }

    get imageClassNameSelected() {
        return this.$store.state.imageClassNameSelected;
    }

    get maxWidth() {
        // @ts-ignore
        return this.$store.state.maxWidth;
    }

    get logBase() {
        // @ts-ignore
        return this.$store.state.logBase;
    }

    get minimapOffsetX() {
        return (this.svgWidth - this.minimapWidth);
    }

    get minimapOffsetY() {
        return 0;
    }

    get zoomActive() {
        return this.zoomBoundariesNeeded['top'] || this.zoomBoundariesNeeded['right'] ||
            this.zoomBoundariesNeeded['bottom'] || this.zoomBoundariesNeeded['left'];
    }

    get calculatePtStrokeWidth() {
        return 2.0 / this.scaleFactor;
    }

    get calculateCircleClass() {
        return {
            'scatter-point': true,
            'notransition': this.preventTransition
        }
    }

    get highlightedPtData() {
        if (window['searchableModels'][this.highlightedId]) {
            return this.dupedModel(window['searchableModels'][this.highlightedId]);
        } else {
            return null;
        }
    }

    get tooltipStyling() {
        if ( this.currZoomTransform ) {
            return {
                top: this.currZoomTransform.applyY(this.yScale(this.highlightedCoord.y)) - 10 + 'px',
                left: this.currZoomTransform.applyX(this.xScale(this.highlightedCoord.x)) + 18 + 'px',
                visibility: this.highlightedCoord ? 'visible' : 'hidden', 
                opacity: this.highlightedCoord ? 1 : 0
            }
        } else {
            return {
                top: this.yScale(this.highlightedCoord.y) - 10 + 'px',
                left: this.xScale(this.highlightedCoord.x) + 18 + 'px',
                visibility: this.highlightedCoord ? 'visible' : 'hidden', 
                opacity: this.highlightedCoord ? 1 : 0
            }
        }
    }

    get sortByOptions() {
        return this.$store.state.sortByOptions;
    }

    get valueAccessors() {
        return this.$store.state.valueAccessors;
    }

    get inspectedModel() {
        return this.$store.getters.inspectedModel;
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
            return d3.format('.3f')(out);
        } else {
            return out;
        }
    }

    public mounted() {
        this.mySvg = d3.select(this.$refs.mySvg as BaseType);
        this.myContainer = d3.select(this.$refs.myContainer as BaseType);
        this.myXAxis = d3.select(this.$refs.myXAxis as BaseType);
        this.myYAxis = d3.select(this.$refs.myYAxis as BaseType);
        this.calculateScales();

        // this.initializeBrush();
        this.initializeZoom();
        this.calculateSvgSize();
        this.reinitializeCoordsData();
        this.calculateVisibleClusters();
        this.listenForResize();
        this.initializationFinished = true;
    }

    private listenForResize() {
        window.addEventListener('resize', () => {
            this.calculateSvgSize()
        });
    }

    public zoomed() {
        if (this.showAxis) {
            this.initializeAxes();
        }
        this.myContainer.attr('transform', d3.event.transform);
        this.currZoomTransform = d3.event.transform;
        this.scaleFactor = d3.event.transform.k;
        this.calculateBoundaries(d3.event.transform);
        this.calculateMinimapBox(d3.event.transform);
        this.calculateVisibleClusters();
    }

    public zoomedXScale(xVal) {
        return (this.xScale(xVal) - this.zoomBoundaries['left'])  * this.svgWidth /
                (this.zoomBoundaries['right'] - this.zoomBoundaries['left']);
    }

    public zoomedYScale(yVal) {
        return (this.yScale(yVal) - this.zoomBoundaries['top'])  * this.svgHeight /
                (this.zoomBoundaries['bottom'] - this.zoomBoundaries['top']);
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData))
    }

    private calculateSvgSize() {
        // @ts-ignore
        this.svgWidth = this.$refs.myScrollableScatter.clientWidth;
        // Need to cap height to stop height from growing due to resizing order
        // We cap it at 30% of browser viewport height
        // @ts-ignore
        this.svgHeight = Math.min(this.$refs.myScrollableScatter.clientHeight, (window.innerHeight || 1000) * 0.3);
        this.minimapWidth = this.svgWidth * 0.25;
        this.minimapHeight = this.svgHeight * 0.25;
        this.calculateMinimapScales();
    }

    private calculateVisibleClusters() {
        // Turn off all cluster centers
        for (let i = 0; i < this.additionalCoordsData.length; i++) {
            this.additionalCoordsData[i]['clusterCenter'] = false;
        }

        // First, filter to the points still visible
        const visiblePts = this.coords.filter((co) => {
            return this.xScale(co.x) >= this.zoomBoundaries['left'] &&
                    this.xScale(co.x) <= this.zoomBoundaries['right'] &&
                    this.yScale(co.y) >= this.zoomBoundaries['top'] &&
                    this.yScale(co.y) <= this.zoomBoundaries['bottom'];
        });

        // We sort by depth, smallest first
        visiblePts.sort((el1, el2) => el1.depth - el2.depth);
        for (let i = 0; i < Math.min(this.MAX_CLUSTERS_SHOWN, visiblePts.length); i++) {
            // We turn on the cluster
            const visiblePt = visiblePts[i];
            this.additionalCoordsData[visiblePt['idx']]['clusterCenter'] = true;
        }
    }

    private calculateFill(co) {
        if (this.$store.getters.mostRecentModelIds.includes(co.uuid)) {
            return 'blue'
        } else if (co.uuid === this.inspectedModel) {
            return 'orange';
        } else if (co.uuid === this.$store.state.mousedOverModelId) {
            return 'orange';
        } else {
            // return this.interpolateGreens(this.colorScale(co.colorScore))
            // return this.interpolateGrays(this.colorScale(co.colorScore))
            return this.colorScale(co.colorScore)
        }
    }

    private calculateStroke(co) {
        if (co.uuid === this.$store.state.mousedOverModelId) {
            return 'gray'
        } else {
            return this.isPtHighlighted(co.index) ? 'black' : 'none';
        }
    }

    private calculatePtRadius(co, coordsIdx) {
        // const unnormalizedRadius = this.isPtClusterCenter(coordsIdx) ? 10 : 3;
        // if (coordsIdx === 1) {
        //     console.log(" for idx 1, unnormalizedRadius is ", unnormalizedRadius);
        // }
        let unnormalizedRadius = this.radiusScale(this.coords[coordsIdx].parameters);
        if (co.uuid === this.$store.state.mousedOverModelId) {
            unnormalizedRadius = 10;
        }
        return unnormalizedRadius / this.scaleFactor;
    }

    private highlightPt(coord, idx) {
        const coordData = this.additionalCoordsData[idx];
        coordData['highlighted'] = true;
        this.highlightedId = coord['uuid'];
        this.highlightedCoord = coord;
        this.$store.commit('SET_MOUSED_OVER_MODEL', coord.uuid);
        // console.log("highlightedCoord is ", this.highlightedCoord);
        this.additionalCoordsData.splice(idx, 1, coordData);
    }

    private dehighlightPt(coord, idx) {
        const coordData = this.additionalCoordsData[idx];
        this.$store.commit('SET_MOUSED_OVER_MODEL', "NONE");
        coordData['highlighted'] = false;
        this.highlightedId = '';
        this.highlightedCoord = null;
        this.additionalCoordsData.splice(idx, 1, coordData);
    }

    private isPtHighlighted(coordsIdx) {
        return this.additionalCoordsData[coordsIdx] && this.additionalCoordsData[coordsIdx].highlighted;
    }

    private isPtClusterCenter(coordsIdx) {
        return this.additionalCoordsData[coordsIdx] && this.additionalCoordsData[coordsIdx].clusterCenter;
    }

    private onMouseOver(coord, idx) {
        this.highlightPt(coord, idx);
        this.$emit('pointMousedOver', coord);
    }

    private onMouseOut(coord, idx) {
        this.dehighlightPt(coord, idx);
    }

    private onMouseClick(coord, idx) {
        this.$store.commit('ADD_SELECTED_MODEL_ID', coord.uuid);
        this.$store.commit('SET_CLICKED_MODEL', coord.uuid);
    }

    private calculateMinimapBox(transform) {
        this.minimapZoomBox['x'] = this.minimapXScale(this.xScale.invert(transform.invertX(0)));
        this.minimapZoomBox['y'] = this.minimapYScale(this.yScale.invert(transform.invertY(0)));
        this.minimapZoomBox['width'] = this.minimapXScale(this.xScale.invert(transform.invertX(this.svgWidth))) -
                                        this.minimapXScale(this.xScale.invert(transform.invertX(0)));
        this.minimapZoomBox['height'] = this.minimapYScale(this.yScale.invert(transform.invertY(this.svgHeight))) -
                                        this.minimapYScale(this.yScale.invert(transform.invertY(0)));
    }

    private calculateBoundaries(transform) {
        this.zoomBoundaries = {
            top: transform.invertY(0),
            right: transform.invertX(this.svgWidth),
            bottom: transform.invertY(this.svgHeight),
            left: transform.invertX(0),
        };

        this.zoomBoundariesNeeded = {
            top: !this.boundaryCloseEnough(0, (transform.invertY(0))),
            right: !this.boundaryCloseEnough(this.svgWidth, (transform.invertX(this.svgWidth))),
            bottom: !this.boundaryCloseEnough(this.svgHeight, (transform.invertY(this.svgHeight))),
            left: !this.boundaryCloseEnough(0, (transform.invertX(0))),
        };
    }

    private boundaryCloseEnough(trueBoundary, currBoundary) {
        return Math.abs(trueBoundary - currBoundary) < this.EPSILON;
    }

    private calculateTriangleCoords(loc = 'top') {
        if (loc === 'top') {
            return '0,20 20,0 40,20';
        } else if (loc === 'right') {
            return '0,0 20,20 0,40';
        } else if (loc === 'bottom') {
            return '0,0 20,20 40,0';
        } else if (loc === 'left') {
            return '20,0 0,20 20,40';
        }
    }

    private calculateTriangleTransform(loc = 'top') {
        if (loc === 'top') {
            return 'translate(' + (-10 + 0.5 * this.svgWidth) + ',0)'; // triangles are 10 pixels in radius
        } else if (loc === 'right') {
            return 'translate(' + (-20 + this.svgWidth) + ',' + (-10 + 0.5 * this.svgHeight) + ')';
        } else if (loc === 'bottom') {
            return 'translate(' + (-10 + 0.5 * this.svgWidth) + ',' + (-20 + this.svgHeight) + ')';
        } else if (loc === 'left') {
            return 'translate(0, ' + (-10 + 0.5 * this.svgHeight) + ')';
        }
    }

    private arrowNeeded(loc = 'top') {
        return this.zoomBoundariesNeeded[loc];
    }

    private initializeZoom() {
        this.mySvg.call(this.zoom);
    }

    private initializeBrush() {
        const that = this;
        this.brush = d3.brush()
        .on('start', function(d) {
            // console.log("brush started")
            // node.each(function(d) { d.previouslySelected = ctrlKey && d.selected; });
            if (!that.ctrlKey) {
                d3.select(this).call(that.brush.move, null);
                // d3.event.target.clear();
                d3.select(this).call(d3.event.target);
            }
        })
        .on('brush', function() {
            if (that.ctrlKey) {
                const selection = d3.event.selection;
                if (d3.event.selection) {
                    // for some reason, this fires one time too many, with a null
                    // selection.
                    const selectedPts = that.coords.filter((co) => {
                        if (that.currZoomTransform) {
                            return co.x >= that.xScale.invert(that.currZoomTransform.invertX(selection[0][0])) &&
                                    co.x <= that.xScale.invert(that.currZoomTransform.invertX(selection[1][0])) &&
                                    co.y >= that.yScale.invert(that.currZoomTransform.invertY(selection[0][1])) &&
                                    co.y <= that.yScale.invert(that.currZoomTransform.invertY(selection[1][1]));
                        } else {
                            return that.xScale(co.x) >= selection[0][0] &&
                                    that.xScale(co.x) <= selection[1][0] &&
                                    that.yScale(co.y) >= selection[0][1] &&
                                    that.yScale(co.y) <= selection[1][1];
                        }
                    });
                    that.selectedPts = selectedPts.map((pt) => ({ index: pt['idx'], uuid: pt['uuid'] }));
                    const numberNewModels = that.selectedPts.filter((m) =>
                        !that.$store.state.selectedModelIdsMappings[m.uuid]).length;

                    if ( that.brushModelsAdded || numberNewModels === 0 ) {
                        that.changeBrushText('No New Models');
                    } else {
                        that.changeBrushText('Add ' + numberNewModels + ' Models');
                    }
                }

                // node.classed("selected", function(d) {
                //     return d.selected = d.previouslySelected ^
                //         (extent[0][0] <= x(d.sepalWidth) && x(d.sepalWidth) < extent[1][0]
                //         && extent[0][1] <= y(d.sepalLength) && y(d.sepalLength) < extent[1][1]);
                // });
            } else {
                // d3.event.target.clear();
                d3.select(this).call(that.brush.move, null);
                d3.select(this).call(d3.event.target);
            }
        })
        .on('end', () => {
            // d3.select(this).call(that.brush.move, null);
            // d3.event.target.clear();
            // d3.select(this).call(d3.event.target);
        });
        // console.log("this.mySvg is ", this.mySvg);
        this.mySvg.select('.brush').call(this.brush);

        this.brushRect = this.mySvg.append('rect')
            .attr('class', 'brushRect')
            .attr('pointer-events', 'all')
            .attr('width', this.svgWidth)
            .attr('height', this.svgHeight)
            .style('fill', 'none');
        d3.select(window).on('keydown', () => {
            that.ctrlKey = d3.event.ctrlKey;
            if (that.ctrlKey) {
                that.brushRect = that.brushRect.attr('pointer-events', 'none');
            } else {
                that.brushRect = that.brushRect.attr('pointer-events', 'all');
            }
        });
        d3.select(window).on('keyup', () => {
            that.ctrlKey = d3.event.ctrlKey;
            if (that.ctrlKey) {
                that.brushRect = that.brushRect.attr('pointer-events', 'none');
            } else {
                that.brushRect = that.brushRect.attr('pointer-events', 'all');
            }
        });

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
        // this.brushModelsAdded = true;
        this.changeBrushText('Models Added');
        this.selectedPts.forEach((mid) => {
            const modelId = mid.uuid;
            // console.log("adding modelId", modelId, " for mid ", mid)
            if (modelId) { this.$store.commit('ADD_SELECTED_MODEL_ID', modelId); }
        });

        this.selectedPts = [];
    }

    private calculateMinimapScales() {
        this.minimapXScale = d3.scaleLinear()
                        .domain(this.xScale.domain())
                        .range([this.minimapOffsetX, this.minimapOffsetX + this.minimapWidth]);

        this.minimapYScale = d3.scaleLinear()
                        .domain(this.yScale.domain())
                        .range([this.minimapOffsetY, this.minimapOffsetY + this.minimapHeight]);
    }

    private calculateScales() {
        this.loading = true;
        // Called when coords are changed, and on constructor

        // Get domain and range for scales
        const maxX: number = +d3.max(this.coords.map((m) => m.x || 0.0)) || 1.0;
        const minX: number = +d3.min(this.coords.map((m) => m.x || 0.0)) || -1.0;
        const maxY: number = +d3.max(this.coords.map((m) => m.y || 2.0)) || 2.0;
        const minY: number = +d3.min(this.coords.map((m) => m.y || 1.0)) || 1.0;
        // const minY: number = 1.0;
        

        const xDelta: number = maxX - minX;
        const yDelta: number = maxY - minY;

        this.xScale = d3.scaleLinear()
                        .domain([minX - 0.1 * xDelta, maxX + 0.1 * xDelta])
                        .range([this.svgPadding, this.svgWidth - this.svgPadding ])
                        .nice();
        if (this.yAxisLog) {
            this.yScale = d3.scaleLog()
                            .domain([maxY, minY])
                            .range([this.svgPadding, this.svgHeight - this.svgPadding ])
                            .nice();
        } else {
            this.yScale = d3.scaleLinear()
                            .domain([maxY + 0.1 * yDelta, minY - 0.1 * yDelta])
                            .range([this.svgPadding, this.svgHeight - this.svgPadding ])
                            .nice();

        }

        this.xScale.clamp(true);
        this.yScale.clamp(true);

        this.zoom.translateExtent([[0, 0], [this.svgWidth, this.svgHeight]]);

        // Get the domain and range for color
        const maxColorVal = +d3.max(this.coords.map((m) => m.colorScore || 0.0)) || 1.0;
        const minColorVal = +d3.min(this.coords.map((m) => m.colorScore || 0.0)) || 0.0;
        // console.log("maxColorVal is ", maxColorVal, " and minColorVal is ", minColorVal);

        if (this.colorCorrect) {
            this.colorScale = d3.scaleLinear()
                            .domain([minColorVal, (minColorVal + maxColorVal) / 3.0, 2.0 * (minColorVal + maxColorVal) / 3.0, maxColorVal])
                            // .domain([0., 1.0])
                            // .range([0.25, 1]);
                            // .range([0, 1]);
                            // @ts-ignore
                            .range(['red', 'black'])
        } else {
            this.colorScale = d3.scaleLinear()
                            .domain([minColorVal, (minColorVal + maxColorVal) / 3.0, 2.0 * (minColorVal + maxColorVal) / 3.0, maxColorVal])
                            // .domain([0., 1.0])
                            // .range([0.25, 1]);
                            // .range([0, 1]);
                            // .range(['lightgray', 'black'])
                            // @ts-ignore
                            .range(['#f7f7f7','#cccccc','#969696','#525252'])

        }

        const maxParamVal = +d3.max(this.coords.map((m) => m.parameters || 0.0)) || 1.0;
        const minParamVal = +d3.min(this.coords.map((m) => m.parameters || 0.0)) || -1.0;
        this.radiusScale = d3.scaleLog()
                        .domain([minParamVal, maxParamVal])
                        // .domain([0.0, 1.0])
                        .range([3, 7]);

        if (this.showAxis) {
            this.initializeAxes()
        } else {
            this.removeAxes();
        }

        this.loading = false;
    }

    private initializeAxes() {
        this.removeAxes();
        this.xAxis = d3.axisBottom(this.xScale).ticks(5);
        this.yAxis = d3.axisLeft(this.yScale).ticks(5);
        const xSubaxis = this.myXAxis.append('g').attr('transform', 'translate(0, ' + (this.svgHeight - this.svgPadding) + ')')
            .call(this.xAxis);
        const ySubaxis = this.myYAxis.append('g').attr('transform', 'translate(' + this.svgPadding + ', 0)')
            .call(this.yAxis);
        if (this.zoomActive) {
            xSubaxis.call(this.xAxis.scale(d3.event.transform.rescaleX(this.xScale)));
            ySubaxis.call(this.yAxis.scale(d3.event.transform.rescaleY(this.yScale)));
        }
    }

    private removeAxes() {
        this.myXAxis.selectAll('*').remove();
        this.myYAxis.selectAll('*').remove();
    }

    private reinitializeCoordsData() {
        for (let i = 0; i < this.coords.length; i++) {
            if (!this.additionalCoordsData[i]) {
                this.additionalCoordsData.push({id: i});
            }
        }
    }

    private idled() {
        this.idleTimeout = null;
    }

    @Watch('coords')
    private onCoordsChanged(newCoords, oldCoords) {
        d3.select('g.scrollable-scatter-chart-axis-x').remove();
        d3.select('.scrollable-scatter-chart-axis-x-label').remove();
        d3.select('g.scrollable-scatter-chart-axis-y').remove();
        d3.select('.scrollable-scatter-chart-axis-y-label').remove();
        this.calculateScales();
        this.calculateMinimapScales();
        // We make sure we have an additionalCoordsData for each coord
        // console.log("reinitializing coords data")
        this.reinitializeCoordsData();

        this.$forceUpdate();
    }

    @Watch('svgHeight')
    private onSvgHeightChanged(newHeight, oldHeight) {
        this.calculateScales();
        this.reinitializeCoordsData();
    }

    @Watch('svgWidth')
    private onSvgWidthChanged(newWidth, oldWidth) {
        this.calculateScales();
        this.reinitializeCoordsData();
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
    .scrollable-scatter-chart-axis {
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
    .scrollable-scatter-chart {
        position: relative;
        margin: auto;
        #scrollable-scatter-chart-tooltip {
            position: absolute;
        }
    }

    .scrollable-scatter {
        position: relative;
    }

    circle {
        -webkit-transition: ease 0.3s all;
        -moz-transition: ease 0.3s all;
        -o-transition: ease 0.3s all;
        transition: ease 0.3s all;
    }

    .notransition {
        -webkit-transition: none !important;
        -moz-transition: none !important;
        -o-transition: none !important;
        transition: none !important;
    }

    .svgSelection {
        background: rgba(0.1,0.1,0.1,0.04);
        border-radius: 5px;
    }

    .zoom {
        cursor: move;
        // fill: none;
        // pointer-events: all;
        // pointer-events: none;
        // z-index: 6;
    }

    .overlay {
        pointer-events: all !important;
        fill: none;
    }

    .add-selection-button {
        background: 'grey';
        border-radius: 10px;
        padding: 5px;
    }
    
    .svgClass {
        // RGB 231, 234, 237
        // background: #e7eaed;
        background: white;
        z-index: -1;
    }

    .minimap-canvas {
        // background: #e7eaed;
        fill: #e7eaed;
        fill-opacity: 0.5;
    }

    .minimap-pts {
        fill: black;
    }

    .scatter-point {
        // fill: black;
        fill-opacity: 0.95;
    }
    
    polygon {
        fill: black;
    }

    #point-tooltip {
        position: absolute;
        // border: 3px solid black;
        // background: #e5c494;
        // background: black;
        background: white;
        visibility:hidden; opacity:0; transition:opacity 0.8s;
        // visibility:visible; opacity:1;
        border-radius:4px;
        min-width:200px;
        max-width:400px;
        z-index:99999999;
        box-sizing:border-box;
        box-shadow:0 1px 8px rgba(0,0,0,0.5);
        padding: 3px;
    }

    #point-tooltip i {
        position:absolute;
        top:10%;
        right:100%;
        margin-top:-12px;
        width:12px;
        height:24px;
        overflow:hidden;
    
    }

    #point-tooltip i::after {
        content:'';
        position:absolute;
        width:12px;
        height:12px;
        left:0;
        top:50%;
        transform:translate(50%,-50%) rotate(-45deg);
        background-color:white;
        box-shadow:0 1px 8px rgba(0,0,0,0.5);
    }

    .coord-description {
        display: flex;
    }

    .coord-description-label {
        text-align: left;
        flex: 0 0 65%;
    }

    .coord-description-value {
        text-align: right;
        flex: 1;
    }

    #scrollable-scatter-minimap-container {
        pointer-events: none;
    }

</style>