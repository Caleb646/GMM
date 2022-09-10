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

window.onload = (e) => {
    trHoverHideFilter();
    let shiftedNavBar = document.getElementById("main");
    shiftedNavBar.className = "main";
}