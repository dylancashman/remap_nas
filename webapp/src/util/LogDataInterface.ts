export enum ColumnType {
    string = 'string',
    number = 'number',
    performance = 'performance',
    model = 'model',
    empty = 'empty',
    lnumber = 'lnumber',
    select = 'select',
    number3 = 'number3',
    running = 'running'
}

export interface TableColumn { name: string; type: ColumnType; value: (d: any) => any; compare?: (d: any) => number; }
export interface TableDatum { id: string; [key: string]: any; }
export interface TableRow { forwardTime: number;
                             backwardTime: number;
                             id: string;
                             iters: number[];
                             loss: number[];
                             memory: number;
                             model: any;
                             params: number;
                             running: boolean;
                             trainAccs: number[];
                             valAccs: number[];
                             }

export default interface LogDataInterface {

    /**
     * list of all project IDs
     * @return {string[]}
     */
    projects(): string[];

    /**
     * table columns for given project
     * @param {string} projectID
     * @return {TableColumn[]}
     */
    tableColumns(projectID: string): TableColumn[];

    /**
     * current table data for project
     * @param {string} projectID
     * @return {TableDatum[]}
     */
    getTableData(projectID: string): TableDatum[];

    /**
     * ???
     * @param {string} projectID
     * @param {string[]} ids
     * @return {any}
     */
    details(projectID: string, ids: string[]): any;

}
