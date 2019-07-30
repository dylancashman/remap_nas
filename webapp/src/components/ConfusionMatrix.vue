<template>
   <div class="modelContainer" :style="styleObjectSelection">
       <!-- <div v-for="metric in modelMetrics" class="metrics">{{ metric }}: {{ model.modelMetrics[metric].toFixed(3) }}</div> -->
       <div :id="'tooltip_matrix_model_'+index" class="tooltip"></div>
       <svg :id="'matrix_model_'+index"></svg>
       <div id="matrixtooltip" style="opacity: 0;"></div>
   </div>
</template>

<script>
// Confusion Matrix Vue component courtesy of Subhajit Das of Georgia Tech

import * as d3 from 'd3';
import _ from 'lodash';
import store from '@/store';

export default {
  name: 'ConfusionMatrix',
//   props: ["model", "index"],
    props: {
      confusionMatrix: Array,
      metrics: Object,
      svgMargin: {
        type: Object,
        default: () => ( { top: 10, right: 10, bottom: 10, left: 10 } )
      },
      cellSize: {
        type: Object,
        default: () => ( { width: 45, height: 30 } )
      },
      fontSize: {
        default: '0.95em'
      }

    },

  data() {
    return {
      // set to true if users hovers a set of instances in this view
      hoverActive: false,
      buckets: 7,
      // colors: [ "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8" ],
      // colorsGood: [ '#f7fcb9','#d9f0a3','#addd8e','#78c679','#41ab5d','#238443' ],
      // colorsBad: [ '#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c' ],
      // colorsGood: ['#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45'],
      // colorsBad: ['#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d'],
      // colorsGood: ['#ffffbf','#e0f3f8','#abd9e9','#74add1'],
      // colorsBad: ['#f46d43','#fdae61','#fee090','#ffffbf'].reverse(),
      colorsGood: ['#ffffbf','#eff9fb','#d5ebf3','#b9d6e8'],
      colorsBad: ['#f9b6a1','#fed6af','#feefc7','#ffffbf'].reverse(),
      // colorsBad: d3.schemeRdBu[11].slice(, 3),
      // colorsGood: d3.schemeRdBu[11].slice(7, 3),
      index: 'CNN',
      model: { modelMetrics: [] },
      legendText: "The <span style='color:red;font-weight:bold;'>red</span> color scale encodes " +
                  "the number of <span style='color:red;font-weight:bold;'>incorrectly</span> " +
                  "classified items, while the <span style='color:green;font-weight:bold;'>green</span> " +
                  "green color encodes the number of <span style='color:green;font-weight:bold;'>correctly</span> " +
                  "classified ones (along the diagonal of the matrix).",
    };
  },
  mounted() {
    // this.$socket.emit("confusionMatrixData", {
    //   predictionFile: this.model.fileUri,
    //   modelId: this.model.modelId,
    // });
    this.drawMatrix();
  },
  sockets: {
    // returnConfusionMatrixData(results) {
    //   if (results.modelId === this.model.modelId) {
    //     this.modelData = results;
    //   }
    // },
  },
  watch: {
    confusionMatrix() {
      this.drawMatrix();
    },
    xLinkingHilite() {
      // console.log("HILITE", this.xLinkingHilite, this.hoverActive);
      // ignore if we are the source of this
      if (this.hoverActive) {
        return;
      }
      const vueThis = this;
      d3.select('#matrix_model_' + this.index)
        .selectAll('.matrixCell')
        .each((d) => {
          if (vueThis.setOverlap(d.set, vueThis.xLinkingHilite.set)) {
            d3.select(this).style('stroke', 'black');
          } else {
            d3.select(this).style('stroke', 'transparent');
          }
        });
    }
  },
  computed: {
      modelData() {
          const labels = [];
          for (let i = 0; i < this.confusionMatrix.length; i++) {
            labels[i] = i;
          }
          return { modelId: 'CNN', matrix: this.confusionMatrix, labels: labels };
      },
    styleObjectSelection() {
      if (this.selected) {
        return {
          border: '2px solid gray'
        };
      } else {
        return {
          border: 'none'
        };
      }
    },
    selected() {
    //   return this.$store.state.socket.selectedModel === this.model.modelId;
        return false;
    },
    xLinkingHilite() {
    //   if (this.$store.state.socket.xLinking.highlight) {
    //     var newStringArray = this.$store.state.socket.xLinking.xLinkIndexes.map(d => "" + d);
    //     return {
    //       array: newStringArray,
    //       set: new Set(newStringArray)
    //     }
    //   } else {
        return {
          array: [],
          set: new Set()
        };
    //   }
    },
    colorScaleGood() {
      return d3.scaleQuantile().domain([0, this.buckets - 1,
                                        d3.max(this.matrixCells, (d) => d.set.size)]).range(this.colorsGood);
    },
    colorScaleBad() {
      return d3.scaleQuantile().domain([0, this.buckets - 1,
                                        d3.max(this.matrixCells, (d) => d.set.size)]).range(this.colorsBad);
    },
    matrixCells() {
      if (this.confusionMatrix) {
        const cells = [];
        for (let i = 0; i < this.confusionMatrix.length; i++) {
          // i is index for gold class (column)
          for (let j = 0; j < this.confusionMatrix.length; j++) {
            cells.push({ goldLabelIndex: i, predictLabelIndex: j, set: new Set(this.confusionMatrix[i][j]) });
          }
        }
        return cells;
      } else {
        return null;
      }
    },
    itemsPerGoldClass() {
      if (this.confusionMatrix) {
        const counts = _.times(this.confusionMatrix.length, _.constant(0));
        for (let i = 0; i < this.confusionMatrix.length; i++) {
          // i is index for gold class (column)
          for (let j = 0; j < this.confusionMatrix.length; j++) {
            counts[i] = counts[i] + this.confusionMatrix[i][j].length;
          }
        }
        return counts;
      } else {
        return [];
      }
    },
    percentageCorrectPerGoldClass() {
      if (this.itemsPerGoldClass) {
        const correctPerClass = [];
        // corret ones are along the diagonal
        for (let i = 0; i < this.confusionMatrix.length; i++) {
          const correct = this.confusionMatrix[i][i].length;
          let percentage = correct / this.itemsPerGoldClass[i];
          if ( percentage === 'NaN' || isNaN(percentage) ) {
            percentage = 0;
          }
          correctPerClass.push(percentage * 100.0);
        }
        return correctPerClass;
      } else {
        return [];
      }
    },
    labelToIndex() {
      if (this.confusionMatrix) {
        const labelToIndex = new Map();
        for (let i = 0; i < this.confusionMatrix.length; i++) {
          labelToIndex.set(this.confusionMatrix[i], i);
        }
      } else {
        return null;
      }
    },
    modelMetrics() {
      const metrics = Object.keys(this.model.modelMetrics);
      metrics.sort();
      return metrics;
    },
    svgWidth() {
      if (this.modelData) {
        const numLabels = this.modelData.labels.length; // + 2;
        const wid = this.cellSize.width * numLabels;
        const width = wid + this.svgMargin.left + this.svgMargin.right;
        return width;
      }
      return 0;
    },
    svgHeight() {
      if (this.modelData) {
        const numLabels = this.modelData.labels.length + 1;
        const ht = this.cellSize.height * numLabels * 1.5 + 30;
        const height = ht - this.svgMargin.bottom;
        return height;
      }
      return 0;
    },
  },
  methods: {
    showTooltip(html, xoffset = 20, yoffset = 40) {
      const tooltip = d3.select(this.$el).select('#matrixtooltip');
      const svg = d3.select(this.$el).select('#matrix_model_' + this.index);
      tooltip.transition().duration(200).style('opacity', 1);
      const x = d3.mouse(svg.node().parentNode)[0] + xoffset;
      const y = d3.mouse(svg.node().parentNode)[1] - yoffset;
      tooltip.html(html);
      tooltip.style('left', (x) + 'px').style('top', (y) + 'px');
    },
    hideTooltip() {
      const tooltip = d3.select(this.$el).select('#matrixtooltip');
      tooltip.transition().duration(200).style('opacity', 0);
    },
    setOverlap(setA, setB) {
      const iterSet = setA.size > setB.size ? setB : setA;
      const otherSet = setA.size > setB.size ? setA : setB;
      for (const elem of iterSet) {
          if (otherSet.has(elem)) {
            return true;
          }
      }
      return false;
    },
    drawMatrix() {
      const vueThis = this;
      let svg = d3.select(vueThis.$el).select('#matrix_model_' + vueThis.index);
      svg.attr('height', vueThis.svgHeight + vueThis.svgMargin.top + vueThis.svgMargin.bottom);
      svg.attr('max-height', vueThis.svgHeight + vueThis.svgMargin.top + vueThis.svgMargin.bottom);
      svg.attr('width', vueThis.svgWidth);
      svg = svg.append('g').attr('transform', 'translate(0, ' + vueThis.svgMargin.top + ')');

      // some constants
      const vSpace = 75 * .3;
      const lastRectY = 0;
      const yRatio = 0.6;
      const textSize = 0.65;
      const legSpace = 60;

      svg.append('rect')
        .attr('x', vueThis.svgMargin.left - 90)
        .attr('y', ( -(vueThis.cellSize.height) + vSpace * 3 ) )
        .attr('width', 90)
        .attr('height', vueThis.cellSize.height * Math.sqrt(vueThis.matrixCells.length) )
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', '#efeded');
      const textX = vueThis.svgMargin.left - 70;
      const textY = ( -(vueThis.cellSize.height) + vSpace * 3 ) +
        (vueThis.cellSize.height * Math.sqrt(vueThis.matrixCells.length) / 2 );
      svg.append('g')
        .attr('transform', 'rotate(-90, ' + textX + ',' + textY + ')')
        .append('text').text('predicted')
        .attr('text-anchor', 'middle')
        .style('font-size', this.fontSize)
        .style('font-weight', 'bold')
        .attr('x', textX)
        .attr('y', textY)
        .on('mouseover', () => {
          vueThis.showTooltip('Those are the labels predicted by the respective model.');
        })
        .on('mouseout', () => {
          vueThis.hideTooltip();
        });
      const verPredLabels = svg
        .selectAll('.verPredLabel')
        .data(vueThis.modelData.labels)
        .enter()
        .append('text')
        .text((d) => d.length > 10 ? d.slice(0, 10) : d )
        .attr('x', () => vueThis.svgMargin.left - 10 )
        .attr('y', (d, i) =>
          (i * vueThis.cellSize.height) - (vueThis.cellSize.height * 0.25) + vSpace * 3
        )
        .style('text-anchor', 'end')
        .style('font-size', this.fontSize)
        .classed('verPredLabel', true)
        .on('mouseover', (d) => {
          vueThis.showTooltip('Label: ' + d);
        })
        .on('mouseout', (d) => {
          vueThis.hideTooltip();
        });
      const hTextX = vueThis.svgMargin.left + (vueThis.cellSize.width * Math.sqrt(vueThis.matrixCells.length) / 2);
      const hTextY = -vueThis.svgMargin.top + 18;
      const weirdHeightOfRect = ( vSpace * 3 ) - vueThis.cellSize.height + vueThis.svgMargin.top;
      svg.append('rect')
        .attr('x', vueThis.svgMargin.left )
        .attr('y', -vueThis.svgMargin.top)
        .attr('width', vueThis.cellSize.width * Math.sqrt(vueThis.matrixCells.length) )
        .attr('height', weirdHeightOfRect)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', '#efeded');
      svg.append('g')
        // .append('text').text('expected')
        .attr('text-anchor', 'middle')
        .style('font-size', this.fontSize)
        .style('font-weight', 'bold')
        .attr('x', hTextX)
        .attr('y', hTextY)
        .on('mouseover', () => {
          vueThis.showTooltip('Those are the correct gold-standard labels provided by the source data set.');
        })
        .on('mouseout', () => {
          vueThis.hideTooltip();
        });
      // percentage labels
      const percentageLabels = svg
        .selectAll('.percentageLabel')
        .data(vueThis.modelData.labels)
        .enter()
        .append('text')
        .text((d, i) => {
          const percentage = vueThis.percentageCorrectPerGoldClass[i];
          return (percentage / 100).toFixed(2);
        })
        .attr('x', (d, i) =>
          (i * vueThis.cellSize.width) + vueThis.cellSize.width * 0.5 + vueThis.svgMargin.left
        )
        .attr('y', vSpace * 0.85)
        .style('text-anchor', 'middle')
        .style('font-size', this.fontSize)
        .style('fill', 'green')
        .style('font-weight', 'bold')
        .classed('percentageLabel', true)
        .on('mouseover', (d, i) => {
          const percentage = vueThis.percentageCorrectPerGoldClass[i].toFixed(2) + '%';
          const label = vueThis.$store.state.datasetLabels[i];
          vueThis.showTooltip('<strong>' + percentage +
            "</strong> of the <strong>items labeled <span style='color:blue;'>" + label +
            "</span></strong> have been <strong style='color:green;'>correctly</strong> classified.");
        })
        .on('mouseout', (d, i) => {
          vueThis.hideTooltip();
        });

      const horLabels = svg
        .selectAll('.horGoldLabel')
        .data(vueThis.modelData.labels)
        .enter()
        .append('text')
        .text((d) => {
          const label = vueThis.$store.state.datasetLabels[d];
          return label.length > 4 ? label.slice(0, 4) : label;
        })
        .attr( 'x', (d, i) =>
          (i * vueThis.cellSize.width) + (vueThis.cellSize.width * 0.5) + vueThis.svgMargin.left
        )
        .attr('y', vSpace * 1.5)
        .style('text-anchor', 'middle')
        .style('font-size', this.fontSize)
        .on('mouseover', (d, i) => {
          const label = vueThis.$store.state.datasetLabels[i];
          
          vueThis.showTooltip('Label: ' + label);
        })
        .on('mouseout', (d) => {
          vueThis.hideTooltip();
        });

      const cells = svg.selectAll('.matrixCell')
        .data(vueThis.matrixCells)
        .enter()
        .append('g')
        .classed('matrixCell', true)
        .on('mouseenter', function(d, i) {
            d3.select(this).style('stroke', 'black');
            vueThis.hoverActive = true;
            const correctSpan = d.predictLabelIndex === d.goldLabelIndex ?
              "<span style='color:green;font-weight:bold;'>correctly</span>" :
                "<span style='color:red;font-weight:bold;'>incorrectly</span>";
            vueThis.showTooltip('Out of the <strong>' + vueThis.itemsPerGoldClass[d.goldLabelIndex] +
              "</strong> items labeled <span style='color:blue;font-weight:bold;'>" +
              vueThis.$store.state.datasetLabels[d.goldLabelIndex] +
              '</span> in ground truth validation data, this model ' + correctSpan +
              ' predicted <strong>' + vueThis.modelData.matrix[d.goldLabelIndex][d.predictLabelIndex].length +
              "</strong> of them as label <span style='color:blue;font-weight:bold;'>" +
              vueThis.$store.state.datasetLabels[d.predictLabelIndex] +
              '</span><br>', 20, 60);
            // do not send hover signal of there are no instances in the cell
            if (d.set.size === 0) {
              return;
            }
        })
        .on('mouseleave', function(d) {
            vueThis.hoverActive = false;
            vueThis.hideTooltip();
            d3.select(this).style('stroke', 'transparent');
        });

      cells
        .append('rect')
        .attr('x', (d) => ( d.goldLabelIndex * vueThis.cellSize.width ) + vueThis.svgMargin.left )
        .attr('y', (d) => ( ( d.predictLabelIndex - 1 ) * vueThis.cellSize.height ) + ( vSpace * 3 ) )
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('width', vueThis.cellSize.width)
        .attr('height', vueThis.cellSize.height)
        .style('fill', (d) => {
          if (d.goldLabelIndex === d.predictLabelIndex) {
            // we are on the diagonal
            return vueThis.colorScaleGood(d.set.size);
          } else {
            return vueThis.colorScaleBad(d.set.size);
          }
        });

      cells
        .append('text')
        .classed('cellLabel', true)
        .text((d) => d.set.size)
        .attr('x', (d) => ( (d.goldLabelIndex * vueThis.cellSize.width) +
          vueThis.svgMargin.left + vueThis.cellSize.width * 0.5 ))
        .attr('y', (d) => (d.predictLabelIndex - 1) * vueThis.cellSize.height +
          vSpace * 3 + vueThis.cellSize.height * 0.75 )
        .style('font-size', this.fontSize)
        .style('text-anchor', 'middle')
        .style('cursor', 'default');

      const elementData = [0].concat(vueThis.colorScaleGood.quantiles());
      const left = vueThis.svgMargin.left / 4;
      const right = (vueThis.svgWidth) - (vueThis.svgMargin.right / 4);
      const verticalSpace = right - left;
      const legendElementWidth = verticalSpace / elementData.length;
      // const legend = svg.append('g')
      //   .classed('legendGroup', true)
      //   .selectAll('.legend')
      //   .data(elementData)
      //   .enter()
      //   .append('g')
      //   .classed('legend', true)
      //   .on('mouseenter', () => vueThis.showTooltip(vueThis.legendText))
      //   .on('mouseleave', () => vueThis.hideTooltip());
      // legend.append('rect')
      //   .attr('x', (d, i) => (legendElementWidth * i) + left)
      //   .attr('y', (vSpace * 1.5) + (vueThis.cellSize.height * this.modelData.labels.length) + 40)
      //   .attr('width', legendElementWidth)
      //   .attr('height', vueThis.cellSize.height * 0.35)
      //   .style('fill', (d, i) => vueThis.colorsGood[i]);
      // legend.append('rect')
      //   .attr('x', (d, i) => (legendElementWidth * i) + left)
      //   .attr('y', (vSpace * 1.5) + (vueThis.cellSize.height * this.modelData.labels.length) +
      //     (42 + vueThis.cellSize.height * 0.35))
      //   .attr('width', legendElementWidth)
      //   .attr('height', vueThis.cellSize.height * 0.35)
      //   .style('fill', (d, i) => vueThis.colorsBad[i]);
      // legend.append('text')
      //   .text((d) => '≥' + Math.round(d))
      //   .attr('x', (d, i) => (legendElementWidth * i) + left)
      //   .attr('y', (vSpace * 1.5) + (vueThis.cellSize.height * this.modelData.labels.length) + 35)
      //   .attr('font-size', '0.8em');

    }
  }
};
</script>
<style scoped>
  svg {
    margin: 0 auto;
    display: block;
  }

  .modelContainer {
    display: flex;
    align-items: center;
    /* overflow: scroll !important; */
    width: 100%;
    /* overflow: scroll; */
    background: transparent;
  }

  /* .modelContainer:hover {
    background: #F7F7F7;
  } */

  .modelMetrics {
    position: relative;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: start;
    padding: 3px;
    border-top: 0.1px solid lightgray;
  }

  .metrics {
    font-size: 0.85em;
    color: rgb(128, 128, 128);
  }

  #matrixtooltip {
    position: absolute;
    text-align: center;
    padding: 3px;
    background: none repeat scroll 0 0 #ffffff;
    border: 1px solid #6F257F;
    pointer-events: none;
    z-index: 10000;
  }
</style>
