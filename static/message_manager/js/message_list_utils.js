function trHoverHideFilter() {
    // only to effect the rows inside of the results div
    let trs = document.querySelector(".results").querySelectorAll("tr");

    let filter = document.getElementById("changelist-filter");
    let filterDisplay;
    for(let t in trs) {
        
        if(!(trs[t] instanceof HTMLElement)) continue;
        trs[t].addEventListener("mouseover", () => {
            filterDisplay = filter.style.display;
            filter.style.display = "none"
            //console.log("listening");
        })

        trs[t].addEventListener("mouseout", () => {
            filter.style.display = filterDisplay;
            //console.log("listening");
        })
    }
}

function removeElements(elementsToRemove) {
    for(let e of elementsToRemove) {
        e.remove();
    }
}

function findRowIndexByColumnName(tableID, columnName) {
    let table = document.getElementById(tableID);
    let regex = new RegExp(`.*${columnName}.*`, 'is');
    for(let row of table.rows) {
        for(let i = 0; i < row.cells.length; i++) {
            let cell = row.cells[i];
            if(regex.test(cell.className)) {
                return i;
            }
        }
    }
    // NOTE: columnName MUST always be found.
    console.assert(false, `Column Name: ${columnName} was not found in table with ID: ${tableID}`);
    return Infinity;
}

function removeTableColumns(tableID, columnCellNumsToRemove) {
    /*
    * Summary. Takes in a table id and list of cells to remove from that tables rows. It then removes them.
    * @param {string} tableID Is the HTML id of the table element
    * @param {list} columnCellNumsToRemove A list of cell indices to be removed from each row. Should be ordered [largest...smallest]  
    */
    let table = document.getElementById(tableID);
    columnCellNumsToRemove.sort().reverse(); // should be in descending order
    console.assert(columnCellNumsToRemove[-1] != -1, `A Column index in columnCellNumsToRemove cannot be -1: ${columnCellNumsToRemove}`);
    let maxIndex = Math.max(...columnCellNumsToRemove);
    for(let row of table.rows) {
        if(maxIndex < row.cells.length) {
            for(let cellNum of columnCellNumsToRemove) {
                row.deleteCell(cellNum);
            } 
        }
        else {
            console.warn(`Max index of ${maxIndex} was larger than cells array ${row.cells.length}`);
        }
    }
}

function addElementsToElement(mainElement, elementsToAdd) {
    for(let e of elementsToAdd) {
        mainElement.innerHTML += e.outerHTML;
    }
}

function stackMessageListColumns(mainColumn, columnsToAdd, columnCellNumsToDelete) {
    /*
    * Summary. In the changelist view there are some columns that can be stacked into a single column. The columns named in 
    * columnsToAdd are stacked in the mainColumn's column. Then the cell ids in columnCellNumsToDelete are used to remove those
    * cells from each row.
    * 
    * @Note If the order changes in the Admin Class in Django the cell ids in columnCellNumsToDelete will have to be changed.
    * @param {string} mainColumn The Django Model Field Name of the column that the other columns will be merged into.
    * @param {list} columnsToAdd A list of Django Model Field Names that will be merged into the mainColumn's column.
    * @param {list} columnCellNumsToDelete A list of cell indices to be removed from each row. Should be ordered [largest...smallest]  
    */
    for(let i = 0; i < 1000; i++) {
        let elementsToAdd = [];
        let prefix = `id_form-${i}-`;
        let mainElement = document.getElementById(prefix + mainColumn);
        if(!mainElement) break;
        mainElement = mainElement.parentElement.parentElement;
        for(let colSuffix of columnsToAdd) {
            let e = document.getElementById(prefix + colSuffix);
            if(e && e.parentElement) {
                elementsToAdd.push(e.parentElement);
            }
                
        }
        addElementsToElement(mainElement, elementsToAdd);
    }
    removeTableColumns("result_list", columnCellNumsToDelete);
}

window.onload = (e) => {
    console.log("LOADING");
    //trHoverHideFilter();
    let shiftedNavBar = document.getElementById("main");
    shiftedNavBar.className = "main";

    let jobElementID = "job_id";
    let columnsToAddToJobID = ["thread_group", "thread_topic", "thread_type"];//, "thread_status"];
    // NOTE need to be in reverse order so when the cell are deleted the next index will still be valid.
    // NOTE if the order in the Django Admin changes these indices will have to be adjusted.
    let threadGroupIndex = findRowIndexByColumnName("result_list", "thread_group");
    let threadTopicIndex = findRowIndexByColumnName("result_list", "thread_topic");
    let threadTypeIndex = findRowIndexByColumnName("result_list", "thread_type");
    let columnCellNumsToDelete = [threadGroupIndex, threadTopicIndex, threadTypeIndex];
    stackMessageListColumns(jobElementID, columnsToAddToJobID, columnCellNumsToDelete);
}