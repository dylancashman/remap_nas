<template>
    <div class='model-ablation-component'>
        <div class='model-parent-floater'
            v-if='parentModelData'
            @click="clickedParent()"
        >
            <v-container
                fluid
                grid-list-md
            >  
                <v-layout row>
                    <h2>Parent</h2>
                </v-layout>
                <v-layout row>
                    <v-flex xs12>
                        <div class='model-parent-chip'>
                            <network-chip
                                :layersData="parentModelData"
                                :orientation="'left'"
                                :resolution="'small'"
                                :fixedWidth="false"
                                :showPlates="false"
                                :maxSize="maxSize"
                                :logBase="logBase"
                                :subselectable="false"
                                :handcraftable="false"
                                :showSelectableActions="false"
                                ref='myParentNetworkChip'
                            />            
                        </div>
                    </v-flex>
                </v-layout>
            </v-container>
        </div>
        <div class='model-ablation-control-floater'
            v-if='inspectedModelData'
        >
            <v-card flat>
                <v-radio-group v-model="ablationType" column>
                    <v-radio label="Ablations" value="Ablation"></v-radio>
                    <v-radio label="Variations" value="Variation"></v-radio>
                    <v-radio label="Handcrafted" value="Handcrafted"></v-radio>
                </v-radio-group>
            </v-card>
        </div>
        <v-container
            fluid
            grid-list-md
            v-if='inspectedModelData'
        >  
            <v-layout row>
                <v-flex xs12 :style="{'padding-bottom': parentModelData ? '90px' : '40px'}">
                    <network-chip
                        :layersData="inspectedModelData"
                        :orientation="'left'"
                        :resolution="'large'"
                        :fixedWidth="false"
                        :showPlates="false"
                        :maxSize="maxSize"
                        :logBase="logBase"
                        :subselectable="ablations || variations"
                        :handcraftable="handcrafted"
                        :showSelectableActions="variations"
                        @selectchange="onSelectedLayersChanged"
                        @handcraftedchanged="onHandcraftChanges"
                        ref='myNetworkChip'
                    />
                </v-flex>
            </v-layout>
            <v-layout row v-if='variations'>
                <v-flex xs4>
                    <v-layout row>
                        <v-flex xs12>
                            <v-slider
                                v-model="numGenerated"
                                thumb-label
                                label="Number of Models to Generate"
                                :max="20"
                                :min="1"
                                >
                                </v-slider>
                        </v-flex>
                    </v-layout>
                    <v-layout row>
                        <v-flex xs12>
                            <v-slider
                                v-model="numChanges"
                                thumb-label
                                label="Number of Changes per Variation"
                                :max="5"
                                :min="1"
                                >
                            </v-slider>
                        </v-flex>
                    </v-layout>
                </v-flex>
            </v-layout>
            <v-layout row v-if='handcrafted'>
                <v-flex xs12>
                    <v-layout row>
                        <v-flex xs4>
                            <h2>Changes</h2>
                            <v-icon @click="restoreHandcraftedTemplate()" 
                                class='option-icon'
                                :title="'Restore Template'"
                            > 
                                refresh
                            </v-icon>

                            <ul>
                                <li v-for="change in handcraftedChanges" style='float: left'>
                                    {{change}}
                                </li>
                            </ul>
                        </v-flex>
                    </v-layout>
                </v-flex>
            </v-layout>
            <v-layout row>
                <v-flex xs12 v-if="variations || ablations">
                    <v-btn color="gray"
                        dark 
                        @click="generateAblations"
                        v-if='generateButtonNeeded'
                    >Generate {{term}}</v-btn>
                    <v-btn color="gray"
                        dark
                        v-else
                        disabled
                        >Ablations Generated</v-btn>
                </v-flex>
                <v-flex xs12 v-else>
                    <v-btn color="gray"
                        dark 
                        @click="generateAblations"
                        v-if='generateButtonNeeded'
                    >Spawn Model</v-btn>
                    <v-btn color="gray"
                        dark
                        v-else
                        disabled
                    >Model Spawned</v-btn>
                </v-flex>
            </v-layout>
            <v-layout row>
                <v-flex xs12>
                    <h3>
                        Child Models
                    </h3>
                    <!-- <model-drawer-v2
                        :selectedModelIds="childIds"
                        :clearable="false"
                        :mini="true"
                        ref="modelDrawer"
                        :legend="false"
                    /> -->
                    <model-queue
                        :mini="true"
                    />
                </v-flex>
            </v-layout>
            <v-layout row>
                <v-flex xs4>
                    <div class='ablation-message' v-if='variations'>
                        <template v-if='anySelection'>
                            <v-flex xs12>
                                <!-- Generate 
                                <span class='ablation-number'>{{numGenerated}}</span>
                                variations with up to
                                <span class='ablation-number'>{{numChanges}}</span>
                                changes in each model, along the following layers: -->
                                <ul class='layer-list'>
                                    <li v-for="(variation, idx) in variationOptions"
                                    >
                                        <div class='layer-selectors'>
                                            <div class='layer-label'
                                                :style="layerOptionsStyle(variation.layerType)"
                                            >
                                                {{variation.layerType}}
                                            </div>
                                            <div class="layer-options" 
                                                v-for="variationType in Object.keys(variation.variationTypes)"
                                                >
                                                <v-icon @click="toggleAction(idx, variationType)" 
                                                    class='option-icon'
                                                    :title="variationType" 
                                                    :style="actionStyle(idx, variationType)">
                                                    {{layerActionIconMapping[variationType]}}
                                                </v-icon>
                                                    <!-- @mouseout="hideActionOptions(idx)"

                                                    @mouseover="showActionOptions(idx, variationType)" -->
                                                <v-icon 
                                                    small
                                                    @click="toggleActionOptions(idx, variationType)"
                                                    class='dropdown-icon'
                                                    v-if="variationType !== 'remove'"
                                                    >
                                                    {{actionExpanded(idx, variationType) ? 'expand_less' : 'expand_more'}}
                                                </v-icon>
                                            </div>
                                        </div>
                                        <div class='layer-choices'>
                                            <v-layout row wrap>

                                                <v-flex xs12
                                                    v-if="actionExpanded(idx, 'replace') || actionExpanded(idx, 'prepend')"
                                                    v-for="validAction in Object.keys(validActionExpandRows(idx))"
                                                >   
                                                    <v-layout row>
                                                        <v-flex xs4>
                                                            <v-checkbox :label="validAction"/>
                                                        </v-flex>
                                                        <v-flex xs8 v-if="validActionExpandRows(idx)">
                                                            <v-select
                                                                @change="checkedActionsExpandedRows"
                                                                :items="Object.keys(validActionExpandRows(idx)[validAction]['options'])"
                                                                attach
                                                                chips
                                                                :label="'test'"
                                                                multiple
                                                            ></v-select>
                                                        </v-flex>

                                                    </v-layout>
                                                </v-flex>
                                                <v-flex xs12
                                                    v-if="actionExpanded(idx, 'reparameterize')"
                                                >
                                                    reparameterize
                                                </v-flex>
                                            </v-layout>
                                        </div>
                                    </li>
                                </ul>
                            </v-flex>
                            <v-flex xs12>
                                <v-btn color="red" @click="clearSelection">Clear Selection</v-btn>
                            </v-flex>
                        </template>
                        <!-- <template v-else>
                            Generate 
                            <span class='ablation-number'>{{numGenerated}}</span>
                            variations along the entire model, with up to
                            <span class='ablation-number'>{{numChanges}}</span>
                            changes in each model.
                        </template> -->
                    </div>
                    <div class='ablation-message' v-else>
                        <template v-if='anySelection'>
                            <v-flex xs12>
                                Generate ablations along the following layers:
                                <ul>
                                    <li v-for="layer in selectedLayers">
                                        {{layer}}
                                    </li>
                                </ul>
                            </v-flex>
                            <v-flex xs12>
                                <v-btn color="red" @click="clearSelection">Clear Selection</v-btn>
                            </v-flex>
                        </template>
                        <template v-else>
                            <!-- Generate ablations for each layer in the model. -->
                        </template>
                    </div>
                </v-flex>
            </v-layout>
        </v-container>
        <v-card v-else>
            Please select a card from the model drawer first.
        </v-card>
    </div>
</template>

<script lang="ts">
                                                                        // <!-- v-for="Object.keys(validActionExpandRows(idx)[validAction])" -->
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import * as axios from 'axios';
import NetworkChip from './NetworkChip.vue';
import ModelDrawerV2 from './ModelDrawerV2.vue';
import ModelQueue from './ModelQueue.vue';
import ColorManager from '../vis/ColorManager';

// export interface QueuedModel {
//     layersData: any[];
//     params: number;
//     estimated_training: number;
//     recency: number;
//     isTraining: false;
// }

@Component({
    components: {
        NetworkChip,
        ModelDrawerV2,
        ModelQueue
    }
})
export default class ModelAblation extends Vue {
    // private selectedLayers = [];
    private numGenerated = 5;
    private numChanges = 3;
    private ablationsGenerated = false;
    private selectedLayerData = [];
    private COLOR_MAPPING: ColorManager = this.$store.state.colorManager;
    private layerActionIconMapping = {
        'prepend': 'low_priority',
        'remove': 'block',
        'replace': 'find_replace',
        'reparameterize': 'create' 
    }
    private handcraftedChanges = [];

    // @Prop({default: false})
    // public variations: boolean;

    private ablationType: string = 'Ablation';

    constructor() {
        super();
        this.$options.sockets = {
        }

    }

    get variations() {
        return this.ablationType === 'Variation';
    }

    get ablations() {
        return this.ablationType === 'Ablation';
    }

    get handcrafted() {
        return this.ablationType === 'Handcrafted';
    }

    get parentInspectionOptions() {
        return this.$store.state.parentInspectionOptions;
    }

    get resolution() { return this.$store.state.resolution; }
    get fixedWidth() { return this.$store.state.fixedWidth; }
    get maxSize() { return this.$store.state.maxWidth; }
    get logBase() { return this.$store.state.logBase; }

    get parentId() {
        if (this.inspectedModelData) {
            return this.inspectedModelData.parentId;
        }
    }

    get parentModelData() {
        if (this.parentId && window['searchableModels'][this.parentId]) {
            return this.dupedModel(window['searchableModels'][this.parentId])
        }
    }

    get valueAccessors() {
        return this.$store.state.valueAccessors;
    }


    get anySelection() {
        return this.selectedLayers().length > 0;
    }

    get term() {
        if (this.variations) {
            return 'Variations';
        } else {
            return 'Ablations';
        }
    }

    get generateButtonNeeded() {
        // return this.variations || !this.ablationsGenerated;
        return true;
    }
    public selectedLayers() {
    //     console.log("in selectedLayers, this.$refs.myNetworkChip is ", this.$refs.myNetworkChip)
        if (this.$refs.myNetworkChip) {
            return this.$refs.myNetworkChip.selectedLayers
        } else {
            return [];
        }
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

    get childIds() {
        return this.$store.state.modelTreeChildren[this.inspectedModelId] || [];
    }

    get children() {
        return this.childIds.map((id) => this.$store.state.modelArchitectures[id]).filter((x) => !!x);
    }

    get childAblationLayers() {
        return this.$store.state.modelTreeChildrenAblationLayers[this.inspectedModelId]
    }

    get childAblationLayerModels() {
        if (this.childAblationLayers) {
            return this.childAblationLayers.map((modelId) => modelId && this.$store.state.modelArchitectures[id] );
        } else {
            return [];
        }
    }

    get childAblationLayerAccuracies() {
        return this.childAblationLayerModels.map((model) => this.$store.state.valueAccessors['Val Acc'](model));
    }

    private clickedParent() {
        this.$store.commit('ADD_SELECTED_MODEL_ID', this.parentId);
    }

    private generateAblations() {
        this.ablationsGenerated = true;
        let layerInstructions = {};
        this.selectedLayers().forEach((l) => { layerInstructions[l] = { 'modify': true } })
        // Then, we filter out the ablations that are already done.
        console.log("sending generateAblations with instructions ", layerInstructions);        

        if (this.variations) {
            this.$socket.emit('generate_variations', { 
                'modelId': this.inspectedModelId,
                'instructions': this.variationOptions,
                'numEpochs': this.inspectedModelData.epochs,
                'numChanges': this.numChanges,
                // 'instructions': { 'selectedLayers': layerInstructions },
                'numModels': this.numGenerated
            });
        } else if (this.ablations) {
            this.$socket.emit('generate_ablations', { 
                'modelId': this.inspectedModelId,
                'instructions': { 'selectedLayers': layerInstructions },
                'numEpochs': this.inspectedModelData.epochs,
                'numModels': this.numGenerated
            });

        } else {
            // handcrafted
            this.$socket.emit('generate_handcrafted', {
                'modelId': this.inspectedModelId,
                'instructions': this.$refs.myNetworkChip.layersDataTemplate.layers,
                'numEpochs': this.inspectedModelData.epochs,
                'changes': this.$refs.myNetworkChip.changes
            })
        }
    }

    get variationOptions() {
        return this.$store.state.variationOptions[this.inspectedModelId]
    }

    private layerOptionsStyle(layerType) {
        return {
            background: this.COLOR_MAPPING.getColor(layerType)
        }
    }

    private clearSelection() {
        this.$refs.myNetworkChip.deselectAll();
    }

    private dupedModel(modelData) {
        return JSON.parse(JSON.stringify(modelData));
    }

    @Watch('inspectedModelId')
    private onInspectedModelIdChanged(newId, oldId) {
        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: this.getInitialVariationOptions()
        });
    }

    private onHandcraftChanges(newChanges) {
        this.handcraftedChanges = newChanges;
    }

    // private onSelectedLayersChanged(newLayers) {
    private onSelectedLayersChanged(newLayers) {
        const addedLayers = newLayers.addedLayers;
        const removedLayers = newLayers.removedLayers;
        let options = this.dupedModel(this.variationOptions);

        if (addedLayers.length > 0) {
            addedLayers.forEach((l) => {
                const regex = /layer-(\d+)-(\w)/g;
                const layerMatches = regex.exec(l);
                const layerNum = layerMatches[1];
                const layerType = layerMatches[2];
                options[layerNum]['selected'] = true;
                if (layerType === 'a') {
                    // we have a layer transition selection
                    options[layerNum]['variationTypes']['prepend']['selected'] = true
                } else {
                    // we have a layer selection
                    options[layerNum]['variationTypes']['prepend']['selected'] = true
                    options[layerNum]['variationTypes']['replace']['selected'] = true;
                    options[layerNum]['variationTypes']['remove']['selected'] = true;
                    options[layerNum]['variationTypes']['reparameterize']['selected'] = true;
                }
            });
        }
        
        if (removedLayers.length > 0) {
            removedLayers.forEach((l) => {
                const regex = /layer-(\d+)-(\w)/g;
                const layerMatches = regex.exec(l);
                const layerNum = layerMatches[1];
                const layerType = layerMatches[2];
                options[layerNum]['selected'] = false;
                if (layerType === 'a') {
                    // we have a layer transition selection
                    options[layerNum]['variationTypes']['prepend']['selected'] = false
                } else {
                    // we have a layer selection
                    options[layerNum]['variationTypes']['prepend']['selected'] = false
                    options[layerNum]['variationTypes']['replace']['selected'] = false;
                    options[layerNum]['variationTypes']['remove']['selected'] = false;
                    options[layerNum]['variationTypes']['reparameterize']['selected'] = false;
                }
            });
        }

        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: options
        });

        // this.selectedLayers = newLayers;
    }

    private getInitialVariationOptions() {
        let variationOptions = [];
        if (this.inspectedModelData) {
            this.inspectedModelData.layers.forEach((layer, idx) => {
                let layerData = {
                    idx: idx,
                    layerType: layer.type,
                    selected: false,
                    variationTypes: {
                        prepend: {
                            selected: false,
                            optionsMousedOver: false,
                            layerTypes: {}
                        },
                        remove: {
                            selected: false,
                            optionsMousedOver: false
                        },
                        replace: {
                            selected: false,
                            optionsMousedOver: false,
                            layerTypes: {}
                        },
                        reparameterize: {
                            selected: false,
                            optionsMousedOver: false,
                            layerParameters: {}
                        }
                    }
                }
                // Then, initialize layerParameters
                const types = ['prepend', 'replace'];
                // console.log("layerData is ", layerData)
                types.forEach((varType) => {
                    Object.keys(this.$store.state.layerOptions).forEach((option) => {
                        // console.log("layerData['variationTypes'][varType] is ", layerData['variationTypes'][varType])
                        layerData['variationTypes'][varType]['layerTypes'][option] = { selected: false, options: {}}
                        this.$store.state.layerOptions[option].forEach((param) => {
                            layerData['variationTypes'][varType]['layerTypes'][option]['options'][param] = {};
                            this.$store.state.hyperparameterOptions[param].forEach((paramVal) => {
                                layerData['variationTypes'][varType]['layerTypes'][option]['options'][param][paramVal] = {'selected': false};
                            })
                        })
                    })
                });

                // need to handle reparameterize differently
                variationOptions.push(layerData)
            })

        }
        // JSON.parse(JSON.stringify(this.$store.state.layerOptions))
        return variationOptions;
    }

    private toggleAction(idx, variationType) {
        let options = this.dupedModel(this.variationOptions);
        options[idx]['variationTypes'][variationType]['selected'] = !options[idx]['variationTypes'][variationType]['selected'];
        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: options
        });
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

    private validActionExpandRows(idx) {
        const currExpandedAction = this.getExpandedAction(idx);
        if (currExpandedAction) {
            // console.log("currExpandedAction is ", currExpandedAction, " and this.variationOptions[idx]['variationTypes'][currExpandedAction] is ", this.variationOptions[idx]['variationTypes'][currExpandedAction])
            return this.variationOptions[idx]['variationTypes'][currExpandedAction]['layerTypes']
        } else {
            return {};
        }
    }

    private getExpandedAction(idx) {
        const variationTypes = Object.keys(this.variationOptions[idx]['variationTypes'])
        const mousedOverTypes = variationTypes.filter((t) => {
            return this.variationOptions[idx]['variationTypes'][t]['optionsMousedOver'];
        })
        return mousedOverTypes[0];
    }

    private actionExpanded(idx, variationType) {
        return this.variationOptions[idx]['variationTypes'][variationType]['optionsMousedOver']; 
    }

    private showActionOptions(idx, variationType) {
        let options = this.dupedModel(this.variationOptions);
        options[idx]['variationTypes'][variationType]['optionsMousedOver'] = true;
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

    private hideActionOptions(idx, variationType) {
        let options = this.dupedModel(this.variationOptions);
        Object.keys(options[idx]['variationTypes']).forEach((type) => {
            options[idx]['variationTypes'][type]['optionsMousedOver'] = false;
        });
        this.$store.commit('SET_VARIATION_OPTIONS', {
            modelId: this.inspectedModelId,
            variationOpts: options
        });
    }

    private checkedActionsExpandedRows(args) {
        console.log("checkedActionsExpandedRows called with args ", args);
    }

    private restoreHandcraftedTemplate() {
        if ( confirm('Restore Template?') ) {
            // Update the backend
            // @ts-ignore
            this.$refs.myNetworkChip.restoreTemplate();
        }
    }

    @Watch('childIds')
    private onChildIdsChanged(newIds, oldIds) {
        // console.log("childIDs changed, forcing update to this stupid model drawer")
        if (this.$refs.modelDrawer) {
            this.$refs.modelDrawer.$forceUpdate();
        }
    }

    @Watch('ablationType')
    private onAblationTypeChanged(newType, oldType) {
        // this.$refs.myNetworkChip.selectedLayers = [];
    }
}

</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss' scoped>
// .network-chips-container {
//     // justify-content: start !important;
//     grid-column-start: 2;
//     grid-column-end: 3;
//     grid-row-start: 1;
//     grid-row-end: 2;
// }

.ablation-message {
    max-width: 500px
}

// .ablation-container {
//     display: grid;
//     grid-template-columns: 1fr 1fr;
// }
.ablation-container-row {
    width: 800px !important;
}

.ablation-number {
    color: green;
}

.layer-list {
    list-style: none;

    li {
        background: #d9d9d9;
        // border-radius: 7px;
        margin-bottom: 3px;
        position: relative;
        width: 440px;
        .layer-selectors {
            padding-left: 200px;
            display: flex;
        }
        .layer-label {
            position: absolute;
            top: 0;
            left: 0;
            color: white;
            font-weight: 700;
            padding: 2px;
        }

        .layer-options {
            padding: 4px;
            border-radius: 2px;
            display: inline-flex;
        }

        .layer-choices {
            visibility: none;
        }

        .option-icon, .dropdown-icon {
            cursor: pointer;
        }

        .dropdown-icon {
            margin-left: -2px;
        }

    }
}

.model-ablation-component {
    position: relative;

    .model-parent-floater {
        z-index: 1000;
        position: absolute;
        top: 10px;
        left: 10px;
        // width: 300px;
        // height: 150px;
        // border-top: 2px dotted lightgray;
        // border-bottom: 2px dotted lightgray;
        border: 2px dotted lightgray;
        padding: 10px;

        border-radius: 4px;
        
        .model-parent-chip {
            text-align: left;
        }
    }

    .model-ablation-control-floater {
        z-index: 1000;
        position: absolute;
        top: 10px;
        right: 20px;
        border: 2px dotted lightgray;
        padding: 10px;
        width: 200px;
        // height: 140px;

        border-radius: 4px;
    }
}

.v-menu__content {
    z-index: 8000000;
}
</style>


