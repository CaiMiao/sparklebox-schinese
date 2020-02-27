TL_ENABLED_TEXT = "<a href='javascript:;' onclick='tlinject_revert()'>禁用翻译</a> " +
                  "(<a href='javascript:;' onclick='tlinject_about()'>啥玩意？</a>)"
TL_DISABLED_TEXT = "<a href='javascript:;' onclick='tlinject_enable()'>启用翻译</a> " +
                   "(<a href='javascript:;' onclick='tlinject_about()'>啥东西？</a>)"
PROMPT_EXTRA_TEXT = "* 这些你提交的字串可能会被作为公共数据导出的一部分而被公开。 " +
                      "这些数据导出【并不会】包含任何能够识别你的信息。 " +
                      "如果你是手滑或者不同意，点取消。\n" +
                    "* 两个星号 '**' 将会移除当前的翻译。通常你并不需要这么做。"
TL_ENABLE_PREF_KEY = "sl$tlEnable"

gTLInjectEnabled = false;

if (!String.prototype.trim) {
    // polyfill from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/Trim
    String.prototype.trim = function() {
        return this.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
    };
}

function env_default_enable_tlinject() {
    var userLocale = navigator.languages? navigator.languages[0]
        : (navigator.language || navigator.userLanguage)
    
    // Default: disable if user language is Japanese, otherwise enable.
    if (userLocale.match(/ja([^A-Za-z]|$)/)) {
        return false
    }
    return true
}

function should_enable_tlinject() {
    var pref = localStorage.getItem(TL_ENABLE_PREF_KEY)
    if (pref === null || (pref !== "true" && pref !== "false")) {
        return env_default_enable_tlinject()
    }

    return pref === "true"? true : false
}

function load_translations(trans, cb) {
    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/api/v1/read_tl", true)
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
    xhr.setRequestHeader("X-Blessing",
        "This request bears the blessing of an Ascended Constituent of the Summer Triangle, granting it the entitlement of safe passage.")
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            returned_list = JSON.parse(xhr.responseText)
            cb(returned_list)
        }
    }
    xhr.send(JSON.stringify(trans))
}

function submit_tl_string(node, text) {
    if (!gTLInjectEnabled) {
        alert("请在提交前按左下角的按钮启用翻译。")
        return;
    }

    var sub = prompt("'" + text + "' 的翻译是啥？？？\n\n" +
        PROMPT_EXTRA_TEXT);

    if (sub === null) return;

    sub = sub.trim()
    if (sub == "") return;

    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/api/v1/send_tl", true)
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
    xhr.setRequestHeader("X-Blessing",
        "This request bears the blessing of an Ascended Constituent of the Summer Triangle, granting it the entitlement of safe passage.")
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var table = {}
                table[text] = sub;
                set_strings_by_table(table);
            } else {
                var j = JSON.parse(xhr.responseText);
                if (j.error) {
                    alert('Failed to submit translation. The server said: "' + j.error + '"');
                }
            }
        }
    }
    xhr.send(JSON.stringify({key: text, tled: sub, security: node.getAttribute("data-summertriangle-assr")}))
}

function set_strings_by_table(table) {
    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        var s = table[strings[i].getAttribute("data-original-string")];
        if (s === undefined) continue;

        strings[i].textContent = s == "**" ? strings[i].getAttribute("data-original-string") : s;
    }
}

function tlinject_activate() {
    var tls = []
    var strings = document.getElementsByClassName("tlable")
    if (strings.length == 0) return;

    for (var i = 0; i < strings.length; i++) {
        if (tls.indexOf(strings[i].textContent) == -1)
            tls.push(strings[i].textContent);

        if (!strings[i].hasAttribute("data-original-string"))
            strings[i].setAttribute("data-original-string", strings[i].textContent);

        if (strings[i].hasAttribute("data-summertriangle-assr"))
            strings[i].setAttribute("onclick", "event.preventDefault(); submit_tl_string(this, this.getAttribute('data-original-string'))")
    }

    if (!should_enable_tlinject()) {
        gTLInjectEnabled = false
        tli_get_banner().innerHTML = TL_DISABLED_TEXT;
        return;
    }

    gTLInjectEnabled = true
    load_translations(tls, function(tls2) {
        for (var i = 0; i < strings.length; i++) {
            strings[i].textContent = tls2[strings[i].textContent] || strings[i].textContent;
        }
        tli_get_banner().innerHTML = TL_ENABLED_TEXT;
    })
}

function tli_get_banner() {
    var node = document.body.querySelector(".crowd_tl_notice");
    if (!node) {
        node = document.createElement("div");
        node.className = "crowd_tl_notice";
        document.body.insertBefore(node, document.body.childNodes[0]);
    }
    return node
}

function tlinject_revert() {
    localStorage.setItem(TL_ENABLE_PREF_KEY, "false")
    gTLInjectEnabled = false

    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        strings[i].textContent = strings[i].getAttribute("data-original-string");
    }
    tli_get_banner().innerHTML = TL_DISABLED_TEXT;
}

function tlinject_enable() {
    localStorage.setItem(TL_ENABLE_PREF_KEY, "true")
    tlinject_activate()
}

function tlinject_about() {
    var banner = "此站使用众包翻译。如果有句子在你悬停在上面时高亮显示，你可以点击并提交翻译。";
    alert(banner);
}
