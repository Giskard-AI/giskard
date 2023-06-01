(function () {
    // HighlightJS
    hljs.addPlugin(new CopyButtonPlugin());
    hljs.highlightAll();

    // Tabs
    let rows = document.querySelectorAll("#gsk-scan .gsk-issue")
    rows.forEach(rowEl => {
        {
            rowEl.addEventListener("click", (event) => {
                {
                    event.preventDefault()
                    if (event.target.classList.contains("gsk-debug")) {
                        {
                            alert("Not implemented yet")
                            return;
                        }
                    }

                    rowEl.classList.toggle("open")
                    rowEl.classList.toggle("bg-zinc-700")
                }
            })
        }
    });

    const tabs = document.querySelectorAll("#gsk-scan [role='tabpanel']")
    const tabHeaders = document.querySelectorAll("#gsk-scan [data-tab-target]")
    tabHeaders.forEach(tabHeader => {
        tabHeader.addEventListener("click", (event) => {
            event.preventDefault()
            const tabId = tabHeader.getAttribute("data-tab-target")

            tabs.forEach(tab => {
                tab.classList.add("hidden")
            })
            tabHeaders.forEach(tabh => {
                tabh.classList.remove("active")
            })

            tabHeader.classList.add("active")
            console.log(tabId)
            document.getElementById(tabId).classList.remove("hidden")

        })
    })
})()