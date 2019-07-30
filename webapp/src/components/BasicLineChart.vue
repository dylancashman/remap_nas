<script>
import { Line } from 'vue-chartjs';

export default {
  extends: Line,
  props: ['chartdata', 'options'],
  mounted() {
    this.renderYourself();
  },
  watch: {
    chartdata() {
      this.renderYourself();
    }
  },
  methods: {
    renderYourself() {
      this.renderChart(this.chartdata, this.options);
    }
  }
};
</script>

<style lang='scss' scoped>
// #line-chart {
//     height: 200px !important;
//     width: 350px !important;
// }
// .chartjs-render-monitor {
//     height: 200px !important;
//     width: 350px !important;
// }
</style>
