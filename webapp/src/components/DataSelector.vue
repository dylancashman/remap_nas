<template>
    <div class='data-selector-component'>
        <v-container
            fluid
            grid-list-md
        >
            <v-layout row wrap>
                <v-flex
                    v-for="image_class in imageClasses"
                    :key="image_class"
                    @click="removeClassClick()"
                >
                    <v-card :class='calculateCardClass(image_class)' 
                        ripple 
                        hover
                        @mouseover="onClassMouseover(image_class)"
                        @mouseout="onClassMouseout(image_class)"
                        @click.native.stop="onClassClick(image_class)"
                        >
                        {{image_class}}
                        <!-- {{$store.state.imageClassHighlighted}} -->
                        <div
                            v-for="image in imageClassExamples[image_class]"
                            class='data-selector-imgs'
                        >
                            <img 
                                v-bind:src="'data:image/png;base64,'+image.imageData" 
                                />
                            <!-- <img 
                                v-bind:src="'data:image/png;base64,'+image.imageData" 
                                @mouseover="onImageMouseover(image.id)"
                                @mouseout="onImageMouseout(image.id)"
                                @click.stop="onImageClick(image.id)"
                                :data-attribute='image.id'
                                :class="calculateImageClass(image.id)"
                                /> -->
                        </div>
                        <!-- <v-img
                            :src="card.src"
                            height="200px"
                        >
                            <v-container
                                fill-height
                                fluid
                                pa-2
                            >
                                <v-layout fill-height>
                                    <v-flex xs12 align-end flexbox>
                                        <span class="headline white--text" v-text="card.title"></span>
                                    </v-flex>
                                </v-layout>
                            </v-container>
                        </v-img> -->
                    </v-card>
                </v-flex>
            </v-layout>
        </v-container>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as axios from 'axios';
import * as Buffer from 'buffer';

@Component({
    components: {
    }
})
export default class DataSelector extends Vue {
    private imageClassExamples = {};

    constructor() {
        super();
        this.imageClasses.forEach((cl) => { this.imageClassExamples[cl] = []; });
    }

    get imageClasses() {
        return this.$store.state.datasetLabels;
    }
    get inspectedModelId() {
        return this.$store.getters.inspectedModel;
    }

    get inspectedModelData() {
        if (window['searchableModels'][this.inspectedModelId]) {
            return this.dupedModel(window['searchableModels'][this.inspectedModelId]);
        } else {
            return null;
        }
    }

    get inspectedModelConfusionMatrix() {
        return this.inspectedModelData['confusion_matrix'];
    }

    public mounted() {
        for(let i = 0; i < 10; i++) {
            this.imageClasses.forEach((imageClass) => {
                this.getRandomClassImage(imageClass);                
            });
        }
    }

    private imageClassSelected(image_class) {
        return this.$store.state.imageClassNameSelected === image_class;
    }

    private onImageMouseover(imageId) {
        this.onImageMouseout();
        this.$store.commit('HIGHLIGHT_IMAGE', imageId);
    }

    private onImageMouseout() {
        // this.$store.commit('DEHIGHLIGHT_IMAGE');
    }

    private onImageClick(imageId) {
        if (this.$store.state.imageIndexSelected === imageId) {
            this.$store.commit("DESELECT_IMAGE");
        } else {
            this.$store.commit('SELECT_IMAGE', imageId);
        }
    }

    private onClassMouseover(image_class) {
        this.$store.commit('HIGHLIGHT_LABEL', image_class);
    }

    private onClassClick(image_class) {
        if (this.$store.state.imageClassNameSelected === image_class) {
            this.$store.commit("DESELECT_LABEL");
        } else {
            this.$store.commit('SELECT_LABEL', image_class);
        }
    }
    
    private removeClassClick() {
        this.$store.commit('DESELECT_LABEL');
    }

    private getRandomClassImage(image_class) {
        let host = window.location.host;
        let path = window.location.pathname;
        // path.endsWith("/") ? window.location.pathname : window.location.pathname + "/";
        // path = path + "socket.io";

        // const url = "http://localhost:5000/get_random_class_image/" + image_class;
        // const url = "http://54.197.177.214/get_random_class_image/" + image_class;
        // const url = "http://localhost:8080/socket-io/get_random_class_image/" + image_class;
        if (path.endsWith('/')) {
            const url = path + 'get_random_class_image/' + image_class;
        } else {
            const url = path + '/get_random_class_image/' + image_class;
        }
        // const url = "http://0.0.0.0:80/get_random_class_image/" + image_class;
        return axios
            .get(url, {
                responseType: 'arraybuffer'
            })
            .then(response => {
                const imageId = response.headers['mast-image-id'];
                this.imageClassExamples[image_class].push({id: +imageId, imageData: btoa(String.fromCharCode.apply(null, new Uint8Array(response.data)))});
                // console.log("response is ", response)
                // console.log("response.data is ", response.data)
            })
    }

    private calculateCardClass(image_class) {
        return {
            'data-selector-cards': true,
            'elevation-24': !this.$store.state.imageClassHighlighted && this.imageClassSelected(image_class)
        }
    }

    private calculateImageClass(imageIdx) {
        return {
            'selectedImage': false && !this.$store.state.imageIndexHighlighted && this.$store.state.imageIndexSelected === imageIdx,
            'highlightedImage': this.$store.state.imageIndexHighlighted === imageIdx
        }
    }

    private onClassMouseout() {
        this.$store.commit('DEHIGHLIGHT_LABEL');
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData))
    }

    private getPerfData(inspectedModelId) {
        let data: any = {};

        // Have to sequential search this for now; build a data structure later
        this.$store.state.perfData.forEach((m) => {
            if (m.id === inspectedModelId) {
                data = m;
            }
        });
        return data;
    }

    @Watch('inspectedModelId')
    private onInspectedModelIdChanged(newId, oldId) {
        // console.log("forcing update, perfdata is ",this.inspectedPerfData);
        this.$forceUpdate();
    }

}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
.data-selector-cards {
    background: black;
    width: 5vw;
    .data-selector-imgs {
        padding: 1px;

        img {
            width: 100%;
        }

        .selectedImage {
            // width: 120%;
        }

        .highlightedImage {
            // width: 140%;
        }
    }
}
</style>


