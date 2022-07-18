function api_request(url, method = "GET") {
    fetch(url, {
        method: method
    }).then(response => {
        if(!response.ok) {
            alert(response.statusText);
        }
        location.reload();
        //alert(response.status);
        return response;

        }).catch(error => {
            alert(error);
            return error;
        }); 
};

const api_endpoints = {
    attachment_download: (message_id, attachment_id) => `/api/message/${message_id}/attachment/${attachment_id}/download/`,
    settings: (key) => `/api/settings/?key=${key}`,
};

function toggle_class(element, original, toggle_to) {
    if (element.classList.contains(original)) {
        // expand table
        element.classList.remove(original);
        element.classList.add(toggle_to);
        return false; // did not return to original class
    }
    else {
        // collapse table
        element.classList.remove(toggle_to);
        element.classList.add(original);
        return true;  // returned to original class
    }
};

async function get_messages(url, id_tag, gmail_thread_id)
{
    let hidden_table = document.getElementById(id_tag);
    let returned_to_original = toggle_class(hidden_table, "collapse", "collapsed");
    if (returned_to_original) return; //do not want make an api call when the table is being collapsed
    
    let TIMEZONE = await fetch(api_endpoints.settings("DEFAULT_TIMEZONE")).then(response => response.json());
    TIMEZONE = TIMEZONE.data;

    let data = await fetch(url).then(response => response.json());
    let messages = JSON.parse(data.data.messages);
    let attachments = JSON.parse(data.data.attachments);
    console.log(messages, attachments);

    let table = "";
    for(let entry in messages)
    {
        entry = messages[entry];
        console.log(entry);
        attachments_links = ""

        for(let attachment in attachments) {
            attachment = attachments[attachment]
            if(attachment.fields.message_id == entry.pk) {
                attachments_links += `
                    <a href="${api_endpoints.attachment_download(entry.fields.message_id, attachment.fields.gmail_attachment_id)}" class="card-link" download>${attachment.fields.filename}</a>
                ` 
            }
        }
        table += `
        <div class="row bg-dark text-white p-2 m-2">
            <div class="card bg-dark text-white" style="">
                <div class="card-body text-white">
                    <h6 class="card-subtitle mb-2 text-muted">From: ${entry.fields.fromm}</h6>
                    <h6 class="card-subtitle mb-2 ">To: ${entry.fields.to}</h6>
                    <h6 class="card-subtitle mb-2 ">Cc: ${entry.fields.cc}</h6>
                    <h6 class="card-subtitle mb-2 text-muted">Received: ${new Date(entry.fields.time_received).toLocaleString("en-US", {timeZone : TIMEZONE})} ${TIMEZONE}</h6>
                    <pre style="white-space: pre-wrap;" class="card-text" id="my_message_${entry.pk}">${ entry.fields.debug_unparsed_body }</pre>
                    ${attachments_links}
                </div>
            </div>
        </div>
        `;
    }
    hidden_table.innerHTML = table;
    choose_text_to_mark();
}

function mark_text(element, regex)
{
    let instance = new Mark(element);
    instance.markRegExp(regex);
};

function choose_text_to_mark()
{
    const match_message_id = new RegExp('my_message_*');
    const email_address_pattern = '([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'
    // match message text on From: email address and email address wrote:
    // "m" makes RegExp treat the whole line as a string
    const start_of_new_email = new RegExp(`From:.*(${email_address_pattern}|[a-zA-Z])|^.*${email_address_pattern}? wrote:`, "m");
    for (let i of document.querySelectorAll('*')) {
        if(match_message_id.test(i.id)) {
            //console.log(i);
            mark_text(i, start_of_new_email);
        }     
    }
}

window.onload = (event) => {
    choose_text_to_mark();
};

