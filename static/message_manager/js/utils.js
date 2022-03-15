

function api_request(url, method = "GET") {
    fetch(url, {
        method: method
    }).then(response => {
        if(!response.ok) {
            alert(response.statusText);
        }
        location.reload();
        return response;

        }).catch(error => {
            alert(error);
            return error;
        }); 
};

async function get_messages(url, id_tag, gmail_thread_id)
{
    var hidden_table = document.getElementById(id_tag);
    if (hidden_table.classList.contains("collapse")) {
        //expand table
        hidden_table.classList.remove("collapse");
        hidden_table.classList.add("collapsed");
    }
    else {
        //collapse table
        hidden_table.classList.remove("collapsed");
        hidden_table.classList.add("collapse");
        return; //do not want make an api call when the table is being collapsed
    }

    let data = await fetch(url).then(response => response.json());
    data = JSON.parse(data.data);
    console.log(data);

    let table = "";
    for(let entry in data)
    {
        entry = data[entry];
        console.log(entry);
        table += `
        <div class="row bg-dark text-white p-2 m-2">
            <div class="card bg-dark text-white" style="">
                <div class="card-body text-white">
                    <h6 class="card-subtitle mb-2 text-muted">From: ${entry.fields.fromm}</h6>
                    <h6 class="card-subtitle mb-2 ">To: ${entry.fields.to}</h6>
                    <h6 class="card-subtitle mb-2 ">Cc: ${entry.fields.cc}</h6>
                    <h6 class="card-subtitle mb-2 text-muted">Received: ${new Date(entry.fields.time_received).toLocaleString("en-US", {timeZone : "America/New_York"})} US/Eastern</h6>
                    <p class="card-text lead">${entry.fields.body}</p>
                </div>
            </div>
        </div>
        `;
    }

    hidden_table.innerHTML = table;
}